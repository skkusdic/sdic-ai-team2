import os
import sqlite3

import dart_fss as dart
from dotenv import load_dotenv

load_dotenv()

DB_PATH = "financials.db"

dart.set_api_key(os.environ["DART_API_KEY"])

_corp_list_cache = None

_LABEL_MAP = {
    "매출액": "매출액",
    "수익(매출액)": "매출액",
    "영업이익": "영업이익",
    "영업이익(손실)": "영업이익",
    "당기순이익": "순이익",
    "당기순이익(손실)": "순이익",
}

_TARGET_KEYS = {"매출액", "영업이익", "순이익"}


def _parse_fs(is_df) -> dict:
    """MultiIndex DataFrame에서 연도별 {매출액, 영업이익, 순이익} 추출 (단위: 억원)."""
    # 연도 컬럼: ('20220101-20221231', ...) 형태에서 시작 연도 추출
    year_cols = {
        col: int(col[0][:4])
        for col in is_df.columns
        if isinstance(col, tuple) and len(col[0]) == 17 and col[0][8] == "-"
    }

    top_level = [c for c in is_df.columns.get_level_values(0) if "손익계산서" in c or "Income" in c]
    label_col = (top_level[0], "label_ko") if top_level else None
    if label_col is None or label_col not in is_df.columns:
        return {}

    result: dict[int, dict] = {}
    for _, row in is_df.iterrows():
        label = str(row[label_col]).strip()
        mapped = _LABEL_MAP.get(label)
        if not mapped:
            continue
        for col, year in year_cols.items():
            if year not in range(2021, 2026):
                continue
            result.setdefault(year, {})
            if mapped not in result[year]:
                try:
                    result[year][mapped] = int(float(str(row[col]).replace(",", ""))) // 100_000_000
                except (ValueError, TypeError):
                    result[year][mapped] = 0

    return {yr: m for yr, m in result.items() if m.keys() >= _TARGET_KEYS}


def _find_corp(corp_list, company_name: str):
    # 정확히 일치하는 기업 우선, 없으면 이름 포함 검색 후 가장 유사한 것 선택
    exact = corp_list.find_by_corp_name(company_name, exactly=True)
    if exact:
        return exact[0]
    fuzzy = corp_list.find_by_corp_name(company_name, exactly=False)
    if not fuzzy:
        return None
    # 이름이 정확히 같은 것 우선, 없으면 첫 번째
    for c in fuzzy:
        if c.corp_name == company_name:
            return c
    return fuzzy[0]


def _fetch_from_dart(company_name: str) -> dict:
    global _corp_list_cache
    if _corp_list_cache is None:
        _corp_list_cache = dart.get_corp_list()
    corp = _find_corp(_corp_list_cache, company_name)
    if corp is None:
        return {}
    try:
        fs = corp.extract_fs(bgn_de="20210101")
    except Exception:
        return {}
    is_df = fs._statements.get("is")
    if is_df is None or is_df.empty:
        return {}
    return _parse_fs(is_df)


def _save_to_db(company_name: str, data: dict) -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS financials (
            company  TEXT,
            year     INTEGER,
            매출액   INTEGER,
            영업이익 INTEGER,
            순이익   INTEGER,
            PRIMARY KEY (company, year)
        )
    """)
    for year, metrics in data.items():
        cur.execute("""
            INSERT OR REPLACE INTO financials (company, year, 매출액, 영업이익, 순이익)
            VALUES (?, ?, ?, ?, ?)
        """, (company_name, year, metrics["매출액"], metrics["영업이익"], metrics["순이익"]))
    conn.commit()
    conn.close()


def get_financials(company_name: str) -> dict:
    data = _fetch_from_dart(company_name)
    if data:
        _save_to_db(company_name, data)
    return data


if __name__ == "__main__":
    data = get_financials("삼성전자")
    if not data:
        print("데이터를 가져오지 못했습니다.")
    else:
        print(f"{'연도':<6} {'매출액':>12} {'영업이익':>12} {'순이익':>12}  (단위: 억원)")
        print("-" * 50)
        for year, metrics in sorted(data.items()):
            print(
                f"{year:<6} "
                f"{metrics['매출액']:>12,} "
                f"{metrics['영업이익']:>12,} "
                f"{metrics['순이익']:>12,}"
            )
