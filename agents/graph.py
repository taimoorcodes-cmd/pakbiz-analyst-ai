# agents/graph.py
# Complete LangGraph workflow with early exit for errors

from langgraph.graph import StateGraph, END
from agents.state import AgentState
from agents.nodes.sql_node import sql_gen_node
from agents.nodes.execute_node import execute_node, should_retry
from agents.nodes.chart_node import chart_node
from agents.nodes.output_node import output_node


def sql_fix_node(state: AgentState) -> AgentState:
    """Resets state so sql_gen_node can try again."""
    print("[GRAPH DEBUG] sql_fix_node clearing error, retrying...")
    state["error"] = ""
    state["status"] = ""
    state["generated_sql"] = ""
    return state


def should_execute(state: AgentState) -> str:
    """
    After generate_sql, decide whether to execute or skip to output.
    Skip execute if:
      - status is 'error' (gibberish, API key missing, etc.)
      - or there's an error AND no SQL was generated
      - or no SQL was generated at all
    """
    status = state.get("status", "")
    error = state.get("error", "")
    sql = state.get("generated_sql", "")

    # Any error state → skip to output
    if status == "error" or (error and not sql):
        preview = (error or "")[:80]
        print(f"[GRAPH DEBUG] Skipping execute — status={status!r}, error={preview!r}")
        return "output"

    # No SQL generated → also skip
    if not sql:
        print("[GRAPH DEBUG] No SQL generated, skipping execute")
        return "output"

    # Valid SQL ready → execute
    print(f"[GRAPH DEBUG] SQL ready, executing: {sql[:80]!r}")
    return "execute"


def build_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("generate_sql", sql_gen_node)
    workflow.add_node("execute", execute_node)
    workflow.add_node("fix_sql", sql_fix_node)
    workflow.add_node("chart", chart_node)
    workflow.add_node("output", output_node)

    workflow.set_entry_point("generate_sql")

    # After SQL generation, conditionally execute or skip to output
    workflow.add_conditional_edges(
        "generate_sql",
        should_execute,
        {
            "execute": "execute",
            "output": "output"
        }
    )

    workflow.add_conditional_edges(
        "execute",
        should_retry,
        {
            "fix_sql": "fix_sql",
            "chart": "chart",
            "output": "output"
        }
    )

    # After fix, try generating again
    workflow.add_edge("fix_sql", "generate_sql")

    workflow.add_edge("chart", "output")
    workflow.add_edge("output", END)

    return workflow.compile()


def run_agent(
    question: str,
    schema: str,
    session_id: str,
    pkr_columns: list = None,
    language: str = "en"
) -> AgentState:

    graph = build_graph()

    initial_state: AgentState = {
        "user_question": question,
        "session_id": session_id,
        "language": language,
        "schema": schema,
        "pkr_columns": pkr_columns or [],
        "raw_df": None,
        "clean_df": None,
        "generated_sql": "",
        "sql_result": None,
        "retry_count": 0,
        "chart_data": None,
        "final_answer": "",
        "cleaning_report": [],
        "error": "",
        "status": "started"
    }

    return graph.invoke(initial_state)