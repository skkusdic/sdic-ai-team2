import streamlit as st
import pandas as pd
from graph import build_graph

st.set_page_config(page_title="AI 재무 컨설팅 어시스턴트", page_icon="📊", layout="wide")

with st.sidebar:
    st.header("프로젝트 정보")
    st.markdown("**팀 이름:** SDIC AI Team 2")
    st.markdown("**분석 기업:** 삼성전자")
    st.markdown("**현재 주차:** 2주차")

st.title("AI 재무 컨설팅 어시스턴트")

company = st.text_input("분석할 기업명을 입력하세요", placeholder="예: 삼성전자")

if st.button("분석 시작", type="primary"):
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
            df = pd.DataFrame([
                {
                    "연도": year,
                    "매출액 (억원)": v["매출액"],
                    "영업이익 (억원)": v["영업이익"],
                    "순이익 (억원)": v["순이익"],
                }
                for year, v in sorted(financials.items())
            ])

            st.subheader(f"{company} 재무 현황")
            st.dataframe(df.set_index("연도"), use_container_width=True)

            st.caption(state["result"])

            st.subheader("Claude AI 분석")
            st.markdown(state["analysis"])

            st.success("분석 완료!")
