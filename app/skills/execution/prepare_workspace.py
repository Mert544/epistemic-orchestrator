from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.runtime.workspace import WorkspaceManager


@dataclass
class PrepareWorkspaceResult:
    ok: bool
    workspace_root: str
    project_dir: str
    repo_name: str | None = None
    error: str | None = None


class PrepareWorkspaceSkill:
    def __init__(self, workspace_manager: WorkspaceManager | None = None) -> None:
        self.workspace_manager = workspace_manager or WorkspaceManager()

    def run(self, repo_url: str | None = None, project_root: str | Path | None = None) -> PrepareWorkspaceResult:
        try:
            if project_root is not None:
                root = self.workspace_manager.ensure_project_root(project_root)
                return PrepareWorkspaceResult(
                    ok=True,
                    workspace_root=str(root),
                    project_dir=str(root),
                    repo_name=root.name,
                )

            repo_name = self.workspace_manager.infer_repo_name(repo_url or "project")
            workspace = self.workspace_manager.create(repo_name=repo_name)
            return PrepareWorkspaceResult(
                ok=True,
                workspace_root=str(workspace.root),
                project_dir=str(workspace.project_dir),
                repo_name=repo_name,
            )
        except Exception as exc:
            return PrepareWorkspaceResult(
                ok=False,
                workspace_root="",
                project_dir="",
                error=str(exc),
            )
