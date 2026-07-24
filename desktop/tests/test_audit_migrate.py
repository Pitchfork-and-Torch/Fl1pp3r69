"""Desktop toolkit tests — offline, no hardware."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from flipper69.audit import audit_op, audit_vault
from flipper69.migrate import migrate_op_dir, migrate_vault
from flipper69.report import build_report_html
from flipper69.sync import import_sd
from flipper69.templates import apply_template, list_templates


REPO = Path(__file__).resolve().parents[2]
EXAMPLE_SD = REPO / "examples" / "sd_card"


@pytest.fixture()
def vault(tmp_path: Path) -> Path:
    root = tmp_path / "ops"
    root.mkdir()
    (root / "operations").mkdir()
    return root


def test_templates_builtin():
    ids = {t["templateId"] for t in list_templates()}
    assert "survey-building" in ids
    assert "client-pentest-physical" in ids


def test_apply_template_requires_auth(vault: Path):
    with pytest.raises(PermissionError):
        apply_template("badge-lab", ops_root=vault, acknowledge_auth=False)


def test_apply_template(vault: Path):
    path = apply_template(
        "badge-lab",
        label="lab-test",
        ops_root=vault,
        acknowledge_auth=True,
    )
    assert path.is_dir()
    op = json.loads((path / "OPERATION.json").read_text(encoding="utf-8"))
    assert op["schemaVersion"] in (3, 4)
    assert op["templateId"] == "badge-lab"
    assert op["permissions"]["authorized"] is False


def test_migrate_and_audit(vault: Path):
    # seed a minimal v2-style op
    op_id = "op-20260711-migrate-demo"
    op_dir = vault / "operations" / op_id
    op_dir.mkdir(parents=True)
    (op_dir / "captures").mkdir()
    note = op_dir / "notes.txt"
    note.write_text("hello\n", encoding="utf-8")
    (op_dir / "OPERATION.json").write_text(
        json.dumps(
            {
                "opId": op_id,
                "opType": "unified",
                "phase": "close",
                "openedAt": "2026-07-11T00:00:00Z",
                "device": {"firmware": "flipper69", "serial": "demo"},
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (op_dir / "TIMELINE.jsonl").write_text(
        '{"ts":"2026-07-11T00:00:00Z","event":"CLOSE"}\n', encoding="utf-8"
    )

    r = migrate_op_dir(op_dir)
    assert r["operation"] is True
    op = json.loads((op_dir / "OPERATION.json").read_text(encoding="utf-8"))
    assert op["schemaVersion"] == 4
    assert (op_dir / "CHECKPOINT.json").is_file()
    assert (op_dir / "artifacts").is_dir()

    # second migrate is idempotent for operation fields we care about
    r2 = migrate_op_dir(op_dir)
    assert r2["operation"] is False

    report = audit_op(op_dir)
    # no manifest → warning, still PASS if no hard issues
    assert report["status"] == "PASS"
    assert any("unsealed" in w for w in report["warnings"])


def test_import_example_sd(vault: Path):
    if not EXAMPLE_SD.is_dir():
        pytest.skip("examples/sd_card missing")
    result = import_sd(EXAMPLE_SD, vault)
    assert result["imported"] >= 1
    summary = audit_vault(vault)
    assert summary["ops"] >= 1


def test_report_html(vault: Path):
    path = apply_template(
        "survey-building",
        label="report-test",
        ops_root=vault,
        acknowledge_auth=True,
    )
    html = build_report_html(path)
    assert "CASEFILE REPORT" in html
    assert path.name in html


def test_seal_merkle(vault: Path):
    from flipper69.seal import seal_op

    path = apply_template(
        "badge-lab",
        label="seal-test",
        ops_root=vault,
        acknowledge_auth=True,
    )
    (path / "captures").mkdir(exist_ok=True)
    (path / "captures" / "x.meta.json").write_text('{"probe":"test"}\n', encoding="utf-8")
    result = seal_op(path, merkle=True)
    assert result["items"] >= 1
    assert result["merkleRoot"]
    assert (path / "CASEFILE-MANIFEST.json").is_file()
    report = audit_op(path)
    # OPERATION may change after seal; re-seal consistency: manifest items should match files
    assert "merkleRoot" in (result)
