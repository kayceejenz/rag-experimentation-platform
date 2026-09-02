import unittest
from uuid import uuid4

from modules.benchmarks.service import BenchmarkService


class Repository:
    def can_access(self, *args):
        return True


class BenchmarkValidationTests(unittest.TestCase):
    def setUp(self):
        self.service = BenchmarkService(Repository())

    def test_dataset_requires_a_case(self):
        with self.assertRaisesRegex(ValueError, "at least one"):
            self.service._prepare_cases([])

    def test_content_hash_is_deterministic(self):
        first = {"case_id": str(uuid4()), "question": "First"}
        second = {"case_id": str(uuid4()), "question": "Second"}
        content_a, digest_a = self.service._prepare_cases([first, second])
        content_b, digest_b = self.service._prepare_cases([second, first])
        self.assertEqual(content_a, content_b)
        self.assertEqual(digest_a, digest_b)

    def test_case_identifiers_are_unique(self):
        case_id = str(uuid4())
        with self.assertRaisesRegex(ValueError, "unique"):
            self.service._prepare_cases(
                [
                    {"case_id": case_id, "question": "First"},
                    {"case_id": case_id, "question": "Second"},
                ]
            )
