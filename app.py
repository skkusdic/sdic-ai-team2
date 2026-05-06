import streamlit as st
import pandas as pd
from graph import build_graph

st.set_page_config(page_title="AI 재무 컨설팅 어시스턴트", page_icon="📊", layout="wide")

st.markdown("""
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');

html, body, [class*="css"], .stMarkdown, .stTextInput, .stButton, p, div {
    font-family: 'Pretendard', -apple-system, sans-serif !important;
}

/* 전체 배경 */
.stApp {
    background-color: #f7f9f7;
    overflow: hidden;
}

/* 무지개 뿌연 데코 블러 원형들 */
.stApp::before {
    content: '';
    position: fixed;
    top: -120px;
    left: -80px;
    width: 480px;
    height: 480px;
    background: radial-gradient(circle, rgba(134,197,152,0.35) 0%, rgba(100,180,140,0.15) 50%, transparent 70%);
    border-radius: 50%;
    filter: blur(60px);
    z-index: 0;
    pointer-events: none;
}
.stApp::after {
    content: '';
    position: fixed;
    top: 60px;
    right: -100px;
    width: 420px;
    height: 420px;
    background: radial-gradient(circle, rgba(180,220,160,0.28) 0%, rgba(120,200,180,0.12) 50%, transparent 70%);
    border-radius: 50%;
    filter: blur(70px);
    z-index: 0;
    pointer-events: none;
}

/* 추가 데코 블러들 */
.deco-blob-1 {
    position: fixed;
    bottom: 100px;
    left: 30%;
    width: 360px;
    height: 360px;
    background: radial-gradient(circle, rgba(160,220,140,0.2) 0%, rgba(100,180,160,0.08) 60%, transparent 80%);
    border-radius: 50%;
    filter: blur(80px);
    z-index: 0;
    pointer-events: none;
}
.deco-blob-2 {
    position: fixed;
    top: 40%;
    right: 15%;
    width: 280px;
    height: 280px;
    background: radial-gradient(circle, rgba(200,230,180,0.22) 0%, rgba(150,210,180,0.1) 60%, transparent 80%);
    border-radius: 50%;
    filter: blur(65px);
    z-index: 0;
    pointer-events: none;
}

/* 사이드바 */
[data-testid="stSidebar"] {
    background-color: rgba(255,255,255,0.85);
    backdrop-filter: blur(12px);
    border-right: 1px solid #e2ebe3;
    z-index: 10;
}
[data-testid="stSidebar"] .stMarkdown p {
    color: #3a4a3d;
    font-size: 0.88rem;
    padding: 0.2rem 0;
}

/* 메인 타이틀 숨기기 */
h1 { display: none; }

/* 페이지 헤더 */
.page-header {
    font-size: 2rem;
    font-weight: 800;
    color: #1a2e1f;
    line-height: 1.2;
    margin-bottom: 0.3rem;
}
/* 하이라이트 긁는 효과 */
.highlight-text {
    background: linear-gradient(120deg, #86c598 0%, #52b788 100%);
    background-repeat: no-repeat;
    background-size: 100% 38%;
    background-position: 0 88%;
    padding: 0 2px;
    color: #1a2e1f;
}
.page-sub {
    font-size: 0.9rem;
    color: #6b7f6e;
    margin-bottom: 2rem;
}

/* 검색창 */
.stTextInput > div > div > input {
    border-radius: 14px !important;
    border: 2.5px solid #2d6a4f !important;
    padding: 0.7rem 1.2rem !important;
    font-family: 'Pretendard', sans-serif !important;
    font-size: 0.95rem !important;
    font-weight: 700 !important;
    background: rgba(255,255,255,0.9) !important;
    color: #1a2e1f !important;
    transition: all 0.15s ease !important;
}
.stTextInput > div > div > input:focus {
    border-color: #1b4332 !important;
    box-shadow: none !important;
    background: #ffffff !important;
}
.stTextInput > div > div > input::placeholder {
    color: #a0b8a6 !important;
    font-weight: 400 !important;
}

/* 버튼 */
[data-testid="stButton"] > button {
    background-color: #2d6a4f !important;
    color: white !important;
    border-radius: 14px !important;
    border: 2.5px solid #2d6a4f !important;
    font-family: 'Pretendard', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    padding: 0.7rem 1.4rem !important;
    transition: all 0.15s ease !important;
    letter-spacing: -0.01em !important;
}
[data-testid="stButton"] > button:hover {
    background-color: #1b4332 !important;
    border-color: #1b4332 !important;
}

/* 지표 카드 */
.metric-card {
    background: rgba(255,255,255,0.88);
    backdrop-filter: blur(10px);
    border-radius: 18px;
    padding: 1.4rem 1.6rem;
    box-shadow: 0 4px 20px rgba(45,106,79,0.08);
    border: 1.5px solid #d8ead9;
}
.metric-label {
    font-size: 0.75rem;
    color: #7a9b7e;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    margin-bottom: 0.5rem;
}
.metric-value {
    font-size: 1.55rem;
    font-weight: 800;
    color: #1a2e1f;
    letter-spacing: -0.03em;
}
.metric-sub {
    font-size: 0.75rem;
    color: #b0c8b3;
    margin-top: 0.35rem;
}

/* 섹션 헤더 */
.section-header {
    font-size: 1rem;
    font-weight: 700;
    color: #0d1f12;
    margin-bottom: 0.8rem;
    margin-top: 1.8rem;
    letter-spacing: -0.01em;
}

/* 분석 카드 */
.analysis-card {
    background: rgba(255,255,255,0.88);
    backdrop-filter: blur(10px);
    border-radius: 18px;
    padding: 1.8rem 2rem;
    box-shadow: 0 4px 20px rgba(45,106,79,0.08);
    border: 1.5px solid #d8ead9;
    line-height: 1.9;
    font-size: 0.92rem;
    color: #2c3e30;
}

/* 태그 */
.tag-green {
    display: inline-block;
    background: #d8f3dc;
    color: #1b4332;
    border-radius: 20px;
    padding: 0.2rem 0.75rem;
    font-size: 0.73rem;
    font-weight: 600;
    letter-spacing: 0.02em;
}

/* dataframe */
[data-testid="stDataFrame"] {
    border-radius: 16px !important;
    overflow: hidden;
    box-shadow: 0 4px 20px rgba(45,106,79,0.08);
    border: 1.5px solid #d8ead9 !important;
}
</style>

<!-- 추가 데코 블러 엘리먼트 -->
<div class="deco-blob-1"></div>
<div class="deco-blob-2"></div>
""", unsafe_allow_html=True)

# 사이드바
with st.sidebar:
    st.markdown("### 📊 AI 재무 분석")
    st.divider()
    st.markdown("**팀**")
    st.markdown("SDIC AI Team 2")
    st.markdown("**분석 기업**")
    st.markdown("삼성전자")
    st.markdown("**현재 주차**")
    st.markdown("2주차")
    st.divider()
    st.markdown('<span class="tag-green">● DART API 연동 준비중</span>', unsafe_allow_html=True)

# 페이지 헤더
st.markdown("""
<div class="page-header">
    <span class="highlight-text">재무 컨설팅 대시보드</span>
</div>
<div class="page-sub">기업명을 입력하면 재무 데이터와 Claude AI 분석을 제공합니다.</div>
""", unsafe_allow_html=True)

# 입력 영역
col1, col2 = st.columns([5, 1])
with col1:
    company = st.text_input("기업명", placeholder="기업명을 입력하세요  ↩", label_visibility="collapsed")
with col2:
    analyze_btn = st.button("분석 시작", type="primary", use_container_width=True)

if analyze_btn:
    if not company:
        st.warning("기업명을 입력해주세요.")
    else:
        with st.spinner("데이터 불러오는 중..."):
            pipeline = build_graph()
            state = pipeline.invoke({"company": company, "data": {}, "result": "", "analysis": ""})

        financials = state["data"]

        if not financials:
            st.error(f"'{company}' 데이터를 찾을 수 없습니다. 삼성전자로 다시 시도해보세요.")
        else:
            latest_year = max(financials.keys())
            latest = financials[latest_year]

            st.markdown(f'<div class="section-header">핵심 지표 — {latest_year}년</div>', unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">매출액</div>
                    <div class="metric-value">{latest['매출액']:,}억</div>
                    <div class="metric-sub">{latest_year}년 기준</div>
                </div>""", unsafe_allow_html=True)
            with c2:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">영업이익</div>
                    <div class="metric-value">{latest['영업이익']:,}억</div>
                    <div class="metric-sub">{latest_year}년 기준</div>
                </div>""", unsafe_allow_html=True)
            with c3:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">순이익</div>
                    <div class="metric-value">{latest['순이익']:,}억</div>
                    <div class="metric-sub">{latest_year}년 기준</div>
                </div>""", unsafe_allow_html=True)

            st.markdown(f'<div class="section-header">{company} 3개년 재무 현황</div>', unsafe_allow_html=True)
            df = pd.DataFrame([
                {
                    "연도": year,
                    "매출액 (억원)": v["매출액"],
                    "영업이익 (억원)": v["영업이익"],
                    "순이익 (억원)": v["순이익"],
                }
                for year, v in sorted(financials.items())
            ])
            st.dataframe(df.set_index("연도"), use_container_width=True)

            st.markdown('<div class="section-header">🤖 Claude AI 분석</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="analysis-card">{state["analysis"]}</div>', unsafe_allow_html=True)

            st.success("분석 완료!")
