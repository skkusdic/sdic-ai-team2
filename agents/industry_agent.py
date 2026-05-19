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
    prompt = (
        f"'{company}'이 속한 '{industry}' 산업 동향을 아래 4개 항목으로 작성해줘.\n"
        "규칙: 각 항목은 줄글 2문장만. 부제목·목록·구분선 없음. 반드시 마침표로 끝낼 것.\n\n"
        "1. 시장 규모 및 성장률 추세\n"
        "2. 핵심 기술 변화 및 혁신 방향\n"
        "3. 정책·규제 환경\n"
        "4. 향후 전망\n\n"
        "출력 형식 예시:\n"
        "1. 시장 규모 및 성장률 추세\n"
        "첫 번째 문장입니다. 두 번째 문장입니다.\n"
    )
    return ask(prompt, max_tokens=2500).strip()


def _specific_analysis(company: str, industry: str, financials: dict) -> str:
    sorted_f = sorted(financials.items())
    if sorted_f:
        yr, dat = sorted_f[-1]
        rev    = dat.get('매출액', 0)
        op     = dat.get('영업이익', 0)
        margin = round(op / rev * 100, 1) if rev else 0
        fin_ctx = f"{yr}년 매출액 {rev:,}억원, 영업이익률 {margin:.1f}%"
    else:
        fin_ctx = "재무 데이터 없음"

    prompt = (
        f"'{company}'({industry}) 산업별 맞춤 분석을 아래 4개 항목으로 작성해줘.\n"
        f"기업 현황: {fin_ctx}\n"
        "규칙: 각 항목은 줄글 2문장만. 부제목·목록·강점/약점 구분 없음. 반드시 마침표로 끝낼 것.\n\n"
        f"1. 산업 특화 핵심 지표 ({industry}에 맞는 KPI — 반도체면 HBM점유율/ASP, 금융이면 BIS비율/NIM 등)\n"
        "2. 규제 환경 및 정책 리스크\n"
        "3. 산업 사이클 현황 (상승초입/정점/하락/바닥 중 현재 위치)\n"
        f"4. '{company}' 경쟁력 평가\n\n"
        "출력 형식 예시:\n"
        "1. 산업 특화 핵심 지표\n"
        "첫 번째 문장입니다. 두 번째 문장입니다.\n"
    )
    return ask(prompt, max_tokens=2500).strip()


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
