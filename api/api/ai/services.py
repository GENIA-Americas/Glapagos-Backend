import openai

from pydantic import BaseModel
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from .exceptions import UnrelatedTopicException


class QueryResponse(BaseModel):
    explanation: str
    query: str


class ChatAssistant:
    @staticmethod
    def chat(msg: str, context: str):

        # prompt = """
        #     You are a BigQuery sql expert that specializes in making queries
        #     you will receive a petition and you must respond with the appropriate
        #     query base on the information that you have been provided, you must
        #     try to answer with a query.
        #
        #
        #     Anything that is not related to making a queries you must refuse
        #     the request"
        # """
        prompt = """
            You are a BigQuery SQL expert specializing in creating queries. 
            You will receive a request and must respond with the appropriate 
            query based on the information provided.
            
            Make sure to:
            1. Use backticks (`) around all field and table names to ensure compatibility with 
            special characters or accents.
            2. Enclose string values in single quotes ('') or double quotes ("").
            3. You must try to answer with a query.

            Anything that is not related to making a queries you must refuse 
            the request"
        """

        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompt},
                {
                    "role": "system",
                    "content": f"this is the context information that you have: {context}",
                },
                {
                    "role": "user",
                    "content": msg,
                },
            ],
            response_format=QueryResponse,
        )

        res = completion.choices[0].message.parsed

        if res.__dict__.get("query", "") != "":
            return res

        raise UnrelatedTopicException(error=_("Error processing the request"))
