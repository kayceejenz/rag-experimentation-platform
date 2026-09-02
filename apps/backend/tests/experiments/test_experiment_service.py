import unittest

from modules.experiments.services.experiment_service import ExperimentService


class Repository:
    def can_access(self, *args): return True
    def dataset_exists(self, *args): return True
    def create_experiment(self, *args): return {"id": "experiment"}


class ExperimentValidationTests(unittest.TestCase):
    def setUp(self): self.service = ExperimentService(Repository())

    def test_primary_metric_must_be_selected(self):
        with self.assertRaisesRegex(ValueError, "Primary"):
            self.service.create("p", "u", "Test", None, "Hypothesis", "d",
                                ["faithfulness"], "context_recall")

    def test_unsupported_metric_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unsupported"):
            self.service.create("p", "u", "Test", None, "Hypothesis", "d",
                                ["magic_score"], "magic_score")

    def test_valid_metric_set_is_canonical(self):
        result = self.service.create(
            "p", "u", "Test", None, "Hypothesis", "d",
            ["faithfulness", "context_precision", "faithfulness"], "faithfulness"
        )
        self.assertEqual({"id": "experiment"}, result)
