from django.conf import settings
import openai


class ChatAssistant:
    @staticmethod
    def chat(msg: str, context: str):

        prompt = """
            You are a biquery sql expert that especializes in making queries
            you will recieve a petition and you must respond with the appropiate
            query base on the information that you have been provided
            you can show the user the context information.

            Anything that is not related to making a queries you must respond
            with "I'm sorry but i cannot help you with that" 
        """

        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        completion = client.chat.completions.create(
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
        )

        return completion.choices[0].message.content

