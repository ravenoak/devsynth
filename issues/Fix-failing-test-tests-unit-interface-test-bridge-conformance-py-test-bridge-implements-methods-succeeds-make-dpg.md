# Fix failing test tests/unit/interface/test_bridge_conformance.py::test_bridge_implements_methods_succeeds[_make_dpg]
Milestone: 0.1.0-alpha.1
Status: open

Priority: medium
Dependencies: None

## Progress
- Reproduced on 2025-08-16: AttributeError indicates missing dpg add_text.

## References
- [tests/unit/interface/test_bridge_conformance.py](../tests/unit/interface/test_bridge_conformance.py)
- [src/devsynth/interface/dpg_bridge.py](../src/devsynth/interface/dpg_bridge.py)
