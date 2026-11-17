#!/usr/bin/env python3
"""Test explicit recovery of pending assets without modifying source photos."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

binary, portrait = (Path(p).resolve() for p in sys.argv[1:3])
with tempfile.TemporaryDirectory(prefix="a-facegroup-recovery-") as tmp:
    root = Path(tmp)
    photos = root / "photos"
    photos.mkdir()
    image = photos / "portrait.png"
    shutil.copyfile(portrait, image)
    original = hashlib.sha256(image.read_bytes()).digest()
    other = photos / "other.png"
    shutil.copyfile(portrait, other)
    library = root / "library"
    manifest = library / "manifest.json"
    env = {**os.environ, "AFACEGROUP_HOME": str(library)}
    def run(*args, success=True):
        result = subprocess.run([str(binary), *map(str, args), "--json"], env=env, capture_output=True, text=True, timeout=120)
        assert (result.returncode == 0) == success, (args, result.returncode, result.stderr)
        return json.loads(result.stdout) if success else result
    def pending():
        state = json.loads(manifest.read_text())
        asset = next(item for item in state["assets"] if item["path"] == str(image))
        asset["pending"] = True
        manifest.write_text(json.dumps(state))
        return asset["id"]
    assert run("scan", photos)["processed"] == 2
    run("forget-pending", image, "--apply", success=False)  # Never delete a completed asset.
    assert run("people", "list")["total_people"] == 1
    asset_id = pending()
    blocked = run("people", "list", success=False)
    assert str(image) in blocked.stderr and "forget-pending" in blocked.stderr
    preview = run("forget-pending", image)
    assert not preview["applied"] and preview["asset_id"] == asset_id
    run("people", "list", success=False)  # Preview must not delete analysis.
    removed = run("forget-pending", image, "--apply")
    assert removed["applied"] and removed["asset_id"] == asset_id
    assert hashlib.sha256(image.read_bytes()).digest() == original
    remaining = run("people", "list")["people"]
    assert len(remaining) == 1 and remaining[0]["paths"] == [str(other)]
    assert hashlib.sha256(other.read_bytes()).digest() == original
    assert run("scan", photos)["processed"] == 1
    link_id = pending()
    assert link_id != asset_id
    image.unlink()
    image.symlink_to(other)
    # Recovery selects the recorded path, not its new symlink target.
    assert run("forget-pending", image)["asset_id"] == link_id
    assert run("forget-pending", image, "--apply")["asset_id"] == link_id
    assert image.is_symlink() and image.resolve() == other.resolve()
    assert hashlib.sha256(other.read_bytes()).digest() == original
    assert run("people", "list")["people"][0]["paths"] == [str(other)]
    image.unlink()
    shutil.copyfile(portrait, image)
    assert run("scan", photos)["processed"] == 1
    new_id = pending()
    assert new_id != link_id
    image.unlink()  # Simulate a source that can no longer be restored.
    run("people", "list", success=False)
    assert run("forget-pending", image, "--apply")["asset_id"] == new_id
    assert run("people", "list")["people"][0]["paths"] == [str(other)]
    assert not image.exists()
    # A failed new asset may never have been inserted into the analyzer.
    broken = photos / "broken.jpg"
    broken.write_bytes(b"not an image")
    failed = run("scan", photos, success=False)
    assert len(json.loads(failed.stdout)["failures"]) == 1
    assert not run("forget-pending", broken)["applied"]
    assert run("forget-pending", broken, "--apply")["applied"]
    assert broken.read_bytes() == b"not an image"
    assert run("people", "list")["people"][0]["paths"] == [str(other)]
print("Pending-asset recovery checks passed")
