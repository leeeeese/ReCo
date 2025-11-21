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

## 📚 주요 API

| 엔드포인트               | 설명                      |
| ------------------------ | ------------------------- |
| `POST /api/v1/recommend` | 전체 추천 워크플로우 실행 |
| `GET /api/v1/history`    | 추천 이력 조회            |
| `GET /api/v1/health`     | 상태 확인                 |

## 🔄 워크플로우 요약

1. **초기화**

   - 사용자 입력을 정규화하고 검색 키워드를 추출합니다.
   - 현재는 페르소나 분류를 사용하지 않으며, 기본 맥락만 전달합니다.

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

## 📝 TODO

- [ ] 자동화된 통합 테스트 작성
- [ ] Streamlit UI와 최신 워크플로우 연결
- [ ] 가격/안전 툴에 대한 캐싱 및 모니터링 추가
- [ ] 운영 환경용 로그/알람 구성
