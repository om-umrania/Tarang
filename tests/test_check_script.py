import os
from pathlib import Path
import shutil
import subprocess

import pytest


@pytest.fixture
def check_runner(tmp_path):
    """Exercise the aggregate runner without recursively invoking pytest."""
    root = tmp_path / "repository with spaces"
    scripts = root / "scripts"
    scripts.mkdir(parents=True)
    script = scripts / "check.sh"
    shutil.copyfile(Path(__file__).resolve().parents[1] / "scripts/check.sh", script)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "dirname").symlink_to(shutil.which("dirname"))
    log = tmp_path / "commands.log"
    for command in ("python3", "node", "git"):
        stub = bin_dir / command
        stub.write_text(
            "#!/bin/sh\n"
            f'printf "%s|%s|%s\\n" "{command}" "$*" "$PWD" >> "$CHECK_LOG"\n'
            'if [ "$1" = "--test" ]; then exit "${BRIDGE_TEST_EXIT:-0}"; fi\n'
        )
        stub.chmod(0o755)

    def run(*, bridge_exit=0, node_available=True):
        if not node_available:
            (bin_dir / "node").unlink()
        result = subprocess.run(
            [shutil.which("bash"), str(script)],
            cwd=tmp_path,
            env={
                **os.environ,
                "PATH": str(bin_dir),
                "CHECK_LOG": str(log),
                "BRIDGE_TEST_EXIT": str(bridge_exit),
            },
            capture_output=True,
            text=True,
        )
        calls = log.read_text().splitlines() if log.exists() else []
        return result, calls

    return root, run


def test_check_runs_bridge_tests_from_repository_root(check_runner):
    root, run = check_runner
    result, calls = run()

    assert result.returncode == 0, result.stderr
    assert calls == [
        f"python3|-|{root}",
        f"node|--test bridge/filter.test.mjs|{root}",
        f"python3|-m pytest -q|{root}",
        f"git|diff --check|{root}",
    ]


def test_check_propagates_bridge_failure(check_runner):
    root, run = check_runner
    result, calls = run(bridge_exit=7)

    assert result.returncode == 7
    assert calls == [
        f"python3|-|{root}",
        f"node|--test bridge/filter.test.mjs|{root}",
    ]


def test_check_explains_missing_node(check_runner):
    _, run = check_runner
    result, calls = run(node_available=False)

    assert result.returncode != 0
    assert "Node.js 22.13+" in result.stderr
    assert "PATH" in result.stderr
    assert calls == []
