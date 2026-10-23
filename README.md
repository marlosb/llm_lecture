# LLM Lecture

LLM Lecture is a simple educational web app that walks visitors through the main stages of building a Large Language Model (LLM).  
It is designed for large touch-screen displays in innovation hubs and supports multiple languages (Portuguese, English, and Spanish).

## Tech Stack

- **Backend:** Python + FastAPI
- **Server:** Uvicorn
- **Environment manager:** UV
- **Frontend:** HTML, CSS, JavaScript (no framework)
- **Content:** JSON files in `static/text/`

## Main Features

- Language selection screen (EN / PT / ES)
- 15-step guided experience with progress bar
- Step-specific content (text, images, interactivity)
- Tokenizer demo using the selected local model's tokenizer
- Local text completion demo (ArthurFriedenreich or GPT-2)
- Chat completion demo (Azure OpenAI GPT-5-nano)
- Reasoning chat completion demo (Azure AI DeepSeek-R1-0528)
- Idle detection (5 minutes) with auto-refresh warning and cancel option

## Project Structure

```text
backend/
  __init__.py
  main.py
  tokenizer.py
  text_completion.py
  chat_complete.py
  models/                         # local model artifacts (gitignored)
static/
  index.html
  css/
    styles.css
  js/
    app.js
  text/
    pt-br.json
    en-us.json
    es-mx.json
  images/
install.py                        # Python installer/downloader logic
install.sh                        # Linux install helper
install.ps1                       # Windows install helper
run.sh                            # Linux run helper
run.ps1                           # Windows run helper
secrets.txt                       # local secrets (gitignored)
```

## Prerequisites

- Python 3.12 (selected by the installers; uv downloads it if needed)
- [uv](https://docs.astral.sh/uv/) installed and available in PATH
- Local completion model: [marlosb/ArthurFriedenreich](https://huggingface.co/marlosb/ArthurFriedenreich), approximately 2.09B parameters. Allow about 5.74 GB for the downloaded weights. GPU inference uses FP16 (~4.18 GB for weights alone); CPU inference uses FP32 (~8.36 GB for weights alone). Both require additional memory for generation and framework overhead.
- Azure OpenAI **Chat Completion** model deployment (for `/api/chat-complete`, currently `GPT-5-nano`)
- Azure AI **Reasoning** model access (for `/api/reasoning-chat-complete`, currently `DeepSeek-R1-0528`)

## Quick Start

### Windows (PowerShell)

```powershell
.\install.ps1
.\run.ps1
```

`install.ps1` auto-detects NVIDIA GPUs (via `nvidia-smi`) and installs PyTorch 2.9.1 with CUDA 12.6 (`cu126`) when available, preserving support for Pascal GPUs such as the GTX 1080. Otherwise, it installs the default PyTorch 2.9.1 build.

### Linux/macOS (bash)

```bash
chmod +x install.sh run.sh
./install.sh
./run.sh
```

`install.sh` uses the same GPU detection and PyTorch 2.9.1 / CUDA 12.6 selection.

Both installers explicitly create the virtual environment with Python 3.12,
regardless of the system Python version, to use a Python ABI supported by the
pinned PyTorch builds. If uv asks to replace an existing `.venv` created with
another Python version, confirm replacement.

Both installers download the model selected by `LLM_MODEL_ID` (see below).
Existing installations must rerun the installer to download the new model and
update dependencies (PyTorch 2.9.1, Transformers >= 4.57.3 and < 5,
and Safetensors).

The selected model runs locally after installation, loading directly in FP16 on CUDA GPUs
without changing the downloaded checkpoint. CPU execution remains FP32.
FP16 reduces memory usage but does not guarantee faster inference on the GTX 1080.
ArthurFriedenreich's custom Transformers code is loaded
with `trust_remote_code=True`; the download is pinned to revision
`fe31fcfc2f907e085461af443da858e9895db726` in `backend/model_config.py`.
ArthurFriedenreich is a Portuguese-only base completion model, not a chat model.
The interface still supports all three languages, but this demo should use
Portuguese prompts. The prompt (including the automatically added BOS token) and
requested completion must fit within its 2,048-token context; larger requests
return HTTP 422 without truncating the prompt. GPT-2 uses its own 1,024-token
context limit.

### Select the local model

Set the OS environment variable `LLM_MODEL_ID` before both installation and
startup. It is read once per process and does not come from `secrets.txt`.
Restart the server after changing it.

| `LLM_MODEL_ID` | Local model directory |
|---|---|
| `marlosb/ArthurFriedenreich` (default) | `backend/models/ArthurFriedenreich` |
| `openai-community/gpt2` | `backend/models/openai-community-gpt2` |

Both the tokenizer demo and text completion use this selection. Unknown or empty
values fail explicitly instead of falling back to another model.

For a GPT-2 deployment on Linux/macOS:

```bash
export LLM_MODEL_ID=openai-community/gpt2
bash install.sh
bash run.sh
```

For a GPT-2 deployment on Windows:

```powershell
$env:LLM_MODEL_ID = "openai-community/gpt2"
.\install.ps1
.\run.ps1
```

Use `marlosb/ArthurFriedenreich` instead for an ArthurFriedenreich deployment,
or leave the variable unset. Configure the same environment variable in the
service definition when running the app as a managed service.

The app will run at:

- `http://127.0.0.1:8000`

## Secrets Configuration

Create (or update) `secrets.txt` in the project root:

These Azure settings are read from this file, not OS environment variables.
Values may be unquoted or enclosed in matching single or double quotes.

```text
# Azure OpenAI chat model (GPT-5-nano)
AZURE_OPENAI_CHAT_ENDPOINT=
AZURE_OPENAI_CHAT_API_KEY=
AZURE_OPENAI_CHAT_DEPLOYMENT=
AZURE_OPENAI_CHAT_MODEL=
AZURE_OPENAI_CHAT_API_VERSION=2025-01-01-preview

# Azure AI reasoning model (DeepSeek-R1-0528)
AZURE_OPENAI_REASONING_ENDPOINT=
AZURE_OPENAI_REASONING_API_KEY=
AZURE_OPENAI_REASONING_DEPLOYMENT=
AZURE_OPENAI_REASONING_MODEL=DeepSeek-R1-0528
AZURE_OPENAI_REASONING_API_VERSION=2024-05-01-preview
```

> For Azure AI `.../models/chat/completions` endpoints, set `AZURE_OPENAI_REASONING_MODEL` to the exact model/deployment name shown in your Azure AI project.

Azure OpenAI v1 endpoints are also supported. Set the endpoint to
`https://YOUR-RESOURCE.services.ai.azure.com/openai/v1` or its full
`/openai/v1/responses` URL. The base v1 URL uses the Responses API, while a full
`/openai/v1/chat/completions` URL uses Chat Completions. Set the corresponding
`MODEL` (or `DEPLOYMENT`) to the deployment name, such as `gpt-5-nano`.
The app uses the configured API key; it does not perform Entra ID authentication.
No `api-version` parameter is added to v1 URLs.

> Note: `secrets.txt` is intentionally gitignored and meant for local testing only.

## API Endpoints

- `GET /` - serves the single-page app
- `GET /api/content/{language_code}` - returns localized step content
- `POST /api/tokenize` - tokenization demo
- `POST /api/text-complete` - text completion with the selected local model
- `POST /api/chat-complete` - Azure chat completion (GPT-5-nano)
- `POST /api/reasoning-chat-complete` - Azure reasoning chat completion (DeepSeek-R1-0528)

## Development Notes

- This project is currently optimized for local/test usage.
- Model artifacts and Python caches are excluded via `.gitignore`.
- If you plan to deploy publicly, add authentication, rate limiting, and stricter secret/error handling.

## Troubleshooting `/api/tokenize` (Step 4)

- If Step 4 shows "Failed to tokenize text.", re-run `install.ps1` (Windows) or `install.sh` (Linux/macOS) with the same `LLM_MODEL_ID` used by the server. The tokenizer demo uses the selected local model directory without loading model weights.
- Check server output for the full exception traceback. The backend now logs tokenizer failures with details.
- The frontend now shows backend `detail` messages for tokenizer errors, which helps diagnose missing files/dependencies on remote machines.
