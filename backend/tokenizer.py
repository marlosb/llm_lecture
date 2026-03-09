import pickle
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import BaseModel


TOKENIZER_FILE: Path = Path(__file__).resolve().parent / "tokenizer" / "tokenizer.pkl"


class TokenizeRequest(BaseModel):
    text: str


class TokenView(BaseModel):
    id: int
    text: str


class TokenizeResponse(BaseModel):
    token_ids: list[int]
    tokens: list[TokenView]


@lru_cache(maxsize=1)
def get_tokenizer_encoding() -> Any:
    if not TOKENIZER_FILE.exists():
        raise FileNotFoundError(f"Tokenizer file not found: {TOKENIZER_FILE}")
    with TOKENIZER_FILE.open("rb") as file_handle:
        return pickle.load(file_handle)


def tokenize_text(payload: TokenizeRequest) -> TokenizeResponse:
    tokenizer: Any = get_tokenizer_encoding()
    token_ids: list[int] = tokenizer.encode_ordinary(payload.text)
    tokens: list[TokenView] = []
    for token_id in token_ids:
        token_bytes: bytes = tokenizer.decode_single_token_bytes(token_id)
        token_text: str = token_bytes.decode("utf-8", errors="replace")
        tokens.append(TokenView(id=token_id, text=token_text))

    return TokenizeResponse(token_ids=token_ids, tokens=tokens)

