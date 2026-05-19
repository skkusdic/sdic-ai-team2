import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from claude_client import ask


def _get_industry(company: str) -> str:
    prompt = (
        f"'{company}'의 주요 사업 분야와 속하는 산업 섹터를 한 문장으로만 답해줘. "
        "예시: '반도체 메모리 및 파운드리 산업'"
    )
    return ask(prompt, max_tokens=80).strip()


def _trend_analysis(company: str, industry: str) -> str:
    prompt = f"""'{company}'이 속한 '{industry}' 산업의 최근 동향을 전문 리포트 스타일로 분석해줘.

아래 항목별로 각 2~3문장씩 한국어로 작성해줘:

1. 시장 규모 및 성장률 추세
   - 글로벌 시장 규모와 CAGR, 국내 시장 현황

2. 핵심 기술 변화 및 혁신 방향
   - 최근 주목받는 기술 트렌드와 패러다임 전환

3. 정책·규제 환경
   - 주요국 정부 정책, 보조금/규제, 공급망 재편 이슈

4. 향후 전망
   - 단기(1~2년) 및 중기(3~5년) 시장 전망과 핵심 변수

번호와 소제목 포함하여 작성해줘."""
    return ask(prompt, max_tokens=900).strip()


def _specific_analysis(company: str, industry: str, financials: dict) -> str:
    sorted_f = sorted(financials.items())
    if sorted_f:
        yr, dat = sorted_f[-1]
        rev = dat.get('매출액', 0)
        op  = dat.get('영업이익', 0)
        margin = round(op / rev * 100, 1) if rev else 0
        fin_ctx = f"{yr}년 기준 매출액 {rev:,}억원, 영업이익률 {margin:.1f}%"
    else:
        fin_ctx = "재무 데이터 없음"

    prompt = f"""'{company}'({industry})에 대한 산업별 맞춤 심층 분석을 전문 리포트 스타일로 작성해줘.

기업 재무 현황: {fin_ctx}

아래 항목별로 각 2~3문장씩 한국어로 작성해줘:

1. 산업 특화 핵심 지표
   - 이 산업에서 중요한 KPI와 '{company}'의 해당 지표 현황
   (예: 반도체 → HBM 점유율/메모리 ASP, 자동차 → 전동화율/CAPA 가동률,
    금융 → BIS 비율/NIM/대손충당금, 유통 → SSS/재고회전율, 바이오 → 파이프라인 임상 단계)

2. 규제 환경 및 정책 리스크
   - 이 산업에 직접 영향을 주는 규제·정책과 대응 방향

3. 산업 사이클 현황
   - 현재 업황이 사이클 어느 위치에 있는지 (상승 초입/정점/하락/바닥) 및 전환 신호

4. 경쟁력 평가
   - 위 지표와 사이클 분석 기반 '{company}'의 산업 내 강점·약점 요약

번호와 소제목 포함하여 작성해줘."""
    return ask(prompt, max_tokens=900).strip()


def industry_agent(state: dict) -> dict:
    company   = state.get('company', '')
    financials = state.get('financials', {})

    if not company:
        return {**state, 'industry': '', 'industry_trend': '', 'industry_specific': ''}

    print(f"[Industry Agent] {company} 산업 분석 중...")

    industry = _get_industry(company)
    print(f"[Industry Agent] 산업 분류: {industry}")

    trend    = _trend_analysis(company, industry)
    specific = _specific_analysis(company, industry, financials)

    print("[Industry Agent] 완료")
    return {
        **state,
        'industry':           industry,
        'industry_trend':     trend,
        'industry_specific':  specific,
    }


if __name__ == '__main__':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    result = industry_agent({
        'company': '삼성전자',
        'financials': {
            2023: {'매출액': 2589354, '영업이익': 65669,  '순이익': 154871},
            2024: {'매출액': 3000000, '영업이익': 320000, '순이익': 280000},
        },
    })
    print('=' * 60)
    print('[산업]', result['industry'])
    print()
    print('[동향 분석]\n', result['industry_trend'])
    print()
    print('[맞춤 분석]\n', result['industry_specific'])
