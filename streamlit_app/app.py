"""
ReCo - 중고거래 상품 추천 시스템
Streamlit 프론트엔드 (Azure OpenAI 기반)

실행 방법:
    streamlit run streamlit_app/app.py

환경변수:
    BACKEND_URL: FastAPI 백엔드 주소 (기본값: http://localhost:8000)
"""

import os
import time
import requests
import streamlit as st
from dotenv import load_dotenv

# .env 로드
load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
RECOMMEND_API = f"{BACKEND_URL}/api/v1/recommend"
HEALTH_API = f"{BACKEND_URL}/api/v1/health"

# ──────────────────────────────────────────────────────────────────
# 페이지 설정
# ──────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ReCo - 중고거래 추천",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────────
# CSS 스타일
# ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* 전체 배경 */
    .stApp {
        background-color: #f8f9fa;
    }

    /* 헤더 */
    .reco-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem 2.5rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
    }
    .reco-header h1 {
        font-size: 2.8rem;
        font-weight: 800;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .reco-header p {
        font-size: 1.1rem;
        opacity: 0.9;
        margin: 0.5rem 0 0 0;
    }

    /* 검색 박스 */
    .search-container {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }

    /* 상품 카드 */
    .product-card {
        background: white;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        margin-bottom: 1rem;
        border-left: 4px solid #667eea;
        box-shadow: 0 2px 8px rgba(0,0,0,0.07);
        transition: transform 0.2s;
    }
    .product-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 16px rgba(0,0,0,0.12);
    }
    .product-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #1a1a2e;
        margin-bottom: 0.3rem;
    }
    .product-price {
        font-size: 1.3rem;
        font-weight: 800;
        color: #667eea;
    }
    .product-meta {
        font-size: 0.85rem;
        color: #6c757d;
        margin-top: 0.3rem;
    }

    /* 점수 배지 */
    .score-badge {
        display: inline-block;
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        border-radius: 20px;
        padding: 0.2rem 0.8rem;
        font-size: 0.8rem;
        font-weight: 600;
    }

    /* 순위 번호 */
    .rank-number {
        font-size: 1.5rem;
        font-weight: 900;
        color: #667eea;
        min-width: 2.5rem;
        text-align: center;
    }

    /* 추론 설명 */
    .reasoning-box {
        background: #f0f0ff;
        border-radius: 8px;
        padding: 0.8rem 1rem;
        margin-top: 0.8rem;
        font-size: 0.9rem;
        color: #4a4a6a;
        border-left: 3px solid #667eea;
    }

    /* 설명 섹션 */
    .ranking-explanation {
        background: white;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        margin-bottom: 1.5rem;
        border-left: 4px solid #764ba2;
        box-shadow: 0 2px 8px rgba(0,0,0,0.07);
        font-size: 0.95rem;
        color: #444;
    }

    /* 상태 표시 */
    .status-ok {
        color: #28a745;
        font-weight: 600;
    }
    .status-err {
        color: #dc3545;
        font-weight: 600;
    }

    /* 사이드바 */
    section[data-testid="stSidebar"] {
        background-color: #f0f0ff;
    }
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────
# 헬퍼 함수
# ──────────────────────────────────────────────────────────────────

def check_backend_health() -> bool:
    """백엔드 서버 상태 확인"""
    try:
        resp = requests.get(HEALTH_API, timeout=3)
        return resp.status_code == 200
    except Exception:
        return False


def call_recommend_api(payload: dict) -> dict:
    """추천 API 호출"""
    try:
        resp = requests.post(
            RECOMMEND_API,
            json=payload,
            timeout=300,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        return {"error": f"백엔드 서버에 연결할 수 없습니다. ({BACKEND_URL})"}
    except requests.exceptions.Timeout:
        return {"error": "요청 시간이 초과되었습니다. (300초)"}
    except requests.exceptions.HTTPError as e:
        return {"error": f"서버 오류: {e.response.status_code} - {e.response.text[:200]}"}
    except Exception as e:
        return {"error": f"알 수 없는 오류: {str(e)}"}


def format_price(price) -> str:
    """가격 포맷팅"""
    try:
        p = int(float(price))
        return f"{p:,}원"
    except (TypeError, ValueError):
        return "가격 미정"


def score_color(score: float) -> str:
    """점수에 따른 색상"""
    if score >= 0.8:
        return "#28a745"
    elif score >= 0.6:
        return "#ffc107"
    else:
        return "#dc3545"


def render_product_card(item: dict, rank: int):
    """상품 카드 렌더링"""
    title = item.get("title", "상품명 없음")
    price = format_price(item.get("price", 0))
    seller = item.get("seller_name", "판매자 없음")
    category = item.get("category", "")
    condition = item.get("condition", "")
    location = item.get("location", "")
    final_score = item.get("final_score", 0.5)
    reasoning = item.get("final_reasoning", "")

    ranking_factors = item.get("ranking_factors", {})
    product_score = ranking_factors.get("product_score", final_score)
    reliability_score = ranking_factors.get("reliability_score", final_score)

    # 순위에 따른 강조 색상
    border_colors = {1: "#FFD700", 2: "#C0C0C0", 3: "#CD7F32"}
    border_color = border_colors.get(rank, "#667eea")

    meta_parts = []
    if category:
        meta_parts.append(f"카테고리: {category}")
    if condition:
        meta_parts.append(f"상태: {condition}")
    if location:
        meta_parts.append(f"지역: {location}")

    medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, f"#{rank}")

    st.markdown(f"""
    <div class="product-card" style="border-left-color: {border_color};">
        <div style="display:flex; align-items:center; gap:1rem;">
            <div class="rank-number" style="color:{border_color};">{medal}</div>
            <div style="flex:1;">
                <div class="product-title">{title}</div>
                <div class="product-price">{price}</div>
                <div class="product-meta">
                    판매자: <strong>{seller}</strong>
                    {' &nbsp;|&nbsp; '.join(meta_parts) and ' &nbsp;|&nbsp; ' + ' &nbsp;|&nbsp; '.join(meta_parts)}
                </div>
            </div>
            <div style="text-align:right; min-width:90px;">
                <div style="font-size:0.75rem; color:#999; margin-bottom:4px;">종합 점수</div>
                <div style="font-size:1.4rem; font-weight:800; color:{score_color(final_score)};">
                    {final_score:.0%}
                </div>
                <div style="font-size:0.72rem; color:#aaa;">
                    상품 {product_score:.0%} · 신뢰 {reliability_score:.0%}
                </div>
            </div>
        </div>
        {f'<div class="reasoning-box">{reasoning}</div>' if reasoning else ''}
    </div>
    """, unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────
# 사이드바
# ──────────────────────────────────────────────────────────────────

def render_sidebar():
    """사이드바: 선호도 설정"""
    with st.sidebar:
        st.markdown("## ⚙️ 추천 설정")
        st.markdown("---")

        st.markdown("### 선호도 설정")
        st.caption("슬라이더를 조정하여 원하는 방향의 추천을 받으세요.")

        trust_safety = st.slider(
            "🔒 신뢰도 / 안전성",
            min_value=0, max_value=100, value=50, step=5,
            help="판매자의 신뢰도와 안전 거래 여부를 중시할수록 높게 설정"
        )
        quality_condition = st.slider(
            "✨ 품질 / 상태",
            min_value=0, max_value=100, value=50, step=5,
            help="상품의 품질과 상태를 중시할수록 높게 설정"
        )
        remote_transaction = st.slider(
            "📦 원격 거래 선호",
            min_value=0, max_value=100, value=50, step=5,
            help="택배 등 비대면 거래를 선호할수록 높게 설정"
        )
        activity_responsiveness = st.slider(
            "⚡ 판매자 활동성",
            min_value=0, max_value=100, value=50, step=5,
            help="빠른 응답과 활발한 판매자를 선호할수록 높게 설정"
        )
        price_flexibility = st.slider(
            "💬 가격 협상 가능성",
            min_value=0, max_value=100, value=50, step=5,
            help="가격 네고가 가능한 판매자를 선호할수록 높게 설정"
        )

        st.markdown("---")
        st.markdown("### 가격 범위")
        use_price_range = st.checkbox("가격 범위 설정", value=False)
        price_min, price_max = None, None
        if use_price_range:
            col1, col2 = st.columns(2)
            with col1:
                price_min = st.number_input("최소 (원)", min_value=0, value=0, step=1000)
            with col2:
                price_max = st.number_input("최대 (원)", min_value=0, value=100000, step=1000)
            if price_min and price_max and price_min > price_max:
                st.warning("최소 가격이 최대 가격보다 큽니다.")
                price_min, price_max = None, None

        st.markdown("---")

        # 백엔드 상태
        st.markdown("### 서버 상태")
        if st.button("상태 확인", use_container_width=True):
            with st.spinner("확인 중..."):
                ok = check_backend_health()
            if ok:
                st.markdown('<span class="status-ok">● 백엔드 정상</span>', unsafe_allow_html=True)
            else:
                st.markdown(
                    f'<span class="status-err">● 백엔드 연결 실패</span><br>'
                    f'<small>{BACKEND_URL}</small>',
                    unsafe_allow_html=True
                )

        st.markdown("---")
        st.caption("ReCo - 중고거래 추천 시스템\nPowered by Azure OpenAI")

    return {
        "trust_safety": float(trust_safety),
        "quality_condition": float(quality_condition),
        "remote_transaction": float(remote_transaction),
        "activity_responsiveness": float(activity_responsiveness),
        "price_flexibility": float(price_flexibility),
        "price_min": float(price_min) if price_min else None,
        "price_max": float(price_max) if price_max else None,
    }


# ──────────────────────────────────────────────────────────────────
# 메인 화면
# ──────────────────────────────────────────────────────────────────

def main():
    # 세션 상태 초기화
    if "results" not in st.session_state:
        st.session_state.results = None
    if "last_query" not in st.session_state:
        st.session_state.last_query = ""
    if "session_id" not in st.session_state:
        st.session_state.session_id = None
    if "execution_time" not in st.session_state:
        st.session_state.execution_time = None

    # 헤더
    st.markdown("""
    <div class="reco-header">
        <h1>🛒 ReCo</h1>
        <p>AI가 분석한 중고거래 상품 추천 &nbsp;·&nbsp; Powered by Azure OpenAI</p>
    </div>
    """, unsafe_allow_html=True)

    # 사이드바에서 설정 가져오기
    prefs = render_sidebar()

    # 검색 영역
    st.markdown('<div class="search-container">', unsafe_allow_html=True)

    col_input, col_btn = st.columns([5, 1])
    with col_input:
        query = st.text_input(
            label="검색어",
            placeholder="예) 아이폰 15 Pro, 닌텐도 스위치, 맥북 M2 ...",
            label_visibility="collapsed",
            value=st.session_state.last_query,
        )
    with col_btn:
        search_clicked = st.button("추천 받기", type="primary", use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # 추천 실행
    if search_clicked:
        if not query or not query.strip():
            st.warning("검색어를 입력해주세요.")
        else:
            st.session_state.last_query = query.strip()

            payload = {
                "search_query": query.strip(),
                "trust_safety": prefs["trust_safety"],
                "quality_condition": prefs["quality_condition"],
                "remote_transaction": prefs["remote_transaction"],
                "activity_responsiveness": prefs["activity_responsiveness"],
                "price_flexibility": prefs["price_flexibility"],
            }

            if prefs["price_min"] is not None:
                payload["price_min"] = prefs["price_min"]
            if prefs["price_max"] is not None:
                payload["price_max"] = prefs["price_max"]

            if st.session_state.session_id:
                payload["session_id"] = st.session_state.session_id

            with st.spinner("AI 에이전트가 상품을 분석 중입니다... (최대 4분 소요)"):
                start = time.time()

                # 진행 상황 표시
                progress_placeholder = st.empty()
                steps = [
                    "상품 특성 분석 중...",
                    "판매자 신뢰도 분석 중...",
                    "최종 추천 생성 중...",
                ]
                for i, step_msg in enumerate(steps):
                    progress_placeholder.info(f"{'⏳' if i < 2 else '🔍'} {step_msg}")
                    time.sleep(0.3)
                progress_placeholder.empty()

                result = call_recommend_api(payload)
                elapsed = time.time() - start

            if "error" in result:
                st.error(f"오류 발생: {result['error']}")
                st.session_state.results = None
            else:
                st.session_state.results = result
                st.session_state.session_id = result.get("session_id")
                st.session_state.execution_time = result.get("execution_time") or elapsed

    # 결과 표시
    if st.session_state.results:
        result = st.session_state.results
        items = result.get("final_item_scores") or result.get("ranked_products") or []

        if not items:
            st.warning("검색 결과가 없습니다. 다른 검색어나 조건으로 다시 시도해보세요.")
        else:
            # 요약 정보
            exec_time = st.session_state.execution_time
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("추천 결과", f"{len(items)}개 상품")
            with col2:
                st.metric("분석 시간", f"{exec_time:.1f}초" if exec_time else "-")
            with col3:
                top_score = items[0].get("final_score", 0) if items else 0
                st.metric("최고 점수", f"{top_score:.0%}")

            # 추천 이유 설명
            explanation = result.get("ranking_explanation", "")
            if explanation:
                st.markdown(f"""
                <div class="ranking-explanation">
                    <strong>📋 추천 이유</strong><br>{explanation}
                </div>
                """, unsafe_allow_html=True)

            st.markdown(f"### 추천 상품 목록 — `{st.session_state.last_query}`")
            st.markdown("---")

            # 상품 카드 렌더링
            for rank, item in enumerate(items, 1):
                render_product_card(item, rank)

            # 세부 데이터 토글
            with st.expander("원본 데이터 보기 (개발자용)"):
                st.json(result)


# ──────────────────────────────────────────────────────────────────
# 앱 진입점
# ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    main()
else:
    main()
