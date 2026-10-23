FROM python:3.12-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:0.12.10 /uv /usr/local/bin/uv

ARG TORCH_PACKAGE=torch==2.9.1
ARG TORCH_BACKEND=cpu

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_HOME=/tmp/huggingface \
    HF_MODULES_CACHE=/tmp/huggingface/modules \
    TORCH_HOME=/tmp/torch \
    CUDA_CACHE_PATH=/tmp/cuda-cache

RUN apt-get update \
    && apt-get install --yes --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists

WORKDIR /app
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system --torch-backend "$TORCH_BACKEND" \
    "$TORCH_PACKAGE" --requirement requirements.txt

COPY install.py .
COPY backend/ backend/
COPY static/ static/

RUN groupadd --gid 10001 app \
    && useradd --uid 10001 --gid app --create-home app \
    && mkdir -p /app/backend/models \
    && chown app:app /app/backend/models

USER 10001:10001
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
