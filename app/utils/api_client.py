"""
FastAPI 클라이언트 래퍼
"""

import requests
import os
from typing import Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 루트의 .env 파일 로드
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


class APIClient:
    """API 클라이언트"""

    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.timeout = 60  # 추천 시스템은 시간이 걸릴 수 있음

    def recommend_products(self, user_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        상품 추천 API 호출
        
        Args:
            user_input: 사용자 입력 데이터
            
        Returns:
            추천 결과
        """
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/recommend",
                json=user_input,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            raise Exception("요청 시간이 초과되었습니다. 잠시 후 다시 시도해주세요.")
        except requests.exceptions.ConnectionError:
            raise Exception(f"서버에 연결할 수 없습니다. ({self.base_url})")
        except requests.exceptions.HTTPError as e:
            raise Exception(f"서버 오류: {e.response.status_code}")
        except Exception as e:
            raise Exception(f"오류 발생: {str(e)}")

    def health_check(self) -> bool:
        """헬스 체크"""
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/health",
                timeout=5
            )
            return response.status_code == 200
        except:
            return False


# 싱글톤 인스턴스
api_client = APIClient()

