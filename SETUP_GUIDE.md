# ReCo 서버 설정 가이드

## 📋 필수 API 키

### 1. OpenAI API Key (필수)

- **용도**: 모든 LLM 기반 Agent에서 사용
  - Persona Classifier
  - Price Agent
  - Safety Agent
  - Persona Matching Agent
  - Recommendation Orchestrator
- **발급 방법**: https://platform.openai.com/api-keys
- **비용**: 사용량에 따라 과금 (gpt-4o-mini는 저렴)
- **설정**: `.env` 파일에 `OPENAI_API_KEY=sk-...` 추가

### 2. SerpAPI Key (선택)

- **용도**: Price Agent의 실시간 시세 조회 폴백용
- **발급 방법**: https://serpapi.com/
- **비용**: 무료 티어 존재 (월 100회)
- **설정**: `.env` 파일에 `SERPAPI_KEY=...` 추가
- **참고**: 없으면 `joongna_search_prices`만 사용 (Playwright 필요)

---

## 🗄️ 데이터베이스 설정

### 기본 설정 (SQLite - 개발용)

가장 간단한 방법입니다. 별도 설치 없이 바로 사용 가능합니다.

```bash
# .env 파일에 설정 (기본값)
DATABASE_URL=sqlite:///./history.db
PRICER_DATABASE_URL=sqlite:///./used_pricer.db
```

**장점:**

- 별도 서버 설치 불필요
- 파일 기반으로 간단함
- 개발/테스트에 적합

**단점:**

- 프로덕션 환경에는 부적합
- 동시 접속 제한

---

### PostgreSQL 설정 (프로덕션 권장)

1. **PostgreSQL 설치**

   ```bash
   # macOS
   brew install postgresql
   brew services start postgresql

   # Ubuntu/Debian
   sudo apt-get install postgresql postgresql-contrib
   sudo systemctl start postgresql
   ```

2. **데이터베이스 생성**

   ```bash
   psql -U postgres
   CREATE DATABASE reco_db;
   CREATE USER reco_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE reco_db TO reco_user;
   \q
   ```

3. **.env 파일 설정**

   ```bash
   DATABASE_URL=postgresql://reco_user:your_password@localhost:5432/reco_db
   ```

4. **의존성 설치 확인**
   ```bash
   pip install psycopg2-binary  # requirements.txt에 이미 포함됨
   ```

---

### MySQL 설정 (기존 MySQL 사용 시)

1. **MySQL 설치 및 데이터베이스 생성**

   ```sql
   CREATE DATABASE reco_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   CREATE USER 'reco_user'@'localhost' IDENTIFIED BY 'your_password';
   GRANT ALL PRIVILEGES ON reco_db.* TO 'reco_user'@'localhost';
   FLUSH PRIVILEGES;
   ```

2. **.env 파일 설정**

   ```bash
   DATABASE_URL=mysql+pymysql://reco_user:your_password@localhost:3306/reco_db
   ```

3. **의존성 확인**
   ```bash
   pip install pymysql  # requirements.txt에 이미 포함됨
   ```

---

## 🚀 초기 설정 단계

### 1. 환경 변수 파일 생성

```bash
# 프로젝트 루트에서
cp env.example .env

# .env 파일 편집
nano .env  # 또는 원하는 에디터
```

### 2. 필수 환경 변수 설정

`.env` 파일에 최소한 다음을 설정:

```bash
OPENAI_API_KEY=sk-your_actual_api_key_here
DATABASE_URL=sqlite:///./history.db  # 또는 PostgreSQL/MySQL URL
```

### 3. Python 패키지 설치

```bash
pip install -r requirements.txt
```

### 4. Playwright 브라우저 설치 (Price Agent용)

```bash
playwright install chromium
```

### 5. 데이터베이스 초기화

```bash
# Python에서 테이블 생성
python -c "from server.db.database import database; database.create_tables()"

# 또는 서버 실행 시 자동 생성됨
```

### 6. 설정 검증

```bash
python server/utils/config.py
```

---

## 📊 데이터베이스 스키마

### 메인 DB (history.db)

- `history` 테이블: 추천 이력 저장
- `products` 테이블: 상품 정보
- `sellers` 테이블: 판매자 정보

### 가격 조회 DB (used_pricer.db)

- `items` 테이블: 가격 조회 이력

---

## 🔍 각 Agent별 필요한 설정

### Price Agent

- ✅ OpenAI API Key (필수)
- ⚠️ SerpAPI Key (선택, 폴백용)
- ✅ Playwright (시세 크롤링용)
- ✅ SQLite/PostgreSQL/MySQL

### Safety Agent

- ✅ OpenAI API Key (필수)
- ✅ SQLite/PostgreSQL/MySQL

### Persona Matching Agent

- ✅ OpenAI API Key (필수)
- ✅ 페르소나 플레이북 파일 (`server/retrieval/playbook/personas/*.md`)
- ✅ SQLite/PostgreSQL/MySQL

### Recommendation Orchestrator

- ✅ OpenAI API Key (필수)
- ✅ 3개 서브에이전트 결과

---

## 🧪 테스트용 최소 설정

개발/테스트만 할 경우:

```bash
# .env 파일
OPENAI_API_KEY=sk-your_key
DATABASE_URL=sqlite:///./history.db
```

이렇게만 설정하면 목업 데이터로 각 Agent를 테스트할 수 있습니다.

---

## ⚠️ 주의사항

1. **API 키 보안**

   - `.env` 파일은 절대 Git에 커밋하지 마세요
   - `.gitignore`에 `.env`가 포함되어 있는지 확인

2. **데이터베이스 백업**

   - 프로덕션 환경에서는 정기적인 백업 필요

3. **Playwright**
   - 시세 크롤링 시 웹사이트 정책에 따라 차단될 수 있음
   - 적절한 딜레이와 에러 처리 필요
