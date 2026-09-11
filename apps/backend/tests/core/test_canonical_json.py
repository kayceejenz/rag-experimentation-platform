import math
import unittest

from modules.core.helpers.canonical_json import (
    InvalidCanonicalJsonError,
    canonical_json,
)


class CanonicalJsonTests(unittest.TestCase):
    def test_object_order_and_whitespace_do_not_change_identity(self) -> None:
        left = canonical_json(
            {"provider": "gemini", "options": {"dimensions": 768, "normalize": True}}
        )
        right = canonical_json(
            {"options": {"normalize": True, "dimensions": 768}, "provider": "gemini"}
        )

        self.assertEqual(left.encoded, right.encoded)
        self.assertEqual(left.sha256, right.sha256)

    def test_meaningful_change_produces_different_identity(self) -> None:
        left = canonical_json({"dimensions": 768})
        right = canonical_json({"dimensions": 1536})

        self.assertNotEqual(left.sha256, right.sha256)

    def test_non_finite_numbers_are_rejected_with_location(self) -> None:
        for value in (math.nan, math.inf, -math.inf):
            with (
                self.subTest(value=value),
                self.assertRaisesRegex(InvalidCanonicalJsonError, r"\$\.temperature"),
            ):
                canonical_json({"temperature": value})

    def test_non_json_values_are_rejected(self) -> None:
        with self.assertRaisesRegex(
            InvalidCanonicalJsonError, "unsupported JSON value set"
        ):
            canonical_json({"values": {"one", "two"}})


if __name__ == "__main__":
    unittest.main()
