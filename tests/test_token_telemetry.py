from pathlib import Path

from app.execution.token_telemetry import TokenBudgetSnapshot, TokenTelemetry


def test_telemetry_records_analysis_and_response():
    telemetry = TokenTelemetry()
    telemetry.record_analysis("scan project files")
    telemetry.record_response("generated report text")
    telemetry.record_memory("memory json")

    snap = telemetry.snapshot()
    assert snap.analysis_tokens > 0
    assert snap.response_tokens > 0
    assert snap.memory_tokens > 0
    assert snap.total_tokens > 0
    assert not snap.exceeded


def test_telemetry_budget_enforcement():
    telemetry = TokenTelemetry(budget_limit=10)
    telemetry.record_analysis("x" * 100)  # 100 chars -> 25 tokens

    snap = telemetry.snapshot()
    assert snap.exceeded is True
    assert telemetry.check_budget() is False


def test_telemetry_budget_unlimited_when_zero():
    telemetry = TokenTelemetry(budget_limit=0)
    telemetry.record_analysis("x" * 10000)
    assert telemetry.check_budget() is True


def test_telemetry_skill_call_tracking():
    telemetry = TokenTelemetry()
    telemetry.record_skill_call("run_research", input_text="objective", output_text="report")
    telemetry.record_skill_call("plan_tasks", input_text="report", output_text="tasks")

    report = telemetry.export_run_report(run_id="r-1")
    assert report["run_id"] == "r-1"
    assert len(report["skill_calls"]) == 2


def test_telemetry_llm_call_tracking():
    telemetry = TokenTelemetry(model="gpt-4o-mini")
    telemetry.record_llm_call(input_tokens=100, output_tokens=50, model="gpt-4o-mini")

    snap = telemetry.snapshot()
    assert snap.llm_input_tokens == 100
    assert snap.llm_output_tokens == 50
    assert snap.cost_usd > 0


def test_telemetry_cost_per_outcome():
    telemetry = TokenTelemetry(model="gpt-4o-mini")
    telemetry.record_llm_call(input_tokens=1000, output_tokens=500)
    cost = telemetry.cost_per_outcome(outcome_count=2)
    assert cost > 0


def test_snapshot_to_dict():
    snap = TokenBudgetSnapshot(
        analysis_tokens=10,
        response_tokens=20,
        memory_tokens=5,
        total_tokens=35,
        limit=100,
        exceeded=False,
    )
    d = snap.to_dict()
    assert d["analysis_tokens"] == 10
    assert d["total_tokens"] == 35
    assert d["exceeded"] is False


def test_telemetry_records_char_count_directly():
    telemetry = TokenTelemetry()
    telemetry.record_analysis(char_count=40)
    telemetry.record_response(char_count=40)
    snap = telemetry.snapshot()
    assert snap.analysis_tokens == 10
    assert snap.response_tokens == 10
