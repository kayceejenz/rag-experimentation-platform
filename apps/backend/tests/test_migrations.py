import unittest
from pathlib import Path


class MigrationTests(unittest.TestCase):
    def test_all_migrations_have_an_outer_transaction(self):
        migration_directory = Path(__file__).parents[1] / "src" / "migrations"
        migrations = sorted(migration_directory.glob("*.sql"))

        self.assertTrue(migrations)
        for migration in migrations:
            source = migration.read_text().strip().lower()
            with self.subTest(migration=migration.name):
                self.assertTrue(source.startswith("begin;"))
                self.assertTrue(source.endswith("commit;"))


if __name__ == "__main__":
    unittest.main()
