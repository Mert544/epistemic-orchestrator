from app.engine.compressed_mode import CompressedModeEngine


def test_compressed_mode_reduces_depth_and_nodes():
    config = {
        "mode": "compressed",
        "max_depth": 5,
        "max_total_nodes": 50,
        "top_k_questions": 3,
    }
    engine = CompressedModeEngine(config)
    assert engine.mode == "compressed"
    assert engine.config["max_depth"] == 2
    assert engine.config["max_total_nodes"] == 10
    assert engine.config["top_k_questions"] == 1


def test_balanced_mode_keeps_original_values():
    config = {
        "mode": "balanced",
        "max_depth": 5,
        "max_total_nodes": 50,
        "top_k_questions": 3,
    }
    engine = CompressedModeEngine(config)
    assert engine.mode == "balanced"
    assert engine.config["max_depth"] == 5
    assert engine.config["max_total_nodes"] == 50
    assert engine.config["top_k_questions"] == 3


def test_compress_report_trims_deep_branches():
    config = {"mode": "compressed"}
    engine = CompressedModeEngine(config)
    report = {
        "objective": "test",
        "main_findings": ["a", "b", "c", "d", "e", "f"],
        "branch_map": {
            "x.a": "claim1",
            "x.a.b": "claim2",
            "x.a.b.c": "claim3",
            "x.a.b.c.d": "claim4",
        },
        "recommended_actions": ["1", "2", "3", "4", "5", "6"],
        "key_risks": ["r1", "r2", "r3", "r4"],
    }
    compressed = engine.compress_report(report)
    assert len(compressed["main_findings"]) <= 5
    assert len(compressed["branch_map"]) <= 8
    assert len(compressed["recommended_actions"]) <= 5
    assert len(compressed.get("key_risks", [])) <= 3


def test_compress_report_passes_through_when_not_compressed():
    config = {"mode": "balanced"}
    engine = CompressedModeEngine(config)
    report = {
        "objective": "test",
        "main_findings": ["a", "b", "c"],
        "branch_map": {"x.a": "claim1"},
    }
    compressed = engine.compress_report(report)
    assert compressed == report


def test_trim_branch_map_limits_depth():
    config = {"mode": "compressed"}
    engine = CompressedModeEngine(config)
    branch_map = {
        "x.a": "c1",
        "x.a.b": "c2",
        "x.a.b.c": "c3",
        "x.a.b.c.d": "c4",
    }
    trimmed = engine._trim_branch_map(branch_map)
    assert "x.a" in trimmed
    assert "x.a.b" in trimmed
    assert "x.a.b.c" not in trimmed
    assert "x.a.b.c.d" not in trimmed
