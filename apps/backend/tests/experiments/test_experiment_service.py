import unittest

from modules.experiments.services.experiment_service import ExperimentService


class Repository:
    def can_access(self, *args):
        return True

    def dataset_exists(self, *args):
        return True

    def create_experiment(self, *args):
        return {"id": "experiment"}

    def detail(self, *args):
        return {"experiment": {"id": "experiment"}}


class Runs:
    def __init__(self):
        self.arguments = None

    def enqueue(self, *args):
        self.arguments = args
        return {"id": "run"}


class ExperimentValidationTests(unittest.TestCase):
    def setUp(self):
        self.service = ExperimentService(Repository())

    def test_primary_metric_must_be_selected(self):
        with self.assertRaisesRegex(ValueError, "Primary"):
            self.service.create(
                "p",
                "u",
                "Test",
                None,
                "Hypothesis",
                "d",
                ["faithfulness"],
                "context_recall",
            )

    def test_unsupported_metric_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unsupported"):
            self.service.create(
                "p",
                "u",
                "Test",
                None,
                "Hypothesis",
                "d",
                ["magic_score"],
                "magic_score",
            )

    def test_valid_metric_set_is_canonical(self):
        result = self.service.create(
            "p",
            "u",
            "Test",
            None,
            "Hypothesis",
            "d",
            ["faithfulness", "context_precision", "faithfulness"],
            "faithfulness",
        )
        self.assertEqual({"id": "experiment"}, result)

    def test_run_targets_only_selected_variants(self):
        runs = Runs()
        service = ExperimentService(
            Repository(), runs, "revision", ["gemini-2.5-flash"]
        )

        result = service.start_run("project", "user", "experiment", ["variant"])

        self.assertEqual({"id": "run"}, result)
        self.assertEqual(["variant"], runs.arguments[-1])
