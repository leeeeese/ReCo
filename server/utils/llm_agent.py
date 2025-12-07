"""
LLM 기반 자율 의사결정 에이전트 유틸리티
각 서브에이전트가 LLM을 활용하여 자율적으로 판단할 수 있도록 지원
"""

import os
from typing import Dict, Any, Optional, List
import time
from openai import OpenAI
from server.utils import config

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


class LLMAgent:
    """LLM 기반 의사결정 에이전트"""

    def __init__(self, system_prompt: str = None):
        self.client = OpenAI(
            api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
        self.model = OPENAI_MODEL
        self.system_prompt = system_prompt
        self.max_retries = config.LLM_MAX_RETRIES
        self.request_timeout = config.LLM_TIMEOUT_SECONDS

    def decide(self,
               context: Dict[str, Any],
               decision_task: str,
               options: Optional[List[Any]] = None,
               format: str = "json") -> Dict[str, Any]:
        """
        LLM을 통한 자율 의사결정

        Args:
            context: 판단에 필요한 컨텍스트 정보
            decision_task: 수행할 결정 작업 설명
            options: 선택 가능한 옵션들
            format: 출력 형식 ("json", "text")
        """
        if not self.client:
            return {"error": "OpenAI API key not found", "fallback": True}

        messages = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})

        user_prompt = self._build_prompt(context, decision_task, options)
        messages.append({"role": "user", "content": user_prompt})

        last_error: Optional[Exception] = None

        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    response_format={
                        "type": "json_object"} if format == "json" else None,
                    temperature=0.7,  # 창의적 판단을 위한 적절한 온도
                    timeout=self.request_timeout,
                )

                result = response.choices[0].message.content
                if format == "json":
                    import json
                    return json.loads(result)
                return {"result": result}

            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    sleep_for = 2 ** attempt
                    time.sleep(sleep_for)
                    continue

        return {"error": str(last_error) if last_error else "LLM 호출 실패", "fallback": True}

    def _build_prompt(self, context: Dict[str, Any], task: str, options: Optional[List[Any]]) -> str:
        """프롬프트 구성"""
        prompt = f"다음 정보를 바탕으로 {task}를 수행해주세요.\n\n"
        prompt += "## 컨텍스트 정보:\n"
        for key, value in context.items():
            prompt += f"- {key}: {value}\n"

        if options:
            prompt += "\n## 선택 가능한 옵션:\n"
            for i, option in enumerate(options, 1):
                prompt += f"{i}. {option}\n"

        prompt += "\n## 요청사항:\n"
        prompt += "상황을 분석하여 가장 적절한 판단을 내려주세요. "
        prompt += "판단 근거와 함께 결과를 JSON 형식으로 반환해주세요."

        return prompt

    def analyze_and_combine(self,
                            sub_agent_results: List[Dict[str, Any]],
                            combination_task: str) -> Dict[str, Any]:
        """
        여러 서브에이전트의 결과를 종합 분석

        Args:
            sub_agent_results: 각 서브에이전트의 판단 결과
            combination_task: 종합 분석 작업 설명
        """
        if not self.client:
            return {"error": "OpenAI API key not found"}

        context = {
            "sub_agent_results": sub_agent_results,
            "combination_task": combination_task
        }

        return self.decide(context, f"다음 서브에이전트들의 결과를 종합하여 {combination_task}")


def create_agent(agent_type: str, system_prompt: str = None) -> LLMAgent:
    """에이전트 타입별로 생성"""
    default_prompts = {
        "persona_classifier": """당신은 중고거래 사용자의 특성을 분석하여 페르소나를 분류하는 전문가입니다.
사용자의 선호도와 행동 패턴을 종합적으로 분석하여 가장 적합한 페르소나를 결정하세요.""",

        "product_agent": """당신은 중고거래에서 판매자가 판매하는 상품의 특성을 종합 분석하는 전문가입니다.
상품 품질 패턴, 시세 대비 가격 전략, 판매자 성향을 분석하여 
사용자와 가장 잘 맞는 판매자를 추천하세요.""",

        "reliability_agent": """당신은 중고거래에서 판매자의 신뢰도를 종합 분석하는 전문가입니다.
거래 행동 패턴, 리뷰 기반 성향, 신뢰도, 활동성을 분석하여 
사용자와 가장 잘 어울리는 신뢰할 수 있는 판매자를 추천하세요.""",

        "persona_matching_agent": """당신은 사용자와 판매자의 페르소나를 매칭하는 전문가입니다.
사용자의 선호도와 판매자의 특성을 비교하여 
가장 잘 어울리는 판매자를 추천하세요.""",

        "final_matcher": """당신은 여러 서브에이전트의 판단을 종합하여 최종 추천을 결정하는 전문가입니다.
가격, 안전거래, 페르소나 매칭의 결과를 종합 분석하여 
사용자에게 가장 적합한 판매자를 최종 추천하세요."""
    }

    prompt = system_prompt or default_prompts.get(agent_type, "")
    return LLMAgent(system_prompt=prompt)
