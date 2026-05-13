import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from data import get_financials
from db import load_financials, save_financials


def run_data_agent(state: dict) -> dict:
    company = state["company"]

    # 캐시 먼저 조회
    cached = load_financials(company)
    if cached:
        print(f"[Data Agent] {company} — 캐시 hit (SQLite)")
        return {
            **state,
            "financials": cached,
            "data_source": "cache",
            "next_agent": "analysis_agent",
        }

    # 캐시 miss → DART 호출 후 저장
    print(f"[Data Agent] {company} — 캐시 miss, DART 호출 중...")
    financials = get_financials(company)
    if financials:
        save_financials(company, financials)
        print(f"[Data Agent] {company} — DART 데이터 저장 완료")

    return {
        **state,
        "financials": financials,
        "data_source": "dart",
        "next_agent": "analysis_agent" if financials else "no_data",
    }


if __name__ == "__main__":
    import pprint
    # 첫 번째 호출 — DART
    print("=== 첫 번째 호출 (DART 예상) ===")
    result = run_data_agent({"company": "삼성전자"})
    print(f"data_source: {result.get('data_source')}")
    pprint.pprint({k: v for k, v in result.items() if k != "financials"})

    # 두 번째 호출 — 캐시
    print("\n=== 두 번째 호출 (캐시 예상) ===")
    result2 = run_data_agent({"company": "삼성전자"})
    print(f"data_source: {result2.get('data_source')}")
