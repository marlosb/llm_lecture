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
- Tokenizer demo
- Local text completion demo (ArthurFriedenreich)
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

- Python 3.10+ (recommended)
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

Both installers download ArthurFriedenreich to `backend/models/ArthurFriedenreich`.
Existing installations must rerun the installer to download the new model and
update dependencies (PyTorch 2.9.1, Transformers >= 4.57.3 and < 5,
and Safetensors).

The model runs locally after installation, loading directly in FP16 on CUDA GPUs
without changing the downloaded checkpoint. CPU execution remains FP32.
FP16 reduces memory usage but does not guarantee faster inference on the GTX 1080.
Its custom Transformers code is loaded
with `trust_remote_code=True`; the download is pinned to revision
`fe31fcfc2f907e085461af443da858e9895db726` in `backend/model_config.py`.
ArthurFriedenreich is a Portuguese-only base completion model, not a chat model.
The interface still supports all three languages, but this demo should use
Portuguese prompts. The prompt (including the automatically added BOS token) and
requested completion must fit within its 2,048-token context; larger requests
return HTTP 422 without truncating the prompt.

The app will run at:

- `http://127.0.0.1:8000`

## Secrets Configuration

Create (or update) `secrets.txt` in the project root:

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

> Note: `secrets.txt` is intentionally gitignored and meant for local testing only.

## API Endpoints

- `GET /` - serves the single-page app
- `GET /api/content/{language_code}` - returns localized step content
- `POST /api/tokenize` - tokenization demo
- `POST /api/text-complete` - local ArthurFriedenreich text completion demo
- `POST /api/chat-complete` - Azure chat completion (GPT-5-nano)
- `POST /api/reasoning-chat-complete` - Azure reasoning chat completion (DeepSeek-R1-0528)

## Development Notes

- This project is currently optimized for local/test usage.
- Model artifacts and Python caches are excluded via `.gitignore`.
- If you plan to deploy publicly, add authentication, rate limiting, and stricter secret/error handling.

## Troubleshooting `/api/tokenize` (Step 4)

- If Step 4 shows "Failed to tokenize text.", re-run `install.ps1` (Windows) or `install.sh` (Linux/macOS) to ensure all dependencies are installed, including `tiktoken`.
- Check server output for the full exception traceback. The backend now logs tokenizer failures with details.
- The frontend now shows backend `detail` messages for tokenizer errors, which helps diagnose missing files/dependencies on remote machines.
