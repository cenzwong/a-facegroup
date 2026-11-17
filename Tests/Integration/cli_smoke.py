#!/usr/bin/env python3
"""Run with the built executable and a licensed portrait; no network needed."""
import base64
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

binary, portrait = map(lambda p: Path(p).resolve(), sys.argv[1:3])
with tempfile.TemporaryDirectory(prefix="a-facegroup-integration-") as tmp:
    root = Path(tmp)
    photos = root / "photos"
    photos.mkdir()
    image = photos / "portrait.png"
    shutil.copyfile(portrait, image)
    original = hashlib.sha256(image.read_bytes()).digest()
    env = {**os.environ, "AFACEGROUP_HOME": str(root / "library")}
    def run(*args, success=True):
        result = subprocess.run([str(binary), *map(str, args), "--json"], env=env, capture_output=True, text=True, timeout=120)
        assert (result.returncode == 0) == success, (args, result.returncode, result.stderr)
        assert "Detected face:" not in result.stderr, result.stderr
        return json.loads(result.stdout)
    first = run("scan", photos)
    assert first["processed"] == 1 and not first["failures"], first
    second = run("scan", photos)
    assert second["skipped"] == 1, second
    # Add a second asset and a no-face image, then reopen and regroup.
    second_image = photos / "second.png"
    shutil.copyfile(portrait, second_image)
    no_face = photos / "blank.png"
    no_face.write_bytes(base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/a1sAAAAASUVORK5CYII="))
    added = run("scan", photos)
    assert added["processed"] == 2 and added["no_faces"] == 1, added
    people = run("people", "list")["people"]
    assert len(people) >= 1, people
    person = next(p for p in people if str(image) in p["paths"])
    assert person["face_count"] >= 1 and person["photo_count"] >= 1
    assert str(image) in run("people", "photos", person["id"])["photos"]
    manifest = (root / "library" / "manifest.json").read_bytes()
    found = run("identify", image)
    assert any(f.get("entity_id") == person["id"] for f in found["faces"]), found
    assert (root / "library" / "manifest.json").read_bytes() == manifest
    assert run("people", "list")["people"] == people
    destination = root / "export"
    preview = run("export", destination)
    assert not preview["applied"] and not destination.exists()
    assert any(i["source"] == str(image) for i in preview["items"])
    assert any(i["source"] == str(no_face) and "/No_Faces/" in i["destination"] for i in preview["items"])
    written = run("export", destination, "--apply")
    assert written["applied"] and all(Path(i["destination"]).is_file() for i in written["items"])
    links = run("export", root / "links", "--mode", "symlink", "--apply")
    assert all(Path(i["destination"]).is_symlink() for i in links["items"])
    broken = photos / "broken.jpg"
    broken.write_bytes(b"not an image")
    failed = run("scan", photos, success=False)
    assert len(failed["failures"]) == 1, failed
    assert run("people", "list")["people"], "A failed asset hid the successful gallery"
    assert hashlib.sha256(image.read_bytes()).digest() == original
    print("Native scan, repeat, reopen, identify and export checks passed")
