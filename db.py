import os
import sqlite3

DB_PATH = os.path.join("data", "sdic.db")


def init_db() -> None:
    """data/sdic.db 초기화 — companies, financials 테이블 생성."""
    os.makedirs("data", exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS companies (
                corp_code  TEXT PRIMARY KEY,
                corp_name  TEXT NOT NULL,
                stock_code TEXT
            )
        """)
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
        conn.commit()


def save_financials(company_name: str, data: dict) -> None:
    """재무 데이터 UPSERT 저장. data = {"2020": {"매출액": ..., "영업이익": ..., "순이익": ...}}"""
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        for year, m in data.items():
            conn.execute(
                "INSERT OR REPLACE INTO financials (company, year, 매출액, 영업이익, 순이익) VALUES (?, ?, ?, ?, ?)",
                (company_name, int(year), m["매출액"], m["영업이익"], m["순이익"]),
            )
        conn.commit()


def load_financials(company_name: str) -> dict:
    """캐시에서 재무 데이터 불러오기. 없으면 빈 dict 반환."""
    if not os.path.exists(DB_PATH):
        return {}
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            "SELECT year, 매출액, 영업이익, 순이익 FROM financials WHERE company = ? ORDER BY year",
            (company_name,),
        ).fetchall()
    return {
        str(year): {"매출액": rev, "영업이익": op, "순이익": net}
        for year, rev, op, net in rows
    }


_ALLOWED_KEYWORD = "SELECT"
_BLOCKED_KEYWORDS = {"DROP", "INSERT", "UPDATE", "DELETE", "CREATE", "ALTER", "ATTACH"}


def execute_sql(sql: str) -> list:
    """SELECT 문만 허용하는 안전 실행 게이트. 위험 구문은 ValueError 발생."""
    normalized = sql.strip().upper()

    if not normalized.startswith(_ALLOWED_KEYWORD):
        raise ValueError(f"SELECT 문만 허용됩니다. 거부된 SQL: {sql!r}")

    for blocked in _BLOCKED_KEYWORDS:
        if blocked in normalized:
            raise ValueError(f"금지된 키워드 '{blocked}' 포함. 거부된 SQL: {sql!r}")

    # 다중 statement 거부 (세미콜론 뒤에 내용이 있는 경우)
    statements = [s.strip() for s in sql.split(";") if s.strip()]
    if len(statements) > 1:
        raise ValueError(f"다중 statement 금지. 거부된 SQL: {sql!r}")

    if not os.path.exists(DB_PATH):
        return []
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(sql).fetchall()
    return rows


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")

    print("=== init_db() ===")
    init_db()
    print("DB 초기화 완료:", DB_PATH)

    print("\n=== save_financials() ===")
    mock = {
        "2022": {"매출액": 2368, "영업이익": 433, "순이익": 554},
        "2023": {"매출액": 2588, "영업이익": 65,  "순이익": 154},
        "2024": {"매출액": 3006, "영업이익": 326, "순이익": 344},
    }
    save_financials("삼성전자", mock)
    print("저장 완료")

    print("\n=== load_financials() ===")
    cached = load_financials("삼성전자")
    for year, m in sorted(cached.items()):
        print(f"  {year}: {m}")

    print("\n=== execute_sql() — 정상 SELECT ===")
    rows = execute_sql("SELECT year, 매출액 FROM financials WHERE company = '삼성전자'")
    for row in rows:
        print(" ", row)

    print("\n=== execute_sql() — DROP 거부 테스트 ===")
    try:
        execute_sql("DROP TABLE financials")
    except ValueError as e:
        print("거부됨 (정상):", e)

    print("\n=== execute_sql() — INSERT 거부 테스트 ===")
    try:
        execute_sql("INSERT INTO financials VALUES ('해커', 2024, 0, 0, 0)")
    except ValueError as e:
        print("거부됨 (정상):", e)

    print("\n=== execute_sql() — 다중 statement 거부 테스트 ===")
    try:
        execute_sql("SELECT * FROM financials; DROP TABLE financials")
    except ValueError as e:
        print("거부됨 (정상):", e)
