#!/usr/bin/env python3
"""Interrupt a native scan with a pending asset and verify safe resumption."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

binary, portrait = (Path(p).resolve() for p in sys.argv[1:3])
with tempfile.TemporaryDirectory(prefix="a-facegroup-interrupted-") as tmp:
    root = Path(tmp)
    photos = root / "photos"
    photos.mkdir()
    for n in range(100):
        shutil.copyfile(portrait, photos / f"{n:03d}.png")
    library = root / "library"
    manifest = library / "manifest.json"
    env = {**os.environ, "AFACEGROUP_HOME": str(library)}
    command = [str(binary), "scan", str(photos), "--json"]
    with (root / "out").open("w") as out, (root / "err").open("w") as err:
        scan = subprocess.Popen(command, env=env, stdout=out, stderr=err)
        pending = None
        deadline = time.monotonic() + 30
        try:
            while time.monotonic() < deadline and scan.poll() is None:
                try:
                    assets = json.loads(manifest.read_text())["assets"]
                    pending = next((asset for asset in assets if asset.get("pending")), None)
                except (FileNotFoundError, json.JSONDecodeError):
                    pass
                if pending:
                    scan.terminate()
                    break
                time.sleep(0.005)
        finally:
            if scan.poll() is None:
                scan.terminate()
            scan.wait(timeout=30)
        assert pending is not None, "Did not observe an in-flight pending asset"
        assert scan.returncode != 0, scan.returncode
    resumed = subprocess.run(command, env=env, capture_output=True, text=True, timeout=120, check=True)
    result = json.loads(resumed.stdout)
    assert result["processed"] + result["skipped"] == 100 and not result["failures"], result
    assets = json.loads(manifest.read_text())["assets"]
    assert len(assets) == 100 and all(not asset.get("pending") for asset in assets)
    assert next(asset for asset in assets if asset["path"] == pending["path"])["id"] == pending["id"]
    print("Interrupted native scan resumed with the same asset ID")
