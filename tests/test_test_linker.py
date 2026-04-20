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
    coverage = linker.analyze(critical_modules=["services/order_service.py", "app/router.py"])

    assert coverage.module_to_tests["app/router.py"] == ["tests/test_router.py"]
    assert coverage.module_to_tests["services/order_service.py"] == []
    assert "services/order_service.py" in coverage.critical_untested_modules
