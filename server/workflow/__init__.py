"""
워크플로우 모듈
"""

from .state import RecommendationState

# 순환 import 방지를 위해 lazy import


def _get_recommendation_workflow():
    from .graph import recommendation_workflow
    return recommendation_workflow


__all__ = ["recommendation_workflow", "RecommendationState"]

# lazy import를 위한 속성


def __getattr__(name):
    if name == "recommendation_workflow":
        return _get_recommendation_workflow()
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
