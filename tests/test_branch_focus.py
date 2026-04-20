from pathlib import Path

from app.memory.persistent_memory import PersistentMemoryStore
from app.orchestrator import FractalResearchOrchestrator
from app.skills.decomposer import Decomposer
from app.skills.evidence_mapper import EvidenceMapper
from app.skills.synthesizer import Synthesizer
from app.skills.validator import Validator


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _build_demo_project(root: Path) -> None:
    _write(root / "app" / "main.py", "from app.api.router import handle_checkout\n\n\ndef main():\n    return handle_checkout({'user_id': 'u1', 'cart_total': 10.0, 'items': ['pen']})\n")
    _write(root / "app" / "api" / "router.py", "from app.config.settings import load_settings\nfrom app.services.order_service import OrderService\n\n\ndef handle_checkout(payload: dict) -> dict:\n    return OrderService(load_settings()).checkout(payload)\n")
    _write(root / "app" / "services" / "order_service.py", "from app.auth.token_service import TokenService\nfrom app.payments.gateway import PaymentGateway\n\n\nclass OrderService:\n    def __init__(self, settings: dict) -> None:\n        self.settings = settings\n        self.tokens = TokenService(settings)\n        self.gateway = PaymentGateway(settings)\n\n    def checkout(self, payload: dict) -> dict:\n        token = self.tokens.issue_checkout_token(payload['user_id'])\n        charge = self.gateway.charge(payload['cart_total'], token, self.settings['currency'])\n        return {'ok': True, 'charge_id': charge['charge_id']}\n")
    _write(root / "app" / "auth" / "token_service.py", "import hashlib\n\n\nclass TokenService:\n    def __init__(self, settings: dict) -> None:\n        self.secret = settings['jwt_secret']\n\n    def issue_checkout_token(self, user_id: str) -> str:\n        return hashlib.sha256(f'{user_id}:{self.secret}'.encode('utf-8')).hexdigest()\n")
    _write(root / "app" / "payments" / "gateway.py", "class PaymentGateway:\n    def __init__(self, settings: dict) -> None:\n        self.provider = settings['payment_provider']\n\n    def charge(self, amount: float, token: str, currency: str) -> dict:\n        return {'charge_id': f'{self.provider}-001', 'amount': amount, 'currency': currency, 'token': token}\n")
    _write(root / "app" / "config" / "settings.py", "def load_settings() -> dict:\n    return {'currency': 'USD', 'payment_provider': 'stripe-like', 'jwt_secret': 'demo-secret'}\n")
    _write(root / "tests" / "test_router.py", "from app.api.router import handle_checkout\n\n\ndef test_checkout_returns_success():\n    result = handle_checkout({'user_id': 'u1', 'cart_total': 10.0, 'items': ['pen']})\n    assert result['ok'] is True\n")
    _write(root / ".github" / "workflows" / "ci.yml", "name: ci\n")
    _write(root / "pyproject.toml", "[project]\nname = 'demo'\n")


def _make_orchestrator(project_root: Path) -> FractalResearchOrchestrator:
    return FractalResearchOrchestrator(
        config={
            'max_depth': 2,
            'max_total_nodes': 40,
            'top_k_questions': 2,
            'min_security': 0.8,
            'min_quality': 0.6,
            'min_novelty': 0.2,
        },
        decomposer=Decomposer(project_root=project_root),
        validator=Validator(evidence_mapper=EvidenceMapper(project_root=project_root)),
        synthesizer=Synthesizer(project_root=project_root),
        memory_store=PersistentMemoryStore(project_root=project_root),
    )


def test_focus_branch_runs_only_selected_fractal_subtree(tmp_path: Path):
    _build_demo_project(tmp_path)
    objective = 'Scan the target project, extract meaningful implementation claims, and continue with constitution-driven fractal questioning.'

    run1 = _make_orchestrator(tmp_path).run(objective)
    focus_branch = next(branch for branch in run1.branch_map if branch.count('.') >= 2)
    focus_claim = run1.branch_map[focus_branch]

    focused = _make_orchestrator(tmp_path).run(objective, focus_branch=focus_branch)

    assert focused.focus_branch == focus_branch
    assert focused.focus_claim == focus_claim
    assert focus_branch in focused.branch_map
    assert all(branch == focus_branch or branch.startswith(focus_branch + '.') for branch in focused.branch_map)
    assert focused.debug_stats['focus_branch_hits'] == 1
    assert focused.previous_run_count == 1


def test_focus_branch_miss_falls_back_to_full_scan(tmp_path: Path):
    _build_demo_project(tmp_path)
    objective = 'Scan the target project, extract meaningful implementation claims, and continue with constitution-driven fractal questioning.'

    run = _make_orchestrator(tmp_path).run(objective, focus_branch='x.z.z')

    assert run.focus_branch == 'x.z.z'
    assert run.focus_claim is None
    assert run.debug_stats['focus_branch_misses'] == 1
    assert len(run.branch_map) >= 6
