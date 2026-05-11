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
    "영업수익": "매출액",
    "영업이익": "영업이익",
    "영업이익(손실)": "영업이익",
    "당기순이익": "순이익",
    "당기순이익(손실)": "순이익",
}

_TARGET_KEYS = {"매출액", "영업이익", "순이익"}


def _parse_fs(is_df) -> dict:
    """MultiIndex DataFrame에서 연도별 {매출액, 영업이익, 순이익} 추출 (단위: 억원)."""
    year_cols = {
        col: int(col[0][:4])
        for col in is_df.columns
        if isinstance(col, tuple) and len(col[0]) == 17 and col[0][8] == "-"
    }

    # level_1 == 'label_ko' 인 컬럼을 직접 찾음
    label_col = next((c for c in is_df.columns if c[1] == "label_ko"), None)
    if label_col is None:
        return {}

    result: dict[int, dict] = {}
    for _, row in is_df.iterrows():
        label = str(row[label_col]).strip()
        mapped = _LABEL_MAP.get(label)
        if not mapped:
            continue
        for col, year in year_cols.items():
            if year not in range(2020, 2025):
                continue
            result.setdefault(year, {})
            if mapped not in result[year]:
                try:
                    result[year][mapped] = int(float(str(row[col]).replace(",", ""))) // 100_000_000
                except (ValueError, TypeError):
                    result[year][mapped] = 0

    return {yr: m for yr, m in result.items() if m.keys() >= _TARGET_KEYS}


def _find_corp(corp_list, company_name: str):
    # 1단계: 정확 일치 (상장사 우선)
    exact = corp_list.find_by_corp_name(company_name, exactly=True)
    if exact:
        listed = [c for c in exact if c.stock_code]
        return listed[0] if listed else exact[0]

    # 2단계: 띄어쓰기 제거 후 정확 일치
    normalized = company_name.replace(" ", "")
    fuzzy = corp_list.find_by_corp_name(normalized, exactly=True)
    if fuzzy:
        listed = [c for c in fuzzy if c.stock_code]
        return listed[0] if listed else fuzzy[0]

    # 3단계: substring 검색, 상장사 우선 + 이름 짧은 것 우선
    candidates = corp_list.find_by_corp_name(company_name, exactly=False)
    if not candidates:
        candidates = corp_list.find_by_corp_name(normalized, exactly=False)
    if not candidates:
        return None
    listed = [c for c in candidates if c.stock_code]
    pool = listed if listed else candidates
    return min(pool, key=lambda c: len(c.corp_name))


def _fetch_fs_statements(corp, separate: bool):
    """CFS(separate=False) 또는 OFS(separate=True)로 IS 조회. 실패 시 None 반환."""
    try:
        fs = corp.extract_fs(
            bgn_de="20200101",
            end_de="20251231",
            fs_tp=("is",),
            dataset="web",
            separate=separate,
            progressbar=False,
        )
        return fs._statements.get("is")
    except Exception:
        return None


def _fetch_from_dart(company_name: str) -> dict:
    global _corp_list_cache
    if _corp_list_cache is None:
        _corp_list_cache = dart.get_corp_list()
    corp = _find_corp(_corp_list_cache, company_name)
    if corp is None:
        return {}

    # CFS(연결) 먼저, 빈 결과면 OFS(별도) fallback
    for separate in (False, True):
        is_df = _fetch_fs_statements(corp, separate)
        if is_df is not None and not is_df.empty:
            result = _parse_fs(is_df)
            if result:
                return result

    return {}


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
        """, (company_name, int(year), metrics["매출액"], metrics["영업이익"], metrics["순이익"]))
    conn.commit()
    conn.close()


def get_financials(company_name: str) -> dict:
    """5개년(2020~2024) 재무 데이터를 반환. 키는 문자열 연도('2020'~'2024')."""
    raw = _fetch_from_dart(company_name)
    if not raw:
        return {}
    # 키를 문자열로 정규화
    data = {str(year): metrics for year, metrics in raw.items()}
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
