# 프로젝트 세션 기록

## 2026-05-07

- 완료: data.py DART API 실연동 (Mock 제거), 5개년(2020~2024) 재무 데이터 반환, corp_list 캐시 적용, agents/data_agent.py 생성 및 테스트
- 미완료: 현대자동차·SK하이닉스·카카오 등 일부 기업 DART 파싱 실패 (계정명 매핑 미완성)
- 다음: [graph.py] LangGraph 노드에 data_agent 연결 — pipeline 흐름 완성 필요

## 2026-05-15

- 완료: data.py 2025년 범위 확장, db.py 신규 생성 (init_db/save_financials/load_financials/execute_sql), agents/data_agent.py SQLite 캐시 연동, graph.py AgentState data_source 추가, .gitignore data/ 추가, 노션 출석관리표·Track Coverage Map·멤버 관리 페이지 생성
- 미완료: db.py companies 테이블 save_company() 미구현, 출석관리표 이모티콘 제거 및 지각 입력 방식 미확정
- 다음: [db.py] save_company() 함수 추가 — companies 테이블 활용 완성
