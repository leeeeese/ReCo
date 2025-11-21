# ReCo - 중고거래 추천 시스템

LangGraph Agent 기반의 중고거래 상품 추천 시스템입니다.

## 🏗️ 아키텍처

```
ReCo/
├── app/                       # Streamlit UI
│   ├── main.py              # Streamlit 메인 애플리케이션
│   ├── components/          # UI 컴포넌트
│   └── utils/               # 유틸리티 함수
├── server/                   # FastAPI 백엔드
│   ├── main.py              # FastAPI 메인 애플리케이션
│   ├── routers/             # API 라우터
│   │   ├── workflow.py     # 워크플로우 API
│   │   └── history.py      # 히스토리 API
│   ├── db/                  # 데이터베이스
│   │   ├── database.py     # DB 연결
│   │   ├── models.py       # SQLAlchemy 모델
│   │   └── schemas.py      # Pydantic 스키마
│   ├── workflow/           # LangGraph 워크플로우
│   │   ├── state.py        # State 정의
│   │   ├── graph.py        # Graph 정의
│   │   └── agents/         # Agent 구현
│   │       ├── persona_classifier.py
│   │       ├── query_generator.py
│   │       ├── product_matching.py
│   │       ├── ranker.py
│   │       ├── router.py
│   │       └── sql_generator.py
│   └── utils/              # 유틸리티
│       ├── config.py
│       └── review_crawler.py
└── requirements.txt
```

## 🚀 설치 및 실행

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 환경변수 설정

```bash
cp env.example .env
# .env 파일을 편집하여 실제 값 입력
```

### 3. 데이터베이스 설정

기본적으로 SQLite를 사용합니다. 필요시 PostgreSQL이나 MySQL 설정 가능.

### 4. 서버 실행

#### FastAPI 백엔드

```bash
cd server
python main.py
```

서버가 실행되면 `http://localhost:8000`에서 API를 사용할 수 있습니다.

API 문서: `http://localhost:8000/docs`

#### Streamlit UI

```bash
cd app
streamlit run main.py
```

브라우저에서 `http://localhost:8501`로 접속할 수 있습니다.

## 📚 API 사용법

### 1. 상품 추천

```bash
curl -X POST "http://localhost:8000/api/v1/recommend" \
  -H "Content-Type: application/json" \
  -d '{
    "search_query": "아이폰 14",
    "price_min": 1000000,
    "price_max": 1500000,
    "category": "스마트폰",
    "location": "서울"
  }'
```

### 2. 페르소나 목록 조회

```bash
curl "http://localhost:8000/api/v1/personas"
```

### 3. 헬스 체크

```bash
curl "http://localhost:8000/api/v1/health"
```

## 🔄 워크플로우

1. **사용자 입력** → 검색 쿼리, 가격 범위, 카테고리 등
2. **페르소나 분류** → 사용자 특성을 10가지 페르소나로 분류
3. **검색 쿼리 생성** → 페르소나에 맞게 쿼리 향상
4. **상품 매칭** → 텍스트 매칭 + 페르소나 매칭
5. **랭킹** → 최종 추천 상품 순서 결정

## 🧠 페르소나 시스템

10가지 페르소나를 5축으로 분류:

- **신뢰·안전** (Trust & Safety)
- **품질·상태** (Quality & Condition)
- **원격거래성향** (Remote Transaction Preference)
- **활동·응답** (Activity & Responsiveness)
- **가격유연성** (Price Flexibility)

## 🛠️ 개발

### Agent 추가

1. `src/agents/`에 새 Agent 파일 생성
2. `src/graphs/recommendation_graph.py`에 노드 추가
3. 라우터에서 조건부 엣지 설정

### State 확장

`src/core/state.py`에서 `RecommendationState`를 수정하여 새로운 상태 필드 추가

## 📝 TODO

- [ ] Agents 파일들의 import 경로 수정
- [ ] 실제 DB 연동 및 데이터 로드
- [ ] LangGraph 워크플로우 통합
- [ ] RAG 벡터 스토어 구현
- [ ] Streamlit UI와 FastAPI 연결
- [ ] 로깅 및 모니터링 추가
- [ ] 단위 테스트 작성

## ⚠️ 주의사항

현재 agents 파일들은 이전 프로젝트 구조에서 가져온 것으로, import 경로가 현재 프로젝트 구조와 맞지 않을 수 있습니다. 수정이 필요합니다:

1. `server/workflow/agents/persona_classifier.py` - import 경로 수정
2. `server/workflow/agents/product_matching.py` - import 경로 수정
3. `server/workflow/agents/ranker.py` - import 경로 수정
4. 기타 필요한 유틸리티 모듈 구현
