from langgraph.graph import StateGraph, END
from typing import TypedDict


class AnalysisState(TypedDict):
    data: dict
    result: str


def load_data(state: AnalysisState) -> AnalysisState:
    mock = {
        "company": "삼성전자",
        "매출액": 300_000_000_000_000,
        "영업이익": 32_000_000_000_000,
        "순이익": 34_000_000_000_000,
    }
    return {"data": mock, "result": ""}


def process_data(state: AnalysisState) -> AnalysisState:
    d = state["data"]
    result = f"분석 준비 완료: 매출액 {d['매출액']:,}원, 영업이익 {d['영업이익']:,}원"
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
