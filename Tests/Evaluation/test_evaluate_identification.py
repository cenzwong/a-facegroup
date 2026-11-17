import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("evaluate_identification", Path(__file__).resolve().parents[2] / "scripts/evaluate_identification.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class IdentificationEvaluationTests(unittest.TestCase):
    def test_known_outcomes(self):
        self.assertEqual(module.classify([{"matched": True, "entity_id": "a"}], "a"), "correct_match")
        self.assertEqual(module.classify([{"matched": True, "entity_id": "b"}], "a"), "wrong_match")
        self.assertEqual(module.classify([{"matched": False}], "a"), "unmatched")

    def test_unknown_and_ambiguous_outcomes(self):
        self.assertEqual(module.classify([{"matched": True, "entity_id": "a"}]), "false_match")
        self.assertEqual(module.classify([{"matched": False}]), "correct_unmatched")
        self.assertEqual(module.classify([]), "no_face")
        self.assertEqual(module.classify([{}, {}]), "multiple_faces")
