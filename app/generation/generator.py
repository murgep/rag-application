import os

from dotenv import load_dotenv
from google import genai


load_dotenv()


class Generator:
    """
    Generates grounded answers using retrieved document context.
    """

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY is not set in the environment."
            )

        self.client = genai.Client(api_key=api_key)

        self.model = "gemini-3.5-flash"

    def generate(self, question: str, context: str) -> str:
        """
        Generate an answer using only the provided context.
        """

        prompt = f"""
You are a document-based question answering assistant.

Answer the user's question ONLY using the information
provided in the context below.

Rules:
1. Do not use outside knowledge.
2. Do not invent facts.
3. Do not make assumptions that are not supported by the context.
4. If the context does not contain enough information to answer
   the question, say:

I don't have enough information in the provided documents to answer this question.

5. Keep the answer clear and concise.

CONTEXT:
----------------
{context}
----------------

QUESTION:
{question}

ANSWER:
"""

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt
        )

        return response.text