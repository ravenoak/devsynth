from typing import Any, Dict

import pytest

from devsynth.domain.interfaces.cli import CLIInterface
from devsynth.domain.interfaces.code_analysis import FileAnalysisResult
from devsynth.domain.interfaces.onnx import OnnxRuntime


class DummyCLI(CLIInterface):
    def initialize_project(self, path: str) -> None:  # pragma: no cover - intentional
        super().initialize_project(path)

    def generate_spec(
        self, requirements_file: str
    ) -> None:  # pragma: no cover - intentional
        super().generate_spec(requirements_file)

    def generate_tests(self, spec_file: str) -> None:  # pragma: no cover - intentional
        super().generate_tests(spec_file)

    def generate_code(self) -> None:  # pragma: no cover - intentional
        super().generate_code()

    def run(self, target: str | None = None) -> None:  # pragma: no cover - intentional
        super().run(target)

    def configure(
        self, key: str | None = None, value: str | None = None
    ) -> dict[str, Any]:  # pragma: no cover - intentional
        return super().configure(key, value)


@pytest.mark.fast
def test_cli_interface_raises_not_implemented() -> None:
    cli = DummyCLI()
    with pytest.raises(NotImplementedError):
        cli.initialize_project("/tmp")


class DummyFileAnalysis(FileAnalysisResult):
    def get_imports(self):  # pragma: no cover - intentional
        return super().get_imports()

    def get_classes(self):  # pragma: no cover - intentional
        return super().get_classes()

    def get_functions(self):  # pragma: no cover - intentional
        return super().get_functions()

    def get_variables(self):  # pragma: no cover - intentional
        return super().get_variables()

    def get_docstring(self):  # pragma: no cover - intentional
        return super().get_docstring()

    def get_metrics(self):  # pragma: no cover - intentional
        return super().get_metrics()


@pytest.mark.fast
def test_file_analysis_result_raises_not_implemented() -> None:
    analysis = DummyFileAnalysis()
    with pytest.raises(NotImplementedError):
        analysis.get_imports()


class DummyOnnx(OnnxRuntime):
    def load_model(self, model_path: str) -> None:  # pragma: no cover - intentional
        super().load_model(model_path)

    def run(self, inputs: dict[str, Any]):  # pragma: no cover - intentional
        return super().run(inputs)


@pytest.mark.fast
def test_onnx_runtime_raises_not_implemented() -> None:
    runtime = DummyOnnx()
    with pytest.raises(NotImplementedError):
        runtime.load_model("model.onnx")
