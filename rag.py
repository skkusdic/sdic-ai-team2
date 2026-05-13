import os
import sys
import sqlite3
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from claude_client import ask

DATA_DIR = "data"
DB_PATH  = "financials.db"


def _load_from_db(company: str) -> dict:
    """financials.db에서 직접 읽어 {year: {매출액, 영업이익, 순이익}} 반환."""
    if not os.path.exists(DB_PATH):
        return {}
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    cur.execute(
        "SELECT year, 매출액, 영업이익, 순이익 FROM financials WHERE company=? ORDER BY year",
        (company,),
    )
    rows = cur.fetchall()
    conn.close()
    return {row[0]: {"매출액": row[1], "영업이익": row[2], "순이익": row[3]} for row in rows}


# ── 1. 청크 생성 ────────────────────────────────────────────────

def _build_chunks(company: str, financials: dict) -> list[str]:
    """연도별 단락 5개 + 종합 단락 1개 = 총 6개 chunk 생성."""
    chunks = []

    sorted_years = sorted(financials.items())

    for year, m in sorted_years:
        revenue    = m.get("매출액",   0)
        op_profit  = m.get("영업이익", 0)
        net_profit = m.get("순이익",   0)
        op_margin  = round(op_profit / revenue * 100, 1) if revenue else 0

        chunk = (
            f"{year}년 실적: {company}의 매출액은 {revenue:,}억원, "
            f"영업이익은 {op_profit:,}억원(영업이익률 {op_margin}%), "
            f"순이익은 {net_profit:,}억원이었다."
        )
        chunks.append(chunk)

    # 종합 단락
    years       = [y for y, _ in sorted_years]
    revenues    = [m["매출액"]   for _, m in sorted_years]
    op_profits  = [m["영업이익"] for _, m in sorted_years]
    net_profits = [m["순이익"]   for _, m in sorted_years]

    best_rev_year = years[revenues.index(max(revenues))]
    best_op_year  = years[op_profits.index(max(op_profits))]

    summary = (
        f"{company} {min(years)}~{max(years)}년 종합: "
        f"최대 매출은 {best_rev_year}년({max(revenues):,}억원), "
        f"최대 영업이익은 {best_op_year}년({max(op_profits):,}억원)이었다. "
        f"분석 기간 평균 매출 {int(sum(revenues)/len(revenues)):,}억원, "
        f"평균 영업이익 {int(sum(op_profits)/len(op_profits)):,}억원, "
        f"평균 순이익 {int(sum(net_profits)/len(net_profits)):,}억원이다."
    )
    chunks.append(summary)

    return chunks


# ── 2. 벡터화 (캐시 포함) ────────────────────────────────────────

def _cache_path(company: str) -> str:
    return os.path.join(DATA_DIR, f"{company}_rag.pkl")


def build_index(company: str) -> tuple[list[str], TfidfVectorizer, object]:
    """chunks, vectorizer, tfidf_matrix 반환. 캐시 있으면 로드, 없으면 학습 후 저장."""
    os.makedirs(DATA_DIR, exist_ok=True)
    cache = _cache_path(company)

    financials = _load_from_db(company)
    if not financials:
        raise ValueError(f"'{company}' 재무 데이터를 찾을 수 없습니다.")

    chunks = _build_chunks(company, financials)

    if os.path.exists(cache):
        print(f"[RAG] 캐시 로드: {cache}")
        vectorizer, tfidf_matrix = joblib.load(cache)
    else:
        print(f"[RAG] 인덱스 생성 후 캐시 저장: {cache}")
        vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4))
        tfidf_matrix = vectorizer.fit_transform(chunks)
        joblib.dump((vectorizer, tfidf_matrix), cache)

    return chunks, vectorizer, tfidf_matrix


# ── 3. 검색 ─────────────────────────────────────────────────────

def search(query: str, chunks: list[str], vectorizer: TfidfVectorizer,
           tfidf_matrix, k: int = 3) -> list[tuple[float, str]]:
    """쿼리와 코사인 유사도 상위 k개 (score, chunk) 반환."""
    query_vec = vectorizer.transform([query])          # transform만 사용, fit 금지
    scores    = cosine_similarity(query_vec, tfidf_matrix).flatten()
    top_idx   = scores.argsort()[::-1][:k]
    return [(float(scores[i]), chunks[i]) for i in top_idx]


# ── 4. 답변 생성 ─────────────────────────────────────────────────

def answer(query: str, retrieved: list[tuple[float, str]]) -> str:
    """검색된 chunk를 컨텍스트로 Claude에 질의."""
    excerpts = "\n\n".join(f"[발췌 {i+1}] {chunk}" for i, (_, chunk) in enumerate(retrieved))

    prompt = f"""아래 발췌문에 있는 수치만 사용해 답변하라. 발췌에 없는 연도나 수치가 필요하면 '정보 부족'이라고 답하라.

=== 발췌문 ===
{excerpts}

=== 질문 ===
{query}"""

    return ask(prompt, max_tokens=600)


# ── 5. 편의 함수 ─────────────────────────────────────────────────

def query_rag(company: str, query: str, k: int = 3) -> str:
    """company + query만 넘기면 검색·답변까지 한 번에 처리."""
    chunks, vectorizer, tfidf_matrix = build_index(company)
    retrieved = search(query, chunks, vectorizer, tfidf_matrix, k=k)
    return answer(query, retrieved)


# ── 6. 단독 실행 ─────────────────────────────────────────────────

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")

    COMPANY = "삼성전자"
    QUERY   = "영업이익 추이를 설명해줘"

    chunks, vectorizer, tfidf_matrix = build_index(COMPANY)
    print(f"\n전체 chunk 수: {len(chunks)}")
    for i, c in enumerate(chunks):
        print(f"  [{i+1}] {c}")

    print(f"\n쿼리: {QUERY}")
    retrieved = search(QUERY, chunks, vectorizer, tfidf_matrix, k=3)
    print("\n검색된 chunk (코사인 유사도 상위 3개):")
    for score, chunk in retrieved:
        print(f"  score={score:.4f} | {chunk}")

    print("\n=== Claude 최종 답변 ===")
    print(answer(QUERY, retrieved))
