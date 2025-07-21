import pytest
from datetime import datetime
from uuid import UUID
from devsynth.domain.models.wsde import WSDE


class TestWSDEModel:
    """Tests for the WSDEModel component.

ReqID: N/A"""

    def test_wsde_initialization_succeeds(self):
        """Test that wsde initialization succeeds.

ReqID: N/A"""
        wsde = WSDE()
        assert wsde.content == ''
        assert wsde.content_type == 'text'
        assert isinstance(wsde.metadata, dict)
        assert isinstance(wsde.created_at, datetime)
        assert isinstance(wsde.updated_at, datetime)
        assert wsde.created_at == wsde.updated_at
        try:
            UUID(wsde.id)
        except ValueError:
            pytest.fail('WSDE id is not a valid UUID')

    def test_wsde_with_custom_values_succeeds(self):
        """Test that wsde with custom values succeeds.

ReqID: N/A"""
        custom_metadata = {'author': 'Test User', 'version': '1.0'}
        custom_time = datetime.now()
        wsde = WSDE(id='custom-id', content='Test content', content_type=
            'code', metadata=custom_metadata, created_at=custom_time,
            updated_at=custom_time)
        assert wsde.id == 'custom-id'
        assert wsde.content == 'Test content'
        assert wsde.content_type == 'code'
        assert wsde.metadata == custom_metadata
        assert wsde.created_at == custom_time
        assert wsde.updated_at == custom_time
