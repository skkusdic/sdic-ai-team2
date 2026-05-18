"""SQL 쿼리 생성 에이전트 - 한국어 질문을 SQL로 변환."""

import sys
from pathlib import Path
import sqlite3

import pandas as pd

from claude_client import ask
from data import _load_from_db as _load_financials

_FINANCIALS_DB = "financials.db"


def text_to_sql(question: str, corp_name: str, financials: dict) -> str:
    """한국어 질문을 SQL SELECT문으로 변환.

    Args:
        question: 사용자의 한국어 질문
        corp_name: 분석 대상 회사명
        financials: {year: {...}, ...} 형태의 재무 데이터

    Returns:
        ```sql로 감싼 SQL SELECT문
    """
    data_years = sorted(int(y) for y in financials.keys())
    min_year = data_years[0]
    max_year = data_years[-1]

    prompt = f"""
[현재 상황]
분석 대상 회사: {corp_name}
보유한 데이터: {min_year}년 ~ {max_year}년 ({len(financials)}개년)

[중요 힌트]
{corp_name}는 {min_year}~{max_year}년 데이터만 존재합니다.
- "5년 평균" 질문 → {min_year}~{max_year}로 해석
- "{min_year-10}년부터" 같은 범위 밖의 요청 → {min_year}부터로 자동 조정

[테이블 스키마]
CREATE TABLE financials (
    company  TEXT,
    year     INTEGER,
    매출액   INTEGER,
    영업이익 INTEGER,
    순이익   INTEGER
);

[변환 예시]
질문: "2024년 매출액은?"
SQL: SELECT year, 매출액 FROM financials WHERE company='{corp_name}' AND year=2024

질문: "5년 순이익 합은?"
SQL: SELECT SUM(순이익) FROM financials WHERE company='{corp_name}' AND year>={min_year} AND year<={max_year}

질문: "평균 영업이익은?"
SQL: SELECT AVG(영업이익) FROM financials WHERE company='{corp_name}' AND year BETWEEN {min_year} AND {max_year}

질문: "최고 매출액은?"
SQL: SELECT MAX(매출액) FROM financials WHERE company='{corp_name}' AND year BETWEEN {min_year} AND {max_year}

질문: "최저 영업이익은?"
SQL: SELECT MIN(영업이익) FROM financials WHERE company='{corp_name}' AND year BETWEEN {min_year} AND {max_year}

[사용자 질문]
{question}

[지시사항]
위의 스키마에 맞춰 SQL SELECT문만 반환해줘.
설명이나 추가 텍스트는 금지.
```sql```로 감싸서 반환.
"""

    response = ask(prompt, max_tokens=200)
    return response


def clean_sql(sql_response: str) -> str:
    """Claude 응답에서 코드펜스와 세미콜론 제거.

    Args:
        sql_response: ```sql\nSELECT ...\n`````` 형태의 응답

    Returns:
        정제된 SQL 문자열
    """
    # 코드펜스 제거
    sql = sql_response.replace("```sql", "").replace("```", "")

    # 끝의 세미콜론 제거
    sql = sql.rstrip(";")

    # 앞뒤 공백 제거
    sql = sql.strip()

    return sql


def execute_sql_safely(sql: str, db) -> dict:
    """SQL을 안전하게 실행하고 변환 실패 vs 실행 실패를 분리해 반환.

    Args:
        sql: 실행할 SQL 문자열
        db: 데이터베이스 객체 (execute_sql 메서드 필요)

    Returns:
        {
            "success": bool,
            "error_type": "conversion_failed" | "execution_failed" | None,
            "result": ... | None,
            "message": str | None,
            "sql": str
        }
    """
    # SQL 유효성 검사
    if "SELECT" not in sql or "FROM" not in sql:
        return {
            "success": False,
            "error_type": "conversion_failed",
            "message": "SQL 변환에 실패했습니다",
            "sql": sql,
            "result": None
        }

    # SQL 실행
    try:
        result = db.execute_sql(sql)
        return {
            "success": True,
            "error_type": None,
            "result": result,
            "message": None,
            "sql": sql
        }
    except Exception as e:
        return {
            "success": False,
            "error_type": "execution_failed",
            "message": f"SQL 실행 실패: {str(e)}",
            "sql": sql,
            "result": None
        }


def text2sql_agent(state: dict) -> dict:
    """Agent 래퍼 함수 (graph에서 호출).

    Args:
        state: {
            "question": str (사용자의 한국어 질문),
            "company": str (현재 분석 중인 회사명),
            "financials": dict (5개년 데이터)
        }

    Returns:
        state에 "sql_result" 추가하여 반환
    """
    question = state["question"]
    company = state["company"]
    financials = state["financials"]
    db = state.get("db")  # state에서 db 객체 추출

    # 1) SQL 생성
    sql_response = text_to_sql(question, company, financials)

    # 2) SQL 정제
    sql = clean_sql(sql_response)

    # 3) SQL 실행
    result = execute_sql_safely(sql, db)

    return {**state, "sql_result": result}


def query(question: str, company: str) -> dict:
    """app.py에서 호출하는 단순 인터페이스.

    Args:
        question: 사용자의 한국어 질문
        company: 분석 대상 회사명 (session_state에서 전달)

    Returns:
        {"sql": str, "df": pd.DataFrame, "success": bool, "message": str | None}
    """
    financials = _load_financials(company)
    if not financials:
        return {
            "sql": "",
            "df": pd.DataFrame(),
            "success": False,
            "message": f"'{company}' 재무 데이터가 없습니다. 먼저 분석을 실행해주세요.",
        }

    # 1) SQL 생성
    sql_response = text_to_sql(question, company, financials)
    sql = clean_sql(sql_response)

    # 2) SQL 유효성 검사
    if "SELECT" not in sql.upper() or "FROM" not in sql.upper():
        return {"sql": sql, "df": pd.DataFrame(), "success": False, "message": "SQL 변환에 실패했습니다."}

    # 3) company 필터 자동 삽입
    if "company" not in sql.lower() and "WHERE" not in sql.upper():
        sql = sql + f" WHERE company = '{company}'"
    elif "company" not in sql.lower():
        sql = sql + f" AND company = '{company}'"

    try:
        with sqlite3.connect(_FINANCIALS_DB) as conn:
            cursor = conn.execute(sql)
            rows = cursor.fetchall()
            col_names = [desc[0] for desc in cursor.description] if cursor.description else []
        df = pd.DataFrame(rows, columns=col_names) if rows else pd.DataFrame(columns=col_names)
        # 수치 컬럼에 억원 단위 포맷 적용
        amount_cols = [c for c in df.columns if any(k in c for k in ("매출액", "영업이익", "순이익", "AVG", "SUM", "MAX", "MIN"))]
        for col in amount_cols:
            df[col] = df[col].apply(lambda v: f"{int(round(v)):,} 억원" if pd.notna(v) else "-")
        return {"sql": sql, "df": df, "success": True, "message": None}
    except Exception as e:
        return {"sql": sql, "df": pd.DataFrame(), "success": False, "message": f"SQL 실행 실패: {e}"}


if __name__ == "__main__":
    # SQLite 기반 테스트 데이터베이스
    class SQLiteTestDB:
        """SQLite 기반 테스트용 데이터베이스."""

        def __init__(self, financials: dict):
            self.conn = sqlite3.connect(":memory:")
            self.cursor = self.conn.cursor()

            # 테이블 생성
            self.cursor.execute("""
                CREATE TABLE financials (
                    year INTEGER PRIMARY KEY,
                    revenue REAL,
                    operating_profit REAL,
                    net_income REAL
                )
            """)

            # 데이터 삽입
            for year, data in financials.items():
                self.cursor.execute("""
                    INSERT INTO financials (year, revenue, operating_profit, net_income)
                    VALUES (?, ?, ?, ?)
                """, (year, data["revenue"], data["operating_profit"], data["net_income"]))

            self.conn.commit()

        def execute_sql(self, sql: str):
            """SQL 실행하고 결과 반환."""
            result = self.cursor.execute(sql).fetchone()
            return result[0] if result else None

    # Mock financials 데이터 (삼성전자 5개년: 2020~2024)
    mock_financials = {
        2020: {"revenue": 236.8, "operating_profit": 32.7, "net_income": 40.2},
        2021: {"revenue": 279.6, "operating_profit": 47.9, "net_income": 55.3},
        2022: {"revenue": 371.5, "operating_profit": 50.6, "net_income": 59.4},
        2023: {"revenue": 365.4, "operating_profit": 47.1, "net_income": 52.1},
        2024: {"revenue": 380.7, "operating_profit": 51.2, "net_income": 58.8},
    }

    mock_db = SQLiteTestDB(mock_financials)

    # 테스트 질문들
    test_questions = [
        "2024년 매출액은?",
        "5년 평균 매출액은?",
        "5년 순이익 합은?",
        "최고 매출액은?",
        "최저 영업이익은?",
    ]

    print("=" * 80)
    print("Text2SQL Agent 테스트")
    print("=" * 80)

    for i, question in enumerate(test_questions, 1):
        print(f"\n[테스트 {i}] {question}")
        print("-" * 80)

        state = {
            "question": question,
            "company": "삼성전자",
            "financials": mock_financials,
            "db": mock_db
        }

        result_state = text2sql_agent(state)
        sql_result = result_state["sql_result"]

        print(f"Success: {sql_result['success']}")
        print(f"Error Type: {sql_result['error_type']}")
        print(f"SQL: {sql_result['sql']}")

        if sql_result['success']:
            print(f"Result: {sql_result['result']}")
        else:
            print(f"Message: {sql_result['message']}")

    # INSERT 문 테스트 (변환 실패 확인)
    print(f"\n[추가 테스트] INSERT 방어 테스트")
    print("-" * 80)

    state = {
        "question": "데이터 삽입해줘",
        "company": "삼성전자",
        "financials": mock_financials,
        "db": mock_db
    }

    result_state = text2sql_agent(state)
    sql_result = result_state["sql_result"]

    print(f"Success: {sql_result['success']}")
    print(f"Error Type: {sql_result['error_type']}")
    print(f"Message: {sql_result['message']}")

    print("\n" + "=" * 80)
    print("테스트 완료")
    print("=" * 80)
