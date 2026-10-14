# agents/nodes/sql_node.py
# Generates SQL using OpenRouter (openrouter/auto)

import os
from openai import OpenAI
from agents.state import AgentState
from security.sql_guard import SQLGuard
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

MODEL = "openrouter/auto"
guard = SQLGuard()


# ============================================
# Gibberish Detection (stricter version — Issue #12 fix)
# ============================================
def _looks_like_gibberish(text: str) -> bool:
    """
    Return True ONLY if the question truly looks like keyboard smash.
    Stricter than before to avoid false positives on real questions.
    """
    if not text:
        return True

    clean = text.strip().lower()
    # Remove digits and punctuation for analysis
    stripped = "".join(c for c in clean if c.isalpha())

    if len(stripped) < 4:
        return False  # too short to judge

    # Rule 1: 6+ consecutive consonants WITHIN a single word
    consonants = "bcdfghjklmnpqrstvwxyz"
    for word in clean.split():
        word_alpha = "".join(c for c in word if c.isalpha())
        run = 0
        for ch in word_alpha:
            if ch in consonants:
                run += 1
                if run >= 6:
                    return True
            else:
                run = 0

    # Rule 2: extremely low vowel ratio (only if text is long)
    vowels = sum(1 for c in stripped if c in "aeiou")
    vowel_ratio = vowels / len(stripped)
    if vowel_ratio < 0.12 and len(stripped) >= 8:
        return True

    # Rule 3: keyboard patterns making up most of the string
    keyboard_patterns = [
        "asdf", "sdfg", "dfgh", "fghj", "ghjk",
        "qwer", "wert", "erty", "rtyu", "tyui",
        "zxcv", "xcvb", "cvbn", "vbnm", "hjkl",
    ]
    for pat in keyboard_patterns:
        if pat in stripped and (len(pat) / len(stripped)) > 0.4:
            return True

    # Rule 4: single long word with very few vowels (e.g. "xyzqwk")
    words = [w for w in clean.split() if w.isalpha()]
    if len(words) == 1 and len(words[0]) >= 5:
        w = words[0]
        w_vowels = sum(1 for c in w if c in "aeiou")
        if w_vowels / len(w) < 0.2:
            return True

    return False


def _clean_sql(text: str) -> str:
    """Strip markdown, backticks, and extra lines from AI response."""
    if not text:
        return ""
    sql = text.strip()
    sql = sql.replace("```sql", "").replace("```SQL", "").replace("```", "")
    sql = sql.strip()
    # Take only the first statement (up to first semicolon or first blank line)
    for sep in ["\n\n", ";"]:
        if sep in sql:
            sql = sql.split(sep)[0]
    sql = sql.strip()
    # Remove any leading labels like "SQL:" or "Query:"
    for label in ["SQL:", "Query:", "sql:", "query:"]:
        if sql.startswith(label):
            sql = sql[len(label):].strip()
    return sql


def sql_gen_node(state: AgentState) -> AgentState:
    try:
        schema = state.get("schema", "")
        question = state.get("user_question", "")

        # --- Gibberish check (early exit) ---
        if _looks_like_gibberish(question):
            print(f"[SQL DEBUG] Gibberish detected: {question!r}")
            state["error"] = (
                "I didn't quite catch that question. "
                "It looks like a keyboard slip! Please ask a clear "
                "question about your data, e.g. "
                "'What is the total revenue?'"
            )
            state["status"] = "error"
            state["generated_sql"] = ""
            return state

        # Check API key exists
        api_key = os.getenv("OPENROUTER_API_KEY", "")
        if not api_key or api_key == "your_openrouter_key_here":
            state["error"] = (
                "OpenRouter API key not set! "
                "Please add your key to .env file"
            )
            state["status"] = "error"
            return state

        # IMPROVED PROMPT with strict LIMIT rules (Issue #13 fix)
        prompt = f"""You are an expert SQLite query generator.

DATABASE SCHEMA:
{schema}

USER QUESTION: {question}

STRICT RULES:
1. Generate a single valid SELECT query for SQLite.
2. Use ONLY the exact column names and table name from the schema above.
3. Never use DROP, DELETE, INSERT, UPDATE, ALTER, or CREATE.
4. Always end with LIMIT 1000 unless the user asks for a specific number.
5. Use LIMIT N ONLY when the user explicitly says a number ("top 5", "first 10").
6. If the question asks "which [X] is highest/most popular/most" WITHOUT a number,
   return the FULL grouped list sorted DESC with LIMIT 1000.
   Do NOT add LIMIT 1 for "which" questions.
7. If the question asks for "top N" or "first N", use ORDER BY ... LIMIT N.
8. If the question is unclear, make the best possible SQL guess using available columns.
9. Return ONLY the raw SQL. No markdown, no backticks, no explanation, no comments.
10. NEVER return an empty response. You MUST return a SQL query.

Examples:
- "Which payment method is most popular?" → SELECT paymentmethod, COUNT(*) AS order_count FROM data GROUP BY paymentmethod ORDER BY order_count DESC LIMIT 1000;
- "Top 5 customers by revenue" → SELECT customername, SUM(quantity * unitprice_pkr) AS total_sales FROM data GROUP BY customername ORDER BY total_sales DESC LIMIT 5;
- "What is the total revenue?" → SELECT SUM(quantity * unitprice_pkr) AS total_revenue FROM data LIMIT 1000;

SQL:"""

        # --- First attempt ---
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a SQLite query generator. "
                        "Return only valid SQLite SELECT queries. "
                        "Never return empty. Never explain."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.1
        )

        raw_sql = _clean_sql(response.choices[0].message.content)
        print(f"[SQL DEBUG] First attempt SQL: {raw_sql!r}")

        # --- Retry once if empty or too short ---
        if not raw_sql or len(raw_sql) < 10:
            print("[SQL DEBUG] Empty response detected, retrying...")
            retry_response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a SQLite query generator. "
                            "You MUST return only a valid SELECT statement. "
                            "Never return empty. Never explain."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt + "\n\nREMINDER: Return SQL only. Never empty."
                    }
                ],
                max_tokens=300,
                temperature=0.0
            )
            raw_sql = _clean_sql(retry_response.choices[0].message.content)
            print(f"[SQL DEBUG] Retry SQL: {raw_sql!r}")

        # --- Final empty check ---
        if not raw_sql or len(raw_sql) < 10:
            state["error"] = (
                "The AI could not generate SQL for this question. "
                "Please try rephrasing, e.g. 'Show first 10 rows sorted by quantity'."
            )
            state["status"] = "error"
            return state

        # --- Validate with SQLGuard ---
        is_safe, result = guard.validate(raw_sql)

        if is_safe:
            state["generated_sql"] = result
            state["status"] = "sql_ready"
        else:
            state["error"] = f"Unsafe SQL: {result}"
            state["status"] = "error"

        return state

    except Exception as e:
        print(f"[SQL ERROR] {str(e)}")
        state["error"] = f"SQL generation failed: {str(e)}"
        state["status"] = "error"
        return state