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
    return {r[0]: {"매출액": r[1], "영업이익": r[2], "순이익": r[3]} for r in rows}


# ── 1. 청크 생성 ────────────────────────────────────────────────

def _build_chunks(company: str, financials: dict) -> list[str]:
    """연도별 단락 5개 + 종합 단락 1개 = 총 6개 chunk 생성."""
    chunks   = []
    sorted_f = sorted(financials.items())

    for year, m in sorted_f:
        rev    = m.get("매출액",   0)
        op     = m.get("영업이익", 0)
        net    = m.get("순이익",   0)
        margin = round(op / rev * 100, 1) if rev else 0

        chunk = (
            f"{year}년 실적: {company}의 매출액은 {rev:,}억원, "
            f"영업이익은 {op:,}억원(영업이익률 {margin}%), "
            f"순이익은 {net:,}억원이었다."
        )
        chunks.append(chunk)

    # 종합 단락
    years      = [y for y, _ in sorted_f]
    revenues   = [m["매출액"]   for _, m in sorted_f]
    op_profits = [m["영업이익"] for _, m in sorted_f]
    net_profits= [m["순이익"]   for _, m in sorted_f]

    best_rev_year = years[revenues.index(max(revenues))]
    best_op_year  = years[op_profits.index(max(op_profits))]

    summary = (
        f"{company} {min(years)}~{max(years)}년 종합: "
        f"최대 매출은 {best_rev_year}년({max(revenues):,}억원), "
        f"최대 영업이익은 {best_op_year}년({max(op_profits):,}억원)이었다. "
        f"평균 매출 {int(sum(revenues)/len(revenues)):,}억원, "
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
        vectorizer   = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4))
        tfidf_matrix = vectorizer.fit_transform(chunks)
        joblib.dump((vectorizer, tfidf_matrix), cache)

    return chunks, vectorizer, tfidf_matrix


# ── 3. 검색 ─────────────────────────────────────────────────────

def search(query: str, chunks: list[str], vectorizer: TfidfVectorizer,
           tfidf_matrix, k: int = 3) -> list[tuple[float, str]]:
    """쿼리와 코사인 유사도 상위 k개 (score, chunk) 반환."""
    query_vec = vectorizer.transform([query])          # transform만, fit 금지
    scores    = cosine_similarity(query_vec, tfidf_matrix).flatten()
    top_idx   = scores.argsort()[::-1][:k]
    return [(float(scores[i]), chunks[i]) for i in top_idx]


# ── 4. 답변 생성 ─────────────────────────────────────────────────

def answer(query: str, retrieved: list[tuple[float, str]]) -> str:
    excerpts = "\n\n".join(
        f"[발췌 {i+1}] {chunk}" for i, (_, chunk) in enumerate(retrieved)
    )
    prompt = f"""아래 발췌문에 있는 수치만 사용해 답변하라. 발췌에 없는 연도나 수치가 필요하면 '정보 부족'이라고 답하라.

=== 발췌문 ===
{excerpts}

=== 질문 ===
{query}"""
    return ask(prompt, max_tokens=600)


# ── 5. 편의 함수 ─────────────────────────────────────────────────

def embed_text(text: str) -> list:
    pass  # TODO: 5주차에 OpenAI embeddings로 전환 예정


def search_app(company: str, question: str, top_k: int = 3) -> list[dict]:
    """app.py 호환 래퍼 — [{"score": float, "text": str}] 형태로 반환."""
    chunks, vectorizer, tfidf_matrix = build_index(company)
    retrieved = search(question, chunks, vectorizer, tfidf_matrix, k=top_k)
    return [{"score": score, "text": chunk} for score, chunk in retrieved]


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

    # 캐시 초기화 후 재생성
    cache = _cache_path(COMPANY)
    if os.path.exists(cache):
        os.remove(cache)

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

    # 캐시 로드 확인
    print("\n--- 재실행 (캐시 로드 확인) ---")
    chunks2, _, _ = build_index(COMPANY)
    print(f"chunk 수: {len(chunks2)} (재학습 없이 로드)")
