"""Adapter providing an OnnxRuntime implementation using onnxruntime."""

from typing import Any, Dict, Union
from collections.abc import Iterable

import onnxruntime as ort

from devsynth.domain.interfaces.onnx import OnnxRuntime
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)


class ONNXRuntimeAdapter(OnnxRuntime):
    """Thin wrapper around ``onnxruntime.InferenceSession``."""

    def __init__(self) -> None:
        self.session: ort.InferenceSession | None = None

    def load_model(self, model_path: str) -> None:
        logger.debug(f"Initializing ONNX runtime with model: {model_path}")
        self.session = ort.InferenceSession(model_path)

    def run(self, inputs: dict[str, Any]) -> Iterable[Any]:
        if self.session is None:
            raise RuntimeError("Model not loaded")
        return self.session.run(None, inputs)
