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

## 서버 실행 필요 여부

### 서버 없이 실행 가능한 테스트
- ✅ 단위 테스트 (`pytest -m unit`)
- ✅ 통합 테스트 (`pytest -m integration`)
- ✅ API 테스트 (`pytest -m api`) - TestClient 사용

### 서버 실행이 필요한 테스트
- ⚠️ **E2E 테스트만** (`pytest -m e2e`) - 실제 브라우저 사용

### E2E 테스트 실행 전 준비

E2E 테스트를 실행하려면 다음 서버들이 실행 중이어야 합니다:

**터미널 1: 백엔드 서버**
```bash
cd server
python main.py
# 또는
uvicorn server.main:app --reload --port 8000
```

**터미널 2: 프론트엔드 서버**
```bash
cd app/frontend
npm run dev
# 포트 3000에서 실행
```

**터미널 3: E2E 테스트 실행**
```bash
pytest -m e2e
```

## 주의사항

1. **LLM 호출**: 대부분의 테스트는 LLM 호출을 모킹하므로 실제 API 키가 필요하지 않습니다.
2. **데이터베이스**: 테스트는 별도의 테스트 DB를 사용하며, 테스트 후 자동으로 정리됩니다.
3. **E2E 테스트**: 프론트엔드(포트 3000)와 백엔드(포트 8000) 서버가 실행 중이어야 합니다.
4. **일반 테스트**: 단위/통합/API 테스트는 서버 없이 실행 가능합니다.

