import pytest

from devsynth.ports.onnx_port import OnnxPort
from tests.unit.fakes.test_fake_onnx_runtime import FakeOnnxRuntime


@pytest.mark.fast
def test_onnx_port_load_and_run_succeeds():
    """Test that onnx port load and run succeeds.

    ReqID: N/A"""
    runtime = FakeOnnxRuntime()
    port = OnnxPort(runtime)
    port.load_model("model.onnx")
    assert runtime.loaded_model == "model.onnx"
    result = list(port.run({"input": [1, 2, 3]}))
    assert result == [{"input": [1, 2, 3]}]
