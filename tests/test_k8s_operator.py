from __future__ import annotations

import pytest

from app.k8s.operator import ApexOperator, ApexRunResource, ApexRunSpec, ApexRunStatus


class TestApexOperator:
    def test_add_and_get(self):
        op = ApexOperator()
        res = ApexRunResource(
            name="scan-1", namespace="default",
            spec=ApexRunSpec(target_repo="https://github.com/x/y", goal="security audit"),
        )
        op.add_resource(res)
        got = op.get_resource("default", "scan-1")
        assert got is not None
        assert got.spec.goal == "security audit"

    def test_reconcile(self):
        op = ApexOperator()
        res = ApexRunResource(
            name="scan-1", namespace="default",
            spec=ApexRunSpec(target_repo="https://github.com/x/y", goal="security audit", mode="report"),
        )
        op.add_resource(res)
        results = op.reconcile_all()
        assert len(results) == 1
        assert results[0]["result"]["ok"] is True
        assert res.status.phase == "Succeeded"

    def test_manifest(self):
        op = ApexOperator()
        res = ApexRunResource(
            name="scan-1", namespace="default",
            spec=ApexRunSpec(target_repo="https://github.com/x/y"),
        )
        manifest = op.to_manifest(res)
        assert manifest["apiVersion"] == "apex.io/v1"
        assert manifest["kind"] == "ApexRun"
        assert manifest["spec"]["targetRepo"] == "https://github.com/x/y"
