# Streamlit Cloud 배포 가이드

## 1. GitHub push
```bash
git add .
git commit -m "week4: 배포 준비"
git push origin main
```

## 2. Streamlit Cloud 연결
1. https://share.streamlit.io 접속 → GitHub 로그인
2. **New app** 클릭
3. Repository: `skkusdic/sdic-ai-team2`
4. Branch: `main`
5. Main file path: `app.py`
6. **Deploy** 클릭

## 3. Secrets 등록
1. 배포 후 앱 대시보드 → **Settings** → **Secrets**
2. 아래 내용 붙여넣기 (실제 키 값으로 교체):
```toml
DART_API_KEY = "your_dart_api_key_here"
ANTHROPIC_API_KEY = "your_anthropic_api_key_here"
```
3. **Save** 클릭 → 앱 자동 재시작

## 4. 확인
- 공개 URL에서 기업명 입력 후 분석 정상 동작 확인
- `data/` 폴더와 `.streamlit/secrets.toml`은 `.gitignore`에 등록되어 GitHub에 올라가지 않음

## 주의
- `.env` 파일은 절대 push 금지
- `secrets.toml`은 절대 push 금지 (`.gitignore`에 등록됨)
- 팀원 모두 push 완료 후 Pipeline Lead가 최종 실행 확인
