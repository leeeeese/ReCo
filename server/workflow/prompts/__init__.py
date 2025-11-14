"""
프롬프트 관리 모듈
각 에이전트의 프롬프트를 별도 파일로 관리
"""

from pathlib import Path

# 프롬프트 디렉토리 경로
PROMPTS_DIR = Path(__file__).parent


def load_prompt(prompt_name: str) -> str:
    """
    프롬프트 파일 로드
    
    Args:
        prompt_name: 프롬프트 파일명 (확장자 제외)
    
    Returns:
        프롬프트 내용
    """
    prompt_file = PROMPTS_DIR / f"{prompt_name}.txt"
    
    if not prompt_file.exists():
        raise FileNotFoundError(f"프롬프트 파일을 찾을 수 없습니다: {prompt_file}")
    
    with open(prompt_file, "r", encoding="utf-8") as f:
        return f.read().strip()

