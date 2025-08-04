from devsynth.interface.mvuu_dashboard import load_traceability


def test_load_traceability_reads_default_file():
    data = load_traceability()
    assert "MVUU-0001" in data
    entry = data["MVUU-0001"]
    assert entry.get("mvuu") is True
