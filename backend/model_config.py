import os
from pathlib import Path


SUPPORTED_MODELS: dict[str, tuple[str, str | None, str]] = {
    "marlosb/ArthurFriedenreich": (
        "ArthurFriedenreich",
        "af0f0c19f3ad871e3b1b4cbda874eff5a484e505",
        "sequence_len",
    ),
    "openai-community/gpt2": ("openai-community-gpt2", None, "n_positions"),
}
MODEL_ID: str = os.environ.get(
    "LLM_MODEL_ID", "marlosb/ArthurFriedenreich"
).strip()
if MODEL_ID not in SUPPORTED_MODELS:
    raise ValueError(
        f"Unsupported LLM_MODEL_ID: {MODEL_ID!r}. "
        f"Choose one of: {', '.join(SUPPORTED_MODELS)}."
    )

MODEL_NAME, MODEL_REVISION, CONTEXT_LENGTH_ATTRIBUTE = SUPPORTED_MODELS[MODEL_ID]
MODEL_DIR: Path = Path(__file__).resolve().parent / "models" / MODEL_NAME
