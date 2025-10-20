"""Unit tests for the ONNX runtime adapter."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

pytest.importorskip("onnxruntime", reason="onnxruntime package is required for these tests")

from devsynth.adapters.onnx_runtime_adapter import ONNXRuntimeAdapter

pytestmark = [pytest.mark.requires_resource("onnxruntime")]


class TestONNXRuntimeAdapter:
    """Test the ONNX runtime adapter functionality."""

    def test_init_creates_empty_adapter(self) -> None:
        """Test that initialization creates an adapter with no session."""
        adapter = ONNXRuntimeAdapter()
        assert adapter.session is None

    def test_load_model_sets_session(self) -> None:
        """Test that load_model properly initializes the ONNX session."""
        adapter = ONNXRuntimeAdapter()

        # Mock the ONNX runtime to avoid needing actual model files
        mock_session = MagicMock()
        with patch(
            "devsynth.adapters.onnx_runtime_adapter.ort.InferenceSession",
            return_value=mock_session,
        ):
            with patch("devsynth.adapters.onnx_runtime_adapter.logger"):
                adapter.load_model("/path/to/model.onnx")

        assert adapter.session is not None

    def test_run_without_loaded_model_raises_error(self) -> None:
        """Test that run raises error when no model is loaded."""
        adapter = ONNXRuntimeAdapter()

        with pytest.raises(RuntimeError, match="Model not loaded"):
            list(adapter.run({"input": np.array([1, 2, 3])}))

    def test_run_with_loaded_model_calls_session_run(self) -> None:
        """Test that run properly calls the ONNX session."""
        adapter = ONNXRuntimeAdapter()

        # Mock the session and its run method
        mock_session = MagicMock()
        mock_session.run.return_value = [np.array([1, 2, 3])]
        adapter.session = mock_session

        inputs = {"input": np.array([[1, 2, 3]])}

        with patch("devsynth.adapters.onnx_runtime_adapter.logger"):
            result = list(adapter.run(inputs))

        # Verify session.run was called with correct parameters
        mock_session.run.assert_called_once_with(None, inputs)
        assert len(result) == 1
        assert isinstance(result[0], np.ndarray)

    def test_run_handles_multiple_outputs(self) -> None:
        """Test that run properly handles multiple outputs from the model."""
        adapter = ONNXRuntimeAdapter()

        # Mock session with multiple outputs
        mock_session = MagicMock()
        mock_session.run.return_value = [
            np.array([1, 2, 3]),
            np.array([[4, 5], [6, 7]]),
        ]
        adapter.session = mock_session

        inputs = {"input": np.array([[1, 2, 3]])}

        with patch("devsynth.adapters.onnx_runtime_adapter.logger"):
            result = list(adapter.run(inputs))

        assert len(result) == 2
        assert isinstance(result[0], np.ndarray)
        assert isinstance(result[1], np.ndarray)
        assert result[0].tolist() == [1, 2, 3]
        assert result[1].tolist() == [[4, 5], [6, 7]]

    def test_run_handles_empty_inputs(self) -> None:
        """Test that run handles empty input dictionaries."""
        adapter = ONNXRuntimeAdapter()

        # Mock session
        mock_session = MagicMock()
        mock_session.run.return_value = []
        adapter.session = mock_session

        with patch("devsynth.adapters.onnx_runtime_adapter.logger"):
            result = list(adapter.run({}))

        mock_session.run.assert_called_once_with(None, {})
        assert len(result) == 0

    def test_run_propagates_onnx_exceptions(self) -> None:
        """Test that ONNX runtime exceptions are properly propagated."""
        adapter = ONNXRuntimeAdapter()

        # Mock session that raises an exception
        mock_session = MagicMock()
        mock_session.run.side_effect = Exception("ONNX runtime error")
        adapter.session = mock_session

        inputs = {"input": np.array([[1, 2, 3]])}

        with pytest.raises(Exception, match="ONNX runtime error"):
            list(adapter.run(inputs))
