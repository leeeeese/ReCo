# ReCo 테스트 가이드

## 테스트 구조

```
tests/
├── __init__.py
├── conftest.py          # 공통 픽스처
├── unit/                # 단위 테스트
│   ├── test_workflow_utils.py
│   ├── test_price_agent.py
│   ├── test_safety_agent.py
│   └── test_orchestrator_agent.py
├── integration/         # 통합 테스트
│   └── test_workflow.py
└── api/                 # API 테스트
    └── test_workflow_api.py
```

## 백엔드 테스트 실행

### 전체 테스트 실행
```bash
pytest
```

### 특정 마커로 테스트 실행
```bash
# 단위 테스트만
pytest -m unit

# 에이전트 테스트만
pytest -m agent

# 통합 테스트만
pytest -m integration

# API 테스트만
pytest -m api
```

### 커버리지 포함 실행
```bash
pytest --cov=server --cov-report=html
```

### 특정 파일 실행
```bash
pytest tests/unit/test_price_agent.py
```

## 프론트엔드 테스트 실행

### 전체 테스트 실행
```bash
cd app/frontend
npm test
```

### Watch 모드
```bash
npm test -- --watch
```

### 커버리지 포함 실행
```bash
npm run test:coverage
```

## 테스트 작성 가이드

### 백엔드 테스트
- `@pytest.mark.unit`: 단위 테스트
- `@pytest.mark.integration`: 통합 테스트
- `@pytest.mark.api`: API 테스트
- `@pytest.mark.agent`: 에이전트 테스트
- `@pytest.mark.slow`: 느린 테스트 (LLM 호출 등)

### 프론트엔드 테스트
- `describe`: 테스트 그룹
- `it`: 개별 테스트
- `expect`: 어설션

## 주의사항

1. **LLM 호출 모킹**: 실제 OpenAI API 호출을 피하기 위해 LLM 에이전트는 모킹합니다.
2. **데이터베이스**: 테스트는 별도의 테스트 DB를 사용합니다.
3. **환경 변수**: 테스트 시 환경 변수가 필요할 수 있습니다.

