"""Port for ONNX runtime operations."""

from typing import Any, Dict, Iterable

from devsynth.logging_setup import DevSynthLogger

from ..domain.interfaces.onnx import OnnxRuntime

logger = DevSynthLogger(__name__)


class OnnxPort:
    """Port that wraps an OnnxRuntime implementation."""

    def __init__(self, runtime: OnnxRuntime):
        self.runtime = runtime

    def load_model(self, model_path: str) -> None:
        """Load an ONNX model using the underlying runtime."""
        logger.debug(f"Loading ONNX model from {model_path}")
        self.runtime.load_model(model_path)

    def run(self, inputs: Dict[str, Any]) -> Iterable[Any]:
        """Run inference on the loaded model."""
        logger.debug("Running ONNX model")
        return self.runtime.run(inputs)
