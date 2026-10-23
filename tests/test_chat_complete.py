import tempfile
import unittest
from pathlib import Path
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


if __name__ == "__main__":
    unittest.main()
