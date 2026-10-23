import os
import runpy
import unittest
from unittest.mock import patch

from backend import model_config


class ModelSelectionTests(unittest.TestCase):
    def test_unset_model_keeps_arthur_as_default(self) -> None:
        with patch.dict(os.environ):
            os.environ.pop("LLM_MODEL_ID", None)
            config = runpy.run_path(model_config.__file__)

        self.assertEqual(config["MODEL_ID"], "marlosb/ArthurFriedenreich")
        self.assertEqual(config["MODEL_DIR"].name, "ArthurFriedenreich")
        self.assertIsNotNone(config["MODEL_REVISION"])

    def test_environment_selects_model_files_and_context(self) -> None:
        cases = (
            ("marlosb/ArthurFriedenreich", "ArthurFriedenreich", "sequence_len"),
            ("openai-community/gpt2", "openai-community-gpt2", "n_positions"),
        )
        for model_id, directory, context_attribute in cases:
            with (
                self.subTest(model_id=model_id),
                patch.dict(os.environ, {"LLM_MODEL_ID": model_id}),
            ):
                config = runpy.run_path(model_config.__file__)
                self.assertEqual(config["MODEL_ID"], model_id)
                self.assertEqual(config["MODEL_DIR"].name, directory)
                self.assertEqual(
                    config["CONTEXT_LENGTH_ATTRIBUTE"], context_attribute
                )

    def test_unknown_or_empty_model_fails_explicitly(self) -> None:
        for model_id in ("unknown/model", ""):
            with (
                self.subTest(model_id=model_id),
                patch.dict(os.environ, {"LLM_MODEL_ID": model_id}),
                self.assertRaisesRegex(ValueError, "Unsupported LLM_MODEL_ID"),
            ):
                runpy.run_path(model_config.__file__)


if __name__ == "__main__":
    unittest.main()
