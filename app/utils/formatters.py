"""
데이터 포맷팅 유틸리티
"""


def format_price(price: float) -> str:
    """가격을 원 단위로 포맷팅"""
    if price is None:
        return "가격 정보 없음"
    return f"{price:,.0f}원"


def format_score(score: float, decimals: int = 2) -> str:
    """점수를 포맷팅"""
    if score is None:
        return "N/A"
    return f"{score:.{decimals}f}"


def format_percentage(value: float) -> str:
    """퍼센트로 포맷팅"""
    if value is None:
        return "N/A"
    return f"{value:.1f}%"


def truncate_text(text: str, max_length: int = 50) -> str:
    """텍스트를 지정된 길이로 자르기"""
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."

