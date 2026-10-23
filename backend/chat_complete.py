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
        value = value.strip()
        if (
            len(value) >= 2
            and value[0] == value[-1]
            and value[0] in ("'", '"')
        ):
            value = value[1:-1]
        values[key.strip()] = value
    return values


def _resolve_url(
    endpoint: str,
    deployment: str,
    api_version: str,
    deployment_error: str,
    prefer_chat_completions: bool = False,
) -> str:
    clean_endpoint: str = endpoint.strip()
    parsed_endpoint = parse.urlparse(clean_endpoint)
    path: str = parsed_endpoint.path.rstrip("/")
    if path == "/openai/v1":
        api_path: str = (
            "chat/completions" if prefer_chat_completions else "responses"
        )
        return parse.urlunparse(
            parsed_endpoint._replace(path=f"{path}/{api_path}")
        )
    if path in ("/openai/v1/responses", "/openai/v1/chat/completions"):
        return parse.urlunparse(parsed_endpoint._replace(path=path))

    if path.endswith(("/chat/completions", "/responses")):
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
    model: str,
    api_version: str,
    missing_secret_error: str,
    missing_deployment_error: str,
    missing_model_error: str,
    system_message: str,
    prefer_chat_completions: bool = False,
) -> ChatCompleteResponse:
    if not endpoint or not api_key:
        raise ValueError(missing_secret_error)

    url: str = _resolve_url(
        endpoint=endpoint,
        deployment=deployment,
        api_version=api_version,
        deployment_error=missing_deployment_error,
        prefer_chat_completions=prefer_chat_completions,
    )

    path: str = parse.urlparse(url).path.rstrip("/")
    uses_responses: bool = path.endswith("/responses")
    body: dict[str, object]
    if uses_responses:
        body = {
            "instructions": system_message,
            "input": payload.text,
        }
    else:
        body = {
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": payload.text},
            ]
        }
    if (
        uses_responses
        or path == "/openai/v1/chat/completions"
        or "/models/chat/completions" in path
    ):
        if not model:
            raise ValueError(missing_model_error)
        body["model"] = model
    request_data: bytes = json.dumps(body).encode("utf-8")
    headers: dict[str, str] = {
        "Content-Type": "application/json",
        "api-key": api_key,
    }
    if "/models/chat/completions" in url:
        headers["Authorization"] = f"Bearer {api_key}"
    req = request.Request(url, data=request_data, headers=headers, method="POST")

    try:
        with request.urlopen(req, timeout=60) as resp:
            response_data = json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        if "/models/chat/completions" in url and "DeploymentNotFound" in detail:
            detail = (
                f"{detail} Hint: for Azure AI /models/chat/completions endpoints, "
                "set AZURE_OPENAI_REASONING_MODEL (or AZURE_OPENAI_CHAT_MODEL) to "
                "the exact model/deployment name available in your Azure AI project."
            )
        raise RuntimeError(f"Azure OpenAI request failed: {detail}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Azure OpenAI connection failed: {exc.reason}") from exc

    completion: str
    if uses_responses:
        completion = "".join(
            part.get("text", "")
            for item in response_data.get("output", [])
            if item.get("type") == "message"
            for part in item.get("content", [])
            if part.get("type") == "output_text"
        )
        if not completion:
            raise RuntimeError(
                "Azure OpenAI response did not include output text."
            )
    else:
        choices = response_data.get("choices", [])
        if not choices:
            raise RuntimeError("Azure OpenAI response did not include choices.")
        completion = choices[0].get("message", {}).get("content", "")
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
    model: str = secrets.get("AZURE_OPENAI_CHAT_MODEL", "") or secrets.get(
        "AZURE_OPENAI_CHAT_DEPLOYMENT", ""
    )
    api_version: str = secrets.get("AZURE_OPENAI_CHAT_API_VERSION", "") or secrets.get(
        "AZURE_OPENAI_API_VERSION", "2024-10-21"
    )
    return _run_azure_chat_complete(
        payload=payload,
        endpoint=endpoint,
        api_key=api_key,
        deployment=deployment,
        model=model,
        api_version=api_version,
        missing_secret_error=(
            "Missing AZURE_OPENAI_CHAT_ENDPOINT and/or AZURE_OPENAI_CHAT_API_KEY "
            "in secrets.txt."
        ),
        missing_deployment_error=(
            "Missing AZURE_OPENAI_CHAT_DEPLOYMENT in secrets.txt for base endpoint mode."
        ),
        missing_model_error=(
            "Missing AZURE_OPENAI_CHAT_MODEL (or AZURE_OPENAI_CHAT_DEPLOYMENT) "
            "in secrets.txt for model-based endpoints."
        ),
        system_message=(
            "You are a helpful and concise assistant. "
            "Always respond in the same language as the user's message."
        ),
    )


def reasoning_chat_complete(payload: ChatCompleteRequest) -> ChatCompleteResponse:
    secrets: dict[str, str] = _load_secrets()
    endpoint: str = secrets.get("AZURE_OPENAI_REASONING_ENDPOINT", "")
    api_key: str = secrets.get("AZURE_OPENAI_REASONING_API_KEY", "")
    deployment: str = secrets.get("AZURE_OPENAI_REASONING_DEPLOYMENT", "")
    model: str = (
        secrets.get("AZURE_OPENAI_REASONING_MODEL", "")
        or secrets.get("AZURE_OPENAI_REASONING_DEPLOYMENT", "")
        or "Phi-4-reasoning"
    )
    api_version: str = secrets.get("AZURE_OPENAI_REASONING_API_VERSION", "") or secrets.get(
        "AZURE_OPENAI_API_VERSION", "2024-10-21"
    )
    return _run_azure_chat_complete(
        payload=payload,
        endpoint=endpoint,
        api_key=api_key,
        deployment=deployment,
        model=model,
        api_version=api_version,
        missing_secret_error=(
            "Missing AZURE_OPENAI_REASONING_ENDPOINT and/or "
            "AZURE_OPENAI_REASONING_API_KEY in secrets.txt."
        ),
        missing_deployment_error=(
            "Missing AZURE_OPENAI_REASONING_DEPLOYMENT in secrets.txt for base endpoint mode."
        ),
        missing_model_error=(
            "Missing AZURE_OPENAI_REASONING_MODEL in secrets.txt for "
            "model-based endpoints."
        ),
        system_message=(
            "Você é um assistente de raciocínio. Explique sempre passo a passo "
            "de forma clara e estruturada. Responda sempre no mesmo idioma da "
            "pergunta do usuário."
        ),
        prefer_chat_completions=True,
    )
