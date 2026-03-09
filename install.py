import subprocess
import sys
from pathlib import Path

MODEL_ID: str = "openai-community/gpt2"
TARGET_DIR: Path = (
    Path(__file__).resolve().parent / "backend" / "models" / "openai-community-gpt2"
)
REQUIRED_PACKAGES: tuple[str, ...] = ("huggingface_hub", "transformers", "torch")


def install_dependencies() -> None:
    subprocess.run(
        [sys.executable, "-m", "pip", "install", *REQUIRED_PACKAGES],
        check=True,
    )


def install_gpt2() -> None:
    from huggingface_hub import snapshot_download

    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    snapshot_download(
        repo_id=MODEL_ID,
        local_dir=str(TARGET_DIR),
        local_dir_use_symlinks=False,
    )
    print(f"Downloaded {MODEL_ID} to {TARGET_DIR}")


def main() -> None:
    install_dependencies()
    install_gpt2()


if __name__ == "__main__":
    main()
