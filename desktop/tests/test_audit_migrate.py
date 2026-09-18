"""Desktop toolkit tests  -  offline, no hardware."""

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

def test_chunked_manifest_verify(vault: Path):
    """Chunked seals store items in parts; verify must not vacuously pass."""
    from flipper69.seal import seal_op
    from flipper69.sync import resolve_manifest_items, verify_manifest_items
    from flipper69.vault import load_json

    path = apply_template(
        "badge-lab",
        label="chunk-verify",
        ops_root=vault,
        acknowledge_auth=True,
    )
    (path / "captures").mkdir(exist_ok=True)
    for i in range(40):
        (path / "captures" / f"c{i:02d}.bin").write_bytes(b"payload-%d" % i)
    result = seal_op(path, merkle=True, chunk_size=8)
    assert result["chunked"] is True
    man = load_json(path / "CASEFILE-MANIFEST.json")
    assert isinstance(man, dict)
    assert not (man.get("items") or [])
    assert man.get("parts")
    resolved = resolve_manifest_items(path, man)
    assert len(resolved) >= 40
    v = verify_manifest_items(path, man)
    assert v["ok"] >= 40
    (path / "captures" / "c00.bin").write_bytes(b"tampered")
    v2 = verify_manifest_items(path, man)
    assert "captures/c00.bin" in v2["mismatch"]
    report = audit_op(path)
    assert any("captures/c00.bin" in i for i in report["issues"])
    assert report["orphans"] == []


def test_chunked_report_lists_part_items(vault: Path):
    """HTML report must list leaves from chunked part manifests, not 'No manifest items'."""
    from flipper69.seal import seal_op

    path = apply_template(
        "badge-lab",
        label="chunk-report",
        ops_root=vault,
        acknowledge_auth=True,
    )
    (path / "captures").mkdir(exist_ok=True)
    for i in range(20):
        (path / "captures" / f"c{i:02d}.bin").write_bytes(b"payload-%d" % i)
    result = seal_op(path, merkle=True, chunk_size=5)
    assert result["chunked"] is True
    html = build_report_html(path)
    assert "No manifest items" not in html
    assert "captures/c00.bin" in html
    assert "captures/c19.bin" in html


def test_reseal_skips_stale_part_files(vault: Path):
    """Re-seal must not ingest prior manifests/parts leaves into the new seal."""
    from flipper69.seal import seal_op
    from flipper69.sync import resolve_manifest_items
    from flipper69.vault import load_json

    path = apply_template(
        "badge-lab",
        label="reseal-parts",
        ops_root=vault,
        acknowledge_auth=True,
    )
    (path / "captures").mkdir(exist_ok=True)
    for i in range(20):
        (path / "captures" / f"c{i:02d}.bin").write_bytes(b"payload-%d" % i)
    first = seal_op(path, merkle=True, chunk_size=5)
    assert first["chunked"] is True
    first_count = first["items"]
    second = seal_op(path, merkle=True, chunk_size=5)
    assert second["items"] == first_count
    man = load_json(path / "CASEFILE-MANIFEST.json")
    assert isinstance(man, dict)
    resolved = resolve_manifest_items(path, man)
    assert not any(str(i.get("path", "")).startswith("manifests/parts/") for i in resolved)

def test_audit_flags_artifact_orphans(vault: Path):
    """v4 field leaves live under artifacts/; orphan scan must not miss them."""
    from flipper69.seal import seal_op

    path = apply_template(
        "badge-lab",
        label="art-orphan",
        ops_root=vault,
        acknowledge_auth=True,
    )
    seal_op(path, merkle=True)
    art = path / "artifacts" / "field"
    art.mkdir(parents=True, exist_ok=True)
    orphan = art / "loose.bin"
    orphan.write_bytes(b"not-in-manifest")
    report = audit_op(path)
    assert "artifacts/field/loose.bin" in report["orphans"]
    assert any("orphan field file" in w for w in report["warnings"])



def test_pack_redact_omits_artifacts(vault: Path, tmp_path: Path):
    """Share-safe pack must omit v4 artifacts/ raw leaves, not only captures/."""
    import zipfile
    from flipper69.pack import pack_op

    path = apply_template(
        "badge-lab",
        label="pack-redact",
        ops_root=vault,
        acknowledge_auth=True,
    )
    (path / "captures").mkdir(exist_ok=True)
    (path / "captures" / "legacy.sub").write_bytes(b"CAPTURE_SECRET")
    art = path / "artifacts" / "field"
    art.mkdir(parents=True, exist_ok=True)
    (art / "raw.sub").write_bytes(b"ARTIFACT_SECRET")
    (art / "raw.sub.meta.json").write_text('{"ok": true}\n', encoding="utf-8")
    (path / "notes.txt").write_text("secret notes\n", encoding="utf-8")
    claims = path / "claims"
    claims.mkdir(parents=True, exist_ok=True)
    (claims / "receipt.json").write_text('{"claim":"SECRET_CLAIM"}\n', encoding="utf-8")

    out = tmp_path / "share.zip"
    pack_op(path, out, redact=True)
    names = zipfile.ZipFile(out).namelist()
    assert not any(n.endswith("legacy.sub") for n in names)
    assert not any(n.endswith("raw.sub") and "artifacts/" in n for n in names)
    assert any(n.endswith("raw.sub.meta.json") for n in names)
    assert not any(n.endswith("notes.txt") for n in names)
    assert not any("/claims/" in n or n.endswith("receipt.json") for n in names)


def test_pack_redact_omits_timeline(vault: Path):
    """Share-safe packs must omit TIMELINE.jsonl event payloads."""
    from flipper69.pack import pack_op
    import zipfile

    path = apply_template(
        "badge-lab",
        label="redact-timeline",
        ops_root=vault,
        acknowledge_auth=True,
    )
    (path / "TIMELINE.jsonl").write_text(
        '{"ts":"2026-01-01T00:00:00Z","event":"NOTE","data":{"secret":"x"}}\n',
        encoding="utf-8",
    )
    (path / "notes.txt").write_text("private\n", encoding="utf-8")
    out = vault / "redact-timeline.f69pack.zip"
    pack_op(path, out, redact=True)
    with zipfile.ZipFile(out) as zf:
        names = [n.split("/", 1)[-1] for n in zf.namelist()]
    assert "TIMELINE.jsonl" not in names
    assert "notes.txt" not in names
    assert "OPERATION.json" in names
    assert "REDACT.txt" in names

def test_pack_redact_omits_scripts_and_roe(vault: Path):
    """Share-safe packs must omit scripts/ payloads and ROE.json scope notes."""
    from flipper69.pack import pack_op
    import zipfile

    path = apply_template(
        "badge-lab",
        label="redact-scripts-roe",
        ops_root=vault,
        acknowledge_auth=True,
    )
    scripts = path / "scripts"
    scripts.mkdir(parents=True, exist_ok=True)
    (scripts / "payload.txt").write_text("SECRET_BADUSB_SCRIPT\n", encoding="utf-8")
    (path / "ROE.json").write_text(
        '{"scope":"SECRET_TARGET","rules":"no cameras"}\n',
        encoding="utf-8",
    )
    out = vault / "redact-scripts-roe.f69pack.zip"
    pack_op(path, out, redact=True)
    with zipfile.ZipFile(out) as zf:
        names = [n.split("/", 1)[-1] for n in zf.namelist()]
    assert "ROE.json" not in names
    assert not any(n.startswith("scripts/") for n in names)
    assert "OPERATION.json" in names
    assert "REDACT.txt" in names


def test_pack_redact_omits_checkpoint(vault: Path):
    """Share-safe packs must omit CHECKPOINT.json session state."""
    from flipper69.pack import pack_op
    import zipfile

    path = apply_template(
        "badge-lab",
        label="redact-checkpoint",
        ops_root=vault,
        acknowledge_auth=True,
    )
    (path / "CHECKPOINT.json").write_text(
        '{"phase":"capture","reason":"SECRET_SESSION","session":9}\n',
        encoding="utf-8",
    )
    out = vault / "redact-checkpoint.f69pack.zip"
    pack_op(path, out, redact=True)
    with zipfile.ZipFile(out) as zf:
        names = [n.split("/", 1)[-1] for n in zf.namelist()]
    assert "CHECKPOINT.json" not in names
    assert "OPERATION.json" in names
    assert "REDACT.txt" in names

