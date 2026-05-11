from fpdf import FPDF
from fpdf.enums import XPos, YPos
import os


def run_report_agent(state: dict) -> dict:
    financials = state.get("financials", {})
    analysis = state.get("analysis", "No analysis available")
    company = state.get("company", "Unknown")

    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Helvetica", "B", size=20)
    pdf.cell(0, 12, text=f"{company} Financial Report", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.ln(6)

    pdf.set_font("Helvetica", size=12)
    pdf.cell(0, 8, text="[ Financials ]", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", size=10)
    for key, value in financials.items():
        pdf.cell(0, 7, text=f"  {key}: {value}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.ln(4)
    pdf.set_font("Helvetica", size=12)
    pdf.cell(0, 8, text="[ Analysis ]", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", size=10)

    safe_analysis = analysis.encode("latin-1", errors="replace").decode("latin-1")
    pdf.multi_cell(0, 7, text=safe_analysis)

    pdf_path = f"{company}_report.pdf"
    pdf.output(pdf_path)

    state["pdf_path"] = os.path.abspath(pdf_path)
    return state


def embed_text(text: str) -> list:
    pass  # TODO: 4주차에 OpenAI embeddings로 구현


if __name__ == "__main__":
    mock_state = {
        "company": "Samsung",
        "financials": {
            "revenue": "300T KRW",
            "operating_profit": "30T KRW",
            "net_income": "25T KRW",
            "total_assets": "500T KRW",
        },
        "analysis": (
            "Samsung Electronics shows strong revenue driven by semiconductor recovery. "
            "Operating margin improved YoY. Memory chip demand remains robust heading into H2."
        ),
    }

    result = run_report_agent(mock_state)
    print(f"PDF generated: {result['pdf_path']}")
