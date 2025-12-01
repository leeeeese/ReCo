"""
API Rate Limiting 미들웨어
사용자별, IP 기반 요청 제한
"""

import time
from typing import Dict, Tuple, Optional
from collections import defaultdict
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from server.utils.logger import get_logger

logger = get_logger(__name__)

# Rate limit 설정
DEFAULT_RATE_LIMIT = 100  # 시간당 기본 요청 수
DEFAULT_WINDOW_SECONDS = 3600  # 1시간


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate Limiting 미들웨어"""

    def __init__(
        self,
        app: ASGIApp,
        requests_per_hour: int = DEFAULT_RATE_LIMIT,
        window_seconds: int = DEFAULT_WINDOW_SECONDS,
        enable_user_limit: bool = True,
        enable_ip_limit: bool = True,
    ):
        super().__init__(app)
        self.requests_per_hour = requests_per_hour
        self.window_seconds = window_seconds
        self.enable_user_limit = enable_user_limit
        self.enable_ip_limit = enable_ip_limit

        # 사용자별 요청 기록: {user_id: [(timestamp, count), ...]}
        self.user_requests: Dict[str, list] = defaultdict(list)

        # IP별 요청 기록: {ip: [(timestamp, count), ...]}
        self.ip_requests: Dict[str, list] = defaultdict(list)

    def _get_client_ip(self, request: Request) -> str:
        """클라이언트 IP 주소 추출"""
        # X-Forwarded-For 헤더 확인 (프록시/로드밸런서 뒤에 있을 때)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # 첫 번째 IP 사용
            return forwarded_for.split(",")[0].strip()

        # X-Real-IP 헤더 확인
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # 직접 연결
        if request.client:
            return request.client.host

        return "unknown"

    def _get_user_id(self, request: Request) -> Optional[str]:
        """사용자 ID 추출 (세션 ID 또는 인증 토큰에서)"""
        # 세션 ID 확인
        session_id = request.headers.get("X-Session-ID")
        if session_id:
            return f"session:{session_id}"

        # Authorization 헤더 확인
        auth_header = request.headers.get("Authorization")
        if auth_header:
            # Bearer 토큰에서 사용자 ID 추출 (간단한 예시)
            # 실제로는 JWT 토큰을 파싱해야 함
            return f"auth:{auth_header[:20]}"

        return None

    def _cleanup_old_requests(self, requests_list: list, current_time: float):
        """오래된 요청 기록 정리"""
        cutoff_time = current_time - self.window_seconds
        return [
            (ts, count)
            for ts, count in requests_list
            if ts > cutoff_time
        ]

    def _check_rate_limit(
        self, identifier: str, requests_list: list, current_time: float
    ) -> Tuple[bool, int, int]:
        """
        Rate limit 확인

        Returns:
            (is_allowed, current_count, limit)
        """
        # 오래된 요청 정리
        requests_list[:] = self._cleanup_old_requests(requests_list, current_time)

        # 현재 시간대 요청 수 계산
        current_count = sum(count for _, count in requests_list)

        # 제한 확인
        is_allowed = current_count < self.requests_per_hour

        if not is_allowed:
            # 다음 요청 가능 시간 계산
            if requests_list:
                oldest_time = min(ts for ts, _ in requests_list)
                reset_time = oldest_time + self.window_seconds
                wait_seconds = max(0, int(reset_time - current_time))
            else:
                wait_seconds = 0

            logger.warning(
                f"Rate limit 초과: {identifier} (현재: {current_count}/{self.requests_per_hour}, 대기: {wait_seconds}초)"
            )

        return is_allowed, current_count, self.requests_per_hour

    async def dispatch(self, request: Request, call_next):
        """미들웨어 요청 처리"""

        # 정적 파일이나 헬스체크는 제외
        if request.url.path in ["/", "/docs", "/openapi.json", "/redoc"]:
            return await call_next(request)

        current_time = time.time()
        client_ip = self._get_client_ip(request)
        user_id = self._get_user_id(request)

        # IP 기반 제한 확인
        if self.enable_ip_limit:
            is_allowed, current_count, limit = self._check_rate_limit(
                f"IP:{client_ip}", self.ip_requests[client_ip], current_time
            )

            if not is_allowed:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "Rate limit exceeded",
                        "message": f"IP 주소당 시간당 {limit}회 요청 제한을 초과했습니다.",
                        "current_count": current_count,
                        "limit": limit,
                        "retry_after": self.window_seconds,
                    },
                    headers={
                        "X-RateLimit-Limit": str(limit),
                        "X-RateLimit-Remaining": str(max(0, limit - current_count)),
                        "X-RateLimit-Reset": str(int(current_time + self.window_seconds)),
                    },
                )

            # 요청 기록 추가
            self.ip_requests[client_ip].append((current_time, 1))

        # 사용자별 제한 확인
        if self.enable_user_limit and user_id:
            is_allowed, current_count, limit = self._check_rate_limit(
                f"User:{user_id}", self.user_requests[user_id], current_time
            )

            if not is_allowed:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "Rate limit exceeded",
                        "message": f"사용자당 시간당 {limit}회 요청 제한을 초과했습니다.",
                        "current_count": current_count,
                        "limit": limit,
                        "retry_after": self.window_seconds,
                    },
                    headers={
                        "X-RateLimit-Limit": str(limit),
                        "X-RateLimit-Remaining": str(max(0, limit - current_count)),
                        "X-RateLimit-Reset": str(int(current_time + self.window_seconds)),
                    },
                )

            # 요청 기록 추가
            self.user_requests[user_id].append((current_time, 1))

        # 요청 처리
        response = await call_next(request)

        # Rate limit 헤더 추가
        if self.enable_ip_limit:
            current_count = sum(
                count
                for _, count in self._cleanup_old_requests(
                    self.ip_requests[client_ip], current_time
                )
            )
            response.headers["X-RateLimit-Limit"] = str(self.requests_per_hour)
            response.headers["X-RateLimit-Remaining"] = str(
                max(0, self.requests_per_hour - current_count)
            )
            response.headers["X-RateLimit-Reset"] = str(
                int(current_time + self.window_seconds)
            )

        return response

