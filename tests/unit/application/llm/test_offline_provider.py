import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from devsynth.application.llm.offline_provider import OfflineProvider


def test_offline_provider_fallback() -> None:
    provider = OfflineProvider()
    assert provider.generate("hello") == "[offline] hello"


def test_offline_provider_loads_model(tmp_path, monkeypatch) -> None:
    called = {}

    def fake_model_from_pretrained(path, *args, **kwargs):
        called["model_path"] = path

        class Dummy:
            def generate(self, **_):
                return torch.tensor([[0]])

        return Dummy()

    def fake_tokenizer_from_pretrained(path, *args, **kwargs):
        called["tokenizer_path"] = path

        class Dummy:
            def __call__(self, text, return_tensors=None):
                return {}

            def decode(self, ids, skip_special_tokens=True):
                return "Hello world"

        return Dummy()

    monkeypatch.setattr(
        AutoModelForCausalLM, "from_pretrained", fake_model_from_pretrained
    )
    monkeypatch.setattr(
        AutoTokenizer, "from_pretrained", fake_tokenizer_from_pretrained
    )

    provider = OfflineProvider({"offline_provider": {"model_path": str(tmp_path)}})
    result = provider.generate("Hello")

    assert result == "Hello world"
    assert called["model_path"] == str(tmp_path)
    assert called["tokenizer_path"] == str(tmp_path)
