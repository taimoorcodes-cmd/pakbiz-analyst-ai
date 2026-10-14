# agents/nodes/output_node.py
# Generates final human-readable answer via OpenRouter

import os
from openai import OpenAI
from agents.state import AgentState
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

MODEL = "openrouter/auto"


def _complete_sentences(text: str) -> str:
    """
    If the text ends mid-sentence (no ., !, ? or newline),
    trim it back to the last complete sentence.
    """
    if not text:
        return text
    stripped = text.rstrip()
    if not stripped:
        return text
    # If it already ends properly, return as-is
    if stripped[-1] in ".!?\"'`)]":
        return stripped
    # Otherwise, cut back to last sentence-ending punctuation
    for i in range(len(stripped) - 1, -1, -1):
        if stripped[i] in ".!?":
            return stripped[:i + 1]
    # Fallback: no punctuation found, return as-is
    return stripped


def _fallback_answer(sql_result, pkr_cols) -> str:
    """Simple template answer if AI fails completely."""
    if sql_result is None or sql_result.empty:
        return "Query ran but returned no results."

    cols = sql_result.columns.tolist()
    first_row = sql_result.iloc[0]

    # Single value case
    if len(sql_result) == 1:
        val = first_row.iloc[-1]
        label = cols[-1].replace("_", " ").title()
        try:
            if isinstance(val, (int, float)):
                if cols[-1] in pkr_cols:
                    return f"Your {label} is Rs {val:,.0f}."
                return f"Your {label} is {val:,.0f}."
        except Exception:
            pass
        return f"Your {label} is {val}."

    # Multi-row case
    return (
        f"Found {len(sql_result)} results. "
        f"See chart and table below for details."
    )


def output_node(state: AgentState) -> AgentState:
    try:
        question = state.get("user_question", "")
        sql_result = state.get("sql_result")
        language = state.get("language", "en")
        pkr_cols = state.get("pkr_columns", [])
        error = state.get("error", "")

        # Error case
        if error and sql_result is None:
            state["final_answer"] = (
                f"Could not answer your question.\n"
                f"Reason: {error}\n\n"
                "Please try rephrasing."
            )
            state["status"] = "complete"
            return state

        # Prepare result string — show more rows so AI knows total count
        if sql_result is not None and not sql_result.empty:
            row_count = len(sql_result)
            preview_count = min(row_count, 20)
            result_str = sql_result.head(preview_count).to_string()
        else:
            result_str = "No results"
            row_count = 0
            preview_count = 0

        lang_instruction = (
            "Respond in simple Roman Urdu."
            if language == "ur"
            else "Respond in clear English."
        )

        prompt = f"""You are a friendly data analyst for Pakistani small businesses.

User Question: {question}

Query Results ({row_count} rows total, showing first {preview_count}):
{result_str}

PKR currency columns: {pkr_cols}

Instructions:
1. {lang_instruction}
2. Give a clear friendly summary
3. Mention specific numbers
4. Format PKR values as Rs X,XXX
5. Give 1-2 actionable business insights
6. Keep under 150 words
7. Use simple language
8. End with a complete sentence. Do not stop mid-sentence.
9. If the total row count is more than what you can see, mention "showing top {preview_count} of {row_count}" when listing results.
10. Do NOT say "the list includes X customers" unless the total count is small. Use the row_count value."""

        # --- First attempt ---
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Friendly data analyst for "
                        "Pakistani small businesses. "
                        "Always finish your sentences completely. "
                        "Be accurate about row counts."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,
            temperature=0.7
        )

        raw_answer = response.choices[0].message.content.strip()
        print(f"[OUTPUT DEBUG] First attempt length: {len(raw_answer)}")

        # --- Retry once if answer is empty or too short ---
        if not raw_answer or len(raw_answer) < 30:
            print("[OUTPUT DEBUG] Response too short, retrying...")
            retry_response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Friendly data analyst. "
                            "Write a complete 2-3 sentence summary. "
                            "Never leave the response empty. "
                            "Be accurate about row counts."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt + "\n\nREMINDER: Respond fully. Do not truncate."
                    }
                ],
                max_tokens=800,
                temperature=0.5
            )
            raw_answer = retry_response.choices[0].message.content.strip()
            print(f"[OUTPUT DEBUG] Retry length: {len(raw_answer)}")

        # --- Final empty check → use fallback template ---
        if not raw_answer or len(raw_answer) < 20:
            print("[OUTPUT DEBUG] Using fallback template answer.")
            raw_answer = _fallback_answer(sql_result, pkr_cols)

        # --- Trim to last complete sentence (no mid-word cutoff) ---
        raw_answer = _complete_sentences(raw_answer)

        state["final_answer"] = raw_answer
        state["status"] = "complete"
        return state

    except Exception as e:
        print(f"[OUTPUT ERROR] {str(e)}")
        # Graceful fallback on any exception
        state["final_answer"] = _fallback_answer(
            state.get("sql_result"),
            state.get("pkr_columns", [])
        )
        state["status"] = "complete"
        return state