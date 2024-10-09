
import openai
from pydantic import BaseModel
from django.conf import settings

class QueryResponse(BaseModel):
    explanation: str
    query: str

class ChatAssistant:
    @staticmethod
    def chat(msg: str, context: str):

        prompt = """
            You are a biquery sql expert that especializes in making queries
            you will recieve a petition and you must respond with the appropiate
            query base on the information that you have been provided.

            Anything that is not related to making a queries you must refuse 
            the request" 
        """

        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system", 
                    "content": prompt
                },
                {
                    "role": "system", 
                    "content": f"this is the context information that you have: {context}"
                },
                {
                    "role": "user",
                    "content": msg,
                },
            ],
            response_format=QueryResponse,
        )

        res = completion.choices[0].message.parsed
        return res

