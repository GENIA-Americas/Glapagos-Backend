import json
import re
from pydantic import BaseModel
from django.utils.translation import gettext_lazy as _
from .exceptions import UnrelatedTopicException
from .providers import get_provider


class QueryResponse(BaseModel):
    explanation: str
    query: str


class ChatAssistant:
    @staticmethod
    def chat(msg: str, context: str):
        system_prompt = (
            "You are a BigQuery SQL expert specializing in creating queries."
            ' Respond ONLY with valid JSON: {"explanation": "...", "query": "..."}'
            " Refuse anything unrelated to queries."
        )
        provider = get_provider()
        raw = provider.complete(msg, system=system_prompt + "\n\nContext: " + context)

        try:
            cleaned = raw.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[-1]
            if cleaned.endswith("```"):
                cleaned = cleaned.rsplit("```", 1)[0]

            try:
                data = json.loads(cleaned.strip())
            except json.JSONDecodeError:
                # Model wrapped the JSON in extra text/reasoning — extract the
                # first {...} block instead of failing outright.
                match = re.search(r"\{.*\}", cleaned, re.DOTALL)
                if not match:
                    raise
                data = json.loads(match.group(0))

            res = QueryResponse(**data)
        except Exception:
            raise UnrelatedTopicException(error=_("Error processing the request"))

        return res
