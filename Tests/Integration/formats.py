#!/usr/bin/env python3
"""Check PNG, JPEG, and HEIC ingestion using a caller-supplied licensed portrait."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

binary, portrait = (Path(p).resolve() for p in sys.argv[1:3])
with tempfile.TemporaryDirectory(prefix="a-facegroup-formats-") as tmp:
    root = Path(tmp)
    photos = root / "photos"
    photos.mkdir()
    shutil.copyfile(portrait, photos / "portrait.png")
    for fmt, suffix in (("jpeg", "jpg"), ("heic", "heic")):
        subprocess.run(["sips", "-s", "format", fmt, str(portrait), "--out", str(photos / f"portrait.{suffix}")], capture_output=True, text=True, timeout=120, check=True)
    env = {**os.environ, "AFACEGROUP_HOME": str(root / "library")}
    def run(*args):
        result = subprocess.run([str(binary), *map(str, args), "--json"], env=env, capture_output=True, text=True, timeout=120, check=True)
        return json.loads(result.stdout)
    scanned = run("scan", photos)
    assert scanned["processed"] == 3 and not scanned["failures"] and not scanned["no_faces"], scanned
    paths = {path for person in run("people", "list")["people"] for path in person["paths"]}
    assert paths == {str(photos / f"portrait.{ext}") for ext in ("png", "jpg", "heic")}, paths
    print("PNG, JPEG, and HEIC face ingestion checks passed")
