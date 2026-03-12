from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import BaseModel


MODEL_DIR: Path = Path(__file__).resolve().parent / "models" / "openai-community-gpt2"


class TokenizeRequest(BaseModel):
    text: str


class TokenView(BaseModel):
    id: int
    text: str


class TokenizeResponse(BaseModel):
    token_ids: list[int]
    tokens: list[TokenView]


@lru_cache(maxsize=1)
def get_tokenizer() -> Any:
    if not MODEL_DIR.exists():
        raise FileNotFoundError(f"Model directory not found: {MODEL_DIR}. Run install.py first.")
    from transformers import GPT2TokenizerFast

    return GPT2TokenizerFast.from_pretrained(str(MODEL_DIR), local_files_only=True)


def tokenize_text(payload: TokenizeRequest) -> TokenizeResponse:
    tokenizer: Any = get_tokenizer()
    token_ids: list[int] = tokenizer.encode(payload.text, add_special_tokens=False)
    tokens: list[TokenView] = []
    for token_id in token_ids:
        token_text: str = tokenizer.decode(
            [token_id], clean_up_tokenization_spaces=False
        )
        tokens.append(TokenView(id=token_id, text=token_text))

    return TokenizeResponse(token_ids=token_ids, tokens=tokens)

