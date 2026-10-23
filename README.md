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
- Reasoning chat completion demo (Azure AI Phi-4-reasoning)
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
Dockerfile                        # Python 3.12 application image
compose.yaml                      # CPU deployment and model download service
compose.gpu.yaml                  # CUDA 12.6 / NVIDIA override
requirements.txt                  # shared application dependencies
install.py                        # model downloader, run inside the container
install.sh / install.ps1          # build image and download the selected model
run.sh / run.ps1                  # create container, wait for health, warm model
docker-common.sh / .ps1           # shared container selection and prerequisites
docker-firewall.sh                # Linux Docker LAN filtering (administrator setup)
secrets.env.example               # host environment file template, no real keys
secrets.txt                       # optional host-only environment file (gitignored)
```

## Prerequisites

- Docker Engine or Docker Desktop using Linux containers, with Docker Compose 2.24+
- Permission to access the Docker daemon; Docker group membership grants root-equivalent host access
- For GPU deployments: an NVIDIA driver and NVIDIA Container Toolkit configured for Docker (or supported Docker Desktop GPU integration)
- Local completion model: [marlosb/ArthurFriedenreich](https://huggingface.co/marlosb/ArthurFriedenreich), approximately 2.09B parameters. Allow about 5.74 GB for the downloaded weights. GPU inference uses FP16 (~4.18 GB for weights alone); CPU inference uses FP32 (~8.36 GB for weights alone). Both require additional memory for generation and framework overhead.
- Azure OpenAI **Chat Completion** model deployment (for `/api/chat-complete`, currently `GPT-5-nano`)
- Azure AI **Reasoning** model access (for `/api/reasoning-chat-complete`, currently `Phi-4-reasoning`)

## Quick Start

### Windows (PowerShell)

```powershell
Copy-Item secrets.env.example secrets.txt
# Edit secrets.txt on the host and add the Azure endpoints and API keys.
.\install.ps1
.\run.ps1
```

### Linux/macOS (bash)

```bash
cp secrets.env.example secrets.txt
chmod 600 secrets.txt
# Edit secrets.txt on the host and add the Azure endpoints and API keys.
bash install.sh
bash run.sh
```

Do not overwrite an existing filled-in secrets file with the example.
No host Python, virtual environment, or uv installation is needed.
The installers build the application image and download the selected model into
the persistent `llm-lecture_models` Docker volume. Existing host model files are
not copied into the image or automatically imported into that volume.

Both platforms auto-detect NVIDIA GPUs using `nvidia-smi`. GPU images use
PyTorch 2.9.1 with CUDA 12.6 (`cu126`), preserving Pascal/GTX 1080 support.
CPU images use the PyTorch 2.9.1 CPU build. Set `LLM_USE_GPU=1` to require GPU
containers, `LLM_USE_GPU=0` to use CPU containers, or leave it unset for detection.
GPU configuration errors fail explicitly; they do not silently switch to CPU.

The run scripts recreate the app container, wait for HTTP health, and warm up
the selected model before reporting success. The container runs in the
background with `restart: unless-stopped`; enable the host Docker service for
startup after reboot. Uvicorn runs without development reload.

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

Set the host environment variable `LLM_MODEL_ID` before both installation and
startup. Compose passes it to the downloader and app containers. It does not
come from `secrets.txt`; rerun the install and run scripts after changing it.

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
or leave the variable unset. Use the same `LLM_USE_GPU` and `LLM_MODEL_ID`
settings whenever invoking the install or run scripts.

The app will run at:

- `http://127.0.0.1:8000`

### LAN access and the firewall

The default published address is **localhost only**. Docker's published ports
can bypass UFW's normal input rules, so a UFW allowlist alone is not sufficient.
For Linux LAN deployments using Docker's iptables backend, first install the
app-specific filter as an administrator. For example:

```bash
sudo bash docker-firewall.sh 10.27.53.47 10.27.53.0/24 8000
export LLM_BIND_ADDRESS=10.27.53.47
export LLM_PORT=8000
bash run.sh
```

Replace the address and subnet with your actual host and trusted clients.
The script limits only this app's published IPv4 address/port in `DOCKER-USER`,
preserving unrelated Docker firewall rules. It installs a root-owned systemd
service and Docker dependency so the filter is restored before Docker starts
after reboot. It does not restart Docker or change SSH/UFW rules.
The Linux run script refuses a LAN bind unless that service is active and its
configured address/port matches. Do not switch Docker to its native nftables
backend without replacing this filtering setup.

For Windows/macOS LAN publishing, set `LLM_BIND_ADDRESS` explicitly and configure
the platform's host firewall separately. Use HTTPS and authentication in front
of the app before allowing untrusted clients.

To stop the app, use Docker Compose with the same GPU files used to start it:

```bash
# GPU deployment:
docker compose -p llm-lecture -f compose.yaml -f compose.gpu.yaml stop app
# CPU deployment:
docker compose -p llm-lecture -f compose.yaml stop app
```

Do not use `down --volumes` unless you intend to delete downloaded models.

## Secrets Configuration

The app reads Azure settings **only from process environment variables**.
There is no secrets-file loader or file fallback in the Python application.

Docker Compose reads a host-only environment file when creating the container
and injects its values. It does **not** mount that file in the container.
`secrets.txt` is the default for compatibility; preferably place the filled file
outside the repository and set `LLM_ENV_FILE` to its absolute path:

```bash
export LLM_ENV_FILE="$HOME/.config/llm-lecture/secrets.env"
```

On Windows, use `$env:LLM_ENV_FILE = "$HOME\.config\llm-lecture\secrets.env"`.
Protect the file with host permissions (`chmod 600` on Linux). Compose supports
unquoted values and matching single/double quotes. Never source the file as a
shell script, commit it, or pass keys as image build arguments.

```text
# Azure OpenAI chat model (GPT-5-nano)
AZURE_OPENAI_CHAT_ENDPOINT=
AZURE_OPENAI_CHAT_API_KEY=
AZURE_OPENAI_CHAT_DEPLOYMENT=
AZURE_OPENAI_CHAT_MODEL=
AZURE_OPENAI_CHAT_API_VERSION=2025-01-01-preview

# Azure AI reasoning model (Phi-4-reasoning)
AZURE_OPENAI_REASONING_ENDPOINT=https://YOUR-RESOURCE.services.ai.azure.com/openai/v1
AZURE_OPENAI_REASONING_API_KEY=
AZURE_OPENAI_REASONING_DEPLOYMENT=Phi-4-reasoning
AZURE_OPENAI_REASONING_MODEL=Phi-4-reasoning
AZURE_OPENAI_REASONING_API_VERSION=
```

> For Azure AI `.../models/chat/completions` endpoints, set `AZURE_OPENAI_REASONING_MODEL` to the exact model/deployment name shown in your Azure AI project.

Azure OpenAI v1 endpoints are also supported. Set the endpoint to
`https://YOUR-RESOURCE.services.ai.azure.com/openai/v1` or its full
`/openai/v1/responses` URL. For the chat demo, a base v1 URL uses the Responses
API. For the reasoning demo, a base v1 URL uses Chat Completions, matching
Phi-4-reasoning's connection example. A full `/openai/v1/chat/completions` URL
also uses Chat Completions. Set the corresponding
`MODEL` (or `DEPLOYMENT`) to the deployment name, such as `gpt-5-nano`.
The app uses the configured API key; it does not perform Entra ID authentication.
No `api-version` parameter is added to v1 URLs.
After changing a key or endpoint in the host file, rerun `run.sh` or `run.ps1`.
They recreate the container with the new environment. Restarting the existing
container alone does not reload the host environment file.

The model downloader does not receive the Azure environment file. The build
context is allowlisted in `.dockerignore`, excluding secrets, host environments,
Git metadata, and model weights. Runtime containers use a non-root user, a
read-only root filesystem and model mount, dropped capabilities, no-new-privileges,
and a writable temporary cache. Logs are rotated.

Environment variables remain visible to Docker/host administrators and a
compromised process can read its own credentials. Use workload identity/a secrets
manager for stronger credential isolation. Containerization does not add API
authentication, rate limiting, or HTTPS.

## API Endpoints

- `GET /` - serves the single-page app
- `GET /api/content/{language_code}` - returns localized step content
- `POST /api/tokenize` - tokenization demo
- `POST /api/text-complete` - text completion with the selected local model
- `POST /api/chat-complete` - Azure chat completion (GPT-5-nano)
- `POST /api/reasoning-chat-complete` - Azure reasoning chat completion (Phi-4-reasoning)

## Development Notes

- This project is currently optimized for local/test usage.
- Model artifacts and Python caches are excluded via `.gitignore`.
- If you plan to deploy publicly, add authentication, rate limiting, and stricter secret/error handling.

## Troubleshooting `/api/tokenize` (Step 4)

- If Step 4 shows "Failed to tokenize text.", re-run `install.ps1` (Windows) or `install.sh` (Linux/macOS) with the same `LLM_MODEL_ID` used by the server. The tokenizer demo uses the selected local model directory without loading model weights.
- Check server output for the full exception traceback. The backend now logs tokenizer failures with details.
- The frontend now shows backend `detail` messages for tokenizer errors, which helps diagnose missing files/dependencies on remote machines.
