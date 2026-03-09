import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.chat_complete import ChatCompleteRequest
from backend.chat_complete import ChatCompleteResponse
from backend.chat_complete import chat_complete as run_chat_complete
from backend.chat_complete import reasoning_chat_complete as run_reasoning_chat_complete
from backend.text_completion import CompletionRequest
from backend.text_completion import CompletionResponse
from backend.text_completion import text_complete as run_text_complete
from backend.tokenizer import TokenizeRequest
from backend.tokenizer import TokenizeResponse
from backend.tokenizer import tokenize_text as run_tokenize_text


BASE_DIR: Path = Path(__file__).resolve().parent.parent
STATIC_DIR: Path = BASE_DIR / "static"
INDEX_FILE: Path = STATIC_DIR / "index.html"
TEXT_DIR: Path = STATIC_DIR / "text"
TOKENIZER_DIR: Path = BASE_DIR / "backend" / "tokenizer"
TOKENIZER_FILE: Path = TOKENIZER_DIR / "tokenizer.pkl"
MODEL_DIR: Path = BASE_DIR / "backend" / "models" / "openai-community-gpt2"
SUPPORTED_LANGUAGE_FILES: dict[str, Path] = {
    "en-us": TEXT_DIR / "en-us.json",
    "pt-br": TEXT_DIR / "pt-br.json",
    "es-mx": TEXT_DIR / "es-mx.json",
}

app: FastAPI = FastAPI(title="LLM Lecture App")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", response_class=FileResponse)
def read_index() -> FileResponse:
    return FileResponse(INDEX_FILE)


@app.get("/api/content/{language_code}")
def read_localized_content(language_code: str) -> dict[str, Any]:
    normalized_code: str = language_code.lower()
    content_file: Path | None = SUPPORTED_LANGUAGE_FILES.get(normalized_code)
    if content_file is None:
        raise HTTPException(status_code=404, detail="Unsupported language code.")
    if not content_file.exists():
        raise HTTPException(status_code=404, detail="Language content file not found.")

    with content_file.open("r", encoding="utf-8") as file_handle:
        content: dict[str, Any] = json.load(file_handle)

    return content


@app.post("/api/tokenize", response_model=TokenizeResponse)
def tokenize_text(payload: TokenizeRequest) -> TokenizeResponse:
    try:
        return run_tokenize_text(payload)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Failed to load tokenizer.",
        ) from exc


@app.post("/api/text-complete", response_model=CompletionResponse)
def text_complete(payload: CompletionRequest) -> CompletionResponse:
    try:
        return run_text_complete(payload)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except ImportError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate text with GPT-2.",
        ) from exc


@app.post("/api/chat-complete", response_model=ChatCompleteResponse)
def chat_complete(payload: ChatCompleteRequest) -> ChatCompleteResponse:
    try:
        return run_chat_complete(payload)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/reasoning-chat-complete", response_model=ChatCompleteResponse)
def reasoning_chat_complete(payload: ChatCompleteRequest) -> ChatCompleteResponse:
    try:
        return run_reasoning_chat_complete(payload)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

