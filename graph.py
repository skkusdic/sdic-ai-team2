from langgraph.graph import StateGraph, END
from data import get_financials
from typing import TypedDict


class AnalysisState(TypedDict):
    data: dict
    result: str


def load_data(state: AnalysisState) -> AnalysisState:
    financials = get_financials("삼성전자")
    return {"data": financials, "result": ""}


def process_data(state: AnalysisState) -> AnalysisState:
    d = state["data"]
    if d:
        latest_year = max(d.keys())
        latest_data = d[latest_year]
        result = f"분석 준비 완료: {latest_year}년 매출액 {latest_data['매출액']:,}억원, 영업이익 {latest_data['영업이익']:,}억원"
        print(result)
    else:
        result = "데이터를 찾을 수 없습니다."
        print(result)
    return {"data": d, "result": result}


def build_graph():
    graph = StateGraph(AnalysisState)
    graph.add_node("load_data", load_data)
    graph.add_node("process_data", process_data)
    graph.set_entry_point("load_data")
    graph.add_edge("load_data", "process_data")
    graph.add_edge("process_data", END)
    return graph.compile()


if __name__ == "__main__":
    app = build_graph()
    final_state = app.invoke({"data": {}, "result": ""})
