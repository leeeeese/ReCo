# 테스트 환경 설정 가이드

## 백엔드 테스트 설정

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. Playwright 브라우저 설치 (E2E 테스트용)
```bash
playwright install chromium
```

### 3. 테스트 실행
```bash
# 전체 테스트
pytest

# 특정 마커만
pytest -m unit
pytest -m integration
pytest -m api

# 커버리지 포함
pytest --cov=server --cov-report=html
```

## 프론트엔드 테스트 설정

### 1. 의존성 설치
```bash
cd app/frontend
npm install
```

### 2. 테스트 실행
```bash
# 전체 테스트
npm test

# Watch 모드
npm test -- --watch

# 커버리지
npm run test:coverage
```

## 환경 변수 설정

테스트 실행 시 다음 환경 변수가 필요할 수 있습니다:

```bash
# .env 파일 또는 환경 변수
OPENAI_API_KEY=your_key_here  # LLM 테스트 시 필요 (모킹 사용 시 불필요)
DATABASE_URL=sqlite:///./test_history.db  # 테스트 DB (자동 설정됨)
```

## 주의사항

1. **LLM 호출**: 대부분의 테스트는 LLM 호출을 모킹하므로 실제 API 키가 필요하지 않습니다.
2. **데이터베이스**: 테스트는 별도의 테스트 DB를 사용하며, 테스트 후 자동으로 정리됩니다.
3. **E2E 테스트**: 프론트엔드와 백엔드 서버가 실행 중이어야 합니다.

