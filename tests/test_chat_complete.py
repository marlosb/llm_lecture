import json
import os
import unittest
from unittest.mock import Mock
from unittest.mock import patch

from backend import chat_complete


class EnvironmentSettingsTests(unittest.TestCase):
    def test_uses_environment_without_reading_configuration_files(self) -> None:
        settings = {
            "AZURE_OPENAI_CHAT_ENDPOINT": "https://example.invalid/openai/v1",
            "AZURE_OPENAI_CHAT_API_KEY": "test-only-environment-key",
            "AZURE_OPENAI_CHAT_MODEL": "test-model",
        }
        expected = chat_complete.ChatCompleteResponse(
            prompt="Hello", completion="OK"
        )
        with (
            patch.dict(os.environ, settings, clear=True),
            patch.object(
                chat_complete, "_run_azure_chat_complete", return_value=expected
            ) as run,
            patch("pathlib.Path.read_text", side_effect=AssertionError),
            patch("builtins.open", side_effect=AssertionError),
        ):
            result = chat_complete.chat_complete(
                chat_complete.ChatCompleteRequest(text="Hello")
            )

        self.assertEqual(result, expected)
        self.assertEqual(
            run.call_args.kwargs["api_key"],
            settings["AZURE_OPENAI_CHAT_API_KEY"],
        )
        self.assertEqual(
            run.call_args.kwargs["endpoint"],
            settings["AZURE_OPENAI_CHAT_ENDPOINT"],
        )

    def test_missing_environment_credentials_fail_explicitly(self) -> None:
        with (
            patch.dict(os.environ, {}, clear=True),
            self.assertRaisesRegex(ValueError, "in the environment"),
        ):
            chat_complete.chat_complete(
                chat_complete.ChatCompleteRequest(text="Hello")
            )


class AzureEndpointTests(unittest.TestCase):
    def setUp(self) -> None:
        settings = {
            "AZURE_OPENAI_CHAT_ENDPOINT": "",
            "AZURE_OPENAI_CHAT_API_KEY": "test-only-key",
            "AZURE_OPENAI_CHAT_MODEL": "test-model",
            "AZURE_OPENAI_CHAT_DEPLOYMENT": "test-deployment",
            "AZURE_OPENAI_CHAT_API_VERSION": "2025-01-01-preview",
        }
        environment_patch = patch.dict(os.environ, settings, clear=True)
        self.settings = environment_patch.start()
        self.addCleanup(environment_patch.stop)
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
                self.settings["AZURE_OPENAI_CHAT_ENDPOINT"] = (
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
                self.settings["AZURE_OPENAI_CHAT_ENDPOINT"] = (
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
        self.settings.update(
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
        self.settings["AZURE_OPENAI_CHAT_ENDPOINT"] = (
            "https://example.invalid/openai/v1/responses"
        )
        self.response.read.return_value = b'{"output": []}'

        with self.assertRaisesRegex(RuntimeError, "did not include output text"):
            chat_complete.chat_complete(
                chat_complete.ChatCompleteRequest(text="Hello")
            )

    def test_phi_reasoning_uses_chat_completions_and_model(self) -> None:
        cases = (
            ("/openai/v1", "", "", "Phi-4-reasoning"),
            ("/openai/v1/", "", "", "Phi-4-reasoning"),
            (
                "/openai/v1/chat/completions",
                "Phi-4-reasoning",
                "",
                "Phi-4-reasoning",
            ),
            ("/openai/v1", "", "custom-deployment", "custom-deployment"),
            ("/openai/v1", "custom-model", "other", "custom-model"),
        )
        for path, model, deployment, expected_model in cases:
            with self.subTest(path=path, model=model, deployment=deployment):
                self.settings.update(
                    AZURE_OPENAI_REASONING_ENDPOINT=(
                        f"https://example.invalid{path}"
                    ),
                    AZURE_OPENAI_REASONING_API_KEY="test-only-key",
                    AZURE_OPENAI_REASONING_MODEL=model,
                    AZURE_OPENAI_REASONING_DEPLOYMENT=deployment,
                    AZURE_OPENAI_REASONING_API_VERSION="2024-05-01-preview",
                )

                result = chat_complete.reasoning_chat_complete(
                    chat_complete.ChatCompleteRequest(text="Explain this")
                )
                req = self.urlopen.call_args.args[0]
                body = json.loads(req.data)

                self.assertEqual(
                    req.full_url,
                    "https://example.invalid/openai/v1/chat/completions",
                )
                self.assertEqual(body["model"], expected_model)
                self.assertEqual(
                    body["messages"][1],
                    {"role": "user", "content": "Explain this"},
                )
                self.assertNotIn("input", body)
                self.assertEqual(result.completion, "OK")


if __name__ == "__main__":
    unittest.main()
