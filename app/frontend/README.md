# ReCo 프론트엔드 실행 가이드

## 빠른 시작

### 1. 의존성 설치

```bash
cd app/frontend
npm install --legacy-peer-deps
```

### 2. 개발 서버 실행

```bash
npm run dev
```

서버가 `http://localhost:5173` (또는 Vite가 할당한 포트)에서 실행됩니다.

**주의**: 백엔드 서버(`http://localhost:8000`)가 먼저 실행되어 있어야 합니다.

## 주요 기능

### 일반 대화

- "안녕하세요", "고마워", "도와줘" 같은 일반 대화에 즉시 응답합니다.
- 인사말, 감사 표현, 짧은 문장은 자동으로 일반 대화로 인식됩니다.

### 상품 추천

- 상품명이나 키워드를 입력하면 AI가 분석하여 추천합니다.
- 가격 범위, 카테고리 필터를 사용할 수 있습니다.
- 실행 시간이 표시됩니다 (개발 환경 콘솔).

## 문제 해결

### npm 캐시 권한 문제

터미널에서 다음 명령어를 실행하세요:

```bash
sudo chown -R $(whoami) ~/.npm
```

### 의존성 충돌

```bash
# npm 캐시 삭제
npm cache clean --force

# node_modules와 package-lock.json 삭제
rm -rf node_modules package-lock.json

# 재설치
npm install --legacy-peer-deps
```

### 백엔드 연결 오류

1. 백엔드 서버가 실행 중인지 확인 (`http://localhost:8000/health`)
2. `.env` 파일에 `VITE_API_BASE_URL`이 올바르게 설정되어 있는지 확인
3. CORS 설정 확인 (백엔드 `server/main.py`)

## 환경 변수

프로젝트 루트에 `.env` 파일을 생성하여 설정할 수 있습니다:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_API_TIMEOUT_MS=120000
```

## 빌드

```bash
npm run build
```

빌드된 파일은 `dist/` 디렉터리에 생성됩니다.

## 테스트

```bash
npm test                # 테스트 실행
npm run test:coverage   # 커버리지 포함
```
