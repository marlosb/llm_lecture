import unittest
from unittest.mock import Mock
from unittest.mock import call
from unittest.mock import patch

from backend import tokenizer


class TokenizerTests(unittest.TestCase):
    def test_tokenizes_without_special_tokens_and_preserves_spacing(self) -> None:
        encoding = Mock()
        encoding.encode.return_value = [42, 81]
        encoding.decode.side_effect = ["O", " Brasil"]
        with patch.object(tokenizer, "get_tokenizer_encoding", return_value=encoding):
            result = tokenizer.tokenize_text(
                tokenizer.TokenizeRequest(text="O Brasil")
            )

        encoding.encode.assert_called_once_with("O Brasil", add_special_tokens=False)
        self.assertEqual(
            encoding.decode.call_args_list,
            [
                call([42], clean_up_tokenization_spaces=False),
                call([81], clean_up_tokenization_spaces=False),
            ],
        )
        self.assertEqual(result.token_ids, [42, 81])
        self.assertEqual([token.text for token in result.tokens], ["O", " Brasil"])
        self.assertEqual([token.id for token in result.tokens], [42, 81])

    def test_loads_and_caches_tokenizer_from_completion_model(self) -> None:
        tokenizer.get_tokenizer_encoding.cache_clear()
        self.addCleanup(tokenizer.get_tokenizer_encoding.cache_clear)
        with (
            patch.object(tokenizer, "MODEL_DIR") as model_dir,
            patch("transformers.AutoTokenizer.from_pretrained") as load_tokenizer,
        ):
            model_dir.exists.return_value = True
            first = tokenizer.get_tokenizer_encoding()
            second = tokenizer.get_tokenizer_encoding()

            load_tokenizer.assert_called_once_with(
                str(model_dir), local_files_only=True
            )
            self.assertIs(first, load_tokenizer.return_value)
            self.assertIs(second, first)

    def test_missing_model_reports_installation_required(self) -> None:
        tokenizer.get_tokenizer_encoding.cache_clear()
        self.addCleanup(tokenizer.get_tokenizer_encoding.cache_clear)
        with patch.object(tokenizer, "MODEL_DIR") as model_dir:
            model_dir.exists.return_value = False
            with self.assertRaisesRegex(
                FileNotFoundError, r"Run install\.sh or install\.ps1"
            ):
                tokenizer.get_tokenizer_encoding()


if __name__ == "__main__":
    unittest.main()
