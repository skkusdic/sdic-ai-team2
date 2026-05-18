from fpdf import FPDF
from fpdf.enums import XPos, YPos
import tempfile
import os


class KoreanPDF(FPDF):
    def __init__(self):
        super().__init__()
        font_path = os.path.join(os.path.dirname(__file__), '..', 'fonts', 'NanumGothic.ttf')
        self.add_font('NanumGothic', '', font_path)
        self.set_font('NanumGothic', size=12)

    def header(self):
        self.set_font('NanumGothic', size=16)
        self.cell(0, 12, 'SDIC AI 기업 재무 분석 리포트', align='C',
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font('NanumGothic', size=9)
        self.cell(0, 10, f'페이지 {self.page_no()}', align='C')


def generate_pdf(company: str, financials: dict, analysis: str) -> str:
    pdf = KoreanPDF()
    pdf.add_page()

    # 기업명
    pdf.set_font('NanumGothic', size=14)
    pdf.cell(0, 10, f'기업명: {company}', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)

    # 1. 재무 데이터 섹션
    pdf.set_font('NanumGothic', size=12)
    pdf.cell(0, 9, '1. 재무 데이터 (단위: 억원)', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)

    col_widths = [30, 50, 50, 50]
    headers = ['연도', '매출액', '영업이익', '순이익']

    pdf.set_font('NanumGothic', size=10)
    for i, h in enumerate(headers):
        pdf.cell(col_widths[i], 8, h, border=1, align='C',
                 new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.ln()

    for year, v in sorted(financials.items()):
        row = [
            str(year),
            f"{v.get('매출액', 0):,}",
            f"{v.get('영업이익', 0):,}",
            f"{v.get('순이익', 0):,}",
        ]
        for i, val in enumerate(row):
            pdf.cell(col_widths[i], 8, val, border=1, align='C',
                     new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.ln()

    pdf.ln(6)

    # 2. Claude AI 분석 섹션
    pdf.set_font('NanumGothic', size=12)
    pdf.cell(0, 9, '2. Claude AI 분석', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)
    pdf.set_font('NanumGothic', size=10)
    pdf.multi_cell(0, 7, analysis)

    # 임시 파일로 저장
    tmp = tempfile.NamedTemporaryFile(
        delete=False, suffix='.pdf', prefix=f'report_{company}_'
    )
    tmp.close()
    pdf.output(tmp.name)
    return tmp.name


def run_report_agent(state: dict) -> dict:
    pdf_path = generate_pdf(
        company=state['company'],
        financials=state['financials'],
        analysis=state['analysis'],
    )
    state['pdf_path'] = pdf_path
    return state


if __name__ == '__main__':
    mock_state = {
        'company': '삼성전자',
        'financials': {
            2019: {'매출액': 2304009, '영업이익': 277685, '순이익': 217389},
            2020: {'매출액': 2368070, '영업이익': 359939, '순이익': 264078},
            2021: {'매출액': 2796048, '영업이익': 516339, '순이익': 399074},
            2022: {'매출액': 3022314, '영업이익': 433766, '순이익': 556541},
            2023: {'매출액': 2589355, '영업이익': 64680,  '순이익': 154871},
        },
        'analysis': (
            '삼성전자는 2022년 최대 매출(302조원)을 기록한 후 2023년 반도체 업황 악화로 '
            '영업이익이 급감하였습니다.\n'
            '메모리 반도체 가격 하락이 주요 원인이며, HBM 및 파운드리 경쟁력 강화가 '
            '향후 회복의 핵심 과제입니다.\n'
            '2024년 하반기 업황 반등이 예상되며, AI 서버 수요 증가로 수익성 개선이 '
            '기대됩니다.'
        ),
    }

    result = run_report_agent(mock_state)
    print(f'PDF 생성 완료: {result["pdf_path"]}')
