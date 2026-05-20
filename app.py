import streamlit as st
import pandas as pd
import os
import re
import plotly.express as px

# Streamlit Cloud: secrets → os.environ 동기화 (로컬엔 secrets.toml 없으므로 무시)
try:
    for _key in ["DART_API_KEY", "ANTHROPIC_API_KEY"]:
        if _key in st.secrets and _key not in os.environ:
            os.environ[_key] = st.secrets[_key]
except Exception:
    pass

from graph import build_graph

try:
    from rag import search_app as rag_search, answer as rag_answer
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False

try:
    from text2sql import query as text2sql_query
    TEXT2SQL_AVAILABLE = True
except ImportError:
    TEXT2SQL_AVAILABLE = False

st.set_page_config(page_title="AI 재무 컨설팅 어시스턴트", layout="wide")

st.markdown("""
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');

html, body, [class*="css"], input, button, textarea, select,
.stMarkdown, .stTextInput, .stButton, p, div, span, h1, h2, h3, h4, h5, h6 {
    font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

.stApp { background-color: #f0f7f2; overflow: hidden; }

.stApp::before {
    content: '';
    position: fixed; top: -140px; left: -100px;
    width: 560px; height: 560px;
    background: radial-gradient(circle, rgba(82,183,136,0.30) 0%, rgba(45,106,79,0.10) 50%, transparent 70%);
    border-radius: 50%; filter: blur(70px);
    z-index: 0; pointer-events: none;
}
.stApp::after {
    content: '';
    position: fixed; top: 50px; right: -120px;
    width: 500px; height: 500px;
    background: radial-gradient(circle, rgba(134,197,152,0.25) 0%, rgba(100,180,140,0.10) 50%, transparent 70%);
    border-radius: 50%; filter: blur(80px);
    z-index: 0; pointer-events: none;
}
.deco-blob-1 {
    position: fixed; bottom: 80px; left: 25%;
    width: 400px; height: 400px;
    background: radial-gradient(circle, rgba(160,220,140,0.18) 0%, transparent 80%);
    border-radius: 50%; filter: blur(90px);
    z-index: 0; pointer-events: none;
}
.deco-blob-2 {
    position: fixed; top: 45%; right: 10%;
    width: 320px; height: 320px;
    background: radial-gradient(circle, rgba(52,211,153,0.15) 0%, transparent 80%);
    border-radius: 50%; filter: blur(70px);
    z-index: 0; pointer-events: none;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, rgba(240,247,242,0.97) 0%, rgba(255,255,255,0.92) 100%);
    backdrop-filter: blur(16px);
    border-right: 1px solid #c8e6c9;
}
[data-testid="stSidebar"] .stMarkdown p {
    color: #3a4a3d; font-size: 0.88rem; padding: 0.2rem 0;
}

h1 { display: none; }

.hero-banner {
    background: linear-gradient(135deg, #1b4332 0%, #2d6a4f 45%, #40916c 100%);
    border-radius: 24px;
    padding: 2.2rem 2.4rem 2rem;
    margin-bottom: 1.8rem;
    position: relative; overflow: hidden;
    box-shadow: 0 8px 32px rgba(27,67,50,0.22);
}
.hero-banner::before {
    content: ''; position: absolute;
    top: -60px; right: -60px;
    width: 260px; height: 260px;
    background: rgba(255,255,255,0.06); border-radius: 50%;
}
.hero-banner::after {
    content: ''; position: absolute;
    bottom: -40px; left: 30%;
    width: 180px; height: 180px;
    background: rgba(255,255,255,0.04); border-radius: 50%;
}
.hero-title {
    font-size: 2rem; font-weight: 800;
    color: #ffffff; line-height: 1.15;
    letter-spacing: -0.04em; margin-bottom: 0.5rem;
    position: relative; z-index: 1;
}
.hero-title span {
    background: linear-gradient(90deg, #95d5b2, #d8f3dc);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;
}
.hero-sub {
    font-size: 0.88rem; color: rgba(255,255,255,0.72);
    position: relative; z-index: 1;
}
.hero-badge {
    display: inline-block;
    background: rgba(255,255,255,0.15);
    border: 1px solid rgba(255,255,255,0.25);
    border-radius: 20px; padding: 0.25rem 0.9rem;
    font-size: 0.72rem; font-weight: 600;
    color: rgba(255,255,255,0.9);
    margin-bottom: 1rem; position: relative; z-index: 1;
}

.stTextInput > div > div > input {
    border-radius: 14px !important;
    border: 2px solid #b7dfc4 !important;
    padding: 0.9rem 1.2rem !important;
    font-size: 0.95rem !important; font-weight: 500 !important;
    background: rgba(255,255,255,0.95) !important; color: #1a2e1f !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
    box-sizing: border-box !important;
}
.stTextInput > div > div > input:focus {
    border-color: #2d6a4f !important;
    box-shadow: 0 0 0 3px rgba(45,106,79,0.12) !important;
    background: #ffffff !important;
}
.stTextInput > div > div > input::placeholder {
    color: #a0b8a6 !important; font-weight: 400 !important;
}

[data-testid="stButton"] > button {
    background: linear-gradient(135deg, #2d6a4f 0%, #40916c 100%) !important;
    color: white !important; border-radius: 14px !important; border: none !important;
    font-weight: 700 !important; font-size: 0.95rem !important;
    padding: 0.9rem 1.4rem !important;
    box-shadow: 0 4px 14px rgba(45,106,79,0.30) !important;
    transition: transform 0.15s, box-shadow 0.15s !important;
}
[data-testid="stButton"] > button:hover {
    background: linear-gradient(135deg, #1b4332 0%, #2d6a4f 100%) !important;
    box-shadow: 0 6px 20px rgba(45,106,79,0.40) !important;
    transform: translateY(-1px) !important;
}
[data-testid="stButton"] > button:active { transform: translateY(0px) !important; }

.step-row {
    display: flex; align-items: center; gap: 0.7rem;
    padding: 0.55rem 0.8rem; border-radius: 12px;
    margin-bottom: 0.4rem; transition: background 0.3s;
}
.step-row.done { background: rgba(45,106,79,0.08); }
.step-row.pending { background: transparent; }
.step-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
.step-dot.done { background: #40916c; }
.step-dot.pending { background: #c8d8c9; }
.step-label { font-size: 0.84rem; font-weight: 600; }
.step-label.done { color: #1b4332; }
.step-label.pending { color: #8aab8e; }

.history-item {
    padding: 0.45rem 0.8rem; border-radius: 10px;
    font-size: 0.83rem; font-weight: 600; color: #2d6a4f;
    background: rgba(45,106,79,0.07);
    margin-bottom: 0.3rem; cursor: pointer;
    transition: background 0.15s;
}
.history-item:hover { background: rgba(45,106,79,0.14); }

[data-testid="stSidebar"] [data-testid="stButton"] > button {
    background: rgba(45,106,79,0.07) !important;
    color: #2d6a4f !important;
    border: none !important;
    border-radius: 10px !important;
    font-size: 0.83rem !important;
    font-weight: 600 !important;
    padding: 0.45rem 0.8rem !important;
    box-shadow: none !important;
    text-align: left !important;
}
[data-testid="stSidebar"] [data-testid="stButton"] > button:hover {
    background: rgba(45,106,79,0.14) !important;
    transform: none !important;
    box-shadow: none !important;
}

.section-header {
    font-size: 0.95rem; font-weight: 700; color: #0d1f12;
    margin-bottom: 0.8rem; margin-top: 1.6rem;
    display: flex; align-items: center; gap: 0.5rem;
}
.section-header::before {
    content: ''; display: inline-block;
    width: 4px; height: 1rem;
    background: linear-gradient(180deg, #40916c, #2d6a4f);
    border-radius: 4px;
}

.source-text {
    font-size: 0.70rem; color: #9ab09d; margin-top: 0.4rem;
    font-weight: 400; letter-spacing: 0.01em;
}

.analysis-card {
    background: rgba(255,255,255,0.92); backdrop-filter: blur(12px);
    border-radius: 20px; padding: 1.8rem 2.2rem;
    box-shadow: 0 4px 24px rgba(45,106,79,0.09);
    border: 1.5px solid #d0e8d3; color: #2c3e30;
}
.analysis-card p {
    font-size: 0.88rem !important; line-height: 1.9 !important;
    color: #2c3e30 !important; margin-bottom: 0.5rem !important;
}

.tag-green {
    display: inline-block; background: #d8f3dc; color: #1b4332;
    border-radius: 20px; padding: 0.2rem 0.75rem;
    font-size: 0.73rem; font-weight: 600;
}

@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(14px); }
    to   { opacity: 1; transform: translateY(0); }
}
.fade-in   { animation: fadeInUp 0.45s ease both; }
.fade-in-1 { animation: fadeInUp 0.45s 0.05s ease both; }

[data-testid="stDataFrame"] {
    border-radius: 16px !important; overflow: hidden;
    box-shadow: 0 4px 20px rgba(45,106,79,0.08);
    border: 1.5px solid #d0e8d3 !important;
}

[data-testid="stTabs"] [role="tab"] {
    font-weight: 600 !important; font-size: 0.88rem !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    color: #1b4332 !important; border-bottom-color: #2d6a4f !important;
}

/* 입력창-버튼 수직 정렬 */
[data-testid="stHorizontalBlock"] {
    align-items: center !important;
}
[data-testid="stHorizontalBlock"] .stTextInput {
    margin-bottom: 0 !important;
}
[data-testid="stHorizontalBlock"] [data-testid="stButton"] {
    margin-bottom: 0 !important;
}
</style>
<div class="deco-blob-1"></div>
<div class="deco-blob-2"></div>
""", unsafe_allow_html=True)

# session_state 초기화
if "history" not in st.session_state:
    st.session_state["history"] = []
if "agent_data" not in st.session_state:
    st.session_state["agent_data"] = False
if "agent_analysis" not in st.session_state:
    st.session_state["agent_analysis"] = False
if "agent_report" not in st.session_state:
    st.session_state["agent_report"] = False

# 사이드바
with st.sidebar:
    st.markdown("### AI 재무 분석")
    st.divider()
    st.markdown("**팀**")
    st.markdown("SDIC AI Team 2")
    st.markdown("**분석 기업**")
    st.markdown(st.session_state.get("company", "—"))
    st.markdown("**현재 주차**")
    st.markdown("4주차")
    st.divider()

    st.markdown("**에이전트 실행 상태**")
    fs = st.session_state.get("final_state", {})
    agent_states = [
        ("Data Agent",     st.session_state["agent_data"]     or bool(fs.get("financials"))),
        ("Analysis Agent", st.session_state["agent_analysis"] or bool(fs.get("analysis"))),
        ("Report Agent",   st.session_state["agent_report"]   or bool(fs.get("pdf_path"))),
    ]
    for label, done in agent_states:
        rc = "done" if done else "pending"
        st.markdown(f"""<div class="step-row {rc}">
            <div class="step-dot {rc}"></div>
            <span class="step-label {rc}">{label}</span>
        </div>""", unsafe_allow_html=True)

    st.divider()

    if st.session_state["history"]:
        st.markdown("**최근 분석 기업**")
        for name in reversed(st.session_state["history"]):
            if st.button(name, key=f"hist_{name}", use_container_width=True):
                st.session_state["selected_company"] = name
        st.divider()

    data_source = st.session_state.get("final_state", {}).get("data_source")
    if data_source:
        label = "캐시" if data_source == "cache" else "DART"
        st.markdown(f'<span class="tag-green">● 데이터 소스: {label}</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="tag-green">● DART API 연동</span>', unsafe_allow_html=True)

# 히어로 배너
st.markdown("""
<div class="hero-banner fade-in">
    <div class="hero-badge">SDIC AI Team 2 · 4주차</div>
    <div class="hero-title">AI <span>재무 컨설팅</span><br>대시보드</div>
    <div class="hero-sub">기업명을 입력하면 DART 실데이터 기반 재무 분석과 Claude AI 인사이트를 제공합니다.</div>
</div>
""", unsafe_allow_html=True)

# 입력 영역
col1, col2 = st.columns([5, 1])
with col1:
    default_company = st.session_state.pop("selected_company", "")
    company = st.text_input("기업명", value=default_company, placeholder="기업명을 입력하세요  ↩", label_visibility="collapsed")
with col2:
    analyze_btn = st.button("분석 시작", type="primary", use_container_width=True)

if analyze_btn or default_company:
    if not company:
        st.error("기업명을 입력해주세요.")
    else:
        st.session_state.pop("final_state", None)
        st.session_state["agent_data"] = False
        st.session_state["agent_analysis"] = False
        st.session_state["agent_report"] = False

        progress_placeholder = st.empty()
        steps = ["Data Agent", "Analysis Agent", "Report Agent"]

        def render_progress(current_step: int):
            html = '<div style="display:flex;gap:1rem;align-items:center;padding:1rem 0;">'
            for i, name in enumerate(steps):
                if i < current_step:
                    color, icon = "#40916c", "✓"
                elif i == current_step:
                    color, icon = "#2d6a4f", "◌"
                else:
                    color, icon = "#c8d8c9", "○"
                html += f'<div style="display:flex;align-items:center;gap:0.4rem;">'
                html += f'<span style="color:{color};font-weight:700;font-size:0.9rem;">{icon} {name}</span>'
                if i < len(steps) - 1:
                    html += '<span style="color:#d0e8d3;font-size:0.8rem;margin:0 0.2rem;">→</span>'
                html += '</div>'
            html += '</div>'
            progress_placeholder.markdown(html, unsafe_allow_html=True)

        render_progress(0)

        with st.spinner(f"{company} 분석 중..."):
            pipeline = build_graph()
            graph_state = pipeline.invoke({
                "request": f"{company} 재무 분석해줘",
                "company": company,
                "next_agent": "",
                "financials": {},
                "analysis": "",
                "industry": "",
                "industry_trend": "",
                "industry_specific": "",
                "competitors": {},
                "competitor_analysis": "",
                "industry": "",
                "industry_trend": "",
                "industry_specific": "",
                "result": "",
                "pdf_path": "",
            })

        render_progress(3)

        # 결과를 session_state에 저장 → PDF 다운로드 후 re-run에서도 화면 유지
        st.session_state["final_state"]    = graph_state
        st.session_state["company"]        = company
        st.session_state["agent_data"]     = True
        st.session_state["agent_analysis"] = bool(graph_state.get("analysis"))
        st.session_state["agent_report"]   = bool(graph_state.get("pdf_path"))

        if company not in st.session_state["history"]:
            st.session_state["history"].append(company)

        if not graph_state.get("financials"):
            st.error(graph_state.get("result", f"'{company}' 데이터를 찾을 수 없습니다."))

# 결과 렌더링 — submitted 블록 밖에서 실행 (PDF 클릭 후 re-run에도 유지)
if "final_state" in st.session_state:
    final_state = st.session_state["final_state"]
    company     = st.session_state["company"]

    financials = final_state.get("financials", {})
    analysis   = final_state.get("analysis", "")
    pdf_path   = final_state.get("pdf_path", "")

    if financials:
        sorted_items = sorted(financials.items())
        latest_year  = sorted_items[-1][0]
        latest       = sorted_items[-1][1]
        prev         = sorted_items[-2][1] if len(sorted_items) >= 2 else None
        num_years    = len(financials)

        # DataFrame 생성
        df = pd.DataFrame([
            {
                "연도": year,
                "매출액 (억원)": v["매출액"],
                "영업이익 (억원)": v["영업이익"],
                "순이익 (억원)": v["순이익"],
                "영업이익률 (%)": round(v["영업이익"] / v["매출액"] * 100, 1) if v["매출액"] else 0,
            }
            for year, v in sorted_items
        ])

        def delta_pct(curr, prev_val):
            if prev_val is None or prev_val == 0:
                return None
            return f'{(curr - prev_val) / abs(prev_val) * 100:+.1f}%'

        latest_rev    = latest["매출액"]
        latest_op     = latest["영업이익"]
        latest_net    = latest["순이익"]
        latest_margin = round(latest_op / latest_rev * 100, 1) if latest_rev else 0

        prev_rev    = prev["매출액"]    if prev else None
        prev_op     = prev["영업이익"]  if prev else None
        prev_net    = prev["순이익"]    if prev else None
        prev_margin = round(prev_op / prev_rev * 100, 1) if (prev and prev_rev) else None
        delta_margin = f'{latest_margin - prev_margin:+.1f}%p' if prev_margin is not None else None

        def fmt(val):
            if val >= 10000:
                return f'{val/10000:.1f} 조원'
            return f'{val:,} 억원'

        tab1, tab2, tab3, tab4 = st.tabs(["재무 데이터", "산업 분석", "Claude 분석", "AI와 대화하기"])

        with tab1:
            # KPI 카드 4장
            st.markdown(f'<div class="section-header">핵심 지표 — {latest_year}년</div>', unsafe_allow_html=True)
            c1, c2, c3, c4 = st.columns(4)
            c1.metric(f'매출액 ({latest_year})',   fmt(latest_rev), delta_pct(latest_rev, prev_rev))
            c2.metric(f'영업이익 ({latest_year})', fmt(latest_op),  delta_pct(latest_op,  prev_op))
            c3.metric(f'순이익 ({latest_year})',   fmt(latest_net), delta_pct(latest_net, prev_net))
            c4.metric(f'영업이익률 ({latest_year})', f'{latest_margin:.1f}%', delta_margin)

            # 재무 테이블
            st.markdown(f'<div class="section-header">{company} {num_years}개년 재무 현황</div>', unsafe_allow_html=True)
            st.dataframe(df.set_index("연도"), use_container_width=True)
            st.markdown('<div class="source-text">출처: 금융감독원 전자공시시스템 (DART) · dart.fss.or.kr</div>', unsafe_allow_html=True)

            # 3지표 추이 차트
            st.markdown(f'<div class="section-header">{company} {num_years}개년 재무 추이</div>', unsafe_allow_html=True)
            fig_main = px.line(
                df, x="연도",
                y=["매출액 (억원)", "영업이익 (억원)", "순이익 (억원)"],
                markers=True,
                title=f"{company} 매출액 / 영업이익 / 순이익 추이",
                color_discrete_sequence=["#2d6a4f", "#40916c", "#74c69d"],
            )
            fig_main.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Pretendard, sans-serif", size=12, color="#3a4a3d"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                margin=dict(l=0, r=0, t=50, b=0),
                xaxis=dict(showgrid=False, linecolor="#d0e8d3"),
                yaxis=dict(gridcolor="rgba(200,230,210,0.4)", linecolor="#d0e8d3",
                           tickformat=",", title="금액 (억원)"),
                height=360,
            )
            st.plotly_chart(fig_main, use_container_width=True)

            # 영업이익률 차트
            st.markdown(f'<div class="section-header">{company} 영업이익률 추이</div>', unsafe_allow_html=True)
            fig_margin = px.line(
                df, x="연도", y="영업이익률 (%)",
                markers=True,
                title=f"{company} 영업이익률 추이",
            )
            fig_margin.update_traces(line_color="#FF6B6B")
            fig_margin.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Pretendard, sans-serif", size=12, color="#3a4a3d"),
                margin=dict(l=0, r=0, t=50, b=0),
                xaxis=dict(showgrid=False, linecolor="#d0e8d3"),
                yaxis=dict(gridcolor="rgba(200,230,210,0.4)", linecolor="#d0e8d3",
                           title="영업이익률 (%)"),
                height=300,
            )
            st.plotly_chart(fig_margin, use_container_width=True)

            # YoY 성장률 표
            st.markdown(f'<div class="section-header">전년 대비 성장률 (YoY)</div>', unsafe_allow_html=True)
            yoy = df[["연도"]].copy()
            for col in ["매출액 (억원)", "영업이익 (억원)", "순이익 (억원)"]:
                yoy[col + " YoY"] = df[col].pct_change().apply(
                    lambda x: f"{x*100:+.1f}%" if pd.notna(x) else "—"
                )
            st.dataframe(yoy[yoy["연도"] != sorted_items[0][0]].set_index("연도"), use_container_width=True)

            # 경쟁사 비교 섹션
            competitors = final_state.get("competitors", {})
            competitor_analysis = final_state.get("competitor_analysis", "")

            if competitors:
                st.markdown(f'<div class="section-header">{company} vs 경쟁사 비교</div>', unsafe_allow_html=True)

                # 경쟁사 데이터 준비
                comp_data = []
                for comp_name, comp_financials in competitors.items():
                    if not comp_financials:
                        continue
                    latest_comp_year = max(comp_financials.keys())
                    latest_comp = comp_financials[latest_comp_year]
                    comp_revenue = latest_comp.get("매출액", 0)
                    comp_op_profit = latest_comp.get("영업이익", 0)
                    comp_op_margin = (comp_op_profit / comp_revenue * 100) if comp_revenue > 0 else 0

                    comp_data.append({
                        "기업명": comp_name,
                        "매출액 (억원)": comp_revenue,
                        "영업이익률 (%)": round(comp_op_margin, 1),
                    })

                # 주 기업 데이터 추가
                main_comp_data = {
                    "기업명": company,
                    "매출액 (억원)": latest_rev,
                    "영업이익률 (%)": latest_margin,
                }
                comp_data.insert(0, main_comp_data)

                comp_df = pd.DataFrame(comp_data)

                # 매출액 비교 차트
                col1, col2 = st.columns(2)

                with col1:
                    fig_revenue = px.bar(
                        comp_df,
                        x="기업명",
                        y="매출액 (억원)",
                        title="매출액 비교",
                        color="기업명",
                        color_discrete_sequence=["#2d6a4f", "#74c69d", "#a8d5ba", "#d8f3dc"],
                    )
                    fig_revenue.update_layout(
                        plot_bgcolor="rgba(0,0,0,0)",
                        paper_bgcolor="rgba(0,0,0,0)",
                        font=dict(family="Pretendard, sans-serif", size=11, color="#3a4a3d"),
                        showlegend=False,
                        margin=dict(l=0, r=0, t=40, b=0),
                        xaxis=dict(showgrid=False, linecolor="#d0e8d3"),
                        yaxis=dict(gridcolor="rgba(200,230,210,0.4)", linecolor="#d0e8d3",
                                   tickformat=",", title="매출액 (억원)"),
                        height=300,
                    )
                    fig_revenue.update_traces(width=0.4)
                    st.plotly_chart(fig_revenue, use_container_width=True)

                with col2:
                    fig_margin = px.bar(
                        comp_df,
                        x="기업명",
                        y="영업이익률 (%)",
                        title="영업이익률 비교",
                        color="기업명",
                        color_discrete_sequence=["#FF6B6B", "#FF9999", "#FFB3B3", "#FFD9D9"],
                    )
                    fig_margin.update_layout(
                        plot_bgcolor="rgba(0,0,0,0)",
                        paper_bgcolor="rgba(0,0,0,0)",
                        font=dict(family="Pretendard, sans-serif", size=11, color="#3a4a3d"),
                        showlegend=False,
                        margin=dict(l=0, r=0, t=40, b=0),
                        xaxis=dict(showgrid=False, linecolor="#d0e8d3"),
                        yaxis=dict(gridcolor="rgba(200,230,210,0.4)", linecolor="#d0e8d3",
                                   title="영업이익률 (%)"),
                        height=300,
                    )
                    fig_margin.update_traces(width=0.4)
                    st.plotly_chart(fig_margin, use_container_width=True)

                # 경쟁사 비교 분석
                if competitor_analysis:
                    st.markdown(f'<div class="section-header">경쟁사 분석</div>', unsafe_allow_html=True)
                    comp_clean = re.sub(r'#+\s*', '', competitor_analysis)
                    comp_clean = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', comp_clean)
                    comp_clean = re.sub(r'\n\n+', '<br><br>', comp_clean)
                    comp_clean = re.sub(r'\n-\s*', '<br>• ', comp_clean)
                    st.markdown(f'<div class="analysis-card fade-in">{comp_clean}</div>', unsafe_allow_html=True)

        with tab2:
            industry = final_state.get("industry", "")
            industry_trend = final_state.get("industry_trend", "")
            industry_specific = final_state.get("industry_specific", "")

            if industry:
                st.markdown(f'<div class="section-header">{industry}</div>', unsafe_allow_html=True)

                if industry_trend:
                    st.markdown(f'<div class="section-header">산업 동향</div>', unsafe_allow_html=True)
                    trend_clean = re.sub(r'#+\s*', '', industry_trend)
                    trend_clean = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', trend_clean)
                    trend_clean = re.sub(r'\n\n+', '<br><br>', trend_clean)
                    trend_clean = re.sub(r'\n-\s*', '<br>• ', trend_clean)
                    st.markdown(f'<div class="analysis-card fade-in">{trend_clean}</div>', unsafe_allow_html=True)

                if industry_specific:
                    st.markdown(f'<div class="section-header">맞춤 분석</div>', unsafe_allow_html=True)
                    spec_clean = re.sub(r'#+\s*', '', industry_specific)
                    spec_clean = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', spec_clean)
                    spec_clean = re.sub(r'\n\n+', '<br><br>', spec_clean)
                    spec_clean = re.sub(r'\n-\s*', '<br>• ', spec_clean)
                    st.markdown(f'<div class="analysis-card fade-in">{spec_clean}</div>', unsafe_allow_html=True)
            else:
                st.info("산업 분석 결과가 없습니다.")

        with tab3:
            if analysis:
                anal_clean = re.sub(r'#+\s*', '', analysis)
                anal_clean = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', anal_clean)
                anal_clean = re.sub(r'\n\n+', '<br><br>', anal_clean)
                anal_clean = re.sub(r'\n-\s*', '<br>• ', anal_clean)
                st.markdown(f'<div class="analysis-card fade-in">{anal_clean}</div>', unsafe_allow_html=True)
            else:
                st.info("분석 결과가 없습니다.")

        with tab4:
            st.markdown('<div class="section-header">AI 질문</div>', unsafe_allow_html=True)

            TEXT2SQL_KEYWORDS = {"평균", "합계", "최대", "최소", "몇", "총", "얼마", "비교", "순위", "합산"}

            def auto_route(question: str) -> str:
                if any(kw in question for kw in TEXT2SQL_KEYWORDS):
                    return "Text2SQL"
                return "RAG"

            mode = st.radio(
                "모드 선택",
                ["자동", "RAG", "Text2SQL"],
                horizontal=True,
                label_visibility="collapsed",
            )
            mode_desc = {
                "자동": "질문 내용에 따라 자동으로 검색 방식을 선택합니다. 수치·계산 관련 질문(평균, 합계, 최대 등)은 Text2SQL로, 나머지는 RAG로 연결됩니다.",
                "RAG": "보고서·텍스트 기반으로 유사한 내용을 찾아 Claude가 답변합니다. '왜', '어떻게', '전망' 같은 질적 질문에 적합합니다.",
                "Text2SQL": "숫자·통계 질문을 SQL로 변환해 데이터베이스에서 직접 조회합니다. '평균 매출은?', '최대 영업이익 연도는?' 같은 질문에 적합합니다.",
            }
            st.caption(mode_desc[mode])

            q_col, btn_col = st.columns([5, 1])
            with q_col:
                question = st.text_input("질문", placeholder="예: 2023년 영업이익이 왜 떨어졌나요?", label_visibility="collapsed")
            with btn_col:
                ask_btn = st.button("질문하기", type="primary", use_container_width=True)

            def render_ai_answer():
                res = st.session_state.get("ai_result")
                if not res:
                    return
                actual_mode = res["mode"]
                st.caption(f"모드: **{actual_mode}**{'  *(자동 선택)*' if res['auto'] else ''}")
                if actual_mode == "RAG":
                    hits = res.get("hits", [])
                    if hits:
                        st.markdown('<div class="section-header">검색 결과 (상위 3개)</div>', unsafe_allow_html=True)
                        for i, hit in enumerate(hits):
                            score = hit["score"]
                            chunk = hit["text"]
                            st.markdown(
                                f'<div style="background:rgba(45,106,79,0.06);border-left:3px solid #74c69d;border-radius:10px;padding:0.7rem 1rem;margin-bottom:0.5rem;">'
                                f'<span style="font-size:0.72rem;color:#8aab8e;font-weight:600;">발췌 {i+1} · 유사도 {score:.3f}</span><br>'
                                f'<span style="font-size:0.85rem;color:#2c3e30;">{chunk}</span>'
                                f'</div>',
                                unsafe_allow_html=True,
                            )
                    st.markdown('<div class="section-header">Claude 답변</div>', unsafe_allow_html=True)
                    raw = res["answer"]
                    clean = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', raw)
                    if "결론:" in clean:
                        body, conclusion = clean.split("결론:", 1)
                        st.markdown(f'<div class="analysis-card fade-in">{body}</div>', unsafe_allow_html=True)
                        st.markdown(f'<div style="background:rgba(45,106,79,0.13);border-left:4px solid #40916c;border-radius:12px;padding:1rem 1.3rem;margin-top:1rem;"><span style="font-size:1.08rem;font-weight:800;color:#1b4332;">결론</span><span style="font-size:1.05rem;font-weight:700;color:#1b4332;">{conclusion}</span></div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="analysis-card fade-in">{clean}</div>', unsafe_allow_html=True)
                else:
                    if res.get("sql"):
                        st.markdown('<div class="section-header">생성된 SQL</div>', unsafe_allow_html=True)
                        st.code(res["sql"], language="sql")
                    if res.get("success") and res.get("df") is not None and not res["df"].empty:
                        st.markdown('<div class="section-header">결과</div>', unsafe_allow_html=True)
                        st.dataframe(res["df"], use_container_width=True)
                    else:
                        st.markdown(f'<div class="analysis-card fade-in">{res.get("message", "결과가 없습니다.")}</div>', unsafe_allow_html=True)

            if ask_btn:
                if not question:
                    st.error("질문을 입력해주세요.")
                else:
                    actual_mode = auto_route(question) if mode == "자동" else mode
                    st.caption(f"모드: **{actual_mode}**{'  *(자동 선택)*' if mode == '자동' else ''}")

                    if actual_mode == "RAG":
                        if RAG_AVAILABLE:
                            with st.spinner("RAG 검색 중..."):
                                hits, all_chunks = rag_search(company, question, top_k=3)
                                all_retrieved = [(1.0, c) for c in all_chunks]
                                ans = rag_answer(question, all_retrieved)
                            st.session_state["ai_result"] = {"mode": "RAG", "auto": mode == "자동", "answer": ans, "hits": hits}
                        else:
                            st.markdown("""<div style="background:rgba(45,106,79,0.07);border-radius:14px;padding:1rem 1.2rem;border:1.5px solid #c8e6c9;color:#2d6a4f;font-size:0.88rem;">
                            RAG 모듈 연결 준비 중입니다. 팀원 작업 완료 후 자동으로 활성화됩니다.
                            </div>""", unsafe_allow_html=True)

                    else:
                        if TEXT2SQL_AVAILABLE:
                            with st.spinner("SQL 생성 중..."):
                                result = text2sql_query(question, company)
                            st.session_state["ai_result"] = {
                                "mode": "Text2SQL", "auto": mode == "자동",
                                "sql": result.get("sql", ""),
                                "df": result.get("df"),
                                "success": result.get("success", False),
                                "message": result.get("message", ""),
                            }
                        else:
                            st.markdown("""<div style="background:rgba(45,106,79,0.07);border-radius:14px;padding:1rem 1.2rem;border:1.5px solid #c8e6c9;color:#2d6a4f;font-size:0.88rem;">
                            Text2SQL 모듈 연결 준비 중입니다. 팀원 작업 완료 후 자동으로 활성화됩니다.
                            </div>""", unsafe_allow_html=True)

            render_ai_answer()

        # PDF 다운로드 (탭 밖)
        if pdf_path and os.path.exists(pdf_path):
            st.markdown("<br>", unsafe_allow_html=True)
            with open(pdf_path, "rb") as f:
                st.download_button(
                    label="PDF 리포트 다운로드",
                    data=f,
                    file_name=f"{company}_재무분석.pdf",
                    mime="application/pdf",
                )

        st.toast(f"{company} 분석 완료!", icon="✅")
