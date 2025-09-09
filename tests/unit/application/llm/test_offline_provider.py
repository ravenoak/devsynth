import pytest

from devsynth.application.llm.offline_provider import OfflineProvider


class TestOfflineProvider:
    @pytest.mark.fast
    def test_generate_prefixes_with_offline(self):
        p = OfflineProvider(config={})
        out = p.generate("Hello world")
        assert out.startswith("[offline] ")
        assert "Hello world" in out

    @pytest.mark.fast
    def test_generate_with_context_concatenates(self):
        p = OfflineProvider()
        ctx = [{"role": "user", "content": "A"}, {"role": "assistant", "content": "B"}]
        out = p.generate_with_context("C", ctx)
        assert out.startswith("[offline] ")
        assert "A" in out and "B" in out and "C" in out

    @pytest.mark.fast
    def test_get_embedding_is_deterministic(self):
        p = OfflineProvider()
        e1 = p.get_embedding("abc")
        e2 = p.get_embedding("abc")
        e3 = p.get_embedding("abcd")
        assert e1 == e2
        assert e1 != e3
        assert all(isinstance(x, float) for x in e1)
        assert len(e1) == 8
