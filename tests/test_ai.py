import json
import os
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from PIL import Image

from cursed import ai


class AiMetadataTests(unittest.TestCase):
    def setUp(self):
        self.image = Image.new("RGB", (4, 4), "red")

    def completion(self, payload):
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content=json.dumps(payload))
                )
            ]
        )

    def test_uses_configured_model_and_returns_valid_metadata(self):
        payload = {
            "subject": "banana",
            "name": "Peel-a-lot",
            "class": "ORGANIC",
            "quirky_text": "Peel me daddy~",
            "lore": "It guards the sacred fruit bowl.",
        }
        client = Mock()
        client.chat.completions.create.return_value = self.completion(payload)

        with patch.dict(
            os.environ,
            {
                "GROQ_API_KEY": "test-key",
                "VISION_MODEL_NAME": "vision-test",
                "VISION_API_ENDPOINT": "https://api.groq.com/openai/v1",
            },
            clear=True,
        ), patch.object(ai, "_client", return_value=client):
            result = ai.generate_entity_metadata(self.image)

        self.assertEqual(result, payload)
        request = client.chat.completions.create.call_args.kwargs
        self.assertEqual(request["model"], "vision-test")
        self.assertNotIn("rarity", result)
        self.assertNotIn("stats", result)

    def test_normalizes_groq_endpoint_for_sdk(self):
        with patch.dict(
            os.environ,
            {
                "GROQ_API_KEY": "test-key",
                "VISION_API_ENDPOINT": "https://api.groq.com/openai/v1/",
            },
            clear=True,
        ), patch.object(ai, "Groq") as groq:
            ai._client()

        self.assertEqual(
            groq.call_args.kwargs["base_url"],
            "https://api.groq.com",
        )

    def test_missing_model_uses_documented_vision_default(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(ai._model_name(), "qwen/qwen3.8-27b")

    def test_legacy_model_uses_documented_vision_default(self):
        with patch.dict(
            os.environ,
            {"VISION_MODEL_NAME": "llama-3.2-11b-vision-preview"},
            clear=True,
        ):
            self.assertEqual(ai._model_name(), "qwen/qwen3.8-27b")

    def test_invalid_endpoint_is_ignored(self):
        with patch.dict(
            os.environ,
            {
                "GROQ_API_KEY": "test-key",
                "VISION_API_ENDPOINT": "not-a-url",
            },
            clear=True,
        ), patch.object(ai, "Groq") as groq:
            ai._client()

        self.assertNotIn("base_url", groq.call_args.kwargs)

    def test_rejects_malformed_metadata(self):
        payload = {
            "subject": "banana",
            "name": "Peel-a-lot",
            "class": "NOT_ALLOWED",
            "quirky_text": "A line",
            "lore": "Lore",
        }
        client = Mock()
        client.chat.completions.create.return_value = self.completion(payload)

        with patch.dict(os.environ, {"GROQ_API_KEY": "test-key"}, clear=True), \
                patch.object(ai, "_client", return_value=client):
            result = ai.generate_entity_metadata(self.image)

        self.assertEqual(result, ai.FALLBACK_DATA)

    def test_missing_key_uses_fallback_without_api_call(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(ai, "_client") as make_client:
            result = ai.generate_entity_metadata(self.image)

        self.assertEqual(result, ai.FALLBACK_DATA)
        make_client.assert_not_called()

    def test_provider_failure_uses_fallback(self):
        client = Mock()
        client.chat.completions.create.side_effect = ai.APIConnectionError(request=Mock())

        with patch.dict(os.environ, {"GROQ_API_KEY": "test-key"}, clear=True), \
                patch.object(ai, "_client", return_value=client):
            result = ai.generate_entity_metadata(self.image)

        self.assertEqual(result, ai.FALLBACK_DATA)


if __name__ == "__main__":
    unittest.main()
