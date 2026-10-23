import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from backend.model_config import MODEL_DIR
from backend.model_config import MODEL_ID
from backend.model_config import MODEL_REVISION


TARGET_DIR: Path = MODEL_DIR
BASE_PACKAGES: tuple[str, ...] = tuple(
    line.strip()
    for line in Path(__file__).with_name("requirements.txt").read_text(
        encoding="utf-8"
    ).splitlines()
    if line.strip() and not line.lstrip().startswith("#")
)
TORCH_PACKAGE: str = "torch==2.9.1"
TORCH_CUDA_PACKAGE: str = "torch==2.9.1+cu126"
TORCH_CUDA_EXTRA_INDEX_URL: str = "https://download.pytorch.org/whl/cu126"


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
        print("NVIDIA GPU detected. Installing PyTorch 2.9.1 (cu126).")
        torch_install_cmd: list[str] = [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--extra-index-url",
            TORCH_CUDA_EXTRA_INDEX_URL,
            TORCH_CUDA_PACKAGE,
        ]
    else:
        print("No NVIDIA GPU detected. Installing default PyTorch build.")
        torch_install_cmd = [sys.executable, "-m", "pip", "install", TORCH_PACKAGE]

    subprocess.run(
        torch_install_cmd,
        check=True,
    )


def install_model() -> None:
    from huggingface_hub import snapshot_download

    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    snapshot_download(
        repo_id=MODEL_ID,
        revision=MODEL_REVISION,
        local_dir=str(TARGET_DIR),
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

    install_model()


if __name__ == "__main__":
    main()
