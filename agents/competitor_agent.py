import sys
import os
from typing import TypedDict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data import get_competitors
from claude_client import ask


class CompetitorState(TypedDict):
    company: str
    competitors: dict  # {회사명: {연도: {지표: 값}}}
    competitor_analysis: str


def calculate_metrics(financials: dict) -> dict:
    """재무 데이터에서 주요 지표 계산 (연도별)"""
    metrics = {}
    for year, data in financials.items():
        revenue = data.get("매출액", 0)
        op_profit = data.get("영업이익", 0)
        net_profit = data.get("순이익", 0)

        op_margin = (op_profit / revenue * 100) if revenue > 0 else 0
        net_margin = (net_profit / revenue * 100) if revenue > 0 else 0

        metrics[year] = {
            "매출액": revenue,
            "영업이익": op_profit,
            "순이익": net_profit,
            "영업이익률": op_margin,
            "순이익률": net_margin,
        }
    return metrics


def compare_competitors(company_name: str, competitors_data: dict) -> str:
    """Claude를 활용한 경쟁사 비교 분석"""

    # 주요 회사의 최신 연도 지표
    main_metrics = None
    if company_name in competitors_data:
        latest_year = max(competitors_data[company_name].keys())
        main_data = competitors_data[company_name][latest_year]
        main_revenue = main_data.get("매출액", 0)
        main_op_margin = (
            (main_data.get("영업이익", 0) / main_revenue * 100)
            if main_revenue > 0
            else 0
        )
        main_metrics = {
            "연도": latest_year,
            "매출액": main_revenue,
            "영업이익률": main_op_margin,
        }

    # 경쟁사별 분석 데이터 생성
    comp_summary = []
    for comp_name, comp_financials in competitors_data.items():
        if comp_name == company_name:
            continue

        latest_year = max(comp_financials.keys())
        comp_data = comp_financials[latest_year]
        comp_revenue = comp_data.get("매출액", 0)
        comp_op_profit = comp_data.get("영업이익", 0)
        comp_op_margin = (comp_op_profit / comp_revenue * 100) if comp_revenue > 0 else 0

        comp_summary.append(
            f"{comp_name}({latest_year}년): 매출액 {comp_revenue:,.0f}억원, 영업이익률 {comp_op_margin:.1f}%"
        )

    # Claude 분석 프롬프트
    prompt = f"""다음은 '{company_name}'과 경쟁사들의 재무 데이터입니다:

"""

    if main_metrics:
        prompt += f"{company_name}({main_metrics['연도']}년): 매출액 {main_metrics['매출액']:,.0f}억원, 영업이익률 {main_metrics['영업이익률']:.1f}%\n"

    prompt += "\n경쟁사:\n" + "\n".join(comp_summary)

    prompt += """

이 데이터를 기반으로 다음 규칙에 따라 한국어로 3-5문장의 경쟁사 비교 분석을 작성해주세요:
1. 매출액 규모 비교
2. 영업이익률 비교 및 시사점
3. '{company_name}'의 경쟁 포지셀
4. 주요 강점/약점

분석 텍스트만 반환하세요."""

    prompt = prompt.replace("{company_name}", company_name)
    return ask(prompt)


def competitor_agent(state: dict) -> dict:
    """Competitor Agent: 경쟁사 비교 분석"""
    company_name = state.get("company", "")
    if not company_name:
        return {**state, "competitor_analysis": "회사명이 없습니다."}

    print(f"[Competitor Agent] {company_name} 경쟁사 분석 중...")
    competitors_data = get_competitors(company_name)

    if not competitors_data:
        print(f"[Competitor Agent] {company_name} 경쟁사 데이터를 찾을 수 없습니다.")
        return {**state, "competitors": {}, "competitor_analysis": "경쟁사 데이터가 없습니다."}

    print(f"[Competitor Agent] {len(competitors_data)}개 경쟁사 데이터 수집 완료")
    analysis = compare_competitors(company_name, competitors_data)
    print(f"[Competitor Agent] 분석 완료")

    return {
        **state,
        "competitors": competitors_data,
        "competitor_analysis": analysis,
    }


if __name__ == "__main__":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    # 테스트
    print("=" * 60)
    print("경쟁사 비교 분석 에이전트 테스트")
    print("=" * 60)
    result = competitor_agent({"company": "삼성전자"})
    print(f"\n경쟁사: {list(result['competitors'].keys())}")
    print(f"\n분석 결과:\n{result['competitor_analysis']}")
    print("=" * 60)
