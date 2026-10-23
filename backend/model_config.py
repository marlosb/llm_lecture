import os
from pathlib import Path


SUPPORTED_MODELS: dict[str, tuple[str, str | None, str]] = {
    "marlosb/ArthurFriedenreich": (
        "ArthurFriedenreich",
        "fe31fcfc2f907e085461af443da858e9895db726",
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
