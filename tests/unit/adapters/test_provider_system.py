from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from devsynth.adapters import provider_system
from devsynth.adapters.provider_system import ProviderError


def test_embed_success():
    provider = MagicMock()
    provider.embed.return_value = [[1.0, 2.0]]
    with patch.object(provider_system, "get_provider", return_value=provider):
        result = provider_system.embed(
            "text", provider_type="lm_studio", fallback=False
        )
        assert result == [[1.0, 2.0]]
        provider.embed.assert_called_once()


def test_embed_error():
    provider = MagicMock()
    provider.embed.side_effect = ProviderError("fail")
    with patch.object(provider_system, "get_provider", return_value=provider):
        with pytest.raises(ProviderError):
            provider_system.embed("text", provider_type="lm_studio", fallback=False)


@pytest.mark.asyncio
async def test_aembed_success():
    provider = MagicMock()
    provider.aembed = AsyncMock(return_value=[[3.0, 4.0]])
    with patch.object(provider_system, "get_provider", return_value=provider):
        result = await provider_system.aembed(
            "text", provider_type="lm_studio", fallback=False
        )
        assert result == [[3.0, 4.0]]
        provider.aembed.assert_called_once()


@pytest.mark.asyncio
async def test_aembed_error():
    provider = MagicMock()
    provider.aembed = AsyncMock(side_effect=ProviderError("boom"))
    with patch.object(provider_system, "get_provider", return_value=provider):
        with pytest.raises(ProviderError):
            await provider_system.aembed(
                "text", provider_type="lm_studio", fallback=False
            )
