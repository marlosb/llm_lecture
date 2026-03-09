import json
from pathlib import Path
from urllib import error
from urllib import parse
from urllib import request

from pydantic import BaseModel


SECRETS_FILE: Path = Path(__file__).resolve().parent.parent / "secrets.txt"


class ChatCompleteRequest(BaseModel):
    text: str


class ChatCompleteResponse(BaseModel):
    prompt: str
    completion: str


def _load_secrets() -> dict[str, str]:
    if not SECRETS_FILE.exists():
        raise FileNotFoundError(
            f"Secrets file not found: {SECRETS_FILE}. Create it with Azure OpenAI values."
        )

    values: dict[str, str] = {}
    for raw_line in SECRETS_FILE.read_text(encoding="utf-8").splitlines():
        line: str = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def _resolve_url(
    endpoint: str,
    deployment: str,
    api_version: str,
    deployment_error: str,
) -> str:
    clean_endpoint: str = endpoint.strip()
    if "/chat/completions" in clean_endpoint:
        url = clean_endpoint
        parsed = parse.urlparse(url)
        query_pairs = parse.parse_qs(parsed.query)
        if "api-version" not in query_pairs and api_version:
            separator = "&" if parsed.query else "?"
            url = f"{url}{separator}{parse.urlencode({'api-version': api_version})}"
        return url

    if not deployment:
        raise ValueError(deployment_error)

    base = clean_endpoint.rstrip("/")
    query: str = parse.urlencode({"api-version": api_version})
    return f"{base}/openai/deployments/{deployment}/chat/completions?{query}"


def _run_azure_chat_complete(
    payload: ChatCompleteRequest,
    endpoint: str,
    api_key: str,
    deployment: str,
    api_version: str,
    missing_secret_error: str,
    missing_deployment_error: str,
    system_message: str,
) -> ChatCompleteResponse:
    if not endpoint or not api_key:
        raise ValueError(missing_secret_error)

    url: str = _resolve_url(
        endpoint=endpoint,
        deployment=deployment,
        api_version=api_version,
        deployment_error=missing_deployment_error,
    )

    body: dict[str, object] = {
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user", "content": payload.text},
        ]
    }
    request_data: bytes = json.dumps(body).encode("utf-8")
    headers: dict[str, str] = {
        "Content-Type": "application/json",
        "api-key": api_key,
    }
    req = request.Request(url, data=request_data, headers=headers, method="POST")

    try:
        with request.urlopen(req, timeout=60) as resp:
            response_data = json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Azure OpenAI request failed: {detail}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Azure OpenAI connection failed: {exc.reason}") from exc

    choices = response_data.get("choices", [])
    if not choices:
        raise RuntimeError("Azure OpenAI response did not include choices.")

    completion: str = choices[0].get("message", {}).get("content", "")
    return ChatCompleteResponse(prompt=payload.text, completion=completion)


def chat_complete(payload: ChatCompleteRequest) -> ChatCompleteResponse:
    secrets: dict[str, str] = _load_secrets()
    endpoint: str = secrets.get("AZURE_OPENAI_CHAT_ENDPOINT", "") or secrets.get(
        "AZURE_OPENAI_ENDPOINT", ""
    )
    api_key: str = secrets.get("AZURE_OPENAI_CHAT_API_KEY", "") or secrets.get(
        "AZURE_OPENAI_API_KEY", ""
    )
    deployment: str = secrets.get("AZURE_OPENAI_CHAT_DEPLOYMENT", "")
    api_version: str = secrets.get("AZURE_OPENAI_CHAT_API_VERSION", "") or secrets.get(
        "AZURE_OPENAI_API_VERSION", "2024-10-21"
    )
    return _run_azure_chat_complete(
        payload=payload,
        endpoint=endpoint,
        api_key=api_key,
        deployment=deployment,
        api_version=api_version,
        missing_secret_error=(
            "Missing AZURE_OPENAI_CHAT_ENDPOINT and/or AZURE_OPENAI_CHAT_API_KEY "
            "in secrets.txt."
        ),
        missing_deployment_error=(
            "Missing AZURE_OPENAI_CHAT_DEPLOYMENT in secrets.txt for base endpoint mode."
        ),
        system_message="Você é um assistente útil e objetivo.",
    )


def reasoning_chat_complete(payload: ChatCompleteRequest) -> ChatCompleteResponse:
    secrets: dict[str, str] = _load_secrets()
    endpoint: str = secrets.get("AZURE_OPENAI_REASONING_ENDPOINT", "")
    api_key: str = secrets.get("AZURE_OPENAI_REASONING_API_KEY", "")
    deployment: str = secrets.get("AZURE_OPENAI_REASONING_DEPLOYMENT", "")
    api_version: str = secrets.get("AZURE_OPENAI_REASONING_API_VERSION", "") or secrets.get(
        "AZURE_OPENAI_API_VERSION", "2024-10-21"
    )
    return _run_azure_chat_complete(
        payload=payload,
        endpoint=endpoint,
        api_key=api_key,
        deployment=deployment,
        api_version=api_version,
        missing_secret_error=(
            "Missing AZURE_OPENAI_REASONING_ENDPOINT and/or "
            "AZURE_OPENAI_REASONING_API_KEY in secrets.txt."
        ),
        missing_deployment_error=(
            "Missing AZURE_OPENAI_REASONING_DEPLOYMENT in secrets.txt for base endpoint mode."
        ),
        system_message=(
            "Você é um assistente de raciocínio. Explique sempre passo a passo "
            "de forma clara e estruturada. Responda sempre no mesmo idioma da "
            "pergunta do usuário."
        ),
    )
