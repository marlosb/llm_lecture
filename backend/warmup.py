import json
from urllib import request


def main() -> None:
    payload: bytes = json.dumps(
        {"text": "Warmup", "max_new_tokens": 1}
    ).encode("utf-8")
    req = request.Request(
        "http://127.0.0.1:8000/api/text-complete",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=180) as response:
        response.read()
    print("Model warm-up completed.")


if __name__ == "__main__":
    main()
