#!/usr/bin/env python3
"""Identify held-out portraits from the documented eight-photo evaluation set."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

binary, photos = (Path(p).resolve() for p in sys.argv[1:3])
names = ["collins", "jemison", "ride", "shepard"]
with tempfile.TemporaryDirectory(prefix="a-facegroup-eval-heldout-") as tmp:
    root = Path(tmp)
    for i, name in enumerate(names):
        directory = root / name / "photos"
        directory.mkdir(parents=True)
        images = sorted(photos.glob(name + "-*"))
        other = sorted(photos.glob(names[(i + 1) % len(names)] + "-*"))
        if len(images) != 2 or len(other) != 2:
            raise SystemExit("Expected the documented two labeled photos for each subject")
        shutil.copyfile(images[0], directory / images[0].name)
        env = {**os.environ, "AFACEGROUP_HOME": str(root / name / "library")}
        def run(*args):
            result = subprocess.run([str(binary), *map(str, args), "--json"], env=env, capture_output=True, text=True, timeout=120, check=True)
            return json.loads(result.stdout)
        scan = run("scan", directory)
        people = run("people", "list")["people"]
        known = run("identify", images[1])["faces"]
        unknown = run("identify", other[1])["faces"]
        assert scan["processed"] == 1 and len(people) == 1
        assert len(known) == 1 and known[0].get("entity_id") == people[0]["id"], (name, known)
        assert len(unknown) == 1 and not unknown[0]["matched"], (name, unknown)
print("Four held-out known and unknown identification checks passed")
