import pytest

from devsynth.feature_markers import (
    FeatureMarker,
    feature_complete_memory_system_integration,
    list_feature_markers,
)


@pytest.mark.fast
def test_feature_marker_enum_values():
    """Enum exposes identifiers for auditing.

    ReqID: FR-98"""

    assert FeatureMarker.EXCEPTIONS_FRAMEWORK.value == "exceptions_framework"
    assert FeatureMarker.FEATURE_MARKERS.value == "feature_markers"
    assert (
        FeatureMarker.COMPLETE_MEMORY_SYSTEM_INTEGRATION.value
        == "complete_memory_system_integration"
    )


@pytest.mark.fast
def test_list_feature_markers_contains_markers():
    """Listing returns all available markers.

    ReqID: FR-98"""

    markers = list_feature_markers()
    assert "exceptions_framework" in markers
    assert "feature_markers" in markers
    assert "complete_memory_system_integration" in markers
    assert callable(feature_complete_memory_system_integration)
