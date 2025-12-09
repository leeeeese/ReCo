# ReCo - 중고거래 추천 시스템

LangGraph 기반 멀티 에이전트 시스템을 활용한 지능형 중고거래 상품 추천 플랫폼입니다.

## ✨ 주요 기능

- **멀티 에이전트 워크플로우**: 상품 특성 분석, 신뢰도 분석, 최종 통합 추천을 담당하는 3개의 전문 에이전트
- **사용자 선호도 기반 추천**: 사용자가 직접 입력한 선호도(신뢰도, 품질, 가격 유연성 등)를 기반으로 맞춤형 추천 제공
- **일반 대화 지원**: 인사말이나 간단한 질문에 자연스럽게 응답
- **정확한 검색**: 키워드별 AND 조건 매칭으로 관련성 높은 상품만 검색
- **실시간 시세 분석**: 시장 가격 데이터 기반 가성비 평가
- **안전거래 평가**: 판매자 신뢰도, 리뷰 분석, 거래 방법 안전성 종합 평가
- **React 프론트엔드**: 현대적인 UI/UX를 제공하는 웹 인터페이스

## 🏗️ 아키텍처

```
ReCo/
├── app/                       # 프론트엔드
│   └── frontend/            # React + Vite + TypeScript
│       ├── src/
│       │   ├── components/  # React 컴포넌트 (Landing, Chat, Recommendation 등)
│       │   ├── components/ui/  # Radix UI 기반 컴포넌트
│       │   ├── utils/       # API 클라이언트
│       │   └── test/        # Vitest 테스트
│       ├── package.json
│       └── vite.config.ts
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
│   │       ├── product_agent.py        # 상품 특성 분석 (품질 패턴, 가격 전략, 판매자 성향)
│   │       ├── reliability_agent.py   # 신뢰도 분석 (거래 행동, 리뷰 성향, 신뢰도, 활동성)
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
npm install --legacy-peer-deps  # 의존성 충돌 시
```

### 3. 환경변수 설정

프로젝트 루트에 `.env` 파일을 생성하고 다음 환경변수를 설정하세요:

**필수 환경변수**:

- `OPENAI_API_KEY`: OpenAI API 키 (필수)

**선택적 환경변수**:

- `OPENAI_MODEL`: 사용할 모델 (기본값: gpt-5-mini)
- `DATABASE_URL`: 데이터베이스 URL (기본값: sqlite:///./history.db)
- `PRICER_DATABASE_URL`: 시세 DB URL (기본값: sqlite:///./used_pricer.db)
- `WORKFLOW_TIMEOUT_SECONDS`: 워크플로우 타임아웃 (기본값: 120초)
- `LLM_TIMEOUT_SECONDS`: LLM 호출 타임아웃 (기본값: 60초)
- `LLM_MAX_RETRIES`: LLM 재시도 횟수 (기본값: 2)
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
# 가상환경 활성화 후
cd server
python -m uvicorn server.main:app --reload --host 0.0.0.0 --port 8000
```

서버가 실행되면 `http://localhost:8000`에서 API를 사용할 수 있습니다.

API 문서: `http://localhost:8000/docs`

#### React 프론트엔드

```bash
cd app/frontend
npm run dev
```

브라우저에서 `http://localhost:5173` (또는 Vite가 할당한 포트)로 접속할 수 있습니다.

**참고**: FastAPI 서버가 먼저 실행되어 있어야 프론트엔드가 정상 작동합니다.

## 📚 주요 API

| 엔드포인트               | 설명                      |
| ------------------------ | ------------------------- |
| `POST /api/v1/recommend` | 전체 추천 워크플로우 실행 |
| `POST /api/v1/chat`      | 일반 대화 처리            |
| `GET /api/v1/history`    | 추천 이력 조회            |
| `GET /api/v1/health`     | 상태 확인                 |

## 🔄 워크플로우 요약

### 1. 초기화 (Initialization)

- 사용자 입력을 정규화하고 검색 키워드를 추출합니다.
- 이전 대화 컨텍스트를 활용하여 검색 쿼리를 생성합니다.
- 사용자 선호도(신뢰도, 품질, 가격 유연성 등)를 파악합니다.

### 2. Product Agent (상품 특성 분석)

- DB에서 상품 목록을 조회합니다 (키워드별 정확한 매칭).
- 3가지 핵심 분석 수행:
  - 판매자의 상품 품질 패턴 분석 (새상품/중고/사용감 등)
  - 시세 대비 가격 전략 분석 (싸게 파는가/비싸게 파는가)
  - 판매자 성향 도출 (예: "좋은 물건을 싸게 파는 판매자")
- `server/workflow/prompts/product_prompt.txt` 프롬프트로 LLM 판단을 수행합니다.
- 상품 특성 관점에서 상위 판매자를 추천합니다 (상위 10명).

### 3. Reliability Agent (신뢰도 분석)

- 판매자 프로필, 리뷰, 거래 리스크를 DB 기반으로 분석합니다.
- 4가지 핵심 분석 수행:
  - 거래 행동 패턴 분석 (직거래/택배, 응답 속도 등)
  - 리뷰 기반 성향 추론 (친절함, 응답 빠름 등)
  - 신뢰도 프로파일링 (신뢰도 점수, 거래 이력 등)
  - 활동성·신뢰도 점수화 (활발한 판매자, 우수 판매자 등)
- `server/workflow/prompts/reliability_prompt.txt` 프롬프트로 LLM 판단을 수행합니다.
- 신뢰도 관점에서 신뢰할 수 있는 판매자를 추천합니다.

### 4. Orchestrator Agent (최종 통합)

- 상품 특성/신뢰도 결과를 `server/workflow/prompts/orchestrator_recommendation_prompt.txt`로 통합합니다.
- Multi-agent outputs 통합, Value & reliability scores 융합
- 사용자 선호도 기반 가중치 적용:
  - 높은 신뢰도 선호도 → 신뢰도 점수에 더 높은 가중치
  - 높은 품질 선호도 → 상품 특성 점수에 더 높은 가중치
  - 균형 잡힌 선호도 → 두 점수에 동일한 가중치
- **구매자-판매자 매칭 최적화**: 판매자 성향을 기반으로 "어떤 구매자에게 이 판매자가 적합한가?" 판단
- 룰베이스 기반으로 추천된 판매자에게 상품을 매칭합니다 (`match_products_to_sellers`).
- LLM 출력이 없을 경우 단순 결합 fallback 로직을 수행합니다.

## 💬 일반 대화 기능

사용자가 "안녕하세요", "고마워", "도와줘" 같은 일반 대화를 입력하면:

1. 프론트엔드에서 일반 대화 패턴을 감지합니다.
2. `/api/v1/chat` 엔드포인트로 요청을 보냅니다.
3. 백엔드에서 적절한 응답을 즉시 반환합니다.
4. 상품 추천 워크플로우를 실행하지 않아 빠르게 응답합니다.

일반 대화로 판단되는 경우:

- 인사말 (안녕하세요, 하이 등)
- 감사 표현 (고마워, 감사합니다 등)
- 짧은 문장 (3자 이하)
- 질문 패턴 (예: "뭐해?", "누구야?")

## 🧱 프롬프트 관리

모든 프롬프트는 `server/workflow/prompts/` 디렉터리에 `.txt` 파일로 분리돼 있으며,  
각 에이전트 초기화 시 `load_prompt()`로 불러옵니다. 내용만 수정하면 즉시 적용됩니다.

- `product_prompt.txt`: 상품 특성 분석 에이전트 프롬프트
- `reliability_prompt.txt`: 신뢰도 분석 에이전트 프롬프트
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

## 🛠️ 기술 스택

### 백엔드

- **FastAPI**: RESTful API 서버
- **LangGraph**: 워크플로우 오케스트레이션
- **OpenAI API**: LLM 통합
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

- ✅ 멀티 에이전트 워크플로우 (Product, Reliability, Orchestrator)
- ✅ 사용자 선호도 기반 추천 시스템 (페르소나 분류 제거)
- ✅ 일반 대화 기능
- ✅ 정확한 키워드 검색 (AND 조건 매칭)
- ✅ React 프론트엔드 (Landing, Chat, Recommendation 페이지)
- ✅ 캐싱 시스템 (Redis/in-memory)
- ✅ Rate Limiting 미들웨어
- ✅ 로깅 시스템
- ✅ 에러 처리 및 Fallback 메커니즘
- ✅ 타임아웃 설정 및 성능 최적화
- ✅ 테스트 프레임워크 (pytest, vitest)
- ✅ 상품 매칭 룰베이스 로직
- ✅ DB 서비스 레이어

## 🔧 주요 개선 사항

### 에러 처리 개선

- 각 에이전트 노드에서 에러 발생 시 적절한 fallback 처리
- LLM 호출 실패 시 기본 결합 로직 사용
- 프론트엔드에서 네트워크 오류, 타임아웃 오류 구분

### 성능 최적화

- 워크플로우 타임아웃: 120초로 증가
- LLM 타임아웃: 60초로 증가
- 상세한 로깅으로 디버깅 용이성 향상

### 사용자 경험 개선

- 일반 대화 기능 추가
- 실행 시간 표시
- 명확한 에러 메시지 제공

## 📝 향후 개선 사항

- [ ] 프론트엔드 에러 바운더리 구현
- [ ] 정답 데이터셋 구축 및 평가 시스템
- [ ] 모니터링 및 알람 시스템
- [ ] 성능 최적화 (쿼리 최적화, 캐싱 전략 개선)
- [ ] 일반 대화 LLM 통합 (현재는 규칙 기반)

## 📚 추가 문서

- [app/frontend/README.md](app/frontend/README.md): 프론트엔드 가이드

## 📄 라이선스

MIT License
