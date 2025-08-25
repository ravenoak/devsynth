from typing import Any, Dict, Iterable, Union

from devsynth.domain.interfaces.onnx import OnnxRuntime


class FakeOnnxRuntime(OnnxRuntime):
    """Simple in-memory fake for ONNX runtime."""

    def __init__(self) -> None:
        self.loaded_model: Union[str, None] = None

    def load_model(self, model_path: str) -> None:
        self.loaded_model = model_path

    def run(self, inputs: Dict[str, Any]) -> Iterable[Any]:
        # Echo the inputs back as inference result
        return [inputs]
