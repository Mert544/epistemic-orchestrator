from pathlib import Path

from app.tools.test_linker import TestLinker


def test_test_linker_maps_modules_to_tests_and_critical_gaps(tmp_path: Path):
    (tmp_path / "app").mkdir()
    (tmp_path / "services").mkdir()
    (tmp_path / "tests").mkdir()

    (tmp_path / "app" / "router.py").write_text(
        "from services.order_service import OrderService\n\ndef handle():\n    return OrderService()\n",
        encoding="utf-8",
    )
    (tmp_path / "services" / "order_service.py").write_text(
        "class OrderService:\n    pass\n",
        encoding="utf-8",
    )
    (tmp_path / "tests" / "test_router.py").write_text(
        "from app.router import handle\n\ndef test_handle():\n    assert handle()\n",
        encoding="utf-8",
    )

    linker = TestLinker(tmp_path)
    # Normalize critical_modules to OS-native paths so cross-platform comparison works.
    coverage = linker.analyze(critical_modules=[str(Path("services/order_service.py")), str(Path("app/router.py"))])

    def _posix_dict(d: dict[str, list[str]]) -> dict[str, list[str]]:
        return {str(Path(k).as_posix()): [str(Path(v).as_posix()) for v in vals] for k, vals in d.items()}

    m2t = _posix_dict(coverage.module_to_tests)
    assert m2t["app/router.py"] == ["tests/test_router.py"]
    assert m2t["services/order_service.py"] == []
    assert "services/order_service.py" in [str(Path(p).as_posix()) for p in coverage.critical_untested_modules]
