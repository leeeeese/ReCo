# ReCo 테스트 가이드

이 문서는 ReCo 프로젝트의 각 컴포넌트를 테스트하는 방법을 안내합니다.

## 📋 목차

1. [환경 설정 확인](#1-환경-설정-확인)
2. [개별 에이전트 테스트](#2-개별-에이전트-테스트)
3. [FastAPI 서버 테스트](#3-fastapi-서버-테스트)
4. [React 프론트엔드 테스트](#4-react-프론트엔드-테스트)
5. [전체 워크플로우 테스트](#5-전체-워크플로우-테스트)
6. [통합 테스트](#6-통합-테스트)

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
from server.test_agents import test_orchestrator_agent
test_orchestrator_agent()
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

## 4. React 프론트엔드 테스트

### 4.1 프론트엔드 실행

**전제 조건**: FastAPI 서버가 먼저 실행되어 있어야 합니다.

```bash
# 백엔드 서버 실행 (터미널 1)
cd server
python main.py
```

```bash
# 프론트엔드 실행 (터미널 2)
cd app/frontend
npm install  # 처음 한 번만
npm run dev
```

브라우저에서 자동으로 열리거나, http://localhost:3000 으로 접속

### 4.2 프론트엔드 테스트 시나리오

#### 4.2.1 챗봇 인터페이스 테스트

1. **홈페이지 접속**
   - http://localhost:3000 접속
   - "챗봇 시작하기" 버튼 클릭

2. **기본 메시지 확인**
   - 초기 환영 메시지가 표시되는지 확인
   - "안녕하세요! ReCo입니다..." 메시지 확인

3. **검색 요청 테스트**
   - 입력창에 "아이폰 14 프로 찾고 있어요" 입력
   - 전송 버튼 클릭 또는 Enter 키 입력
   - 로딩 메시지 표시 확인
   - 추천 결과가 카드 형태로 표시되는지 확인

4. **추천 결과 확인**
   - 상품 카드에 다음 정보가 표시되는지 확인:
     - 상품명
     - 가격
     - 추천 점수
     - 추천 이유
   - 여러 상품이 표시되는지 확인

5. **에러 처리 테스트**
   - 백엔드 서버를 중지한 상태에서 메시지 전송
   - 에러 메시지가 표시되는지 확인

#### 4.2.2 사이드바 기능 테스트

1. **최근 검색**
   - 여러 검색을 수행한 후
   - 사이드바의 "최근 검색" 목록 확인
   - 최근 검색 항목 클릭 시 입력창에 자동 입력되는지 확인

2. **카테고리 필터**
   - 사이드바의 카테고리 배지 클릭
   - 선택된 카테고리가 하이라이트되는지 확인

#### 4.2.3 반응형 디자인 테스트

1. **브라우저 창 크기 조절**
   - 데스크톱 크기: 사이드바 표시 확인
   - 모바일 크기: 사이드바 숨김 확인

### 4.3 브라우저 개발자 도구 확인

1. **네트워크 탭**
   - 메시지 전송 시 `/api/v1/recommend` 요청 확인
   - 요청/응답 데이터 확인
   - 응답 시간 확인

2. **콘솔 탭**
   - 에러 메시지 확인
   - API 호출 로그 확인

### 4.4 Streamlit UI 테스트 (레거시)

```bash
# 가상환경 활성화 후
streamlit run app/main.py
```

브라우저에서 자동으로 열리거나, http://localhost:8501 로 접속

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
4. `orchestrator_agent` - 최종 추천 통합

### 5.3 워크플로우 상태 확인

```python
# test_workflow_state.py
from server.workflow.graph import recommendation_workflow
from server.utils.mock_data import get_mock_user_input
import json

app = recommendation_workflow()
initial_state = {
    "user_input": get_mock_user_input(),
    "search_query": {},
    "persona_classification": None,
    "price_agent_recommendations": None,
    "safety_agent_recommendations": None,
    "final_seller_recommendations": None,
    "final_item_scores": None,
    "ranking_explanation": "",
    "current_step": "start",
    "completed_steps": [],
    "error_message": None,
    "execution_start_time": None,
    "execution_time": None,
}

result = app.invoke(initial_state)

print("=" * 50)
print("워크플로우 실행 결과")
print("=" * 50)
print(f"현재 단계: {result.get('current_step')}")
print(f"완료된 단계: {result.get('completed_steps')}")
print(f"실행 시간: {result.get('execution_time', 0):.2f}초")
print(f"페르소나 타입: {result.get('persona_classification', {}).get('persona_type', 'N/A')}")
print(f"최종 추천 판매자 수: {len(result.get('final_seller_recommendations', []))}")
print(f"최종 추천 상품 수: {len(result.get('final_item_scores', []))}")
print(f"에러 메시지: {result.get('error_message', 'None')}")
```

---

## 6. 통합 테스트

### 6.1 전체 시스템 통합 테스트

**목적**: 프론트엔드 → 백엔드 → 워크플로우 → 응답 → 프론트엔드 전체 흐름 테스트

#### 6.1.1 준비 단계

```bash
# 터미널 1: 백엔드 서버 실행
cd server
python main.py

# 터미널 2: 프론트엔드 실행
cd app/frontend
npm run dev
```

#### 6.1.2 테스트 시나리오

1. **기본 추천 테스트**
   - 프론트엔드에서 "아이폰 14 프로 찾고 있어요" 입력
   - 추천 결과가 정상적으로 표시되는지 확인
   - 상품 카드에 모든 정보가 표시되는지 확인

2. **다양한 검색어 테스트**
   - "MacBook Pro 2023"
   - "에어팟 프로 2세대"
   - "Canon EOS R6"
   - 각 검색어에 대해 결과가 나오는지 확인

3. **에러 처리 테스트**
   - 백엔드 서버 중지
   - 프론트엔드에서 메시지 전송
   - 에러 메시지가 표시되는지 확인
   - 백엔드 서버 재시작 후 정상 작동 확인

4. **성능 테스트**
   - 여러 번 연속으로 검색 요청
   - 응답 시간 확인 (일반적으로 10-30초)
   - 메모리 누수 확인

### 6.2 API 응답 형식 검증

```python
# test_api_response.py
import requests
import json

url = "http://localhost:8000/api/v1/recommend"
payload = {
    "search_query": "아이폰 14 프로",
    "trust_safety": 70,
    "quality_condition": 80,
    "remote_transaction": 60,
    "activity_responsiveness": 75,
    "price_flexibility": 50,
}

response = requests.post(url, json=payload)
data = response.json()

# 응답 형식 검증
assert "status" in data
assert "final_item_scores" in data or "ranked_products" in data
assert "persona_classification" in data

if data.get("final_item_scores"):
    for item in data["final_item_scores"]:
        assert "product_id" in item
        assert "title" in item
        assert "price" in item
        assert "final_score" in item
        assert "ranking_factors" in item
        assert "seller_name" in item

print("✅ API 응답 형식 검증 통과")
print(json.dumps(data, indent=2, ensure_ascii=False))
```

### 6.3 CORS 테스트

```bash
# 프론트엔드에서 백엔드로 요청이 정상적으로 전송되는지 확인
# 브라우저 개발자 도구 → Network 탭에서 확인

# CORS 에러가 발생하는 경우:
# - server/main.py의 CORS 설정 확인
# - 프론트엔드 포트가 allow_origins에 포함되어 있는지 확인
```

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
# 포트 8000이 사용 중인 경우 (백엔드)
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8000 | xargs kill -9

# 포트 3000이 사용 중인 경우 (프론트엔드)
# Windows
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:3000 | xargs kill -9

# 또는 다른 포트 사용
# 백엔드: uvicorn server.main:app --port 8001
# 프론트엔드: vite.config.ts에서 port 변경
```

### 프론트엔드 빌드 오류

```bash
# Node.js 버전 확인 (18+ 필요)
node --version

# 의존성 재설치
cd app/frontend
rm -rf node_modules package-lock.json
npm install

# 캐시 클리어
npm cache clean --force
```

### API 연결 실패

```bash
# 백엔드 서버 실행 확인
curl http://localhost:8000/api/v1/health

# 프론트엔드 환경 변수 확인
cd app/frontend
cat .env  # VITE_API_BASE_URL 확인

# CORS 설정 확인
# server/main.py의 allow_origins에 프론트엔드 포트 포함 확인
```

---

## 📝 테스트 체크리스트

### 백엔드
- [ ] 환경 변수 설정 확인
- [ ] 데이터베이스 테이블 생성 확인
- [ ] 개별 에이전트 테스트 통과
- [ ] FastAPI 서버 실행 및 API 호출 성공
- [ ] 전체 워크플로우 실행 성공
- [ ] API 응답 형식 검증 통과

### 프론트엔드
- [ ] Node.js 18+ 설치 확인
- [ ] 프론트엔드 의존성 설치 완료
- [ ] 개발 서버 실행 성공
- [ ] 챗봇 인터페이스 정상 작동
- [ ] API 연동 정상 작동
- [ ] 추천 결과 표시 확인
- [ ] 에러 처리 확인
- [ ] 반응형 디자인 확인

### 통합
- [ ] 프론트엔드 → 백엔드 통신 확인
- [ ] 전체 워크플로우 통합 테스트 통과
- [ ] CORS 설정 확인
- [ ] 성능 테스트 통과

---

## 💡 팁

1. **개발 중에는 FastAPI 서버를 `--reload` 옵션으로 실행**하여 코드 변경 시 자동 재시작
2. **에이전트 테스트는 목업 데이터를 사용**하므로 실제 API 키 없이도 기본 동작 확인 가능
3. **Swagger UI**를 활용하면 API 테스트가 더 편리합니다
4. **각 에이전트의 로그를 확인**하여 실행 과정을 추적할 수 있습니다
5. **프론트엔드 개발 시 브라우저 개발자 도구를 활용**하여 네트워크 요청과 응답을 확인하세요
6. **Vite의 HMR(Hot Module Replacement)** 기능으로 코드 변경 시 자동 새로고침됩니다
7. **백엔드와 프론트엔드를 동시에 실행**할 때는 두 개의 터미널을 사용하세요
8. **프로덕션 빌드 테스트**: `npm run build` 후 빌드된 파일로 테스트해보세요
