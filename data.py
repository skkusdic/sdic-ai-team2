import sqlite3

DB_PATH = "financials.db"

MOCK_DATA = {
    "삼성전자": {
        2022: {"매출액": 302_231, "영업이익": 43_376, "순이익": 55_654},
        2023: {"매출액": 258_935, "영업이익":  6_567, "순이익": 15_487},
        2024: {"매출액": 300_870, "영업이익": 32_726, "순이익": 34_082},
    }
}


def _save_to_db(company_name: str, data: dict) -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS financials (
            company TEXT,
            year    INTEGER,
            매출액  INTEGER,
            영업이익 INTEGER,
            순이익  INTEGER,
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
    # TODO: dart-fss 연동
    data = MOCK_DATA.get(company_name, {})
    if data:
        _save_to_db(company_name, data)
    return data


if __name__ == "__main__":
    data = get_financials("삼성전자")
    print(f"{'연도':<6} {'매출액':>12} {'영업이익':>12} {'순이익':>12}  (단위: 억원)")
    print("-" * 50)
    for year, metrics in sorted(data.items()):
        print(
            f"{year:<6} "
            f"{metrics['매출액']:>12,} "
            f"{metrics['영업이익']:>12,} "
            f"{metrics['순이익']:>12,}"
        )
