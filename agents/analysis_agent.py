import sys
import os
from typing import TypedDict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from claude_client import ask


class AnalysisState(TypedDict):
    request: str
    company: str
    next_agent: str
    financials: dict
    analysis: str
    result: str
    pdf_path: str


def analyze(financials: dict) -> str:
    """5개년 재무 데이터를 분석해서 한국어 인사이트 생성"""

    # 연도별 데이터 추출 및 정렬
    sorted_years = sorted(financials.items())

    # 분석용 데이터 포맷팅
    financial_summary = []
    for year, data in sorted_years:
        revenue = data.get("매출액", 0)
        op_profit = data.get("영업이익", 0)
        net_profit = data.get("순이익", 0)

        if revenue > 0:
            op_margin = (op_profit / revenue) * 100
        else:
            op_margin = 0

        financial_summary.append(
            f"{year}년: 매출액 {revenue:,.0f}억원, 영업이익 {op_profit:,.0f}억원 (영업이익률 {op_margin:.1f}%), 순이익 {net_profit:,.0f}억원"
        )

    # 최신 연도 정보
    latest_year, latest_data = sorted_years[-1]
    latest_revenue = latest_data.get("매출액", 0)
    latest_op_profit = latest_data.get("영업이익", 0)

    if latest_revenue > 0:
        latest_op_margin = (latest_op_profit / latest_revenue) * 100
    else:
        latest_op_margin = 0

    # Claude에 분석 요청
    prompt = f"""다음은 기업의 5년간 재무 데이터입니다:

{chr(10).join(financial_summary)}

이 데이터를 분석해서 다음 규칙에 따라 한국어로 3-5문장의 분석을 작성해주세요:
1. 첫 문장은 반드시 "이 기업의 영업이익률은 {latest_op_margin:.1f}%로"로 시작
2. 최신 연도({latest_year}년) 기준으로 분석
3. 5년간의 추세(상승/하락/안정)를 포함
4. 실질적인 재무 인사이트를 제공
5. 마침표로 끝나기

분석 텍스트만 반환하세요."""

    return ask(prompt)


def analysis_agent(state: AnalysisState) -> AnalysisState:
    """Analysis Agent: 재무 분석"""
    if not state["financials"]:
        return {**state, "analysis": "분석할 데이터가 없습니다."}

    print(f"[Analysis Agent] {state['company']} 분석 중...")
    analysis_text = analyze(state["financials"])
    print(f"[Analysis Agent] 분석 완료")
    return {**state, "analysis": analysis_text}


if __name__ == "__main__":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    # 5개년 mock data
    mock_financials = {
        2021: {
            "매출액": 149_883_000_000_000,
            "영업이익": 17_589_000_000_000,
            "순이익": 16_108_000_000_000,
        },
        2022: {
            "매출액": 302_315_000_000_000,
            "영업이익": 43_127_000_000_000,
            "순이익": 55_314_000_000_000,
        },
        2023: {
            "매출액": 259_146_000_000_000,
            "영업이익": 6_348_000_000_000,
            "순이익": 15_119_000_000_000,
        },
        2024: {
            "매출액": 300_098_000_000_000,
            "영업이익": 32_156_000_000_000,
            "순이익": 34_052_000_000_000,
        },
        2025: {
            "매출액": 320_450_000_000_000,
            "영업이익": 38_920_000_000_000,
            "순이익": 40_815_000_000_000,
        },
    }

    print("=" * 60)
    print("Claude 재무 분석 결과:")
    print("=" * 60)
    analysis_result = analyze(mock_financials)
    print(analysis_result)
    print("=" * 60)
