# agents/nodes/upload_node.py
# Handles file upload and cleaning in pipeline

from agents.state import AgentState
from data.validator import FileValidator
from data.cleaner import DataCleaner
from data.database import get_db


def upload_node(state: AgentState) -> AgentState:
    try:
        uploaded_file = state.get("uploaded_file")
        session_id = state.get("session_id", "default")

        if uploaded_file is None:
            state["error"] = "No file provided"
            state["status"] = "error"
            return state

        validator = FileValidator()
        result = validator.validate(uploaded_file)

        if not result['success']:
            state["error"] = " | ".join(result['errors'])
            state["status"] = "error"
            return state

        cleaner = DataCleaner()
        clean_df, report = cleaner.clean(result['dataframe'])

        db = get_db(session_id)
        success = db.load_dataframe(clean_df)

        if not success:
            state["error"] = "Failed to load to database"
            state["status"] = "error"
            return state

        state["raw_df"] = result['dataframe']
        state["clean_df"] = clean_df
        state["schema"] = db.get_schema()
        state["pkr_columns"] = cleaner.pkr_columns
        state["cleaning_report"] = report
        state["status"] = "uploaded"
        return state

    except Exception as e:
        state["error"] = f"Upload failed: {str(e)}"
        state["status"] = "error"
        return state


def clean_node(state: AgentState) -> AgentState:
    try:
        raw_df = state.get("raw_df")
        if raw_df is None:
            state["error"] = "No data to clean"
            state["status"] = "error"
            return state

        cleaner = DataCleaner()
        clean_df, report = cleaner.clean(raw_df)

        state["clean_df"] = clean_df
        state["cleaning_report"] = report
        state["pkr_columns"] = cleaner.pkr_columns
        state["status"] = "cleaned"
        return state

    except Exception as e:
        state["error"] = f"Cleaning failed: {str(e)}"
        state["status"] = "error"
        return state