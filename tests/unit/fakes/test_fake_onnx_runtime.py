from typing import Any, Dict, Union
from collections.abc import Iterable

from devsynth.domain.interfaces.onnx import OnnxRuntime


class FakeOnnxRuntime(OnnxRuntime):
    """Simple in-memory fake for ONNX runtime."""

    def __init__(self) -> None:
        self.loaded_model: str | None = None

    def load_model(self, model_path: str) -> None:
        self.loaded_model = model_path

    def run(self, inputs: dict[str, Any]) -> Iterable[Any]:
        # Echo the inputs back as inference result
        return [inputs]
