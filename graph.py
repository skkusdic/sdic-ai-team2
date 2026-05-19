import sys
from langgraph.graph import StateGraph, END
from typing import TypedDict, Literal, Optional
from claude_client import ask
from agents.analysis_agent import analyze as analyze_financials, analysis_agent
from agents.data_agent import run_data_agent
from agents.competitor_agent import competitor_agent
from agents.report_agent import run_report_agent


class AnalysisState(TypedDict):
    request: str
    company: str
    next_agent: str
    financials: dict
    analysis: str
    competitors: dict
    competitor_analysis: str
    result: str
    pdf_path: str
    data_source: Optional[str]


def supervisor_node(state: AnalysisState) -> AnalysisState:
    """Supervisor: 다음 agent 결정"""
    if not state["financials"]:
        print("[Supervisor] 재무 데이터가 없음 → data_agent로 라우팅 결정")
        return {**state, "next_agent": "data_agent"}

    prompt = f"""현재 상태:
- 요청: {state['request']}
- 기업: {state['company']}
- 재무 데이터: {'있음' if state['financials'] else '없음'}
- 분석 완료: {'yes' if state['analysis'] else 'no'}
- 경쟁사 분석: {'yes' if state['competitor_analysis'] else 'no'}
- 보고서 생성: {'yes' if state['result'] else 'no'}

다음 단계를 결정하세요. 응답은 정확히 하나만: "data_agent", "analysis_agent", "competitor_agent", "report_agent" 중 하나.

규칙:
1. 데이터가 없으면 → "data_agent"
2. 데이터는 있지만 분석 없으면 → "analysis_agent"
3. 분석은 있지만 경쟁사 분석 없으면 → "competitor_agent"
4. 경쟁사 분석은 있지만 보고서 없으면 → "report_agent"
5. 모두 완료되면 → "report_agent" (완료 신호)"""

    next_agent = ask(prompt, max_tokens=50).strip()

    if next_agent not in ["data_agent", "analysis_agent", "competitor_agent", "report_agent"]:
        next_agent = "analysis_agent"

    print(f"[Supervisor] Claude가 다음 agent 결정: {next_agent}")
    return {**state, "next_agent": next_agent}


def data_agent(state: AnalysisState) -> AnalysisState:
    """Data Agent: 재무 데이터 수집"""
    print(f"[Data Agent] {state['company']} 데이터 조회 중...")
    result = run_data_agent(state)
    if result["financials"]:
        print(f"[Data Agent] {len(result['financials'])}개년 데이터 획득 완료")
    else:
        print(f"[Data Agent] 데이터를 찾을 수 없음")
        result["result"] = f"'{state['company']}' 기업의 재무 데이터를 찾을 수 없습니다. 회사명을 다시 확인해주세요."
    return result


def route_by_next_agent(state: AnalysisState) -> str:
    """Supervisor의 next_agent 값에 따라 라우팅"""
    return state["next_agent"]


def check_financials(state: AnalysisState) -> Literal["no_data", "has_data"]:
    """데이터 존재 여부 확인"""
    return "has_data" if state["financials"] else "no_data"


def build_graph():
    """LangGraph Supervisor 파이프라인"""
    graph = StateGraph(AnalysisState)

    # 노드 등록
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("data_agent", data_agent)
    graph.add_node("analysis_agent", analysis_agent)
    graph.add_node("competitor_agent", competitor_agent)
    graph.add_node("report_agent", run_report_agent)

    # 진입점
    graph.set_entry_point("supervisor")

    # 조건부 라우팅: supervisor의 next_agent 결정에 따라 분기
    graph.add_conditional_edges(
        "supervisor",
        route_by_next_agent,
        {
            "data_agent": "data_agent",
            "analysis_agent": "analysis_agent",
            "competitor_agent": "competitor_agent",
            "report_agent": "report_agent",
        },
    )

    # 조건부 라우팅: data_agent 후 financials 확인
    graph.add_conditional_edges(
        "data_agent",
        check_financials,
        {
            "no_data": END,
            "has_data": "analysis_agent",
        },
    )

    # 고정 경로: analysis_agent → competitor_agent → report_agent → END
    graph.add_edge("analysis_agent", "competitor_agent")
    graph.add_edge("competitor_agent", "report_agent")
    graph.add_edge("report_agent", END)

    return graph.compile()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # Windows cp949 한글 깨짐 방지

    app = build_graph()
    initial_state = {
        "request": "삼성전자 재무 분석해줘",
        "company": "삼성전자",
        "next_agent": "",
        "financials": {},
        "analysis": "",
        "competitors": {},
        "competitor_analysis": "",
        "result": "",
        "pdf_path": "",
        "data_source": None,
    }

    print("=" * 60)
    print("LangGraph Supervisor 파이프라인 실행")
    print("=" * 60)
    final_state = app.invoke(initial_state)
    print("=" * 60)
    print("최종 상태:")
    print("=" * 60)
    print(f"[company] {final_state['company']}")
    print(f"[next_agent] {final_state['next_agent']}")
    print(f"[financials] {len(final_state['financials'])}개년 데이터")
    print(f"[result]\n{final_state['result']}")
