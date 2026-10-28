import os

from dotenv import load_dotenv
from google import genai
from google.genai import types


load_dotenv()


class Embedder:
    """
    Generate embeddings using Google's Gemini Embedding model.
    """

    def __init__(
        self,
        model_name: str = "gemini-embedding-2",
        output_dimensionality: int = 1536,
    ):
        self.model_name = model_name
        self.output_dimensionality = output_dimensionality

        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY is not configured."
            )

        self.client = genai.Client(
    api_key=api_key,
    http_options=types.HttpOptions(
        timeout=30_000,
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

    def embed_text(self, text: str) -> list[float]:
        """
        Generate an embedding for a single text.
        """

        if not text.strip():
            raise ValueError(
                "Cannot generate an embedding for empty text."
            )

        result = self.client.models.embed_content(
            model=self.model_name,
            contents=text,
            config=types.EmbedContentConfig(
                output_dimensionality=self.output_dimensionality,
            ),
        )

        return result.embeddings[0].values

    def embed_texts(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        """
        Generate separate embeddings for multiple texts.
        """

        if not texts:
            return []

        cleaned_texts = [
            text
            for text in texts
            if text.strip()
        ]

        if not cleaned_texts:
            return []

        # Gemini Embedding 2 aggregates multiple plain
        # inputs into one embedding. To obtain one
        # embedding per text, create a separate Content
        # object for each input.
        contents = [
            types.Content(
                parts=[
                    types.Part.from_text(text=text)
                ]
            )
            for text in cleaned_texts
        ]

        result = self.client.models.embed_content(
            model=self.model_name,
            contents=contents,
            config=types.EmbedContentConfig(
                output_dimensionality=self.output_dimensionality,
            ),
        )

        return [
            embedding.values
            for embedding in result.embeddings
        ]