"""Thin litellm wrapper. Works with a LiteLLM proxy (LLM_API_BASE/LLM_API_KEY)
or Azure AI Studio (LLM_MODEL=azure/<deployment> + AZURE_* env vars, which
litellm picks up on its own)."""

import json
import re

import litellm

from .config import Settings


class LLM:
    def __init__(self, settings: Settings):
        self.s = settings

    def complete(self, system: str, user: str, temperature: float = 0.7) -> str:
        kwargs = {}
        if self.s.llm_api_base:
            kwargs["api_base"] = self.s.llm_api_base
        if self.s.llm_api_key:
            kwargs["api_key"] = self.s.llm_api_key
        resp = litellm.completion(
            model=self.s.llm_model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
            **kwargs,
        )
        return resp.choices[0].message.content.strip()

    def complete_json(self, system: str, user: str) -> dict:
        raw = self.complete(system, user, temperature=0.2)
        # tolerate code fences and surrounding prose
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            raise ValueError(f"LLM did not return JSON: {raw[:200]}")
        return json.loads(match.group(0))
