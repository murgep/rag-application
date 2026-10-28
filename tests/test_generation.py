import os
from unittest.mock import Mock, patch
import pytest
from google.genai import types
from app.generation.generator import Generator
@pytest.fixture(autouse=True)
def mock_gemini_api_key(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-api-key")
    
def test_generation():
    mock_response = Mock()
    mock_response.text = (
        "Employees receive 24 days of paid annual leave "
        "every calendar year."
    )

    with patch(
        "app.generation.generator.genai.Client"
    ) as mock_client_class:
        mock_client = mock_client_class.return_value
        mock_client.models.generate_content.return_value = mock_response

        generator = Generator()

        context = """
        Our company provides employees with 24 days of paid annual leave
        every calendar year.
        """

        question = "How many days of annual leave do employees receive?"

        answer = generator.generate(
            question=question,
            context=context,
        )

        assert answer == (
            "Employees receive 24 days of paid annual leave "
            "every calendar year."
        )

        mock_client.models.generate_content.assert_called_once()

        call_kwargs = (
            mock_client.models.generate_content.call_args.kwargs
        )

        assert call_kwargs["model"] == "gemini-3.5-flash"
        assert question in call_kwargs["contents"]
        assert context.strip() in call_kwargs["contents"]



def test_generator_configures_http_timeout():
    with patch(
        "app.generation.generator.genai.Client"
    ) as mock_client_class:
        generator = Generator()

        mock_client_class.assert_called_once()

        client_options = mock_client_class.call_args.kwargs["http_options"]

        assert client_options.timeout == 90_000

def test_generator_configures_retry_options():
    with patch(
        "app.generation.generator.genai.Client"
    ) as mock_client_class:
        Generator()

        http_options = mock_client_class.call_args.kwargs["http_options"]
        retry_options = http_options.retry_options

        assert retry_options.attempts == 2
        assert retry_options.initial_delay == 1.0
        assert retry_options.max_delay == 4.0
        assert retry_options.exp_base == 2.0
        assert retry_options.jitter == 1.0
        assert retry_options.http_status_codes == [500, 502, 503, 504]


def test_generator_retry_policy_excludes_quota_errors():
    with patch(
        "app.generation.generator.genai.Client"
    ) as mock_client_class:
        Generator()

        http_options = mock_client_class.call_args.kwargs["http_options"]
        retry_options = http_options.retry_options

        assert 503 in retry_options.http_status_codes
        assert 429 not in retry_options.http_status_codes


def test_generator_returns_mocked_response_without_live_api_call():
    mock_response = Mock()
    mock_response.text = "Employees receive 24 days of annual leave."

    with patch(
        "app.generation.generator.genai.Client"
    ) as mock_client_class:
        mock_client = mock_client_class.return_value
        mock_client.models.generate_content.return_value = mock_response

        generator = Generator()
        answer = generator.generate(
            question="How many days of annual leave?",
            context="Employees receive 24 days of annual leave.",
        )

        assert answer == "Employees receive 24 days of annual leave."
        mock_client.models.generate_content.assert_called_once()

def test_generator_rejects_empty_response():
    mock_response = Mock()
    mock_response.text = "   "

    with patch(
        "app.generation.generator.genai.Client"
    ) as mock_client_class:
        mock_client = mock_client_class.return_value
        mock_client.models.generate_content.return_value = mock_response

        generator = Generator()

        with pytest.raises(RuntimeError, match="empty response"):
            generator.generate(
                question="What is the leave policy?",
                context="The company provides annual leave.",
            )


def test_generator_logs_and_reraises_generation_failure(caplog):
    import logging

    with patch(
        "app.generation.generator.genai.Client"
    ) as mock_client_class:
        mock_client = mock_client_class.return_value
        mock_client.models.generate_content.side_effect = RuntimeError(
            "Simulated generation failure"
        )

        generator = Generator()

        with caplog.at_level(logging.ERROR, logger="app.generation.generator"):
            with pytest.raises(
                RuntimeError, match="Simulated generation failure"
            ):
                generator.generate(
                    question="What is the leave policy?",
                    context="The company provides annual leave.",
                )

    assert "Gemini answer generation failed." in caplog.text
