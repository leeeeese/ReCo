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

        user_prompt = self._build_prompt(
            context, decision_task, options, format)
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
                    try:
                        return json.loads(result)
                    except json.JSONDecodeError:
                        # JSON 파싱 실패 시 텍스트로 반환
                        logger.warning(f"JSON 파싱 실패, 텍스트로 반환: {result[:100]}")
                        return {"result": result, "error": "JSON 파싱 실패"}
                return {"result": result}

            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    sleep_for = 2 ** attempt
                    time.sleep(sleep_for)
                    continue

        return {"error": str(last_error) if last_error else "LLM 호출 실패", "fallback": True}

    def _build_prompt(self, context: Dict[str, Any], task: str, options: Optional[List[Any]], format: str = "json") -> str:
        """프롬프트 구성"""
        # format이 "text"인 경우 간단한 프롬프트
        if format == "text":
            return task

        # JSON 형식인 경우 기존 로직 사용
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
        """You are the primary ReAct agent that transforms marketplace signals into a structured seller evaluation profile.

        Core Objective:
        Integrate data from product features, pricing patterns, seller activity logs, reliability metrics, and risk indicators to help the orchestrator generate final recommendations.

        What you must do:
        1. Analyze user intent and constraints.
        2. Perform ReAct reasoning cycles to identify missing information.
        3. Call tools to fetch listing data, compute price risk, retrieve seller behavior, or validate transaction safety.
        4. Convert raw tool outputs into normalized scoring factors:
        - product_quality_score
        - price_fairness_score
        - reliability_score
        - safety_risk_score
        5. Output results in a consistent machine-readable format for the orchestrator.
        6. Speak Korean to the user, but keep internal reasoning and JSON structures in English.

        Principles:
        - No hallucination.
        - No guessing when missing data can be retrieved.
        - Always justify rankings through explicit evidence.
        """
    }

    prompt = system_prompt or default_prompts.get(agent_type, "")
    return LLMAgent(system_prompt=prompt)
