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
    missing = subprocess.run([str(binary), "--json"], env=env, capture_output=True, text=True, timeout=120)
    assert missing.returncode != 0 and not missing.stdout and "Missing command" in missing.stderr
    empty = root / "empty"
    empty.mkdir()
    empty_result = run("scan", empty)
    assert empty_result["processed"] == 0 and empty_result["skipped"] == 0 and not empty_result["failures"], empty_result
    (empty / "ignored.txt").write_text("not an image")
    unsupported = run("scan", empty)
    assert unsupported["processed"] == 0 and not unsupported["failures"], unsupported
    first = run("scan", photos)
    assert first["processed"] == 1 and not first["failures"], first
    second = run("scan", photos)
    assert second["skipped"] == 1, second
    manifest_path = root / "library" / "manifest.json"
    def read_manifest():
        return json.loads(manifest_path.read_text())
    asset_id = read_manifest()["assets"][0]["id"]
    # A separate partial scan must not remove previously indexed photos.
    assert run("scan", empty)["processed"] == 0
    assert len(read_manifest()["assets"]) == 1 and read_manifest()["assets"][0]["id"] == asset_id
    # Replacing an existing photo must update its original asset, not add a new one.
    image.write_bytes(image.read_bytes() + b"\n")
    stale_export = subprocess.run([str(binary), "export", str(root / "stale-export"), "--apply", "--json"], env=env, capture_output=True, text=True, timeout=120)
    assert stale_export.returncode != 0 and not (root / "stale-export").exists(), stale_export
    changed = run("scan", photos)
    assert changed["processed"] == 1 and len(read_manifest()["assets"]) == 1, changed
    assert read_manifest()["assets"][0]["id"] == asset_id
    forced = run("scan", photos, "--force")
    assert forced["processed"] == 1 and read_manifest()["assets"][0]["id"] == asset_id
    # Simulate an interrupted submission after its pending marker was saved.
    state = read_manifest()
    state["assets"][0]["pending"] = True
    manifest_path.write_text(json.dumps(state))
    retried = run("scan", photos)
    assert retried["processed"] == 1 and read_manifest()["assets"][0]["id"] == asset_id
    original = hashlib.sha256(image.read_bytes()).digest()
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
    text_list = subprocess.run([str(binary), "people", "list"], env=env, capture_output=True, text=True, timeout=120, check=True)
    assert person["id"] in text_list.stdout and "faces:" in text_list.stdout
    text_photos = subprocess.run([str(binary), "people", "photos", person["id"]], env=env, capture_output=True, text=True, timeout=120, check=True)
    assert str(image) in text_photos.stdout
    quiet = subprocess.run([str(binary), "people", "list", "--quiet"], env=env, capture_output=True, text=True, timeout=120, check=True)
    assert not quiet.stdout
    manifest = (root / "library" / "manifest.json").read_bytes()
    found = run("identify", image)
    assert any(f.get("entity_id") == person["id"] for f in found["faces"]), found
    assert (root / "library" / "manifest.json").read_bytes() == manifest
    assert run("people", "list")["people"] == people
    destination = root / "export"
    preview = run("export", destination)
    assert not preview["applied"] and not destination.exists()
    text_preview = subprocess.run([str(binary), "export", str(destination)], env=env, capture_output=True, text=True, timeout=120, check=True)
    assert "Preview:" in text_preview.stdout and str(image) in text_preview.stdout and not destination.exists()
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
    pending = next(a for a in read_manifest()["assets"] if a["path"] == str(broken))
    assert pending["pending"] is True
    # Repair the failed image and ensure the pending identifier is reused.
    shutil.copyfile(portrait, broken)
    repaired = run("scan", photos)
    assert repaired["processed"] == 1 and not repaired["failures"], repaired
    assert next(a for a in read_manifest()["assets"] if a["path"] == str(broken))["id"] == pending["id"]
    assert hashlib.sha256(image.read_bytes()).digest() == original
    print("Native scan, repeat, reopen, identify and export checks passed")
