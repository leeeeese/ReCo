# ReCo - 중고거래 추천 시스템

LangGraph Agent 기반의 중고거래 상품 추천 시스템입니다.

## 🏗️ 아키텍처

```
ReCo/
├── app/                       # 프론트엔드
│   ├── frontend/            # React + Vite 프론트엔드
│   │   ├── src/             # 소스 코드
│   │   │   ├── components/  # React 컴포넌트
│   │   │   └── utils/       # 유틸리티 (API 클라이언트)
│   │   ├── package.json     # Node.js 의존성
│   │   └── vite.config.ts   # Vite 설정
│   └── pages/               # Streamlit 페이지 (레거시)
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
│   │       ├── price_agent.py         # 가격 합리성 판단
│   │       ├── safety_agent.py        # 안전거래 판단
│   │       ├── orchestrator_agent.py  # 최종 통합/랭킹
│   │       ├── price_updater.py       # 시세 크롤러
│   │       └── tool.py                # 공용/전용 툴 묶음
│   └── utils/
│       ├── config.py
│       └── workflow_utils.py
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

### 4. 데이터베이스 설정

기본적으로 SQLite를 사용합니다. 필요시 PostgreSQL이나 MySQL 설정 가능.
자세한 내용은 [SETUP_GUIDE.md](SETUP_GUIDE.md)를 참고하세요.

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

1. **초기화**

   - 사용자 입력을 정규화하고 검색 키워드를 추출합니다.
   - 페르소나 분류를 수행합니다.

2. **Price Agent**

   - DB에서 상품 목록을 가져와 `item_market_tool`, `price_risk_tool` 등을 통해 시세/판매자 정보를 정량화합니다.
   - `server/workflow/prompts/price_prompt.txt` 프롬프트로 LLM 판단을 수행해 가격 관점 추천을 생성합니다.

3. **Safety Agent**

   - 판매자 프로필/리뷰/거래 리스크를 DB 기반 툴로 계산합니다.
   - `server/workflow/prompts/safety_prompt.txt` 프롬프트로 LLM 판단을 수행해 안전 관점 추천을 생성합니다.

4. **Orchestrator Agent**
   - 가격/안전 결과를 `server/workflow/prompts/orchestrator_recommendation_prompt.txt`로 통합한 뒤,  
     `orchestrator_ranking_prompt.txt`로 최종 상품 랭킹을 생성합니다.
   - LLM 출력이 없을 경우 단순 결합 fallback 로직을 수행합니다.

## 🧱 프롬프트 관리

모든 프롬프트는 `server/workflow/prompts/` 디렉터리에 `.txt` 파일로 분리돼 있으며,  
각 에이전트 초기화 시 `load_prompt()`로 불러옵니다. 내용만 수정하면 즉시 적용됩니다.

## 🛠️ 기술 스택

### 백엔드

- **FastAPI**: RESTful API 서버
- **LangGraph**: 워크플로우 오케스트레이션
- **LangChain**: LLM 통합
- **SQLAlchemy**: ORM
- **SQLite/PostgreSQL/MySQL**: 데이터베이스

### 프론트엔드

- **React 18**: UI 라이브러리
- **TypeScript**: 타입 안정성
- **Vite**: 빌드 도구
- **Tailwind CSS**: 스타일링
- **Radix UI**: 접근성 컴포넌트
- **Lucide React**: 아이콘

## 📝 TODO

- [ ] 자동화된 통합 테스트 작성
- [ ] 가격/안전 툴에 대한 캐싱 및 모니터링 추가
- [ ] 운영 환경용 로그/알람 구성
