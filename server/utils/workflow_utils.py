"""
워크플로우 유틸리티 함수들
persona_classifier, query_generator 등의 간단한 작업을 수행
"""

from typing import Dict, Any
from server.workflow.state import RecommendationState, PersonaType, PersonaVector, PERSONA_PROTOTYPES
from server.utils.tools import (
    normalize_slider_inputs,
    extract_keywords,
    enhance_query_for_persona,
    create_filters
)
from server.utils.llm_agent import create_agent
from server.retrieval.vector_store import VectorStore
from server.retrieval.retriever import PlaybookRetriever
from pathlib import Path
import json


def classify_persona(user_input: Dict[str, Any]) -> Dict[str, Any]:
    """페르소나 분류"""
    # LLM 기반 페르소나 분류
    llm_agent = create_agent("persona_classifier")

    user_prefs = {
        "trust_safety": user_input.get("trust_safety", 50.0),
        "quality_condition": user_input.get("quality_condition", 50.0),
        "remote_transaction": user_input.get("remote_transaction", 50.0),
        "activity_responsiveness": user_input.get("activity_responsiveness", 50.0),
        "price_flexibility": user_input.get("price_flexibility", 50.0),
        "search_query": user_input.get("search_query", ""),
        "category": user_input.get("category", ""),
        "location": user_input.get("location", "")
    }

    user_vector = normalize_slider_inputs(user_prefs)

    # 페르소나 플레이북 로드
    persona_descriptions = {}
    persona_dir = Path("./server/retrieval/playbook/personas")
    if persona_dir.exists():
        for persona_file in persona_dir.glob("*.md"):
            persona_type = persona_file.stem
            try:
                with open(persona_file, 'r', encoding='utf-8') as f:
                    persona_descriptions[persona_type] = f.read()
            except Exception:
                pass

    context = {
        "user_preferences": user_prefs,
        "user_vector": user_vector,
        "persona_descriptions": persona_descriptions,
        "available_personas": [p.value for p in PersonaType]
    }

    decision = llm_agent.decide(
        context=context,
        decision_task="사용자의 선호도와 행동 패턴을 분석하여 가장 적합한 페르소나를 선택해주세요. "
        "플레이북에 정의된 10가지 페르소나 중 하나를 선택하고, 선택 근거를 설명해주세요.",
        options=[p.value for p in PersonaType],
        format="json"
    )

    # LLM 결과 파싱
    if decision.get("fallback"):
        # Fallback: 기본 페르소나
        persona_type = PersonaType.HYBRID_TRADE
        confidence = 0.5
        reason = "기본 페르소나"
    else:
        selected_persona = decision.get(
            "selected_persona") or decision.get("persona")
        try:
            persona_type = PersonaType(selected_persona)
            confidence = decision.get("confidence", 0.7)
            reason = decision.get("reasoning", "LLM 기반 판단")
        except (ValueError, AttributeError):
            persona_type = PersonaType.HYBRID_TRADE
            confidence = 0.5
            reason = "페르소나 파싱 실패"

    matched_prototype = PERSONA_PROTOTYPES[persona_type]["vector"]

    return {
        "persona_type": persona_type,
        "confidence": confidence,
        "vector": user_vector,
        "matched_prototype": matched_prototype,
        "reason": reason,
        "llm_reasoning": decision.get("reasoning", "")
    }


def generate_search_query(user_input: Dict[str, Any], persona_classification: Dict[str, Any]) -> Dict[str, Any]:
    """검색 쿼리 생성"""
    original_query = user_input.get("search_query", "")
    persona_type = persona_classification.get("persona_type")

    keywords = extract_keywords(original_query)
    enhanced_query = enhance_query_for_persona(original_query, persona_type)
    filters = create_filters(user_input)

    return {
        "original_query": original_query,
        "enhanced_query": enhanced_query,
        "keywords": keywords,
        "filters": filters
    }
