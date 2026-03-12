import argparse
import shutil
import subprocess
import sys
from pathlib import Path

MODEL_ID: str = "openai-community/gpt2"
TARGET_DIR: Path = (
    Path(__file__).resolve().parent / "backend" / "models" / "openai-community-gpt2"
)
BASE_PACKAGES: tuple[str, ...] = ("fastapi", "uvicorn", "huggingface_hub", "transformers", "tiktoken")
TORCH_CUDA_EXTRA_INDEX_URL: str = "https://download.pytorch.org/whl/cu121"


def has_nvidia_gpu() -> bool:
    nvidia_smi: str | None = shutil.which("nvidia-smi")
    if nvidia_smi is None:
        return False

    result = subprocess.run(
        [nvidia_smi, "-L"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def install_dependencies() -> None:
    subprocess.run(
        [sys.executable, "-m", "pip", "install", *BASE_PACKAGES],
        check=True,
    )

    if has_nvidia_gpu():
        print("NVIDIA GPU detected. Installing CUDA-enabled PyTorch (cu121).")
        torch_install_cmd: list[str] = [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--extra-index-url",
            TORCH_CUDA_EXTRA_INDEX_URL,
            "torch",
        ]
    else:
        print("No NVIDIA GPU detected. Installing default PyTorch build.")
        torch_install_cmd = [sys.executable, "-m", "pip", "install", "torch"]

    subprocess.run(
        torch_install_cmd,
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
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--skip-deps",
        action="store_true",
        help="Skip dependency installation and only download model files.",
    )
    args = parser.parse_args()

    if not args.skip_deps:
        install_dependencies()

    install_gpt2()


if __name__ == "__main__":
    main()
