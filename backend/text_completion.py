from functools import lru_cache
from typing import Any

from pydantic import BaseModel
from pydantic import Field

from backend.model_config import CONTEXT_LENGTH_ATTRIBUTE
from backend.model_config import MODEL_DIR
from backend.model_config import MODEL_ID


class ContextLengthError(ValueError):
    pass


class CompletionRequest(BaseModel):
    text: str
    max_new_tokens: int = Field(default=60, ge=1, le=200)


class CompletionResponse(BaseModel):
    prompt: str
    completion: str
    full_text: str


@lru_cache(maxsize=1)
def get_text_completion_runtime() -> tuple[Any, Any, str]:
    if not MODEL_DIR.exists():
        raise FileNotFoundError(
            f"Model directory not found: {MODEL_DIR}. "
            "Run install.sh or install.ps1 first."
        )

    try:
        import torch
        from transformers import AutoModelForCausalLM
        from transformers import AutoTokenizer
    except ImportError as exc:
        raise ImportError(
            "Missing dependencies. Rebuild the image with "
            "install.sh or install.ps1."
        ) from exc

    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.float16 if device == "cuda" else torch.float32
    tokenizer = AutoTokenizer.from_pretrained(str(MODEL_DIR), local_files_only=True)
    model = AutoModelForCausalLM.from_pretrained(
        str(MODEL_DIR),
        local_files_only=True,
        trust_remote_code=MODEL_ID == "marlosb/ArthurFriedenreich",
        dtype=dtype,
    )
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token_id = tokenizer.eos_token_id

    model.to(device)
    model.eval()
    return tokenizer, model, device


def text_complete(payload: CompletionRequest) -> CompletionResponse:
    tokenizer, model, device = get_text_completion_runtime()
    import torch

    encoded = tokenizer(payload.text, return_tensors="pt")
    prompt_len: int = encoded["input_ids"].shape[-1]
    context_length: int = getattr(model.config, CONTEXT_LENGTH_ATTRIBUTE)
    if prompt_len + payload.max_new_tokens > context_length:
        raise ContextLengthError(
            f"Prompt and completion must fit within {context_length} tokens "
            f"(prompt: {prompt_len}, requested completion: {payload.max_new_tokens})."
        )
    encoded = {key: value.to(device) for key, value in encoded.items()}

    with torch.inference_mode():
        generated = model.generate(
            **encoded,
            max_new_tokens=payload.max_new_tokens,
            do_sample=True,
            top_p=0.95,
            temperature=0.9,
            pad_token_id=tokenizer.pad_token_id,
            use_cache=MODEL_ID == "openai-community/gpt2",
        )

    completion_ids = generated[0][prompt_len:]
    completion: str = tokenizer.decode(completion_ids, skip_special_tokens=True)
    full_text: str = payload.text + completion
    return CompletionResponse(
        prompt=payload.text,
        completion=completion,
        full_text=full_text,
    )
