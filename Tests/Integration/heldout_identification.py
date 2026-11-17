#!/usr/bin/env python3
"""Check identification against separate labeled portraits supplied by the caller."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

if len(sys.argv) not in (5, 6):
    raise SystemExit("Usage: heldout_identification.py <binary> <indexed> <known> <unknown> [mixed-group]")
binary, indexed, known, unknown = (Path(p).resolve() for p in sys.argv[1:5])
mixed_group = Path(sys.argv[5]).resolve() if len(sys.argv) == 6 else None
with tempfile.TemporaryDirectory(prefix="a-facegroup-heldout-") as tmp:
    root = Path(tmp)
    photos = root / "photos"
    photos.mkdir()
    shutil.copyfile(indexed, photos / indexed.name)
    env = {**os.environ, "AFACEGROUP_HOME": str(root / "library")}
    def run(*args):
        result = subprocess.run([str(binary), *map(str, args), "--json"], env=env, capture_output=True, text=True, timeout=120, check=True)
        return json.loads(result.stdout)
    assert run("scan", photos)["processed"] == 1
    people = run("people", "list")["people"]
    assert len(people) == 1, people
    manifest_path = root / "library" / "manifest.json"
    before = manifest_path.read_bytes()
    known_faces = run("identify", known)["faces"]
    unknown_faces = run("identify", unknown)["faces"]
    assert len(known_faces) == 1 and known_faces[0].get("entity_id") == people[0]["id"], known_faces
    assert len(unknown_faces) == 1 and not unknown_faces[0]["matched"], unknown_faces
    if mixed_group is not None:
        mixed_faces = run("identify", mixed_group)["faces"]
        assert len(mixed_faces) == 2, mixed_faces
        assert sum(face.get("entity_id") == people[0]["id"] for face in mixed_faces) == 1, mixed_faces
        assert sum(not face["matched"] for face in mixed_faces) == 1, mixed_faces
    assert manifest_path.read_bytes() == before
    assert run("people", "list")["people"] == people
    print("Held-out known and unknown identification checks passed" + (", including mixed group" if mixed_group else ""))
