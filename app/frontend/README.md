# ReCo Frontend

React + Vite + TypeScript 기반 프론트엔드 애플리케이션

## 설치 및 실행

### 1. 의존성 설치

```bash
cd app/frontend
npm install
```

### 2. 환경 변수 설정

```bash
cp .env.example .env
```

`.env` 파일에서 FastAPI 서버 URL을 설정하세요:
```
VITE_API_BASE_URL=http://localhost:8000
```

### 3. 개발 서버 실행

```bash
npm run dev
```

브라우저에서 `http://localhost:3000`으로 접속하세요.

### 4. 빌드

```bash
npm run build
```

빌드된 파일은 `build` 폴더에 생성됩니다.

## FastAPI 백엔드 연동

프론트엔드는 `http://localhost:8000`에서 실행되는 FastAPI 서버와 통신합니다.

FastAPI 서버가 실행 중이어야 정상적으로 작동합니다.

## 주요 기능

- 챗봇 인터페이스를 통한 상품 추천
- 실시간 API 연동
- 반응형 디자인
- Tailwind CSS + Radix UI

