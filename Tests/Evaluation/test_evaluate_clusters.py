import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("evaluate_clusters", Path(__file__).resolve().parents[2] / "scripts/evaluate_clusters.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class EvaluationTests(unittest.TestCase):
    def test_counts_false_pairs_and_missing_separately(self):
        labels = [{"path": "/tmp/a", "person": "A"}, {"path": "/tmp/b", "person": "A"}, {"path": "/tmp/c", "person": "B"}, {"path": "/tmp/d", "person": "B"}, {"path": "/tmp/e", "person": "C"}]
        people = {"people": [{"id": "1", "paths": ["/tmp/a", "/tmp/c"]}, {"id": "2", "paths": ["/tmp/b", "/tmp/d"]}]}
        result = module.score(labels, people)
        self.assertEqual(result["false_merge_pairs"], 2)
        self.assertEqual(result["false_split_pairs"], 2)
        self.assertEqual(result["unassigned_photos"], 1)

    def test_rejects_ambiguous_or_unlabeled_paths(self):
        labels = [{"path": "/tmp/a", "person": "A"}]
        with self.assertRaises(ValueError):
            module.score(labels, {"people": [{"id": "1", "paths": ["/tmp/a"]}, {"id": "2", "paths": ["/tmp/a"]}]})
        with self.assertRaises(ValueError):
            module.score(labels, {"people": [{"id": "1", "paths": ["/tmp/other"]}]})
        with self.assertRaises(ValueError):
            module.score(labels * 2, {"people": []})

    def test_perfect_clustering(self):
        labels = [{"path": "/tmp/a", "person": "A"}, {"path": "/tmp/b", "person": "A"}]
        result = module.score(labels, {"people": [{"id": "1", "paths": ["/tmp/a", "/tmp/b"]}]})
        self.assertEqual((result["false_merge_pairs"], result["false_split_pairs"], result["unassigned_photos"]), (0, 0, 0))
