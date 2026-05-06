from langgraph.graph import StateGraph, END
from data import get_financials
from claude_client import ask
from typing import TypedDict


class AnalysisState(TypedDict):
    company: str
    data: dict
    result: str
    analysis: str


def load_data(state: AnalysisState) -> AnalysisState:
    financials = get_financials(state["company"])
    return {"company": state["company"], "data": financials, "result": "", "analysis": ""}


def process_data(state: AnalysisState) -> AnalysisState:
    d = state["data"]
    if d:
        latest_year = max(d.keys())
        latest_data = d[latest_year]
        result = f"분석 준비 완료: {latest_year}년 매출액 {latest_data['매출액']:,}억원, 영업이익 {latest_data['영업이익']:,}억원"
    else:
        result = "데이터를 찾을 수 없습니다."
    return {"company": state["company"], "data": d, "result": result, "analysis": ""}


def analyze(state: AnalysisState) -> AnalysisState:
    company = state["company"]
    d = state["data"]
    if not d:
        return {**state, "analysis": "분석할 데이터가 없습니다."}

    rows = "\n".join(
        f"  {year}년: 매출액 {v['매출액']:,}억원, 영업이익 {v['영업이익']:,}억원, 순이익 {v['순이익']:,}억원"
        for year, v in sorted(d.items())
    )
    prompt = f"""다음은 {company}의 최근 3개년 재무 데이터입니다 (단위: 억원):

{rows}

위 데이터를 바탕으로 아래 항목을 한국어로 분석해주세요:
1. 매출 및 수익성 추이 (2~3문장)
2. 주목할 만한 변화 또는 리스크 (2~3문장)
3. 종합 의견 (1~2문장)"""

    analysis = ask(prompt, max_tokens=800)
    return {**state, "analysis": analysis}


def build_graph():
    graph = StateGraph(AnalysisState)
    graph.add_node("load_data", load_data)
    graph.add_node("process_data", process_data)
    graph.add_node("analyze", analyze)
    graph.set_entry_point("load_data")
    graph.add_edge("load_data", "process_data")
    graph.add_edge("process_data", "analyze")
    graph.add_edge("analyze", END)
    return graph.compile()


if __name__ == "__main__":
    app = build_graph()
    final_state = app.invoke({"company": "삼성전자", "data": {}, "result": "", "analysis": ""})
    print(final_state["analysis"])
