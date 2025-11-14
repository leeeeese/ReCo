"""
전체 워크플로우 테스트 스크립트
LangGraph 워크플로우를 처음부터 끝까지 실행하는 테스트
"""

from server.workflow.graph import recommendation_workflow
from server.utils.mock_data import get_mock_user_input
from server.workflow.state import RecommendationState
import json

def test_full_workflow():
    """전체 워크플로우 테스트"""
    print("=" * 60)
    print("ReCo 전체 워크플로우 테스트")
    print("=" * 60)
    
    # 워크플로우 초기화
    app = recommendation_workflow()
    
    # 초기 상태 생성
    initial_state: RecommendationState = {
        "user_input": get_mock_user_input(),
        "search_query": {},
        "persona_classification": None,
        "seller_item_scores": [],
        "final_item_scores": [],
        "sql_query": None,
        "ranking_explanation": "",
        "current_step": "start",
        "completed_steps": [],
        "error_message": None,
        "price_agent_recommendations": None,
        "safety_agent_recommendations": None,
        "persona_matching_recommendations": None,
        "final_seller_recommendations": None,
        "mock_sellers_with_products": None,
        "mock_sellers_with_persona": None,
    }
    
    print("\n📥 초기 입력:")
    print(f"  - 검색어: {initial_state['user_input'].get('search_query', 'N/A')}")
    print(f"  - 카테고리: {initial_state['user_input'].get('category', 'N/A')}")
    print(f"  - 위치: {initial_state['user_input'].get('location', 'N/A')}")
    
    print("\n🚀 워크플로우 실행 중...\n")
    
    try:
        # 워크플로우 실행
        result = app.invoke(initial_state)
        
        print("=" * 60)
        print("✅ 워크플로우 실행 완료")
        print("=" * 60)
        
        print(f"\n📊 실행 결과:")
        print(f"  - 최종 단계: {result.get('current_step')}")
        print(f"  - 완료된 단계: {', '.join(result.get('completed_steps', []))}")
        
        # 페르소나 분류 결과
        persona = result.get('persona_classification')
        if persona:
            print(f"\n👤 페르소나 분류:")
            print(f"  - 타입: {persona.get('persona_type', 'N/A')}")
            print(f"  - 신뢰도: {persona.get('confidence', 'N/A')}")
        
        # 검색 쿼리
        search_query = result.get('search_query', {})
        if search_query:
            print(f"\n🔍 검색 쿼리:")
            print(f"  - 키워드: {search_query.get('keywords', 'N/A')}")
            print(f"  - 필터: {search_query.get('filters', {})}")
        
        # 서브 에이전트 결과
        price_recs = result.get('price_agent_recommendations', {})
        safety_recs = result.get('safety_agent_recommendations', {})
        persona_recs = result.get('persona_matching_recommendations', {})
        
        print(f"\n💰 가격 에이전트:")
        print(f"  - 추천 판매자 수: {len(price_recs.get('recommended_sellers', []))}")
        
        print(f"\n🔒 안전거래 에이전트:")
        print(f"  - 추천 판매자 수: {len(safety_recs.get('recommended_sellers', []))}")
        
        print(f"\n🎯 페르소나 매칭 에이전트:")
        print(f"  - 추천 판매자 수: {len(persona_recs.get('recommended_sellers', []))}")
        
        # 최종 추천
        final_recs = result.get('final_seller_recommendations', [])
        print(f"\n🏆 최종 추천:")
        print(f"  - 추천 판매자 수: {len(final_recs)}")
        
        if final_recs:
            print(f"\n  상위 3개 판매자:")
            for i, seller in enumerate(final_recs[:3], 1):
                print(f"    {i}. {seller.get('seller_id', 'N/A')} - 점수: {seller.get('final_score', 'N/A')}")
        
        # 최종 상품 점수
        final_scores = result.get('final_item_scores', [])
        if final_scores:
            print(f"\n📦 최종 상품 점수:")
            print(f"  - 랭킹된 상품 수: {len(final_scores)}")
            if len(final_scores) > 0:
                print(f"  - 최고 점수: {final_scores[0].get('final_score', 'N/A')}")
        
        # 에러 확인
        error = result.get('error_message')
        if error:
            print(f"\n⚠️  에러 메시지: {error}")
        else:
            print(f"\n✅ 에러 없음")
        
        print("\n" + "=" * 60)
        
        return result
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    test_full_workflow()

