from fpdf import FPDF


def generate_report(company_name: str, financials: list, analysis: str) -> str:
    """빈 PDF 1장 생성 — 4주차에 내용 채울 예정."""
    pdf = FPDF()
    pdf.add_page()

    output_path = f"{company_name}_report.pdf"
    pdf.output(output_path)
    return output_path


def embed_document(text: str) -> list:
    # TODO: OpenAI embeddings로 RAG 구현
    pass


def _format_report(data: dict) -> str:
    company = data.get("company", "")
    lines = [f"[ {company} 재무 요약 ]"]
    for year_data in data.get("financials", []):
        year = year_data["year"]
        revenue = year_data["revenue"]
        operating_profit = year_data["operating_profit"]
        net_income = year_data["net_income"]
        lines.append(f"{year}년: 매출 {revenue}조 / 영업이익 {operating_profit}조 / 순이익 {net_income}조")
    return "\n".join(lines)


if __name__ == "__main__":
    mock_financials = [
        {"year": 2022, "revenue": 302, "operating_profit": 43, "net_income": 55},
        {"year": 2023, "revenue": 259, "operating_profit": 6,  "net_income": 15},
        {"year": 2024, "revenue": 300, "operating_profit": 32, "net_income": 34},
    ]
    path = generate_report("삼성전자", mock_financials, "")
    print(f"PDF 생성 완료: {path}")
