# agents/nodes/execute_node.py
# Executes SQL with self-correction logic

from agents.state import AgentState
from data.database import get_db


def execute_node(state: AgentState) -> AgentState:
    try:
        sql = state.get("generated_sql", "")
        session_id = state.get("session_id", "default")

        # If no SQL was generated, treat as sql_failed so retry logic kicks in
        if not sql:
            state["error"] = "No SQL to execute"
            state["status"] = "sql_failed"
            return state

        db = get_db(session_id)
        result = db.execute_query(sql)

        if result.empty:
            state["sql_result"] = result
            state["final_answer"] = (
                "Query ran but returned no results. "
                "Try a different question."
            )
            state["status"] = "complete"
            state["error"] = ""
        else:
            state["sql_result"] = result
            state["status"] = "executed"
            state["error"] = ""

        return state

    except Exception as e:
        state["error"] = str(e)
        state["status"] = "sql_failed"
        return state


def should_retry(state: AgentState) -> str:
    """LangGraph conditional edge with proper retry limit."""
    status = state.get("status", "")
    retry_count = state.get("retry_count", 0)
    MAX_RETRIES = 2

    # Failed → retry up to MAX_RETRIES times
    if status == "sql_failed" and retry_count < MAX_RETRIES:
        state["retry_count"] = retry_count + 1
        print(f"[GRAPH DEBUG] Retry #{state['retry_count']} → fix_sql")
        return "fix_sql"

    # Failed too many times → give up, route to output for graceful error
    if status == "sql_failed":
        print(f"[GRAPH DEBUG] Max retries ({MAX_RETRIES}) reached → output")
        state["error"] = (
            "Could not generate a working SQL query after 2 attempts. "
            "Please try rephrasing your question."
        )
        state["status"] = "complete"
        return "output"

    # SQL executed successfully → chart
    if status == "executed":
        return "chart"

    # Empty result / complete → output
    if status == "complete":
        return "output"

    # Default fallback
    return "output"