import unittest
from unittest.mock import Mock
from unittest.mock import patch

import torch
from fastapi import HTTPException

from backend import main
from backend import text_completion


class TextCompletionTests(unittest.TestCase):
    def setUp(self) -> None:
        model_patch = patch.object(
            text_completion, "MODEL_ID", "marlosb/ArthurFriedenreich"
        )
        context_patch = patch.object(
            text_completion, "CONTEXT_LENGTH_ATTRIBUTE", "sequence_len"
        )
        model_patch.start()
        context_patch.start()
        self.addCleanup(model_patch.stop)
        self.addCleanup(context_patch.stop)
        self.tokenizer = Mock(pad_token_id=65527, eos_token_id=None)
        self.tokenizer.return_value = {
            "input_ids": torch.tensor([[65527, 1]]),
            "attention_mask": torch.tensor([[1, 1]]),
        }
        self.tokenizer.decode.return_value = " brasileiro"
        self.model = Mock()
        self.model.config.sequence_len = 4
        self.model.generate.return_value = torch.tensor([[65527, 1, 2, 3]])
        self.runtime_patch = patch.object(
            text_completion,
            "get_text_completion_runtime",
            return_value=(self.tokenizer, self.model, "cpu"),
        )
        self.runtime_patch.start()
        self.addCleanup(self.runtime_patch.stop)

    def test_completes_at_context_limit_without_eos_or_kv_cache(self) -> None:
        payload = text_completion.CompletionRequest(
            text="O futebol",
            max_new_tokens=2,
        )

        result = text_completion.text_complete(payload)

        self.assertEqual(result.prompt, "O futebol")
        self.assertEqual(result.completion, " brasileiro")
        self.assertEqual(result.full_text, "O futebol brasileiro")
        decoded_ids = self.tokenizer.decode.call_args.args[0]
        self.assertEqual(decoded_ids.tolist(), [2, 3])
        generation_args = self.model.generate.call_args.kwargs
        self.assertEqual(generation_args["pad_token_id"], 65527)
        self.assertFalse(generation_args["use_cache"])
        self.assertEqual(generation_args["max_new_tokens"], 2)
        self.assertTrue(
            torch.equal(
                generation_args["attention_mask"],
                self.tokenizer.return_value["attention_mask"],
            )
        )

    def test_rejects_context_overflow_before_generating(self) -> None:
        payload = text_completion.CompletionRequest(
            text="O futebol",
            max_new_tokens=3,
        )

        with self.assertRaisesRegex(text_completion.ContextLengthError, "4 tokens"):
            text_completion.text_complete(payload)

        self.model.generate.assert_not_called()

    def test_api_reports_context_overflow_as_422(self) -> None:
        payload = text_completion.CompletionRequest(
            text="O futebol",
            max_new_tokens=3,
        )

        with self.assertRaises(HTTPException) as raised:
            main.text_complete(payload)

        self.assertEqual(raised.exception.status_code, 422)
        self.assertIn("requested completion: 3", raised.exception.detail)

    def test_gpt2_uses_its_context_limit_and_kv_cache(self) -> None:
        payload = text_completion.CompletionRequest(
            text="O futebol", max_new_tokens=2
        )
        self.model.config.n_positions = 3
        with (
            patch.object(text_completion, "MODEL_ID", "openai-community/gpt2"),
            patch.object(
                text_completion, "CONTEXT_LENGTH_ATTRIBUTE", "n_positions"
            ),
        ):
            with self.assertRaisesRegex(
                text_completion.ContextLengthError, "3 tokens"
            ):
                text_completion.text_complete(payload)
            self.model.generate.assert_not_called()

            self.model.config.n_positions = 4
            text_completion.text_complete(payload)

        self.assertTrue(self.model.generate.call_args.kwargs["use_cache"])


class RuntimeLoadingTests(unittest.TestCase):
    def test_loads_fp16_on_cuda_and_fp32_on_cpu(self) -> None:
        self.addCleanup(text_completion.get_text_completion_runtime.cache_clear)
        cases = (
            ("marlosb/ArthurFriedenreich", "cuda", torch.float16, True),
            ("marlosb/ArthurFriedenreich", "cpu", torch.float32, True),
            ("openai-community/gpt2", "cuda", torch.float16, False),
            ("openai-community/gpt2", "cpu", torch.float32, False),
        )
        for model_id, device, dtype, trust_remote_code in cases:
            with self.subTest(model_id=model_id, device=device):
                text_completion.get_text_completion_runtime.cache_clear()
                tokenizer = Mock(pad_token_id=65527, eos_token_id=None)
                model = Mock()

                with (
                    patch.object(text_completion, "MODEL_DIR") as model_dir,
                    patch.object(text_completion, "MODEL_ID", model_id),
                    patch(
                        "transformers.AutoTokenizer.from_pretrained",
                        return_value=tokenizer,
                    ),
                    patch(
                        "transformers.AutoModelForCausalLM.from_pretrained",
                        return_value=model,
                    ) as load_model,
                    patch("torch.cuda.is_available", return_value=device == "cuda"),
                ):
                    model_dir.exists.return_value = True
                    runtime = text_completion.get_text_completion_runtime()

                    load_model.assert_called_once_with(
                        str(model_dir),
                        local_files_only=True,
                        trust_remote_code=trust_remote_code,
                        dtype=dtype,
                    )

                self.assertEqual(runtime, (tokenizer, model, device))
                model.to.assert_called_once_with(device)
                model.eval.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
