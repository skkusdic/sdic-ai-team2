"""SQL 쿼리 생성 에이전트 - 한국어 질문을 SQL로 변환."""

import sys
from pathlib import Path
import sqlite3

from claude_client import ask


def text_to_sql(question: str, corp_name: str, financials: dict) -> str:
    """한국어 질문을 SQL SELECT문으로 변환.

    Args:
        question: 사용자의 한국어 질문
        corp_name: 분석 대상 회사명
        financials: {year: {...}, ...} 형태의 재무 데이터

    Returns:
        ```sql로 감싼 SQL SELECT문
    """
    data_years = sorted(financials.keys())
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
    company TEXT,
    year INTEGER,
    매출액 INTEGER,
    영업이익 INTEGER,
    순이익 INTEGER
);

[중요: 반드시 company 필터 적용]
모든 쿼리는 WHERE company='{corp_name}' 조건을 포함해야 합니다.

[변환 예시]
질문: "2024년 매출액은?"
SQL: SELECT 매출액 FROM financials WHERE company='{corp_name}' AND year=2024

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


def query(question: str, company: str, financials: dict, db) -> dict:
    """App에서 호출하는 public API.

    Args:
        question: 사용자의 한국어 질문
        company: 분석 대상 회사명
        financials: {year: {...}, ...} 형태의 재무 데이터
        db: 데이터베이스 객체

    Returns:
        {"success": bool, "error_type": str, "result": ..., "message": str, "sql": str}
    """
    state = {
        "question": question,
        "company": company,
        "financials": financials,
        "db": db
    }
    result_state = text2sql_agent(state)
    return result_state["sql_result"]


if __name__ == "__main__":
    # SQLite 기반 테스트 데이터베이스
    class SQLiteTestDB:
        """SQLite 기반 테스트용 데이터베이스."""

        def __init__(self, company: str, financials: dict):
            self.conn = sqlite3.connect(":memory:")
            self.cursor = self.conn.cursor()

            # 테이블 생성 (실제 db.py 스키마와 동일)
            self.cursor.execute("""
                CREATE TABLE financials (
                    company TEXT,
                    year INTEGER,
                    매출액 REAL,
                    영업이익 REAL,
                    순이익 REAL,
                    PRIMARY KEY (company, year)
                )
            """)

            # 데이터 삽입
            for year, data in financials.items():
                self.cursor.execute("""
                    INSERT INTO financials (company, year, 매출액, 영업이익, 순이익)
                    VALUES (?, ?, ?, ?, ?)
                """, (company, year, data["매출액"], data["영업이익"], data["순이익"]))

            self.conn.commit()

        def execute_sql(self, sql: str):
            """SQL 실행하고 결과 반환."""
            result = self.cursor.execute(sql).fetchone()
            return result[0] if result else None

    # Mock financials 데이터 (삼성전자 5개년: 2020~2024, 실제 스키마와 동일)
    mock_financials = {
        2020: {"매출액": 236.8, "영업이익": 32.7, "순이익": 40.2},
        2021: {"매출액": 279.6, "영업이익": 47.9, "순이익": 55.3},
        2022: {"매출액": 371.5, "영업이익": 50.6, "순이익": 59.4},
        2023: {"매출액": 365.4, "영업이익": 47.1, "순이익": 52.1},
        2024: {"매출액": 380.7, "영업이익": 51.2, "순이익": 58.8},
    }

    company = "삼성전자"
    mock_db = SQLiteTestDB(company, mock_financials)

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

        result = query(question, company, mock_financials, mock_db)

        print(f"Success: {result['success']}")
        print(f"Error Type: {result['error_type']}")
        print(f"SQL: {result['sql']}")

        if result['success']:
            print(f"Result: {result['result']}")
        else:
            print(f"Message: {result['message']}")

    # INSERT 문 테스트 (변환 실패 확인)
    print(f"\n[추가 테스트] INSERT 방어 테스트")
    print("-" * 80)

    result = query("데이터 삽입해줘", company, mock_financials, mock_db)

    print(f"Success: {result['success']}")
    print(f"Error Type: {result['error_type']}")
    print(f"Message: {result['message']}")

    print("\n" + "=" * 80)
    print("테스트 완료")
    print("=" * 80)
