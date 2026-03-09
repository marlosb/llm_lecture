from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import BaseModel
from pydantic import Field


MODEL_DIR: Path = Path(__file__).resolve().parent / "models" / "openai-community-gpt2"


class CompletionRequest(BaseModel):
    text: str
    max_new_tokens: int = Field(default=60, ge=1, le=200)


class CompletionResponse(BaseModel):
    prompt: str
    completion: str
    full_text: str


@lru_cache(maxsize=1)
def get_gpt2_runtime() -> tuple[Any, Any, str]:
    if not MODEL_DIR.exists():
        raise FileNotFoundError(
            f"Model directory not found: {MODEL_DIR}. Run install.py first."
        )

    try:
        import torch
        from transformers import AutoModelForCausalLM
        from transformers import AutoTokenizer
    except ImportError as exc:
        raise ImportError(
            "Missing dependencies. Run install.py to install required packages."
        ) from exc

    tokenizer = AutoTokenizer.from_pretrained(str(MODEL_DIR), local_files_only=True)
    model = AutoModelForCausalLM.from_pretrained(str(MODEL_DIR), local_files_only=True)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token_id = tokenizer.eos_token_id

    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)
    model.eval()
    return tokenizer, model, device


def text_complete(payload: CompletionRequest) -> CompletionResponse:
    tokenizer, model, device = get_gpt2_runtime()
    import torch

    encoded = tokenizer(payload.text, return_tensors="pt")
    encoded = {key: value.to(device) for key, value in encoded.items()}

    with torch.no_grad():
        generated = model.generate(
            **encoded,
            max_new_tokens=payload.max_new_tokens,
            do_sample=True,
            top_p=0.95,
            temperature=0.9,
            pad_token_id=tokenizer.eos_token_id,
        )

    prompt_len: int = encoded["input_ids"].shape[-1]
    completion_ids = generated[0][prompt_len:]
    completion: str = tokenizer.decode(completion_ids, skip_special_tokens=True)
    full_text: str = payload.text + completion
    return CompletionResponse(
        prompt=payload.text,
        completion=completion,
        full_text=full_text,
    )

