# Apex Orchestrator — Agent Development Guide

## Product Identity

- **Name:** Apex Orchestrator
- **Tagline:** Agents for fractal codebase intelligence
- **Vision:** Branch-aware, memory-aware, supervised engineering agent evolving toward guarded autonomous coding

## Build & Test

```bash
# Setup
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .[dev]

# Run all tests
pytest

# Run specific test groups
pytest tests/test_semantic_patch_generator.py
pytest tests/test_retry_engine.py
pytest tests/test_git_pr_loop.py
pytest tests/test_token_telemetry.py
pytest tests/test_compressed_mode.py
pytest tests/test_llm_router.py

# Run the main orchestrator
python -m app.main

# Run with automation plans
export EPISTEMIC_TARGET_ROOT=/path/to/project
export EPISTEMIC_AUTOMATION_PLAN=project_scan
python -m app.main
```

## Architecture Decisions

### 1. No Mandatory External Dependencies
- LLM integration is **optional** via `llm.provider: none` (default)
- `openai` package is **not** in default dependencies
- All core features work with stdlib only

### 2. AST Before LLM
- Semantic patch generator tries AST transforms first
- Only falls back to draft/LLM if no safe transform applies
- This keeps the system deterministic and auditable

### 3. Token Budget Awareness
- Every run tracks token consumption
- Budget limit can be set in config (`token_budget_limit`)
- Exceeded budget stops expansion gracefully

### 4. Cross-Platform Path Handling
- Always use `Path.as_posix()` when asserting paths in tests
- Never assume `/` separator in assertions

## Coding Conventions

- **Imports:** `from __future__ import annotations` at top
- **Type hints:** Required for public APIs
- **Dataclasses:** Prefer over raw dicts for structured data
- **Tests:** Use `tmp_path` fixture, self-contained demo projects
- **Error handling:** Graceful degradation, never crash the orchestrator

## Configuration

Key config values in `config/default.yaml`:

```yaml
mode: balanced              # balanced | compressed
max_depth: 3
max_total_nodes: 20
top_k_questions: 2
token_budget_limit: 0       # 0 = unlimited

llm:
  provider: none            # none | openai | local
  api_key: ""
  base_url: "https://api.openai.com/v1"
  model: "gpt-4o-mini"
  max_tokens: 2048
  temperature: 0.2
```

## Safety Rules

1. Never make external API calls unless user explicitly configures `llm.provider`
2. Always use `expected_old_content` in patches
3. Never modify files outside project root
4. Sensitive edits require human review (blocked from auto-retry)
5. Max changed files default: 5 (configurable)

## Automation Plans

| Plan | Purpose |
|---|---|
| `project_scan` | Full repo analysis |
| `focused_branch` | Deepen one branch |
| `verify_project` | Profile + test run |
| `semantic_patch_loop` | Research → semantic patch → verify → retry |
| `semantic_apply_loop` | Clone → semantic patch → verify → retry |
| `git_pr_loop` | Diff → commit → PR summary |
| `full_autonomous_loop` | End-to-end: research → patch → verify → retry → commit → PR → telemetry |
| `telemetry_only` | Research + token report |

## Adding a New Skill

1. Implement skill function in `app/automation/skills.py`
2. Register in `build_default_registry()`
3. Add plan step in `app/automation/plans.py` if needed
4. Write test in `tests/test_<feature>.py`
5. Update this guide
