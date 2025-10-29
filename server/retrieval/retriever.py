"""
RAG Retriever
"""

from typing import List, Dict, Any
from .vector_store import VectorStore


class PlaybookRetriever:
    """페르소나 플레이북 Retriever"""

    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store

    def get_persona_candidates(self, user_prefs: Dict[str, Any]) -> List[Dict[str, Any]]:
        """페르소나 후보 검색"""
        # TODO: 실제 검색 로직 구현
        return []
