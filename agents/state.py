# agents/state.py
# LangGraph state — data that flows between all nodes

from typing import TypedDict, Optional, Any


class AgentState(TypedDict):
    # Input
    user_question: str
    session_id: str
    language: str

    # Data
    raw_df: Optional[Any]
    clean_df: Optional[Any]
    schema: str
    pkr_columns: list

    # SQL
    generated_sql: str
    sql_result: Optional[Any]
    retry_count: int

    # Output
    chart_data: Optional[Any]
    final_answer: str
    cleaning_report: list

    # Status
    error: str
    status: str