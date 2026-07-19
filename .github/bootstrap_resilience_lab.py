from __future__ import annotations

import base64
import io
import zipfile
from pathlib import Path


root = Path(__file__).resolve().parents[1]
parts = sorted((root / ".github").glob("bootstrap_payload.part*"))
if len(parts) != 11:
    raise SystemExit(f"expected 11 payload parts, found {len(parts)}")

encoded = "".join(part.read_text(encoding="utf-8") for part in parts)
archive = zipfile.ZipFile(io.BytesIO(base64.b64decode(encoded)))

for member in archive.infolist():
    target = (root / member.filename).resolve()
    if target != root and root not in target.parents:
        raise SystemExit(f"unsafe archive path: {member.filename}")

archive.extractall(root)

for part in parts:
    part.unlink()

Path(__file__).unlink()
workflow = root / ".github" / "workflows" / "bootstrap-resilience-lab.yml"
if workflow.exists():
    workflow.unlink()

print(f"extracted {len(archive.infolist())} Build Week files")
