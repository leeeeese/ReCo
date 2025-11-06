# ReCo 테스트 가이드

이 문서는 ReCo 프로젝트의 각 컴포넌트를 테스트하는 방법을 안내합니다.

## 📋 목차

1. [환경 설정 확인](#1-환경-설정-확인)
2. [개별 에이전트 테스트](#2-개별-에이전트-테스트)
3. [FastAPI 서버 테스트](#3-fastapi-서버-테스트)
4. [Streamlit UI 테스트](#4-streamlit-ui-테스트)
5. [전체 워크플로우 테스트](#5-전체-워크플로우-테스트)

---

## 1. 환경 설정 확인

### 1.1 설정 검증
```bash
# 가상환경 활성화
source .venv/bin/activate

# 설정 검증
python server/utils/config.py
```

**예상 출력:**
```
=== ReCo 설정 검증 ===
openai_api_key: ✅ 설정됨
serpapi_key: ✅ 설정됨
database_url: sqlite:///./history.db
playbook_dir: ./server/retrieval/playbook
playbook_exists: True
```

### 1.2 데이터베이스 테이블 생성 확인
```bash
python -c "from server.db.database import database; database.create_tables(); print('테이블 생성 완료!')"
```

---

## 2. 개별 에이전트 테스트

### 2.1 전체 에이전트 테스트
```bash
# 모든 에이전트를 순차적으로 테스트
python server/test_agents.py
```

### 2.2 개별 에이전트 테스트

#### 페르소나 분류 테스트
```bash
python -c "
from server.utils.workflow_utils import classify_persona
from server.utils.mock_data import get_mock_user_input

user_input = get_mock_user_input()
result = classify_persona(user_input)
print('페르소나 분류 결과:', result)
"
```

#### 가격 에이전트 테스트
```bash
python -c "
from server.test_agents import test_price_agent
test_price_agent()
"
```

#### 안전거래 에이전트 테스트
```bash
python -c "
from server.test_agents import test_safety_agent
test_safety_agent()
"
```

#### 페르소나 매칭 에이전트 테스트
```bash
python -c "
from server.test_agents import test_persona_matching_agent
test_persona_matching_agent()
"
```

#### 최종 추천 오케스트레이터 테스트
```bash
python -c "
from server.test_agents import test_recommendation_orchestrator
test_recommendation_orchestrator()
"
```

**예상 출력 예시:**
```
==================================================
가격 에이전트 테스트
==================================================

결과:
- 상태: price_analyzed
- 추천 판매자 수: 3
- 에러: None
```

---

## 3. FastAPI 서버 테스트

### 3.1 서버 실행
```bash
# 방법 1: uvicorn 직접 실행
uvicorn server.main:app --host 0.0.0.0 --port 8000 --reload

# 방법 2: Python 모듈로 실행
python server/main.py
```

서버가 실행되면 다음 URL에서 접근 가능:
- **API 문서**: http://localhost:8000/docs
- **루트 엔드포인트**: http://localhost:8000/

### 3.2 API 테스트 (curl)

#### 루트 엔드포인트
```bash
curl http://localhost:8000/
```

#### 추천 API 호출
```bash
curl -X POST "http://localhost:8000/api/v1/recommend" \
  -H "Content-Type: application/json" \
  -d '{
    "search_query": "아이폰 14 프로",
    "trust_safety": 70,
    "quality_condition": 80,
    "remote_transaction": 60,
    "activity_responsiveness": 75,
    "price_flexibility": 50,
    "category": "스마트폰",
    "location": "서울",
    "price_min": 500000,
    "price_max": 1500000
  }'
```

### 3.3 API 테스트 (Python requests)

```python
import requests
import json

# 추천 API 호출
url = "http://localhost:8000/api/v1/recommend"
payload = {
    "search_query": "아이폰 14 프로",
    "trust_safety": 70,
    "quality_condition": 80,
    "remote_transaction": 60,
    "activity_responsiveness": 75,
    "price_flexibility": 50,
    "category": "스마트폰",
    "location": "서울",
    "price_min": 500000,
    "price_max": 1500000
}

response = requests.post(url, json=payload)
print(json.dumps(response.json(), indent=2, ensure_ascii=False))
```

### 3.4 Swagger UI 사용
브라우저에서 http://localhost:8000/docs 로 접속하여:
1. `/api/v1/recommend` 엔드포인트 클릭
2. "Try it out" 버튼 클릭
3. Request body 입력
4. "Execute" 버튼 클릭하여 테스트

---

## 4. Streamlit UI 테스트

### 4.1 UI 실행
```bash
# 가상환경 활성화 후
streamlit run app/main.py
```

브라우저에서 자동으로 열리거나, http://localhost:8501 로 접속

### 4.2 UI 테스트 시나리오
1. **검색 조건 입력**
   - 상품명: "아이폰 14 프로"
   - 카테고리: "스마트폰"
   - 가격 범위: 500,000원 ~ 1,500,000원
   - 지역: "서울"

2. **사용자 선호도 설정**
   - 신뢰·안전: 70
   - 품질·상태: 80
   - 원격거래성향: 60
   - 활동·응답: 75
   - 가격유연성: 50

3. **추천 시작 버튼 클릭**
   - API 호출이 성공하면 결과가 표시됩니다
   - 실패 시 에러 메시지가 표시됩니다

**참고**: FastAPI 서버가 실행 중이어야 UI가 정상 작동합니다.

---

## 5. 전체 워크플로우 테스트

### 5.1 Python 스크립트로 전체 워크플로우 테스트

```python
# test_full_workflow.py
from server.workflow.graph import recommendation_workflow
from server.utils.mock_data import get_mock_user_input

# 워크플로우 초기화
app = recommendation_workflow()

# 초기 상태 생성
initial_state = {
    "user_input": get_mock_user_input(),
    "search_query": {},
    "persona_classification": None,
    "seller_item_scores": [],
    "final_item_scores": [],
    "sql_query": None,
    "ranking_explanation": "",
    "current_step": "start",
    "completed_steps": [],
    "error_message": None,
    "price_agent_recommendations": None,
    "safety_agent_recommendations": None,
    "persona_matching_recommendations": None,
    "final_seller_recommendations": None,
    "mock_sellers_with_products": None,
    "mock_sellers_with_persona": None,
}

# 워크플로우 실행
result = app.invoke(initial_state)

print("=" * 50)
print("전체 워크플로우 실행 결과")
print("=" * 50)
print(f"최종 단계: {result.get('current_step')}")
print(f"완료된 단계: {result.get('completed_steps')}")
print(f"최종 추천 판매자 수: {len(result.get('final_seller_recommendations', []))}")
```

실행:
```bash
python test_full_workflow.py
```

### 5.2 단계별 워크플로우 확인

각 에이전트가 실행되는 순서:
1. `init` - 페르소나 분류 및 검색 쿼리 생성
2. `price_agent` - 가격 분석 (병렬)
3. `safety_agent` - 안전거래 분석 (병렬)
4. `persona_matching_agent` - 페르소나 매칭 (병렬)
5. `recommendation_orchestrator` - 최종 추천 통합

---

## 🔍 문제 해결

### OpenAI API 키 오류
```bash
# .env 파일 확인
cat .env | grep OPENAI_API_KEY

# 환경 변수 확인
python -c "import os; print('OPENAI_API_KEY:', '설정됨' if os.getenv('OPENAI_API_KEY') else '미설정')"
```

### 데이터베이스 연결 오류
```bash
# SQLite 사용 시 (기본값)
DATABASE_URL=sqlite:///./history.db

# PostgreSQL 사용 시
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
```

### 포트 충돌
```bash
# 포트 8000이 사용 중인 경우
lsof -ti:8000 | xargs kill -9

# 또는 다른 포트 사용
uvicorn server.main:app --port 8001
```

---

## 📝 테스트 체크리스트

- [ ] 환경 변수 설정 확인
- [ ] 데이터베이스 테이블 생성 확인
- [ ] 개별 에이전트 테스트 통과
- [ ] FastAPI 서버 실행 및 API 호출 성공
- [ ] Streamlit UI 실행 및 동작 확인
- [ ] 전체 워크플로우 실행 성공

---

## 💡 팁

1. **개발 중에는 FastAPI 서버를 `--reload` 옵션으로 실행**하여 코드 변경 시 자동 재시작
2. **에이전트 테스트는 목업 데이터를 사용**하므로 실제 API 키 없이도 기본 동작 확인 가능
3. **Swagger UI**를 활용하면 API 테스트가 더 편리합니다
4. **각 에이전트의 로그를 확인**하여 실행 과정을 추적할 수 있습니다

