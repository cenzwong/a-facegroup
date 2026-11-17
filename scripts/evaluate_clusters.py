#!/usr/bin/env python3
"""Score CLI person clusters against labels for single-person photos, offline."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys


def score(labels, output):
    """Count false pairs among assigned images; separately report unassigned images."""
    if not isinstance(labels, list) or not isinstance(output.get("people"), list):
        raise ValueError("Expected a label list and a people-list JSON object")
    truth = {}
    for item in labels:
        if not isinstance(item, dict) or not isinstance(item.get("path"), str) or not item["path"] or not isinstance(item.get("person"), str) or not item["person"]:
            raise ValueError("Each label needs a nonempty path and person")
        path = str(Path(item["path"]).resolve())
        if path in truth:
            raise ValueError("A photo appears more than once in the labels")
        truth[path] = item["person"]
    if not truth:
        raise ValueError("At least one labeled photo is required")
    assigned = {}
    ids = set()
    for person in output["people"]:
        if not isinstance(person, dict) or not isinstance(person.get("id"), str) or not person["id"] or not isinstance(person.get("paths"), list):
            raise ValueError("Each cluster needs an id and paths")
        cluster = person["id"]
        if cluster in ids:
            raise ValueError("Duplicate cluster ID")
        ids.add(cluster)
        for raw in person["paths"]:
            if not isinstance(raw, str) or not raw:
                raise ValueError("Cluster paths must be nonempty strings")
            path = str(Path(raw).resolve())
            if path not in truth:
                raise ValueError("Cluster contains a photo outside the labeled set")
            if path in assigned and assigned[path] != cluster:
                raise ValueError("A photo appears in multiple clusters; single-person photos are required")
            assigned[path] = cluster
    label_counts = Counter(truth[path] for path in assigned)
    cluster_counts = Counter(assigned.values())
    cells = Counter((truth[path], cluster) for path, cluster in assigned.items())
    pairs = lambda counts: sum(count * (count - 1) // 2 for count in counts)
    true_pairs = pairs(cells.values())
    return {
        "labeled_photos": len(truth),
        "assigned_photos": len(assigned),
        "unassigned_photos": len(truth) - len(assigned),
        "labeled_people": len(set(truth.values())),
        "returned_clusters": len(ids),
        "false_merge_pairs": pairs(cluster_counts.values()) - true_pairs,
        "false_split_pairs": pairs(label_counts.values()) - true_pairs,
        "note": "Pair counts include assigned photos only; unassigned photos are reported separately.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("labels", type=Path, help="JSON array of {path, person} objects; one person per image")
    parser.add_argument("people", type=Path, help="JSON from a-facegroup people list --json")
    args = parser.parse_args()
    try:
        result = score(json.loads(args.labels.read_text()), json.loads(args.people.read_text()))
    except (OSError, ValueError, TypeError, AttributeError) as error:
        parser.exit(1, f"error: {error}\n")
    json.dump(result, sys.stdout, indent=2, sort_keys=True)
    print()


if __name__ == "__main__":
    main()
