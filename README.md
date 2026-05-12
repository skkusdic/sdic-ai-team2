# SDIC AI 기업 재무 분석 어시스턴트

LangGraph Supervisor, Streamlit, DART API, Claude AI, fpdf2를 활용한 자동 재무 분석 플랫폼입니다. 기업명을 입력하면 재무 데이터를 수집하고 AI가 분석한 후 한글 PDF 리포트를 생성합니다.

## 주요 기능

- **자동 데이터 수집**: DART API를 통한 실시간 재무 데이터 조회
- **AI 분석**: Claude를 활용한 한국어 재무 인사이트 생성
- **PDF 리포트**: 한글 폰트 지원 자동 리포트 생성
- **멀티 에이전트 파이프라인**: LangGraph Supervisor로 데이터 수집 -> 분석 -> 리포트 생성 흐름 자동화
- **웹 UI**: Streamlit 기반 직관적인 사용자 인터페이스

## 폴더 구조

```
.
├── graph.py                           # LangGraph 파이프라인 정의
├── app.py                             # Streamlit UI
├── data.py                            # DART API 데이터 수집
├── claude_client.py                   # Claude API 호출
├── report.py                          # PDF 생성 유틸리티
├── agents/
│   ├── __init__.py
│   ├── data_agent.py                  # 데이터 수집 에이전트
│   ├── analysis_agent.py              # 분석 에이전트
│   └── report_agent.py                # 리포트 생성 에이전트
├── fonts/
│   └── NanumGothic.ttf                # 한글 폰트
├── requirements.txt
├── .env                               # API 키 설정
└── README.md
```

## 설치

### 1. 저장소 클론
```bash
git clone https://github.com/skkusdic/sdic-ai-team2.git
cd sdic-ai-team2
```

### 2. 의존성 설치
```bash
pip install -r requirements.txt
```

### 3. 환경 변수 설정
`.env` 파일을 생성하고 다음을 추가합니다:
```
DART_API_KEY=your_dart_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

## 실행

```bash
streamlit run app.py
```

브라우저에서 `http://localhost:8501` 접속 후 기업명을 입력하면 분석이 시작됩니다.

## 5분 시연 시나리오

### 케이스 1: 본인 팀 배정 회사
**Team 1**: 에이피알 / **Team 2**: 삼성전자 / **Team 3**: LG 이노텍

```
회사명 입력 → 제출
```

**예상 화면**:
- 사이드바: "Data Agent: 완료" "Analysis Agent: 완료" "Report Agent: 완료"
- 탭1 (KPI)
  - 4개 재무 지표 카드 (매출액, 영업이익, 순이익, 영업이익률)
  - 5개년 재무 데이터 테이블
  - 연도별 매출액/영업이익 트렌드 차트 (2개)
  - 전년대비(YoY) 변화율 테이블
- 탭2 (분석)
  - Claude AI 생성 한국어 분석 텍스트 (3-5문장)
  - 한글 PDF 다운로드 버튼

### 케이스 2: 카카오

```
회사명 입력: 카카오 → 제출
```

**예상 화면**:
- IT 회사로 인식되어 영업수익 alias 매핑 성공
- 케이스 1과 동일하게 완전한 분석 결과 표시

### 케이스 3: asdfasdf (존재하지 않는 회사)

```
회사명 입력: asdfasdf → 제출
```

**예상 화면**:
- 사이드바: "Data Agent: 완료" "Analysis Agent: 대기" "Report Agent: 대기"
- 빨간 박스 에러 메시지: "'asdfasdf' 기업의 재무 데이터를 찾을 수 없습니다. 회사명을 다시 확인해주세요."
- 크래시 없이 안정적으로 처리

## 다음 주 (Week 4) 예정

- SQLite 캐시 고도화로 성능 개선
- RAG(Retrieval Augmented Generation) 기반 고급 분석
- Text2SQL을 통한 자연어 쿼리 지원
- Streamlit Cloud 배포로 공개 URL 접근 가능
