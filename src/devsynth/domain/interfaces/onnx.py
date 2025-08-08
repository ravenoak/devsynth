from abc import ABC, abstractmethod
from typing import Any, Dict, Iterable

from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)


class OnnxRuntime(ABC):
    """Protocol for ONNX runtime implementations."""

    @abstractmethod
    def load_model(self, model_path: str) -> None:
        """Load an ONNX model from the given path."""
        raise NotImplementedError

    @abstractmethod
    def run(self, inputs: Dict[str, Any]) -> Iterable[Any]:
        """Run inference on the loaded model."""
        raise NotImplementedError
