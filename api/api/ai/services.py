import logging
import time
from typing import Optional

import openai
from openai import RateLimitError, APIConnectionError, APITimeoutError

from pydantic import BaseModel
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from .exceptions import UnrelatedTopicException

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds


class QueryResponse(BaseModel):
    explanation: str
    query: str


class ChatAssistant:
    SYSTEM_PROMPT = """
        You are a BigQuery SQL expert specializing in creating queries.
        You will receive a request and must respond with the appropriate
        query based on the information provided.

        Make sure to:
        1. Use backticks (`) around all field and table names to ensure compatibility with
           special characters or accents.
        2. Enclose string values in single quotes ('') or double quotes ("").
        3. You must try to answer with a query.
        4. Never include DROP, DELETE, TRUNCATE, INSERT, UPDATE, or ALTER statements.

        Anything that is not related to making queries you must refuse the request.
    """

    @staticmethod
    def _build_messages(msg: str, context: str, history: Optional[list] = None) -> list:
        messages = [
            {"role": "system", "content": ChatAssistant.SYSTEM_PROMPT},
            {"role": "system", "content": f"Context information: {context}"},
        ]
        if history:
            for entry in history:
                messages.append({"role": entry["role"], "content": entry["content"]})
        messages.append({"role": "user", "content": msg})
        return messages

    @staticmethod
    def chat(msg: str, context: str, history: Optional[list] = None) -> QueryResponse:
        """
        Sends a message to the AI assistant with optional conversation history.

        Args:
            msg: The user's message.
            context: BigQuery table context (path and schema).
            history: Optional list of previous {"role", "content"} dicts.

        Returns:
            QueryResponse with explanation and SQL query.

        Raises:
            UnrelatedTopicException: If the request is not SQL-related.
        """
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        messages = ChatAssistant._build_messages(msg, context, history)

        last_error = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                completion = client.beta.chat.completions.parse(
                    model="gpt-4o-mini",
                    max_tokens=1024,
                    messages=messages,
                    response_format=QueryResponse,
                )
                res = completion.choices[0].message.parsed

                if res and res.query:
                    return res

                raise UnrelatedTopicException(error=_("Error processing the request"))

            except (RateLimitError, APIConnectionError, APITimeoutError) as exc:
                last_error = exc
                logger.warning(
                    "OpenAI transient error (attempt %d/%d): %s", attempt, MAX_RETRIES, exc
                )
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY * attempt)
            except UnrelatedTopicException:
                raise
            except Exception as exc:
                logger.error("Unexpected OpenAI error: %s", exc, exc_info=True)
                raise UnrelatedTopicException(error=_("Error processing the request")) from exc

        logger.error("OpenAI failed after %d attempts: %s", MAX_RETRIES, last_error)
        raise UnrelatedTopicException(error=_("Service temporarily unavailable. Please try again."))
