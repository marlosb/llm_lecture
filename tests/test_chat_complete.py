import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock
from unittest.mock import patch

from backend import chat_complete


class SecretsParsingTests(unittest.TestCase):
    def test_accepts_quoted_and_unquoted_configuration_values(self) -> None:
        cases = (
            ("https://example.invalid/", "https://example.invalid/"),
            ('"https://example.invalid/"', "https://example.invalid/"),
            ("'https://example.invalid/'", "https://example.invalid/"),
            ('"value=with=equals"', "value=with=equals"),
            ("", ""),
            ('""', ""),
            ('"unmatched', '"unmatched'),
        )
        with tempfile.TemporaryDirectory() as directory:
            secrets_file = Path(directory) / "secrets.txt"
            for raw_value, expected in cases:
                with (
                    self.subTest(raw_value=raw_value),
                    patch.object(chat_complete, "SECRETS_FILE", secrets_file),
                ):
                    secrets_file.write_text(
                        f"# Comment\n\n SETTING = {raw_value} \n",
                        encoding="utf-8",
                    )
                    self.assertEqual(
                        chat_complete._load_secrets(), {"SETTING": expected}
                    )


class AzureEndpointTests(unittest.TestCase):
    def setUp(self) -> None:
        self.secrets = {
            "AZURE_OPENAI_CHAT_ENDPOINT": "",
            "AZURE_OPENAI_CHAT_API_KEY": "test-only-key",
            "AZURE_OPENAI_CHAT_MODEL": "test-model",
            "AZURE_OPENAI_CHAT_DEPLOYMENT": "test-deployment",
            "AZURE_OPENAI_CHAT_API_VERSION": "2025-01-01-preview",
        }
        secrets_patch = patch.object(
            chat_complete, "_load_secrets", return_value=self.secrets
        )
        secrets_patch.start()
        self.addCleanup(secrets_patch.stop)
        open_patch = patch.object(chat_complete.request, "urlopen")
        self.urlopen = open_patch.start()
        self.addCleanup(open_patch.stop)
        self.response = Mock()
        self.urlopen.return_value.__enter__.return_value = self.response
        self.response.read.return_value = json.dumps(
            {"choices": [{"message": {"content": "OK"}}]}
        ).encode()

    def test_v1_responses_preserves_route_and_reads_output_text(self) -> None:
        self.response.read.return_value = json.dumps(
            {
                "output": [
                    {"type": "reasoning", "summary": []},
                    {
                        "type": "message",
                        "content": [
                            {"type": "output_text", "text": "Hello"},
                            {"type": "output_text", "text": " world"},
                        ],
                    },
                ]
            }
        ).encode()
        for path in (
            "/openai/v1",
            "/openai/v1/",
            "/openai/v1/responses",
            "/openai/v1/responses/",
        ):
            with self.subTest(path=path):
                self.secrets["AZURE_OPENAI_CHAT_ENDPOINT"] = (
                    f"https://example.invalid{path}"
                )
                result = chat_complete.chat_complete(
                    chat_complete.ChatCompleteRequest(text="Hello")
                )
                req = self.urlopen.call_args.args[0]
                body = json.loads(req.data)

                self.assertEqual(
                    req.full_url,
                    "https://example.invalid/openai/v1/responses",
                )
                self.assertEqual(body["model"], "test-model")
                self.assertEqual(body["input"], "Hello")
                self.assertIn("instructions", body)
                self.assertNotIn("messages", body)
                self.assertEqual(result.completion, "Hello world")

    def test_chat_completions_preserves_legacy_and_v1_formats(self) -> None:
        cases = (
            (
                "",
                "/openai/deployments/test-deployment/chat/completions"
                "?api-version=2025-01-01-preview",
                False,
            ),
            (
                "/models/chat/completions?api-version=2024-05-01-preview",
                "/models/chat/completions?api-version=2024-05-01-preview",
                True,
            ),
            (
                "/openai/v1/chat/completions",
                "/openai/v1/chat/completions",
                True,
            ),
        )
        for path, expected_path, needs_model in cases:
            with self.subTest(path=path):
                self.secrets["AZURE_OPENAI_CHAT_ENDPOINT"] = (
                    f"https://example.invalid{path}"
                )
                result = chat_complete.chat_complete(
                    chat_complete.ChatCompleteRequest(text="Hello")
                )
                req = self.urlopen.call_args.args[0]
                body = json.loads(req.data)

                self.assertEqual(
                    req.full_url, f"https://example.invalid{expected_path}"
                )
                self.assertEqual(body["messages"][1]["content"], "Hello")
                self.assertEqual("model" in body, needs_model)
                if needs_model:
                    self.assertEqual(body["model"], "test-model")
                self.assertEqual(result.completion, "OK")

    def test_v1_requires_model_or_deployment_before_sending(self) -> None:
        self.secrets.update(
            AZURE_OPENAI_CHAT_ENDPOINT="https://example.invalid/openai/v1",
            AZURE_OPENAI_CHAT_MODEL="",
            AZURE_OPENAI_CHAT_DEPLOYMENT="",
        )

        with self.assertRaisesRegex(ValueError, "AZURE_OPENAI_CHAT_MODEL"):
            chat_complete.chat_complete(
                chat_complete.ChatCompleteRequest(text="Hello")
            )

        self.urlopen.assert_not_called()

    def test_responses_without_output_text_reports_failure(self) -> None:
        self.secrets["AZURE_OPENAI_CHAT_ENDPOINT"] = (
            "https://example.invalid/openai/v1/responses"
        )
        self.response.read.return_value = b'{"output": []}'

        with self.assertRaisesRegex(RuntimeError, "did not include output text"):
            chat_complete.chat_complete(
                chat_complete.ChatCompleteRequest(text="Hello")
            )


if __name__ == "__main__":
    unittest.main()
