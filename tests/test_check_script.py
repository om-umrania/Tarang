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
            'if [ "$1" = "-e" ]; then exit "${NODE_VERSION_EXIT:-0}"; fi\n'
            'if [ "$1" = "--test" ]; then exit "${BRIDGE_TEST_EXIT:-0}"; fi\n'
        )
        stub.chmod(0o755)

    def run(*, bridge_exit=0, node_available=True, version_exit=0):
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
                "NODE_VERSION_EXIT": str(version_exit),
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
    assert calls[0].startswith("node|-e ")
    assert calls[1:] == [
        f"python3|-|{root}",
        f"node|--test bridge/filter.test.mjs|{root}",
        f"python3|-m pytest -q|{root}",
        f"git|diff --check|{root}",
    ]


def test_check_propagates_bridge_failure(check_runner):
    root, run = check_runner
    result, calls = run(bridge_exit=7)

    assert result.returncode == 7
    assert calls[0].startswith("node|-e ")
    assert calls[1:] == [
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


def test_check_rejects_unsupported_node(check_runner):
    _, run = check_runner
    result, calls = run(version_exit=1)
    assert result.returncode != 0
    assert "Node.js 22.13+" in result.stderr
    assert "unsupported" in result.stderr
    assert len(calls) == 1
    assert calls[0].startswith("node|-e ")


@pytest.mark.parametrize("version,supported", [
    ("18.20.8", False), ("20.19.0", False), ("22.12.0", False),
    ("22.13.0", True), ("22.22.0", True), ("24.0.0", True),
])
def test_node_minimum_version_boundary(version, supported):
    script = (Path(__file__).resolve().parents[1] / "scripts/check.sh").read_text()
    expression = script.split("if ! node -e '", 1)[1].split("'", 1)[0]
    result = subprocess.run([
        "node", "-e",
        f'Object.defineProperty(process.versions, "node", {{value: "{version}"}});' + expression,
    ], capture_output=True, text=True)
    assert result.returncode == (0 if supported else 1), result.stderr
