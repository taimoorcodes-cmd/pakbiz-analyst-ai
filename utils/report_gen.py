# utils/report_gen.py
# PDF and Excel report generation

import pandas as pd
from io import BytesIO
from datetime import datetime

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph,
        Table, TableStyle, Spacer
    )
    REPORTLAB_OK = True
except ImportError:
    REPORTLAB_OK = False


def generate_pdf_report(
    question: str,
    answer: str,
    df: pd.DataFrame,
    cleaning_report: list = None
) -> bytes:
    if not REPORTLAB_OK:
        return _simple_report(question, answer, df)

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=0.5*inch, leftMargin=0.5*inch,
        topMargin=0.5*inch, bottomMargin=0.5*inch
    )
    styles = getSampleStyleSheet()
    story = []

    story.append(
        Paragraph("PakBiz AI Analyst Report",
                  styles['Title']))
    story.append(Spacer(1, 0.2*inch))

    date_str = datetime.now().strftime(
        "%B %d, %Y at %I:%M %p")
    story.append(
        Paragraph(f"Generated: {date_str}",
                  styles['Normal']))
    story.append(Spacer(1, 0.3*inch))

    story.append(
        Paragraph("Question:", styles['Heading2']))
    story.append(Paragraph(question, styles['Normal']))
    story.append(Spacer(1, 0.2*inch))

    story.append(
        Paragraph("AI Analysis:", styles['Heading2']))
    story.append(Paragraph(answer, styles['Normal']))
    story.append(Spacer(1, 0.3*inch))

    if df is not None and not df.empty:
        story.append(
            Paragraph("Results:", styles['Heading2']))
        story.append(Spacer(1, 0.1*inch))

        display_df = df.head(20)
        data = [display_df.columns.tolist()] + \
               display_df.values.tolist()
        data = [
            [str(c)[:30] for c in row] for row in data]

        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0),
             colors.HexColor('#2563EB')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('PADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(table)

    if cleaning_report:
        story.append(Spacer(1, 0.2*inch))
        story.append(
            Paragraph("Cleaning Summary:",
                      styles['Heading2']))
        for item in cleaning_report:
            story.append(
                Paragraph(f"• {item}", styles['Normal']))

    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph(
        "PakBiz AI Analyst — OpenRouter + LangGraph",
        styles['Normal']
    ))

    doc.build(story)
    return buffer.getvalue()


def _simple_report(
        question, answer, df) -> bytes:
    out = BytesIO()
    out.write(b"PakBiz AI Analyst Report\n")
    out.write(f"Question: {question}\n".encode())
    out.write(f"Answer: {answer}\n\n".encode())
    if df is not None:
        out.write(df.to_csv(index=False).encode())
    return out.getvalue()


def dataframe_to_excel(df: pd.DataFrame) -> bytes:
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as w:
        df.to_excel(w, index=False, sheet_name='Analysis')
        ws = w.sheets['Analysis']
        for col in ws.columns:
            max_len = max(
                len(str(c.value or '')) for c in col)
            ws.column_dimensions[
                col[0].column_letter].width = min(
                    max_len + 2, 40)
    return buffer.getvalue()