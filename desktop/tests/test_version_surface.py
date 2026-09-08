"""Product version and authorized-use surface stay honest."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from flipper69 import __release__, __version__
from flipper69.sync import import_sd
from flipper69.templates import apply_template


REPO = Path(__file__).resolve().parents[2]


def test_product_version_is_argus_veil():
    assert __version__ == "4.0.0"
    assert __release__ == "ARGUS VEIL"


def test_check_version_surface_script():
    script = REPO / "scripts" / "check_version_surface.py"
    proc = subprocess.run([sys.executable, str(script)], cwd=REPO, check=False)
    assert proc.returncode == 0


def test_import_receipts_stamp_toolkit_version(tmp_path: Path):
    vault = tmp_path / "ops"
    vault.mkdir()
    (vault / "operations").mkdir()
    result = import_sd(REPO / "examples" / "sd_card", vault)
    assert result["imported"] >= 1
    receipts = list((vault / "operations").glob("*/DESKTOP-RECEIPTS.jsonl"))
    assert receipts
    line = json.loads(receipts[0].read_text(encoding="utf-8").splitlines()[0])
    assert line["ver"] == __version__


def test_new_template_ops_are_v4(tmp_path: Path):
    vault = tmp_path / "ops"
    vault.mkdir()
    (vault / "operations").mkdir()
    path = apply_template(
        "survey-building",
        label="version-surface",
        ops_root=vault,
        acknowledge_auth=True,
    )
    op = json.loads((path / "OPERATION.json").read_text(encoding="utf-8"))
    assert op["schemaVersion"] == 4
    assert op["device"]["version"] == "4.0.0"
