import streamlit as st
import pandas as pd
import time

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
            time.sleep(1)

        df = pd.DataFrame({
            "연도": [2022, 2023, 2024],
            "매출액 (억원)": [3_023_515, 2_589_355, 3_008_147],
            "영업이익 (억원)": [433_766, 64_840, 326_634],
            "순이익 (억원)": [554_589, 154_871, 341_916],
        })

        st.subheader(f"{company} 재무 현황 (2022~2024)")
        st.dataframe(df.set_index("연도"), use_container_width=True)
        st.success("분석 완료!")
