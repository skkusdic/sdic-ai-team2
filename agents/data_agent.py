import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from data import get_financials, _load_from_db


def run_data_agent(state: dict) -> dict:
    company = state["company"]

    # 캐시 먼저 조회 (data.py의 financials.db 기준)
    cached = _load_from_db(company)
    if cached:
        print(f"[Data Agent] {company} — 캐시 hit (SQLite), {len(cached)}개년")
        return {
            **state,
            "financials": cached,
            "data_source": "cache",
            "next_agent": "analysis_agent",
        }

    # 캐시 miss → DART 호출 및 저장 (get_financials 내부에서 처리)
    print(f"[Data Agent] {company} — 캐시 miss, DART 호출 중...")
    financials = get_financials(company)

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
