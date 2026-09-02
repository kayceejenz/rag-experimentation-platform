import unittest
from modules.prompts.services.prompt_service import PromptService


class Repository:
    def can_access(self,*args): return True


class PromptValidationTests(unittest.TestCase):
    def setUp(self): self.service=PromptService(Repository())
    def test_variables_are_inferred_deterministically(self):
        variables,digest=self.service._validate("rag_answer","Answer {{question}} from {{ context }} and {{context}}")
        self.assertEqual(["context","question"],variables); self.assertEqual(64,len(digest))
    def test_rag_prompt_requires_context_and_question(self):
        with self.assertRaisesRegex(ValueError,"require"):
            self.service._validate("rag_answer","Answer {{question}}")
    def test_invalid_variable_syntax_is_rejected(self):
        with self.assertRaisesRegex(ValueError,"invalid"):
            self.service._validate("system","Hello {{ user-name }}")
    def test_empty_template_is_rejected(self):
        with self.assertRaisesRegex(ValueError,"empty"):
            self.service._validate("system","   ")
