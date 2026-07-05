"""GitHub Actions workflow contract tests.

These tests are deliberately text-level. They guard the operational simplicity
contract: the workflow must run the same lockfile that meta hashes, verify
invariants before snapshot creation, and only write canonical snapshots on main.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _wf(name: str) -> str:
    return (ROOT / ".github" / "workflows" / name).read_text(encoding="utf-8")


def test_workflows_install_from_lock_not_floating_requirements():
    for name in ("ci.yml", "collect_c_us.yml", "healthcheck.yml"):
        text = _wf(name)
        assert "pip install -r requirements.lock" in text
        assert "pip install -r requirements.txt" not in text


def test_collect_runs_tests_before_writing_snapshot_and_avoids_rebase():
    text = _wf("collect_c_us.yml")
    assert "if: github.ref_name == 'main'" in text
    assert "git pull --ff-only" in text
    assert "git pull --rebase" not in text
    assert text.index("python -m pytest -q") < text.index("python run_snapshot.py")
    assert "git push origin HEAD:${GITHUB_REF_NAME}" in text


def test_healthcheck_is_main_only_and_lock_based():
    text = _wf("healthcheck.yml")
    assert "if: github.ref_name == 'main'" in text
    assert "pip install -r requirements.lock" in text
