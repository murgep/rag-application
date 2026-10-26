import os
import logging

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

logger = logging.getLogger(__name__)


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

        self.client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(
                timeout=90_000,
                retry_options=types.HttpRetryOptions(
                    attempts=2,
                    initial_delay=1.0,
                    max_delay=4.0,
                    exp_base=2.0,
                    jitter=1.0,
                    http_status_codes=[500, 502, 503, 504],
                ),
            ),
        )

        self.model = "gemini-3.5-flash"

    def generate(
        self,
        question: str,
        context: str,
        request_id: str | None = None,
    ) -> str:
        """
        Generate a grounded answer using the provided context.

        Args:
            question: The user's question.
            context: Retrieved document context.
            request_id: Optional ID for tracing requests across logs.

        Returns:
            The generated answer.

        Raises:
            RuntimeError: If generation returns no answer.
            Exception: Re-raises generation service errors.
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

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
            )

            answer = response.text if response else None

            if not answer or not answer.strip():
                logger.error(
                    "Gemini returned an empty response. request_id=%s",
                    request_id,
                )
                raise RuntimeError(
                    "The generation service returned an empty response."
                )

            return answer.strip()

        except Exception:
            logger.exception("Gemini answer generation failed.")
            if request_id:
                logger.error(
                    "Generation failure request_id=%s",
                    request_id,
                )
            raise
