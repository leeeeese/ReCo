# ReCo - 중고거래 추천 시스템

LangGraph 기반 멀티 에이전트 시스템을 활용한 지능형 중고거래 상품 추천 플랫폼입니다.

## ✨ 주요 기능

- **🤖 멀티 에이전트 워크플로우**: 상품 특성 분석, 신뢰도 분석, 최종 통합을 담당하는 3개의 전문 에이전트
- **🎯 사용자 의도 기반 추천**: "친절한 판매자", "가격이 싼", "아이폰 14" 같은 자연어 입력을 LLM이 분석하여 맞춤형 추천
- **💬 일반 대화 지원**: 인사말이나 간단한 질문에 자연스럽게 응답 (gpt-4o-mini, 30초 타임아웃)
- **⚡ 성능 최적화**: Orchestrator는 gpt-5-mini, 서브 에이전트는 gpt-4o-mini로 속도와 품질 균형
- **🎨 현대적인 UI**: React + TypeScript + Tailwind CSS 기반 반응형 웹 인터페이스
- **📊 실시간 시세 분석**: 시장 가격 데이터 기반 가성비 평가

## 🏗️ 시스템 아키텍처

### 에이전트 워크플로우

```
사용자 입력: "친절한 판매자가 파는 가격이 싼 아이폰 14"
      ↓
  초기화 (Initialization)
      ↓
  ┌─────────────────┴─────────────────┐
  ↓                                   ↓
ProductAgent                   ReliabilityAgent
(gpt-4o-mini)                  (gpt-4o-mini)
가격/할인율 좋은                신뢰도 좋은
판매자 47명 조회                판매자 47명 조회
  ↓                                   ↓
  └─────────────────┬─────────────────┘
                    ↓
          Orchestrator Agent
             (gpt-5-mini)
    사용자 의도 분석 및 최종 선택
    "친절" + "가격 싼" + "아이폰 14"
                    ↓
         상품 매칭 (Rule-based)
                    ↓
           상위 10개 결과 반환
```

### 디렉터리 구조

```
ReCo/
├── app/frontend/              # React 프론트엔드
│   ├── src/
│   │   ├── components/       # UI 컴포넌트
│   │   ├── utils/api.ts      # API 클라이언트
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
├── server/                    # FastAPI 백엔드
│   ├── main.py               # 메인 애플리케이션
│   ├── routers/
│   │   └── workflow.py       # 워크플로우 API
│   ├── workflow/
│   │   ├── state.py          # State 정의
│   │   ├── graph.py          # Graph 정의
│   │   ├── prompts/          # LLM 프롬프트
│   │   └── agents/           # 에이전트 구현
│   │       ├── product_agent.py
│   │       ├── reliability_agent.py
│   │       └── orchestrator_agent.py
│   ├── db/                   # 데이터베이스
│   │   ├── models.py         # SQLAlchemy 모델
│   │   └── product_service.py
│   └── utils/
│       ├── llm_agent.py      # LLM 래퍼
│       ├── config.py         # 설정
│       └── tools.py          # 유틸리티
└── requirements.txt
```

## 🚀 빠른 시작

### 필수 요구사항

- **Python 3.10+**
- **Node.js 18+**
- **OpenAI API Key**

### 1. 저장소 클론

```bash
git clone <repository-url>
cd ReCo
```

### 2. 환경변수 설정

프로젝트 루트에 `.env` 파일을 생성하고 다음을 입력하세요:

```bash
# 필수
OPENAI_API_KEY=your-api-key-here

# 선택사항 (기본값 사용 가능)
OPENAI_MODEL=gpt-5-mini
DATABASE_URL=sqlite:///./history.db
PRICER_DATABASE_URL=sqlite:///./used_pricer.db
WORKFLOW_TIMEOUT_SECONDS=240
LLM_TIMEOUT_SECONDS=180
LLM_MAX_RETRIES=0
```

### 3. 백엔드 설정

```bash
# Python 가상환경 생성 및 활성화
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt

# 데이터베이스 마이그레이션 (선택사항)
python server/db/migrate_csv.py
```

### 4. 프론트엔드 설정

```bash
cd app/frontend
npm install
```

### 5. 실행

#### 백엔드 실행

```bash
# 프로젝트 루트에서
python -m uvicorn server.main:app --reload --host 0.0.0.0 --port 8000
```

서버 실행 확인: http://localhost:8000/docs

#### 프론트엔드 실행 (새 터미널)

```bash
cd app/frontend
npm run dev
```

브라우저 접속: http://localhost:5173

**⚠️ 중요**: 백엔드가 먼저 실행되어 있어야 프론트엔드가 정상 작동합니다!

## 💡 사용 방법

### 상품 추천 받기

1. 프론트엔드 접속 (http://localhost:5173)
2. 검색창에 자연어로 입력:
   - "친절한 판매자가 파는 가격이 싼 아이폰 14"
   - "믿을 수 있고 가격도 괜찮은 맥북"
   - "거래 많은 판매자 갤럭시"
3. 약 1-2분 후 추천 결과 확인

### 일반 대화

- "안녕", "고마워", "도와줘" 등의 간단한 메시지 입력 시 즉시 응답 (3-5초)

## 🤖 에이전트 상세 설명

### ProductAgent (상품 특성 분석)

**역할**: 가격과 할인율 기준으로 판매자 분석

**프로세스**:

1. DB에서 모든 카테고리 판매자 조회 (검색어 필터 없음)
2. LLM이 상품 품질, 가격 전략, 판매자 성향 분석
3. 가격 관점에서 좋은 판매자 추천

**모델**: `gpt-4o-mini` (빠른 응답)

### ReliabilityAgent (신뢰도 분석)

**역할**: 판매자 신뢰도와 리뷰 기준으로 분석

**프로세스**:

1. DB에서 모든 카테고리 판매자 조회 (검색어 필터 없음)
2. LLM이 거래 행동, 리뷰 성향, 신뢰도 분석
3. 신뢰도 관점에서 좋은 판매자 추천

**모델**: `gpt-4o-mini` (빠른 응답)

### OrchestratorAgent (최종 통합)

**역할**: 사용자 의도 파악 및 최종 판매자 선택

**프로세스**:

1. 사용자 입력 분석: "친절한" + "가격 싼" + "아이폰 14"
2. ProductAgent와 ReliabilityAgent 결과 통합
3. 사용자 의도에 맞는 판매자 선택
4. 선택된 판매자의 상품 매칭 (최대 5개/판매자)
5. 최종 상위 10개 상품 반환

**모델**: `gpt-5-mini` (강력한 추론)

## 📚 주요 API

| 엔드포인트               | 설명                      | 타임아웃 |
| ------------------------ | ------------------------- | -------- |
| `POST /api/v1/recommend` | 전체 추천 워크플로우 실행 | 240초    |
| `POST /api/v1/chat`      | 일반 대화 처리            | 30초     |
| `GET /api/v1/health`     | 상태 확인                 | -        |

## 🛠️ 기술 스택

### 백엔드

- **FastAPI** - RESTful API 서버
- **LangGraph** - 워크플로우 오케스트레이션
- **OpenAI API** - LLM 통합 (gpt-5-mini, gpt-4o-mini)
- **SQLAlchemy** - ORM
- **SQLite** - 데이터베이스 (개발환경)
- **Pydantic** - 데이터 검증

### 프론트엔드

- **React 18** - UI 라이브러리
- **TypeScript** - 타입 안정성
- **Vite** - 빌드 도구
- **Tailwind CSS** - 스타일링
- **Radix UI** - 접근성 컴포넌트

## ⚙️ 환경변수 상세

| 변수명                     | 설명                 | 기본값                       |
| -------------------------- | -------------------- | ---------------------------- |
| `OPENAI_API_KEY`           | OpenAI API 키 (필수) | -                            |
| `OPENAI_MODEL`             | 기본 모델            | `gpt-5-mini`                 |
| `DATABASE_URL`             | 데이터베이스 URL     | `sqlite:///./history.db`     |
| `PRICER_DATABASE_URL`      | 시세 DB URL          | `sqlite:///./used_pricer.db` |
| `WORKFLOW_TIMEOUT_SECONDS` | 워크플로우 타임아웃  | `240`                        |
| `LLM_TIMEOUT_SECONDS`      | LLM 호출 타임아웃    | `180`                        |
| `LLM_MAX_RETRIES`          | LLM 재시도 횟수      | `0`                          |
| `USER_AGENT`               | 크롤러 User Agent    | Mozilla/5.0...               |
