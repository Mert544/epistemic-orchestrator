from app.skills.safety.enhanced_safety_governor import EnhancedSafetyGovernor


def test_governor_allows_safe_patch():
    governor = EnhancedSafetyGovernor()
    result = governor.evaluate(["app/main.py", "tests/test_main.py"])
    assert result.ok is True
    assert result.violations == []
    assert result.requires_human_review is False


def test_governor_blocks_too_many_files():
    governor = EnhancedSafetyGovernor({"safety": {"max_changed_files": 2}})
    result = governor.evaluate(["a.py", "b.py", "c.py"])
    assert result.ok is False
    assert any("Too many changed files" in v for v in result.violations)


def test_governor_blocks_restricted_paths():
    governor = EnhancedSafetyGovernor()
    result = governor.evaluate(["app/main.py", ".env.production"])
    assert result.ok is False
    assert any("Restricted path touched" in v for v in result.violations)
    assert result.requires_human_review is True


def test_governor_blocks_line_diff_too_large():
    governor = EnhancedSafetyGovernor({"safety": {"max_line_diff_per_file": 10}})
    result = governor.evaluate(["app/main.py"], {"app/main.py": 25})
    assert result.ok is False
    assert any("Line diff too large" in v for v in result.violations)


def test_human_required_policy():
    governor = EnhancedSafetyGovernor({"safety": {"review_policy": "human_required"}})
    result = governor.evaluate(["app/main.py"])
    assert result.ok is False
    assert result.requires_human_review is True
    assert any("human approval" in v for v in result.violations)


def test_custom_restricted_paths():
    governor = EnhancedSafetyGovernor({"safety": {"restricted_paths": ["*.vault"]}})
    result = governor.evaluate(["secrets.vault", "app/main.py"])
    assert result.ok is False
    assert any("secrets.vault" in v for v in result.violations)


def test_governor_result_to_dict():
    result = EnhancedSafetyGovernor().evaluate(["a.py"])
    d = result.to_dict()
    assert "ok" in d
    assert "violations" in d
    assert "policy" in d
    assert "requires_human_review" in d


def test_is_restricted_glob_matching():
    governor = EnhancedSafetyGovernor()
    assert governor._is_restricted(".env", [".env*"]) is True
    assert governor._is_restricted(".env.local", [".env*"]) is True
    assert governor._is_restricted("secrets/data.json", ["secrets/**"]) is True
    assert governor._is_restricted("app/main.py", ["secrets/**"]) is False
