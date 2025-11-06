"""
Agent 테스트 스크립트
각 Agent를 CLI에서 테스트할 수 있는 간단한 스크립트
"""

from server.utils.workflow_utils import classify_persona, generate_search_query
from server.workflow.agents import (
    price_agent_node,
    safety_agent_node,
    persona_matching_agent_node,
    recommendation_orchestrator_node,
)
from server.utils.mock_data import (
    get_mock_user_input,
    get_mock_sellers_with_products,
    get_mock_sellers_with_persona,
    get_mock_persona_classification,
    get_mock_search_query,
    get_mock_state,
)
import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_price_agent():
    """가격 에이전트 테스트"""
    print("=" * 50)
    print("가격 에이전트 테스트")
    print("=" * 50)

    state = get_mock_state()
    state["search_query"] = get_mock_search_query()

    # 목업 데이터로 sellers_with_products 설정 (실제로는 agent 내부에서 조회)
    # 여기서는 테스트를 위해 state에 직접 추가하지 않고 agent 내부 로직에 의존

    result = price_agent_node(state)

    print(f"\n결과:")
    print(f"- 상태: {result.get('current_step')}")
    print(
        f"- 추천 판매자 수: {len(result.get('price_agent_recommendations', {}).get('recommended_sellers', []))}")
    print(f"- 에러: {result.get('error_message')}")

    return result


def test_safety_agent():
    """안전거래 에이전트 테스트"""
    print("\n" + "=" * 50)
    print("안전거래 에이전트 테스트")
    print("=" * 50)

    state = get_mock_state()

    result = safety_agent_node(state)

    print(f"\n결과:")
    print(f"- 상태: {result.get('current_step')}")
    print(
        f"- 추천 판매자 수: {len(result.get('safety_agent_recommendations', {}).get('recommended_sellers', []))}")
    print(f"- 에러: {result.get('error_message')}")

    return result


def test_persona_matching_agent():
    """페르소나 매칭 에이전트 테스트"""
    print("\n" + "=" * 50)
    print("페르소나 매칭 에이전트 테스트")
    print("=" * 50)

    state = get_mock_state()
    state["persona_classification"] = get_mock_persona_classification()

    result = persona_matching_agent_node(state)

    print(f"\n결과:")
    print(f"- 상태: {result.get('current_step')}")
    print(
        f"- 추천 판매자 수: {len(result.get('persona_matching_recommendations', {}).get('recommended_sellers', []))}")
    print(f"- 에러: {result.get('error_message')}")

    return result


def test_recommendation_orchestrator():
    """추천 오케스트레이터 테스트"""
    print("\n" + "=" * 50)
    print("추천 오케스트레이터 테스트")
    print("=" * 50)

    from server.utils.mock_data import (
        get_mock_price_agent_result,
        get_mock_safety_agent_result,
        get_mock_persona_matching_result,
    )

    state = get_mock_state()
    state["persona_classification"] = get_mock_persona_classification()

    # 3개 서브에이전트 결과 설정
    state["price_agent_recommendations"] = get_mock_price_agent_result()
    state["safety_agent_recommendations"] = get_mock_safety_agent_result()
    state["persona_matching_recommendations"] = get_mock_persona_matching_result()

    result = recommendation_orchestrator_node(state)

    print(f"\n결과:")
    print(f"- 상태: {result.get('current_step')}")
    print(
        f"- 최종 추천 판매자 수: {len(result.get('final_seller_recommendations', []))}")
    print(f"- 랭킹된 상품 수: {len(result.get('final_item_scores', []))}")
    print(f"- 에러: {result.get('error_message')}")

    return result


def test_persona_classification():
    """페르소나 분류 테스트"""
    print("\n" + "=" * 50)
    print("페르소나 분류 테스트")
    print("=" * 50)

    user_input = get_mock_user_input()

    result = classify_persona(user_input)

    print(f"\n결과:")
    print(f"- 페르소나 타입: {result.get('persona_type')}")
    print(f"- 신뢰도: {result.get('confidence')}")
    print(f"- 근거: {result.get('reason')}")

    return result


def main():
    """메인 테스트 함수"""
    print("\n" + "=" * 50)
    print("ReCo Agent 테스트 스크립트")
    print("=" * 50)

    # 환경 변수 확인
    if not os.getenv("OPENAI_API_KEY"):
        print("\n⚠️  경고: OPENAI_API_KEY가 설정되지 않았습니다.")
        print("   .env 파일을 확인하거나 환경 변수를 설정해주세요.")
        print("   LLM 기능이 제대로 작동하지 않을 수 있습니다.\n")

    tests = {
        "1": ("페르소나 분류", test_persona_classification),
        "2": ("가격 에이전트", test_price_agent),
        "3": ("안전거래 에이전트", test_safety_agent),
        "4": ("페르소나 매칭 에이전트", test_persona_matching_agent),
        "5": ("추천 오케스트레이터", test_recommendation_orchestrator),
        "all": ("모든 테스트 실행", None),
    }

    if len(sys.argv) > 1:
        test_key = sys.argv[1]
    else:
        print("\n테스트할 Agent를 선택하세요:")
        for key, (name, _) in tests.items():
            print(f"  {key}: {name}")
        print()
        test_key = input("선택 (1-5, all): ").strip().lower()

    if test_key == "all":
        test_persona_classification()
        test_price_agent()
        test_safety_agent()
        test_persona_matching_agent()
        test_recommendation_orchestrator()
    elif test_key in tests:
        name, test_func = tests[test_key]
        if test_func:
            try:
                test_func()
            except Exception as e:
                print(f"\n❌ 오류 발생: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("이 옵션은 아직 구현되지 않았습니다.")
    else:
        print("잘못된 선택입니다.")


if __name__ == "__main__":
    main()
