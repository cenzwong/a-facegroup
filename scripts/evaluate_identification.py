#!/usr/bin/env python3
"""Evaluate held-out identification using two labeled single-face photos per person."""
import argparse
from collections import Counter
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


def classify(faces, expected_id=None):
    if not faces:
        return "no_face"
    if len(faces) != 1:
        return "multiple_faces"
    face = faces[0]
    if expected_id is None:
        return "false_match" if face["matched"] else "correct_unmatched"
    if not face["matched"]:
        return "unmatched"
    return "correct_match" if face.get("entity_id") == expected_id else "wrong_match"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("binary", type=Path)
    parser.add_argument("labels", type=Path, help="JSON array of {path, person} objects")
    parser.add_argument("scratch", type=Path, help="existing directory for temporary galleries")
    args = parser.parse_args()
    binary = args.binary.resolve()
    labels = json.loads(args.labels.read_text())
    subjects = {}
    seen = set()
    for item in labels:
        if not isinstance(item, dict) or not isinstance(item.get("person"), str) or not item["person"] or not isinstance(item.get("path"), str) or not item["path"]:
            parser.error("each label must have a nonempty path and person")
        path = Path(item["path"]).resolve()
        if path in seen or not path.is_file():
            parser.error("each labeled path must be a unique existing file")
        seen.add(path)
        subjects.setdefault(item["person"], []).append(path)
    if len(subjects) < 2 or any(len(paths) != 2 for paths in subjects.values()):
        parser.error("provide exactly two photos for each of at least two people")
    names = sorted(subjects)
    for paths in subjects.values():
        paths.sort()
    known_counts, unknown_counts = Counter(), Counter()
    with tempfile.TemporaryDirectory(prefix="a-facegroup-identify-", dir=args.scratch) as tmp:
        root = Path(tmp)
        for index, name in enumerate(names):
            # Numeric names avoid using label text in temporary paths.
            directory = root / str(index) / "photos"
            directory.mkdir(parents=True)
            source = subjects[name][0]
            shutil.copyfile(source, directory / source.name)
            env = {**os.environ, "AFACEGROUP_HOME": str(root / str(index) / "library")}
            def run(*command):
                result = subprocess.run([str(binary), *map(str, command), "--json"], env=env, capture_output=True, text=True, timeout=120)
                if result.returncode:
                    raise RuntimeError(f"CLI command failed with status {result.returncode}: {result.stderr.strip()}")
                return json.loads(result.stdout)
            scan = run("scan", directory)
            people = run("people", "list")["people"]
            if scan["processed"] != 1 or len(people) != 1 or people[0]["face_count"] != 1:
                known_counts["ambiguous_or_undetected_gallery"] += 1
                unknown_counts["ambiguous_or_undetected_gallery"] += 1
                continue
            known_counts[classify(run("identify", subjects[name][1])["faces"], people[0]["id"])] += 1
            unknown = subjects[names[(index + 1) % len(names)]][1]
            unknown_counts[classify(run("identify", unknown)["faces"])] += 1
    print(json.dumps({"people": len(names), "known_outcomes": dict(known_counts), "unknown_outcomes": dict(unknown_counts), "method": "One indexed photo and one held-out photo per person; unknown is the next person's held-out photo."}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
