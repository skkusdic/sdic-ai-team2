import io
import os
import sqlite3
import zipfile
import requests
import xml.etree.ElementTree as ET

from dotenv import load_dotenv

load_dotenv()

DB_PATH = "financials.db"
DART_ENDPOINT = "https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json"
DART_CORPCODE_URL = "https://opendart.fss.or.kr/api/corpCode.xml"

_corp_map_cache = None  # {corp_name: (corp_code, stock_code), ...}

_REVENUE_LABELS = {"매출액", "영업수익", "수익(매출액)"}
_OPERATING_LABELS = {"영업이익", "영업이익(손실)", "영업손실"}
_NET_LABELS = {"당기순이익", "당기순이익(손실)", "당기순손실"}

_CORP_ALIASES = {
    "네이버": "NAVER",
    "케이티": "KT",
    "에스케이텔레콤": "SK텔레콤",
    "엘지전자": "LG전자",
    "엘지이노텍": "LG이노텍",
    "엘지화학": "LG화학",
    "엘지에너지솔루션": "LG에너지솔루션",
    "엘지생활건강": "LG생활건강",
    "엘지유플러스": "LG유플러스",
    "에스케이하이닉스": "SK하이닉스",
    "에스케이이노베이션": "SK이노베이션",
    "현대차": "현대자동차",
    "기아차": "기아",
    "포스코": "POSCO홀딩스",
    "비비큐": "BBQ",
}


def _get_dart_api_key() -> str:
    key = os.environ.get("DART_API_KEY", "")
    if not key:
        try:
            import streamlit as st
            key = st.secrets.get("DART_API_KEY", "")
            if key:
                os.environ["DART_API_KEY"] = key
        except Exception:
            pass
    return key


def _get_corp_map() -> dict:
    """DART corpCode.xml API로 회사명 → (corp_code, stock_code) 맵 반환."""
    global _corp_map_cache
    if _corp_map_cache is not None:
        return _corp_map_cache

    resp = requests.get(DART_CORPCODE_URL, params={"crtfc_key": _get_dart_api_key()}, timeout=30)
    with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
        xml_data = z.read("CORPCODE.xml")

    root = ET.fromstring(xml_data)
    corp_map = {}
    for item in root.findall("list"):
        name = (item.findtext("corp_name") or "").strip()
        code = (item.findtext("corp_code") or "").strip()
        stock = (item.findtext("stock_code") or "").strip()
        if name and code:
            corp_map[name] = (code, stock)

    _corp_map_cache = corp_map
    return corp_map


def _find_corp_code(company_name: str) -> str:
    corp_map = _get_corp_map()
    raw = company_name.strip()
    no_space = raw.replace(" ", "")

    candidates = [raw, no_space]
    if no_space in _CORP_ALIASES:
        candidates.append(_CORP_ALIASES[no_space])

    # 정확히 일치 (상장사 우선)
    for cand in candidates:
        if cand in corp_map:
            code, stock = corp_map[cand]
            return code

    # 부분 일치 (짧은 이름 우선)
    for cand in candidates:
        matches = [(name, code, stock) for name, (code, stock) in corp_map.items() if cand in name]
        listed = [(n, c, s) for n, c, s in matches if s]
        pool = listed if listed else matches
        if pool:
            return min(pool, key=lambda x: len(x[0]))[1]

    return ""


def _extract_year(corp_code: str, year: int, fs_div: str) -> dict:
    """fnlttSinglAcntAll API로 단년 손익 추출 (XBRL 우회). fs_div: 'CFS' 또는 'OFS'."""
    params = {
        "crtfc_key": _get_dart_api_key(),
        "corp_code": corp_code,
        "bsns_year": str(year),
        "reprt_code": "11011",
        "fs_div": fs_div,
    }
    try:
        resp = requests.get(DART_ENDPOINT, params=params, timeout=10).json()
    except Exception:
        return {}

    items = resp.get("list", [])
    data = {}
    for item in items:
        if item.get("sj_div") not in ("IS", "CIS"):
            continue
        nm = item.get("account_nm", "").strip()
        amt = item.get("thstrm_amount", "").replace(",", "")
        if not amt or amt == "-":
            continue
        try:
            val = int(amt) // 100_000_000
        except (ValueError, TypeError):
            continue
        if nm in _REVENUE_LABELS and "매출액" not in data:
            data["매출액"] = val
        elif nm in _OPERATING_LABELS and "영업이익" not in data:
            data["영업이익"] = val
        elif nm in _NET_LABELS and "순이익" not in data:
            data["순이익"] = val
    return data


def _fetch_from_dart(company_name: str) -> dict:
    corp_code = _find_corp_code(company_name)
    if not corp_code:
        return {}

    result = {}
    for year in range(2020, 2026):
        # CFS(연결) 먼저, 없으면 OFS(별도) fallback
        year_data = _extract_year(corp_code, year, "CFS")
        if not year_data or not {"매출액", "영업이익", "순이익"}.issubset(year_data):
            ofs = _extract_year(corp_code, year, "OFS")
            if ofs:
                # CFS에서 부분적으로 받은 키 보존, 빈 곳만 OFS로 채움
                for k, v in ofs.items():
                    year_data.setdefault(k, v)
        if {"매출액", "영업이익", "순이익"}.issubset(year_data):
            result[year] = year_data

    return result


def _init_db(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS financials (
            company  TEXT,
            year     INTEGER,
            매출액   INTEGER,
            영업이익 INTEGER,
            순이익   INTEGER,
            PRIMARY KEY (company, year)
        )
    """)


def _save_to_db(company_name: str, data: dict) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        _init_db(conn)
        for year, m in data.items():
            conn.execute(
                "INSERT OR REPLACE INTO financials (company, year, 매출액, 영업이익, 순이익) VALUES (?, ?, ?, ?, ?)",
                (company_name, int(year), m["매출액"], m["영업이익"], m["순이익"]),
            )
        conn.commit()


def _load_from_db(company_name: str) -> dict:
    if not os.path.exists(DB_PATH):
        return {}
    with sqlite3.connect(DB_PATH) as conn:
        _init_db(conn)
        rows = conn.execute(
            "SELECT year, 매출액, 영업이익, 순이익 FROM financials WHERE company = ? ORDER BY year DESC LIMIT 5",
            (company_name,),
        ).fetchall()
    return {
        str(year): {"매출액": rev, "영업이익": op, "순이익": net}
        for year, rev, op, net in sorted(rows)  # 오름차순 정렬
    }


def get_financials(company_name: str) -> dict:
    """최신 연도 기준 최대 5개년 재무 데이터. 키는 문자열 연도. 단위: 억원."""
    cached = _load_from_db(company_name)
    if cached:
        return cached

    raw = _fetch_from_dart(company_name)
    if not raw:
        return {}

    data = {str(year): metrics for year, metrics in raw.items()}
    _save_to_db(company_name, data)
    return _load_from_db(company_name)


if __name__ == "__main__":
    import sys
    import time
    sys.stdout.reconfigure(encoding="utf-8")

    for name in ["삼성전자", "카카오", "LG이노텍", "에이피알", "네이버", "asdfasdf"]:
        t0 = time.time()
        d = get_financials(name)
        elapsed = time.time() - t0
        if not d:
            print(f"[{name}] no data ({elapsed:.1f}s)")
            continue
        print(f"[{name}] {len(d)}개년 ({elapsed:.1f}s)")
        for y, m in sorted(d.items()):
            print(f"  {y}: {m}")
