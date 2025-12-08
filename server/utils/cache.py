"""
캐싱 시스템
Redis 또는 in-memory 캐시를 사용하여 데이터 캐싱
"""

import json
import hashlib
import time
from typing import Any, Optional, Callable
from functools import wraps
from datetime import datetime, timedelta

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

import os
from server.utils.logger import get_logger

logger = get_logger(__name__)

# Redis 설정
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
REDIS_ENABLED = os.getenv("REDIS_ENABLED", "false").lower() == "true"

# In-memory 캐시 (Redis가 없을 때 사용)
_in_memory_cache: dict = {}
_cache_ttl: dict = {}


class CacheManager:
    """캐싱 관리자 - Redis 또는 in-memory 캐시 사용"""

    def __init__(self):
        self.redis_client = None
        self.use_redis = False

        if REDIS_ENABLED and REDIS_AVAILABLE:
            try:
                self.redis_client = redis.from_url(
                    REDIS_URL,
                    decode_responses=True,
                    socket_connect_timeout=2,
                    socket_timeout=2,
                )
                # 연결 테스트
                self.redis_client.ping()
                self.use_redis = True
                logger.info("Redis 캐시 연결 성공")
            except Exception as e:
                logger.warning(f"Redis 연결 실패, in-memory 캐시 사용: {e}")
                self.use_redis = False
        else:
            logger.info("Redis 비활성화, in-memory 캐시 사용")

    def _make_key(self, prefix: str, key: str) -> str:
        """캐시 키 생성"""
        if isinstance(key, (dict, list)):
            key_str = json.dumps(key, sort_keys=True)
        else:
            key_str = str(key)
        key_hash = hashlib.md5(key_str.encode()).hexdigest()
        return f"reco:{prefix}:{key_hash}"

    def get(self, prefix: str, key: str) -> Optional[Any]:
        """캐시에서 값 가져오기"""
        cache_key = self._make_key(prefix, key)

        if self.use_redis and self.redis_client:
            try:
                value = self.redis_client.get(cache_key)
                if value:
                    return json.loads(value)
            except Exception as e:
                logger.warning(f"Redis get 오류: {e}")
        else:
            # In-memory 캐시
            if cache_key in _in_memory_cache:
                # TTL 확인
                if cache_key in _cache_ttl:
                    if time.time() < _cache_ttl[cache_key]:
                        return _in_memory_cache[cache_key]
                    else:
                        # TTL 만료
                        del _in_memory_cache[cache_key]
                        del _cache_ttl[cache_key]

        return None

    def set(
        self,
        prefix: str,
        key: str,
        value: Any,
        ttl_seconds: int = 3600,
    ) -> bool:
        """캐시에 값 저장"""
        cache_key = self._make_key(prefix, key)

        try:
            value_json = json.dumps(value, default=str, ensure_ascii=False)
        except (TypeError, ValueError) as e:
            logger.warning(f"캐시 값 직렬화 실패: {e}")
            return False

        if self.use_redis and self.redis_client:
            try:
                self.redis_client.setex(cache_key, ttl_seconds, value_json)
                return True
            except Exception as e:
                logger.warning(f"Redis set 오류: {e}")
                return False
        else:
            # In-memory 캐시
            _in_memory_cache[cache_key] = value
            _cache_ttl[cache_key] = time.time() + ttl_seconds
            return True

    def delete(self, prefix: str, key: str) -> bool:
        """캐시에서 값 삭제"""
        cache_key = self._make_key(prefix, key)

        if self.use_redis and self.redis_client:
            try:
                self.redis_client.delete(cache_key)
                return True
            except Exception as e:
                logger.warning(f"Redis delete 오류: {e}")
                return False
        else:
            # In-memory 캐시
            if cache_key in _in_memory_cache:
                del _in_memory_cache[cache_key]
            if cache_key in _cache_ttl:
                del _cache_ttl[cache_key]
            return True

    def clear_prefix(self, prefix: str) -> int:
        """특정 prefix의 모든 캐시 삭제"""
        count = 0

        if self.use_redis and self.redis_client:
            try:
                pattern = f"reco:{prefix}:*"
                keys = self.redis_client.keys(pattern)
                if keys:
                    count = self.redis_client.delete(*keys)
            except Exception as e:
                logger.warning(f"Redis clear_prefix 오류: {e}")
        else:
            # In-memory 캐시
            keys_to_delete = [
                k for k in _in_memory_cache.keys() if k.startswith(f"reco:{prefix}:")
            ]
            for key in keys_to_delete:
                del _in_memory_cache[key]
                if key in _cache_ttl:
                    del _cache_ttl[key]
            count = len(keys_to_delete)

        return count


# 전역 캐시 인스턴스
cache_manager = CacheManager()


# ==================== 캐싱 데코레이터 ====================

def cached(prefix: str, ttl_seconds: int = 3600):
    """
    함수 결과를 캐싱하는 데코레이터

    Args:
        prefix: 캐시 prefix
        ttl_seconds: 캐시 유지 시간 (초)

    Example:
        @cached("price_data", ttl_seconds=3600)
        def get_price_data(query: str):
            ...
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 캐시 키 생성 (함수명 + 인자)
            cache_key = {
                "func": func.__name__,
                "args": args,
                "kwargs": kwargs,
            }

            # 캐시에서 조회
            cached_value = cache_manager.get(prefix, cache_key)
            if cached_value is not None:
                logger.debug(f"캐시 히트: {func.__name__}")
                return cached_value

            # 캐시 미스 - 함수 실행
            result = func(*args, **kwargs)

            # 결과 캐싱
            cache_manager.set(prefix, cache_key, result, ttl_seconds)
            logger.debug(f"캐시 저장: {func.__name__}")

            return result

        return wrapper

    return decorator


# ==================== 특정 데이터 타입 캐싱 ====================

def cache_price_data(query: str, data: Any, ttl_seconds: int = 3600):
    """시세 데이터 캐싱 (1시간 기본)"""
    return cache_manager.set("price_data", query, data, ttl_seconds)


def get_cached_price_data(query: str) -> Optional[Any]:
    """캐시된 시세 데이터 조회"""
    return cache_manager.get("price_data", query)


def cache_search_results(query: str, results: Any, ttl_seconds: int = 1800):
    """검색 결과 캐싱 (30분 기본)"""
    return cache_manager.set("search_results", query, results, ttl_seconds)


def get_cached_search_results(query: str) -> Optional[Any]:
    """캐시된 검색 결과 조회"""
    return cache_manager.get("search_results", query)


def clear_all_cache():
    """모든 캐시 삭제"""
    cache_manager.clear_prefix("price_data")
    cache_manager.clear_prefix("search_results")
    logger.info("모든 캐시 삭제 완료")
