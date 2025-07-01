import sys
import types
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))

import devsynth.domain.interfaces.llm  # required for relative imports

spec = importlib.util.spec_from_file_location(
    "devsynth.application.llm.offline_provider",
    ROOT / "src/devsynth/application/llm/offline_provider.py",
)
offline_provider = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = offline_provider
spec.loader.exec_module(offline_provider)  # type: ignore
OfflineProvider = offline_provider.OfflineProvider


def test_offline_provider_fallback() -> None:
    provider = OfflineProvider()
    assert provider.generate("hello") == "[offline] hello"
    # embeddings are deterministic
    assert provider.get_embedding("hello") == provider.get_embedding("hello")


def test_offline_provider_loads_local_model(tmp_path, monkeypatch) -> None:
    called = {}

    def fake_model_from_pretrained(path, *_, **__):
        called["model_path"] = path

        class DummyModel:
            def generate(self, **_):
                return [[0]]

        return DummyModel()

    def fake_tokenizer_from_pretrained(path, *_, **__):
        called["tokenizer_path"] = path

        class DummyTokenizer:
            def __call__(self, text, return_tensors=None):
                called["input_text"] = text
                return {}

            def decode(self, ids, skip_special_tokens=True):
                return "Hello world"

        return DummyTokenizer()

    FakeModelCls = types.SimpleNamespace(
        from_pretrained=staticmethod(fake_model_from_pretrained)
    )
    FakeTokCls = types.SimpleNamespace(
        from_pretrained=staticmethod(fake_tokenizer_from_pretrained)
    )

    class DummyTorch:
        def no_grad(self):
            class Ctx:
                def __enter__(self):
                    return None

                def __exit__(self, exc_type, exc, tb):
                    pass

            return Ctx()

    monkeypatch.setattr(offline_provider, "AutoModelForCausalLM", FakeModelCls)
    monkeypatch.setattr(offline_provider, "AutoTokenizer", FakeTokCls)
    monkeypatch.setattr(offline_provider, "torch", DummyTorch())

    provider = OfflineProvider({"offline_provider": {"model_path": str(tmp_path)}})
    result = provider.generate("Hello")

    assert result == "Hello world"
    assert called["model_path"] == str(tmp_path)
    assert called["tokenizer_path"] == str(tmp_path)
