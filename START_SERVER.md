# 서버 실행 가이드

## 백엔드 서버 실행

### 방법 1: uvicorn 직접 실행 (권장)

```bash
cd /Users/leeseeun/Desktop/ReCo
source .venv/bin/activate  # 가상환경 활성화 (있는 경우)
python -m uvicorn server.main:app --reload --host 0.0.0.0 --port 8000
```

### 방법 2: main.py 실행

```bash
cd /Users/leeseeun/Desktop/ReCo
source .venv/bin/activate  # 가상환경 활성화 (있는 경우)
cd server
python main.py
```

### 확인 방법

서버가 정상 실행되면:

- 터미널에 "Application startup complete" 메시지가 표시됩니다
- 브라우저에서 `http://localhost:8000/docs` 접속 시 API 문서가 보입니다
- `http://localhost:8000/api/v1/health` 접속 시 `{"status":"healthy","service":"ReCo"}` 응답이 옵니다

## 프론트엔드 서버 실행

```bash
cd /Users/leeseeun/Desktop/ReCo/app/frontend
npm run dev
```

프론트엔드는 보통 `http://localhost:5173`에서 실행됩니다.

## 문제 해결

### 백엔드가 시작되지 않는 경우

1. **가상환경 확인**

   ```bash
   source .venv/bin/activate
   ```

2. **의존성 설치 확인**

   ```bash
   pip install -r requirements.txt
   ```

3. **환경변수 확인**

   - `.env` 파일에 `OPENAI_API_KEY`가 설정되어 있는지 확인
   - 프로젝트 루트에 `.env` 파일이 있는지 확인

4. **포트 사용 중인 경우**

   ```bash
   # 8000 포트를 사용하는 프로세스 확인
   lsof -i :8000

   # 프로세스 종료 (필요시)
   kill -9 <PID>
   ```

### 프론트엔드가 백엔드에 연결되지 않는 경우

1. **백엔드 서버가 실행 중인지 확인**

   - `http://localhost:8000/api/v1/health` 접속 테스트

2. **CORS 설정 확인**

   - 백엔드 `server/main.py`에서 프론트엔드 포트가 허용되어 있는지 확인
   - 현재 허용 포트: `localhost:3000`, `localhost:5173`

3. **프론트엔드 API URL 확인**
   - 브라우저 개발자 도구 콘솔에서 네트워크 오류 확인
   - `app/frontend/src/utils/api.ts`에서 `API_BASE_URL` 확인
