# ReCo 프론트엔드 실행 가이드

## 문제 해결

### 1. npm 캐시 권한 문제 해결

터미널에서 다음 명령어를 실행하세요:

```bash
sudo chown -R 501:20 "/Users/leeseeun/.npm"
```

### 2. 의존성 설치

```bash
cd app/frontend
npm install --legacy-peer-deps
```

### 3. 개발 서버 실행

```bash
npm run dev
```

서버가 `http://localhost:3000`에서 실행됩니다.

## 문제가 계속되면

npm 캐시를 완전히 비우고 다시 시도:

```bash
# npm 캐시 삭제 (권한 문제 해결 후)
npm cache clean --force

# node_modules와 package-lock.json 삭제
rm -rf node_modules package-lock.json

# 재설치
npm install --legacy-peer-deps
```
