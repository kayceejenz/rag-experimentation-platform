import unittest

from integrations.retrieval_store import PgVectorKnowledgeSearch


class RetrievalScoreTests(unittest.TestCase):
    def build_search(self, distance_metric):
        return PgVectorKnowledgeSearch(
            "postgresql://unused",
            embedder=object(),
            provider="gemini",
            model_name="embedding-model",
            distance_metric=distance_metric,
        )

    def test_cosine_score_is_normalized_to_zero_one(self):
        search = self.build_search("cosine")

        self.assertEqual(search._score_expression("distance"), "1-((distance)/2)")

    def test_other_distance_score_contracts_are_unchanged(self):
        inner_product = self.build_search("inner_product")
        l2 = self.build_search("l2")

        self.assertEqual(inner_product._score_expression("distance"), "-(distance)")
        self.assertEqual(l2._score_expression("distance"), "1/(1+(distance))")


if __name__ == "__main__":
    unittest.main()
