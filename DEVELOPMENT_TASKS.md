# ReCo 개발 작업 목록

프론트엔드, 백엔드, AI 에이전트를 통틀어 추가로 필요한 개발 작업 목록입니다.

## 🔴 우선순위 높음 (즉시 필요)

(현재 우선순위 높은 작업 없음)

---

## 🟡 우선순위 중간 (중요하지만 급하지 않음)


### 7. 프론트엔드 에러 바운더리
**현재 상태**: 기본 에러 처리만 있음
**필요 작업**:
- React Error Boundary 구현
- 전역 에러 핸들러
- 에러 리포팅 (선택사항)
- 사용자 친화적 에러 UI

**파일**: `app/frontend/src/components/ErrorBoundary.tsx` 생성

---


### 9. 추천 판매자 상품 노출 로직
**필요 작업**:
- 에이전트가 추천한 판매자 목록에서 상품 조회
- 판매자별 상품을 DB에서 가져와 무작위 5~10개 선택
- 프론트엔드에 노출할 API/응답 구조 정의
- 중복/품절 상품 필터링 로직
- UI에 판매자별 상품 카드 표시

**파일**:
- `server/routers/workflow.py` 또는 별도 추천 API (상품 리스트 포함)
- `server/db/product_service.py` (판매자 상품 조회 함수)
- 프론트엔드 컴포넌트 (`app/frontend/src/components/RecommendationPage.tsx` 등)

---

## 📋 구현 우선순위 (일괄 진행)

1. 캐싱 시스템 (기본)
5. API Rate Limiting
6. 환경 변수 검증 강화
7. 프론트엔드 에러 바운더리
8. 정답 데이터셋 구축
9. 추천 판매자 상품 노출 로직

---

## 🛠️ 기술 스택 제안

### 로깅
- Python: `structlog` 또는 `loguru`
- 프론트엔드: `winston` 또는 기본 `console`

### 캐싱
- Redis (프로덕션)
- `functools.lru_cache` (개발)

### 테스트
- 백엔드: `pytest`, `pytest-asyncio` ✅
- 프론트엔드: `vitest`, `@testing-library/react` ✅

### 모니터링
- Prometheus + Grafana
- 또는 간단한 메트릭 수집

---


