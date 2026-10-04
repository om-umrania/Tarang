"""Catch the missing static homepage that previously passed Vercel's build."""

import json
from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    "fault",
    [
        None,
        "root_output",
        "missing_homepage",
        "missing_asset",
        "missing_dashboard_route",
    ],
)
def test_vercel_output_contract(tmp_path, fault):
    shutil.copytree(ROOT / "docs", tmp_path / "docs")
    config = json.loads((ROOT / "vercel.json").read_text())
    if fault == "root_output":
        config["outputDirectory"] = "."
    elif fault == "missing_homepage":
        (tmp_path / "docs/index.html").unlink()
    elif fault == "missing_asset":
        (tmp_path / "docs/dashboard.js").unlink()
    elif fault == "missing_dashboard_route":
        config["rewrites"] = [
            r for r in config["rewrites"] if r["source"] != "/dashboard"
        ]
    (tmp_path / "vercel.json").write_text(json.dumps(config))
    result = subprocess.run(
        ["node", str(ROOT / "scripts/check_site.mjs")],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert result.returncode == (1 if fault else 0), result.stdout + result.stderr
    assert config["buildCommand"] == "node scripts/check_site.mjs"
