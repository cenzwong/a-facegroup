#!/usr/bin/env python3
"""Verify unmatched identification and group-photo export with a licensed two-face image."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

binary, fixture = (Path(p).resolve() for p in sys.argv[1:3])
with tempfile.TemporaryDirectory(prefix="a-facegroup-multiple-") as tmp:
    root = Path(tmp)
    photos = root / "photos"
    photos.mkdir()
    image = photos / "group.png"
    shutil.copyfile(fixture, image)
    original = hashlib.sha256(image.read_bytes()).digest()
    env = {**os.environ, "AFACEGROUP_HOME": str(root / "library")}
    def run(*args):
        result = subprocess.run([str(binary), *map(str, args), "--json"], env=env, capture_output=True, text=True, timeout=120, check=True)
        assert "Detected face:" not in result.stderr
        return json.loads(result.stdout)
    unidentified = run("identify", image)
    assert len(unidentified["faces"]) >= 2 and all(not face["matched"] for face in unidentified["faces"]), unidentified
    assert run("people", "list")["total_people"] == 0
    scanned = run("scan", photos)
    assert scanned["processed"] == 1 and not scanned["failures"], scanned
    people = run("people", "list")["people"]
    members = [p for p in people if str(image) in p["paths"]]
    assert len(members) >= 2, people
    destination = root / "export"
    preview = run("export", destination)
    entries = [item for item in preview["items"] if item["source"] == str(image)]
    assert len(entries) >= 2 and len({i["destination"] for i in entries}) == len(entries), preview
    assert not destination.exists()
    applied = run("export", destination, "--apply")
    assert all(Path(i["destination"]).read_bytes() == image.read_bytes() for i in applied["items"])
    assert hashlib.sha256(image.read_bytes()).digest() == original
    print("Unmatched identification and multi-person export checks passed")
