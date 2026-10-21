import unittest
from unittest.mock import patch

import install


class DependencyInstallationTests(unittest.TestCase):
    def test_gpu_install_pins_pascal_compatible_cuda_build(self) -> None:
        with (
            patch.object(install, "has_nvidia_gpu", return_value=True),
            patch.object(install.subprocess, "run") as run,
        ):
            install.install_dependencies()

        command = run.call_args.args[0]
        self.assertIn("torch==2.9.1+cu126", command)
        self.assertIn("https://download.pytorch.org/whl/cu126", command)
        self.assertTrue(run.call_args.kwargs["check"])

    def test_cpu_install_does_not_request_cuda_build(self) -> None:
        with (
            patch.object(install, "has_nvidia_gpu", return_value=False),
            patch.object(install.subprocess, "run") as run,
        ):
            install.install_dependencies()

        command = run.call_args.args[0]
        self.assertIn("torch==2.9.1", command)
        self.assertNotIn("--extra-index-url", command)


if __name__ == "__main__":
    unittest.main()
