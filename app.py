# app.py
# PakBiz AI Analyst — Main Streamlit App
# OpenRouter + LangGraph + SQLite
# Theme: Navy Blue + Cyan

import streamlit as st
import pandas as pd
import uuid
import os
from dotenv import load_dotenv

load_dotenv()

from data.validator import FileValidator
from data.cleaner import DataCleaner
from data.database import get_db
from security.input_sanitizer import InputSanitizer
from agents.graph import run_agent
from utils.formatters import format_pkr
from utils.report_gen import (
    generate_pdf_report, dataframe_to_excel)

# ============================================
# PAGE CONFIG
# ============================================
st.set_page_config(
    page_title="PakBiz AI Analyst",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# CUSTOM CSS — Navy + Cyan Professional Theme
# ============================================
st.markdown("""
<style>
/* ---- Global background: Navy gradient ---- */
.stApp {
    background: linear-gradient(135deg, #0a1929 0%, #0f2942 50%, #0a1929 100%);
    color: #e2e8f0;
}

/* ---- Main title with cyan gradient ---- */
.main-title {
    font-size: 2.4rem;
    font-weight: 800;
    background: linear-gradient(90deg, #06b6d4 0%, #3b82f6 50%, #8b5cf6 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-align: center;
    padding: 1rem 0 0.2rem 0;
    letter-spacing: 0.5px;
}

.subtitle {
    text-align: center;
    color: #94a3b8;
    margin-bottom: 1.5rem;
    font-size: 1rem;
}

/* ---- Answer box ---- */
.answer-box {
    background: #0f2942;
    border: 1px solid #1e3a5f;
    border-left: 4px solid #10b981;
    border-radius: 10px;
    padding: 1.2rem;
    margin: 0.8rem 0;
    color: #e2e8f0;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

/* ---- Question box ---- */
.question-box {
    background: #0f2942;
    border-left: 4px solid #06b6d4;
    padding: 0.8rem 1rem;
    border-radius: 0 8px 8px 0;
    margin: 0.5rem 0;
    color: #e2e8f0;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

/* ---- Metric cards ---- */
.metric-card {
    background: #0f2942;
    border: 1px solid #1e3a5f;
    border-radius: 12px;
    padding: 1.2rem;
    text-align: center;
    color: #e2e8f0;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.metric-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 20px rgba(6, 182, 212, 0.25);
    border-color: #06b6d4;
}

/* ---- Sidebar ---- */
[data-testid="stSidebar"] {
    background: #0a1929;
    border-right: 1px solid #1e3a5f;
}

[data-testid="stSidebar"] * {
    color: #e2e8f0;
}

/* ---- Buttons ---- */
.stButton > button {
    border-radius: 8px;
    font-weight: 600;
    transition: all 0.2s ease;
    background: linear-gradient(135deg, #0f2942 0%, #1e3a5f 100%);
    color: #e2e8f0;
    border: 1px solid #1e3a5f;
}

.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 16px rgba(6, 182, 212, 0.3);
    border-color: #06b6d4;
    color: #06b6d4;
}

.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #0891b2 0%, #06b6d4 100%);
    color: white;
    border: none;
}

.stButton > button[kind="primary"]:hover {
    box-shadow: 0 6px 20px rgba(6, 182, 212, 0.5);
    color: white;
}

/* ---- Text inputs ---- */
.stTextInput input {
    background: #0f2942;
    color: #e2e8f0;
    border: 1px solid #1e3a5f;
    border-radius: 8px;
}

.stTextInput input:focus {
    border-color: #06b6d4;
    box-shadow: 0 0 0 2px rgba(6, 182, 212, 0.2);
}

.stTextInput label {
    color: #94a3b8 !important;
}

/* ==========================================
   DATAFRAME — dark navy theme
   ========================================== */
[data-testid="stDataFrame"] {
    background: #0f2942 !important;
    border: 1px solid #1e3a5f !important;
    border-radius: 10px !important;
    overflow: hidden !important;
}

[data-testid="stDataFrame"] > div {
    background: #0f2942 !important;
}

[data-testid="stDataFrame"] table {
    background: #0f2942 !important;
    color: #e2e8f0 !important;
}

[data-testid="stDataFrame"] thead tr th {
    background: #0a1929 !important;
    color: #06b6d4 !important;
    font-weight: 700 !important;
    border-bottom: 1px solid #1e3a5f !important;
}

[data-testid="stDataFrame"] tbody tr td {
    background: #0f2942 !important;
    color: #e2e8f0 !important;
    border-bottom: 1px solid #1e3a5f !important;
}

[data-testid="stDataFrame"] tbody tr:hover td {
    background: #1e3a5f !important;
}

[data-testid="stDataFrame"] button {
    background: #1e3a5f !important;
    color: #06b6d4 !important;
    border: 1px solid #1e3a5f !important;
}

[data-testid="stDataFrame"] button:hover {
    background: #06b6d4 !important;
    color: #0a1929 !important;
}

[data-testid="stDataFrame"] svg {
    fill: #06b6d4 !important;
}

/* ==========================================
   DOWNLOAD BUTTONS
   ========================================== */
[data-testid="stDownloadButton"] button {
    background: linear-gradient(135deg, #0f2942 0%, #1e3a5f 100%) !important;
    color: #06b6d4 !important;
    border: 1px solid #06b6d4 !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
}

[data-testid="stDownloadButton"] button:hover {
    background: linear-gradient(135deg, #0891b2 0%, #06b6d4 100%) !important;
    color: #ffffff !important;
    box-shadow: 0 6px 16px rgba(6, 182, 212, 0.4) !important;
    transform: translateY(-1px) !important;
}

[data-testid="stDownloadButton"] button * {
    color: inherit !important;
}

/* ==========================================
   EXPANDER
   ========================================== */
[data-testid="stExpander"] {
    background: #0f2942 !important;
    border: 1px solid #1e3a5f !important;
    border-radius: 10px !important;
    margin: 0.5rem 0 !important;
}

[data-testid="stExpander"] details {
    background: #0f2942 !important;
    border-radius: 10px !important;
}

[data-testid="stExpander"] summary {
    background: #0f2942 !important;
    color: #06b6d4 !important;
    font-weight: 600 !important;
    border-radius: 10px !important;
}

[data-testid="stExpander"] summary:hover {
    background: #1e3a5f !important;
    color: #06b6d4 !important;
}

[data-testid="stExpander"] summary svg {
    fill: #06b6d4 !important;
}

[data-testid="stExpander"] > details > div {
    background: #0f2942 !important;
    color: #e2e8f0 !important;
}

[data-testid="stExpander"] code {
    background: #051424 !important;
    color: #06b6d4 !important;
}

/* Legacy streamlit expander header */
.streamlit-expanderHeader {
    font-weight: 600;
    color: #06b6d4;
    background: #0f2942;
    border-radius: 8px;
}

/* ==========================================
   METRICS (Rows / Columns / etc.)
   ========================================== */
[data-testid="stMetric"] {
    background: #0f2942 !important;
    border: 1px solid #1e3a5f !important;
    border-radius: 10px !important;
    padding: 1rem !important;
}

[data-testid="stMetricValue"] {
    color: #06b6d4 !important;
    font-weight: 700 !important;
}

[data-testid="stMetricLabel"] {
    color: #94a3b8 !important;
}

/* ---- Selectbox ---- */
.stSelectbox select, [data-baseweb="select"] {
    background: #0f2942 !important;
    color: #e2e8f0 !important;
    border: 1px solid #1e3a5f !important;
}

[data-baseweb="select"] * {
    color: #e2e8f0 !important;
}

[data-baseweb="popover"] {
    background: #0f2942 !important;
}

[data-baseweb="popover"] * {
    background: #0f2942 !important;
    color: #e2e8f0 !important;
}

[data-baseweb="menu"] {
    background: #0f2942 !important;
}

/* ---- Success / Info / Warning boxes ---- */
[data-testid="stAlert"] {
    background: #0f2942 !important;
    border-radius: 10px;
    color: #e2e8f0;
    border: 1px solid #1e3a5f;
}

[data-testid="stAlert"] * {
    color: #e2e8f0 !important;
}

/* ---- Code blocks (SQL) ---- */
.stCode, pre, code {
    background: #051424 !important;
    color: #06b6d4 !important;
    border-radius: 8px !important;
    border: 1px solid #1e3a5f !important;
}

/* ---- Divider ---- */
hr {
    border-color: #1e3a5f;
}

/* ---- Headings ---- */
h1, h2, h3, h4, h5, h6 {
    color: #e2e8f0 !important;
}

/* ---- Paragraph text ---- */
p, span, label, div {
    color: #cbd5e1;
}

/* ---- File uploader ---- */
[data-testid="stFileUploader"] {
    background: #0f2942 !important;
    border-radius: 10px;
    padding: 1rem;
    border: 1px solid #1e3a5f;
}

[data-testid="stFileUploader"] section {
    background: #0f2942 !important;
    border: 2px dashed #1e3a5f !important;
    border-radius: 10px;
    color: #e2e8f0 !important;
}

[data-testid="stFileUploader"] section:hover {
    border-color: #06b6d4 !important;
}

[data-testid="stFileUploader"] section * {
    color: #e2e8f0 !important;
}

[data-testid="stFileUploader"] label {
    color: #94a3b8 !important;
}

[data-testid="stFileUploader"] button {
    background: #1e3a5f !important;
    color: #e2e8f0 !important;
    border: 1px solid #06b6d4 !important;
}

/* ---- Spinner ---- */
.stSpinner > div {
    border-top-color: #06b6d4 !important;
}
</style>
""", unsafe_allow_html=True)

# ============================================
# SESSION STATE
# ============================================
defaults = {
    'session_id': str(uuid.uuid4()),
    'db_loaded': False,
    'clean_df': None,
    'schema': "",
    'pkr_columns': [],
    'chat_history': [],
    'language': 'en',
    'cleaning_report': []
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ============================================
# HEADER
# ============================================
st.markdown(
    '<div class="main-title">📊 PakBiz AI Analyst</div>',
    unsafe_allow_html=True
)
st.markdown(
    '<div class="subtitle">Upload business data • '
    'Ask in English or Urdu • Get instant insights</div>',
    unsafe_allow_html=True
)

# ============================================
# SIDEBAR
# ============================================
with st.sidebar:
    st.subheader("⚙️ Settings")
    lang = st.selectbox(
        "Response Language",
        ["English", "Urdu (Roman)"]
    )
    st.session_state.language = (
        "ur" if lang == "Urdu (Roman)" else "en")

    st.divider()
    st.subheader("📁 Upload Data")

    uploaded_file = st.file_uploader(
        "Upload CSV (max 100,000 rows)",
        type=['csv']
    )

    if uploaded_file:
        with st.spinner("🔍 Validating..."):
            validator = FileValidator()
            result = validator.validate(uploaded_file)

        if result['success']:
            st.success("✅ File valid!")
            for w in result['warnings']:
                st.warning(w)

            meta = result['metadata']
            st.info(
                f"📊 {meta['rows']:,} rows • "
                f"{meta['columns']} cols • "
                f"{meta['file_size_mb']} MB"
            )

            if st.button("🧹 Clean & Load",
                         type="primary",
                         use_container_width=True):
                with st.spinner("🧹 Cleaning data..."):
                    cleaner = DataCleaner()
                    clean_df, report = cleaner.clean(
                        result['dataframe'])

                with st.spinner("💾 Loading DB..."):
                    db = get_db(st.session_state.session_id)
                    ok = db.load_dataframe(clean_df)

                if ok:
                    st.session_state.clean_df = clean_df
                    st.session_state.schema = db.get_schema()
                    st.session_state.pkr_columns = (
                        cleaner.pkr_columns)
                    st.session_state.db_loaded = True
                    st.session_state.cleaning_report = report
                    st.success("✅ Ready for analysis!")
                    st.rerun()
                else:
                    st.error("❌ Failed to load data")
        else:
            for err in result['errors']:
                st.error(f"❌ {err}")

    st.divider()

    if st.session_state.db_loaded:
        st.success("🟢 Data loaded")

        if st.button("🗑️ Clear Session",
                     use_container_width=True):
            db = get_db(st.session_state.session_id)
            db.cleanup()
            for key in ['db_loaded', 'clean_df',
                        'chat_history', 'schema',
                        'pkr_columns', 'cleaning_report']:
                st.session_state[key] = (
                    False if key == 'db_loaded'
                    else None if key in ['clean_df']
                    else [] if key in [
                        'chat_history', 'pkr_columns',
                        'cleaning_report']
                    else ""
                )
            st.session_state.session_id = str(uuid.uuid4())
            st.rerun()

# ============================================
# MAIN CONTENT
# ============================================
if not st.session_state.db_loaded:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="metric-card">
        <h3>📤 Upload</h3>
        <p>Upload CSV from sidebar</p>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="metric-card">
        <h3>💬 Ask</h3>
        <p>Ask in English or Urdu</p>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="metric-card">
        <h3>📊 Insights</h3>
        <p>Get charts and AI insights</p>
        </div>""", unsafe_allow_html=True)

    st.info("👈 Upload a CSV file from sidebar to start!")

else:
    df = st.session_state.clean_df

    # Quick stats
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rows", f"{len(df):,}")
    c2.metric("Columns", len(df.columns))
    num_cols = df.select_dtypes(
        include=['float64', 'int64']).columns
    c3.metric("Numeric Cols", len(num_cols))
    c4.metric("PKR Cols",
              len(st.session_state.pkr_columns))

    # Data preview + downloads
    with st.expander("👀 Preview Cleaned Data"):
        st.dataframe(df.head(10), use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            csv = df.to_csv(index=False)
            st.download_button(
                "⬇️ Download CSV",
                csv, "cleaned_data.csv",
                "text/csv",
                use_container_width=True
            )
        with col2:
            excel = dataframe_to_excel(df)
            st.download_button(
                "⬇️ Download Excel",
                excel, "cleaned_data.xlsx",
                "application/vnd.openxmlformats-"
                "officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

    with st.expander("📋 Cleaning Report"):
        for item in st.session_state.cleaning_report:
            st.write(item)

    st.divider()

    # Suggested questions
    st.subheader("💡 Suggested Questions")
    str_col = df.select_dtypes(include=['object']).columns
    num_col_list = list(num_cols)
    str_col_list = list(str_col)

    suggestions = []
    if num_col_list:
        suggestions.append(
            f"What is the total {num_col_list[0]}?")
        suggestions.append(
            f"Show top 10 rows by {num_col_list[0]}")
    if str_col_list and num_col_list:
        suggestions.append(
            f"Show {num_col_list[0]} grouped by "
            f"{str_col_list[0]}"
        )
    suggestions.append("Show me summary statistics")

    sug_cols = st.columns(2)
    for i, sug in enumerate(suggestions[:4]):
        with sug_cols[i % 2]:
            if st.button(
                    f"💬 {sug}",
                    use_container_width=True,
                    key=f"sug_{i}"):
                st.session_state.current_q = sug

    st.divider()

    # Chat history
    for chat in st.session_state.chat_history:
        st.markdown(
            f'<div class="question-box">'
            f'🧑 {chat["question"]}</div>',
            unsafe_allow_html=True
        )
        if chat.get("answer"):
            st.markdown(
                f'<div class="answer-box">'
                f'🤖 {chat["answer"]}</div>',
                unsafe_allow_html=True
            )

        # ---- CHART or KPI CARD ----
        if chat.get("chart"):
            chart = chat["chart"]
            if isinstance(chart, dict) and chart.get("type") == "kpi":
                kpi_val = chart.get("value")
                kpi_label = chart.get("label", "")
                kpi_sub = chart.get("sub_label")

                if isinstance(kpi_val, (int, float)):
                    try:
                        formatted = f"{kpi_val:,.2f}".rstrip('0').rstrip('.')
                    except Exception:
                        formatted = str(kpi_val)
                else:
                    formatted = str(kpi_val)

                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, #0891b2 0%, #06b6d4 50%, #3b82f6 100%);
                    color: white;
                    border-radius: 14px;
                    padding: 1.8rem 2rem;
                    margin: 1rem 0;
                    box-shadow: 0 8px 24px rgba(6, 182, 212, 0.35);
                    text-align: center;
                    border: 1px solid rgba(6, 182, 212, 0.5);
                ">
                    <div style="
                        font-size: 0.9rem;
                        letter-spacing: 2px;
                        text-transform: uppercase;
                        opacity: 0.9;
                        margin-bottom: 0.6rem;
                        font-weight: 600;
                    ">📊 {kpi_label}</div>
                    <div style="
                        font-size: 3rem;
                        font-weight: 800;
                        line-height: 1.1;
                        text-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
                    ">{formatted}</div>
                    {f'<div style="font-size: 1.2rem; opacity: 0.95; margin-top: 0.6rem; font-weight: 500;">{kpi_sub}</div>' if kpi_sub else ''}
                </div>
                """, unsafe_allow_html=True)
            else:
                chart.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="rgba(15,41,66,0.6)",
                    plot_bgcolor="rgba(15,41,66,0.4)",
                    font=dict(color="#e2e8f0"),
                    title_font=dict(color="#06b6d4", size=18),
                )
                st.plotly_chart(
                    chart,
                    use_container_width=True,
                    key=f"chart_{chat['id']}"
                )

        if chat.get("table") is not None and \
                not chat["table"].empty:
            st.dataframe(
                chat["table"],
                use_container_width=True
            )
            if chat.get("answer"):
                pdf = generate_pdf_report(
                    chat["question"],
                    chat["answer"],
                    chat["table"],
                    st.session_state.cleaning_report
                )
                st.download_button(
                    "⬇️ Download PDF Report",
                    pdf,
                    f"report_{chat['id'][:8]}.pdf",
                    "application/pdf",
                    key=f"pdf_{chat['id']}"
                )

        if chat.get("sql"):
            with st.expander("🔍 SQL Used"):
                st.code(chat["sql"], language="sql")

    # Question input
    default_q = getattr(
        st.session_state, 'current_q', "")
    question = st.text_input(
        "Ask your question:",
        value=default_q,
        placeholder=(
            "e.g. Which product has highest sales? / "
            "Sabse zyada sale kaunsi hai?"
        )
    )

    col1, col2 = st.columns([3, 1])
    with col1:
        ask = st.button(
            "🚀 Analyze",
            type="primary",
            use_container_width=True
        )
    with col2:
        if st.button("🗑️ Clear Chat",
                     use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()

    if ask and question:
        sanitizer = InputSanitizer()
        is_valid, _ = sanitizer.is_valid_question(question)
        clean_q = sanitizer.sanitize_question(question)

        if not is_valid:
            st.error("Question too short or too long")
        else:
            with st.spinner("🤖 Analyzing..."):
                result = run_agent(
                    question=clean_q,
                    schema=st.session_state.schema,
                    session_id=st.session_state.session_id,
                    pkr_columns=st.session_state.pkr_columns,
                    language=st.session_state.language
                )

            st.session_state.chat_history.append({
                "id": str(uuid.uuid4()),
                "question": clean_q,
                "answer": result.get("final_answer", ""),
                "chart": result.get("chart_data"),
                "table": result.get("sql_result"),
                "sql": result.get("generated_sql", "")
            })

            if hasattr(st.session_state, 'current_q'):
                del st.session_state.current_q

            st.rerun()