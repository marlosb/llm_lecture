import argparse
import json
import math
import statistics
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed
from dataclasses import dataclass
from http.client import HTTPException
from urllib import error
from urllib import request
from urllib.parse import urlparse


PROMPTS: tuple[str, ...] = (
    "A historia do futebol brasileiro comecou muito antes dos grandes estadios. "
    "Nos primeiros campos, jogadores e torcedores",
    "Em uma pequena cidade do interior do Brasil, uma professora decidiu criar "
    "uma biblioteca. Na primeira semana, ela",
    "A viagem pelo Brasil comecou em uma manha de domingo. Ao longo do caminho, "
    "as paisagens e as pessoas",
    "O desenvolvimento da ciencia no Brasil envolve universidades, escolas e "
    "centros de pesquisa. Uma historia que ilustra esse trabalho",
    "No bairro onde cresci, a feira de sabado era o ponto de encontro das "
    "familias. Entre as bancas de frutas e verduras,",
    "Aprender uma nova habilidade exige pratica e curiosidade. Quando comecei "
    "a estudar musica, descobri que",
)


@dataclass
class Result:
    number: int
    seconds: float
    characters: int = 0
    failure: str | None = None


def complete(base_url: str, text: str, tokens: int, timeout: float) -> str:
    payload = json.dumps({"text": text, "max_new_tokens": tokens}).encode("utf-8")
    req = request.Request(
        f"{base_url}/api/text-complete",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=timeout) as response:
        body = json.load(response)
    if not isinstance(body, dict) or not isinstance(body.get("completion"), str):
        raise ValueError("Response must contain a 'completion' string.")
    return body["completion"]


def measure(
    number: int, base_url: str, tokens: int, timeout: float
) -> Result:
    started = time.perf_counter()
    try:
        completion = complete(
            base_url, PROMPTS[(number - 1) % len(PROMPTS)], tokens, timeout
        )
    except error.HTTPError as exc:
        with exc:
            detail = exc.read().decode("utf-8", errors="replace")
        return Result(
            number, time.perf_counter() - started,
            failure=f"HTTP {exc.code}: {detail}",
        )
    except (error.URLError, OSError, HTTPException, ValueError) as exc:
        return Result(
            number, time.perf_counter() - started,
            failure=f"{type(exc).__name__}: {exc}",
        )
    return Result(number, time.perf_counter() - started, len(completion))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Load-test the deployed local text-completion API."
    )
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--requests", type=int, default=6)
    parser.add_argument("--concurrency", type=int, default=1)
    parser.add_argument("--max-new-tokens", type=int, default=1000)
    parser.add_argument("--timeout", type=float, default=600)
    args = parser.parse_args(argv)
    url = urlparse(args.base_url)
    if url.scheme not in ("http", "https") or not url.netloc:
        parser.error("--base-url must be an HTTP(S) URL.")
    if args.requests < 1 or args.concurrency < 1:
        parser.error("--requests and --concurrency must be positive.")
    if not 1 <= args.max_new_tokens <= 2000:
        parser.error("--max-new-tokens must be between 1 and 2000.")
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error("--timeout must be a finite positive number.")
    base_url = args.base_url.rstrip("/")

    print("Warming up with 16 output tokens (excluded from measurements)...")
    warmup = measure(1, base_url, 16, args.timeout)
    if warmup.failure is not None:
        print(f"Warm-up failed: {warmup.failure}")
        return 1

    print(
        f"Running {args.requests} requests; concurrency={args.concurrency}; "
        f"max_new_tokens={args.max_new_tokens}; timeout={args.timeout:g}s"
    )
    print("KV caching is controlled by the server, not this client.")
    results: list[Result] = []
    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        futures = [
            executor.submit(
                measure, number, base_url, args.max_new_tokens, args.timeout
            )
            for number in range(1, args.requests + 1)
        ]
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            status = (
                f"FAILED: {result.failure}" if result.failure is not None
                else f"OK: {result.characters} characters"
            )
            print(f"Request {result.number}: {result.seconds:.2f}s; {status}")
    elapsed = time.perf_counter() - started
    successful = [item for item in results if item.failure is None]
    print(
        f"\nSucceeded: {len(successful)}/{args.requests}; "
        f"failed: {args.requests - len(successful)}; wall time: {elapsed:.2f}s"
    )
    if successful:
        latencies = sorted(item.seconds for item in successful)
        p95 = latencies[math.ceil(0.95 * len(latencies)) - 1]
        print(
            "Successful request latency (seconds): "
            f"min={latencies[0]:.2f}, mean={statistics.mean(latencies):.2f}, "
            f"p95={p95:.2f}, max={latencies[-1]:.2f}"
        )
        print(
            f"Throughput: {len(successful) / elapsed:.3f} successful requests/s; "
            f"{sum(item.characters for item in successful) / elapsed:.1f} "
            "completion characters/s"
        )
    return 0 if len(successful) == args.requests else 1


if __name__ == "__main__":
    raise SystemExit(main())
