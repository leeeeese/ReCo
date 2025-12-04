# ReCo - 중고거래 추천 시스템

LangGraph 기반 멀티 에이전트 시스템을 활용한 지능형 중고거래 상품 추천 플랫폼입니다.

## ✨ 주요 기능

- **멀티 에이전트 워크플로우**: 가격 분석, 안전거래 평가, 최종 통합 추천을 담당하는 3개의 전문 에이전트
- **페르소나 기반 추천**: 사용자 선호도를 분석하여 맞춤형 추천 제공
- **정확한 검색**: 키워드별 AND 조건 매칭으로 관련성 높은 상품만 검색
- **실시간 시세 분석**: 시장 가격 데이터 기반 가성비 평가
- **안전거래 평가**: 판매자 신뢰도, 리뷰 분석, 거래 방법 안전성 종합 평가
- **React 프론트엔드**: 현대적인 UI/UX를 제공하는 웹 인터페이스

## 🏗️ 아키텍처

```
ReCo/
├── app/                       # 프론트엔드
│   ├── frontend/            # React + Vite + TypeScript
│   │   ├── src/
│   │   │   ├── components/  # React 컴포넌트 (Landing, Chat, Recommendation 등)
│   │   │   ├── components/ui/  # Radix UI 기반 컴포넌트
│   │   │   ├── utils/       # API 클라이언트
│   │   │   └── test/        # Vitest 테스트
│   │   ├── package.json
│   │   └── vite.config.ts
│   └── pages/               # Streamlit 페이지 (레거시)
├── server/                   # FastAPI 백엔드
│   ├── main.py              # FastAPI 메인 애플리케이션
│   ├── routers/             # API 라우터
│   │   ├── workflow.py     # 워크플로우 API
│   │   └── history.py      # 히스토리 API
│   ├── middleware/         # 미들웨어
│   │   └── rate_limit.py   # Rate Limiting
│   ├── db/                  # 데이터베이스
│   │   ├── database.py     # DB 연결 및 설정
│   │   ├── models.py       # SQLAlchemy 모델
│   │   ├── schemas.py      # Pydantic 스키마
│   │   ├── product_service.py  # 상품 조회 서비스
│   │   └── conversation_service.py  # 대화 관리
│   ├── workflow/           # LangGraph 워크플로우
│   │   ├── state.py        # State 정의
│   │   ├── graph.py        # Graph 정의
│   │   ├── prompts/        # LLM 프롬프트 파일
│   │   └── agents/         # Agent 구현
│   │       ├── price_agent.py         # 가격 합리성 판단
│   │       ├── safety_agent.py        # 안전거래 판단
│   │       ├── orchestrator_agent.py  # 최종 통합/랭킹
│   │       └── price_updater.py       # 시세 크롤러
│   └── utils/
│       ├── config.py        # 설정 관리
│       ├── logger.py        # 로깅 시스템
│       ├── cache.py         # 캐싱 시스템 (Redis/in-memory)
│       ├── llm_agent.py     # LLM 에이전트 래퍼
│       ├── tools.py         # 공통 유틸리티 및 룰베이스 매칭
│       └── workflow_utils.py # 워크플로우 유틸리티
├── tests/                   # 테스트
│   ├── unit/               # 단위 테스트
│   ├── integration/        # 통합 테스트
│   ├── api/                # API 테스트
│   └── e2e/                # E2E 테스트
└── requirements.txt
```

## 🚀 설치 및 실행

### 1. 백엔드 의존성 설치

```bash
# Python 가상환경 생성 (권장)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Python 패키지 설치
pip install -r requirements.txt
```

### 2. 프론트엔드 의존성 설치

```bash
# Node.js 18+ 필요
cd app/frontend
npm install
```

### 3. 환경변수 설정

```bash
cp env.example .env
# .env 파일을 편집하여 실제 값 입력
```

**필수 환경변수**:

- `OPENAI_API_KEY`: OpenAI API 키 (필수)
- `OPENAI_MODEL`: 사용할 모델 (기본값: gpt-4o-mini)

**선택적 환경변수**:

- `DATABASE_URL`: 데이터베이스 URL (기본값: SQLite)
- `REDIS_ENABLED`: Redis 캐싱 사용 여부 (기본값: false)
- `REDIS_URL`: Redis 연결 URL
- `RATE_LIMIT_PER_HOUR`: 시간당 요청 제한 (기본값: 100)

### 4. 데이터베이스 설정

기본적으로 SQLite를 사용합니다. 필요시 PostgreSQL이나 MySQL 설정 가능.

**CSV 데이터 마이그레이션** (선택사항):

```bash
python server/db/migrate_csv.py
```

### 5. 서버 실행

#### FastAPI 백엔드

```bash
cd server
python main.py
```

서버가 실행되면 `http://localhost:8000`에서 API를 사용할 수 있습니다.

API 문서: `http://localhost:8000/docs`

#### React 프론트엔드

```bash
# 프론트엔드 의존성 설치 (처음 한 번만)
cd app/frontend
npm install

# 개발 서버 실행
npm run dev
```

브라우저에서 `http://localhost:3000`으로 접속할 수 있습니다.

**참고**: FastAPI 서버가 먼저 실행되어 있어야 프론트엔드가 정상 작동합니다.

#### Streamlit UI (레거시)

```bash
cd app
streamlit run main.py
```

브라우저에서 `http://localhost:8501`로 접속할 수 있습니다.

## 📚 주요 API

| 엔드포인트               | 설명                      |
| ------------------------ | ------------------------- |
| `POST /api/v1/recommend` | 전체 추천 워크플로우 실행 |
| `GET /api/v1/history`    | 추천 이력 조회            |
| `GET /api/v1/health`     | 상태 확인                 |

## 🔄 워크플로우 요약

1. **초기화 (Initialization)**

   - 사용자 입력을 정규화하고 검색 키워드를 추출합니다.
   - 페르소나 분류를 수행합니다 (price_sensible, balanced, risk_averse 등).
   - 검색 쿼리를 생성합니다 (키워드별 AND 조건 매칭).

2. **Price Agent (가격 분석)**

   - DB에서 상품 목록을 조회합니다 (키워드별 정확한 매칭).
   - 시세 데이터와 가격 리스크를 분석합니다.
   - `server/workflow/prompts/price_prompt.txt` 프롬프트로 LLM 판단을 수행합니다.
   - 가격 관점에서 상위 판매자를 추천합니다 (상위 10명).

3. **Safety Agent (안전거래 분석)**

   - 판매자 프로필, 리뷰, 거래 리스크를 DB 기반으로 분석합니다.
   - `server/workflow/prompts/safety_prompt.txt` 프롬프트로 LLM 판단을 수행합니다.
   - 안전거래 관점에서 신뢰할 수 있는 판매자를 추천합니다.

4. **Orchestrator Agent (최종 통합)**
   - 가격/안전 결과를 `server/workflow/prompts/orchestrator_recommendation_prompt.txt`로 통합합니다.
   - 사용자 페르소나에 맞게 가중치를 조정하여 최종 판매자 랭킹을 생성합니다.
   - 룰베이스 기반으로 추천된 판매자에게 상품을 매칭합니다 (`match_products_to_sellers`).
   - LLM 출력이 없을 경우 단순 결합 fallback 로직을 수행합니다.

## 🧱 프롬프트 관리

모든 프롬프트는 `server/workflow/prompts/` 디렉터리에 `.txt` 파일로 분리돼 있으며,  
각 에이전트 초기화 시 `load_prompt()`로 불러옵니다. 내용만 수정하면 즉시 적용됩니다.

- `price_prompt.txt`: 가격 분석 에이전트 프롬프트
- `safety_prompt.txt`: 안전거래 분석 에이전트 프롬프트
- `orchestrator_recommendation_prompt.txt`: 판매자 통합 추천 프롬프트
- `orchestrator_ranking_prompt.txt`: 상품 랭킹 프롬프트 (현재 미사용)

## 🧪 테스트

### 백엔드 테스트

```bash
# 전체 테스트 실행
pytest

# 특정 마커로 테스트
pytest -m unit          # 단위 테스트만
pytest -m integration   # 통합 테스트만
pytest -m api           # API 테스트만

# 커버리지 포함
pytest --cov=server --cov-report=html
```

### 프론트엔드 테스트

```bash
cd app/frontend
npm test                # 테스트 실행
npm run test:coverage   # 커버리지 포함
```

자세한 내용은 [tests/README.md](tests/README.md)를 참고하세요.

## 🛠️ 기술 스택

### 백엔드

- **FastAPI**: RESTful API 서버
- **LangGraph**: 워크플로우 오케스트레이션
- **LangChain**: LLM 통합
- **SQLAlchemy**: ORM
- **SQLite/PostgreSQL/MySQL**: 데이터베이스
- **Redis**: 캐싱 (선택사항)
- **Pydantic**: 데이터 검증
- **pytest**: 테스트 프레임워크

### 프론트엔드

- **React 18**: UI 라이브러리
- **TypeScript**: 타입 안정성
- **Vite**: 빌드 도구
- **Tailwind CSS**: 스타일링
- **Radix UI**: 접근성 컴포넌트
- **Vitest**: 테스트 프레임워크
- **Testing Library**: 컴포넌트 테스트

## ✅ 구현 완료 기능

- ✅ 멀티 에이전트 워크플로우 (Price, Safety, Orchestrator)
- ✅ 페르소나 기반 추천 시스템
- ✅ 정확한 키워드 검색 (AND 조건 매칭)
- ✅ React 프론트엔드 (Landing, Chat, Recommendation 페이지)
- ✅ 캐싱 시스템 (Redis/in-memory)
- ✅ Rate Limiting 미들웨어
- ✅ 로깅 시스템
- ✅ 테스트 프레임워크 (pytest, vitest)
- ✅ 상품 매칭 룰베이스 로직
- ✅ DB 서비스 레이어

## 📝 향후 개선 사항

자세한 내용은 [DEVELOPMENT_TASKS.md](DEVELOPMENT_TASKS.md)를 참고하세요.

- [ ] 프론트엔드 에러 바운더리 구현
- [ ] 정답 데이터셋 구축 및 평가 시스템
- [ ] 모니터링 및 알람 시스템
- [ ] 성능 최적화 (쿼리 최적화, 캐싱 전략 개선)

## 📚 추가 문서

- [DEVELOPMENT_TASKS.md](DEVELOPMENT_TASKS.md): 개발 작업 목록
- [tests/README.md](tests/README.md): 테스트 가이드
- [app/frontend/README.md](app/frontend/README.md): 프론트엔드 가이드
