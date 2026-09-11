import unittest
from unittest.mock import Mock, patch
from uuid import uuid4

from modules.sources.models.error_model import SourcePreviewUnsupportedError
from modules.sources.services.source_service import SourceService


class SourcePreviewTests(unittest.TestCase):
    def setUp(self):
        self.repository = Mock()
        self.service = SourceService(self.repository, "storage/sources")

    def version(self, filename: str, content_type: str = "application/octet-stream"):
        self.repository.latest_version.return_value = {
            "filename": filename,
            "content_type": content_type,
            "storage_key": f"example/{filename}",
        }

    @patch("modules.sources.services.source_service.resolve_file")
    def test_safe_preview_type_is_derived_from_extension(self, resolve_file):
        resolve_file.return_value = (Mock(), False)
        self.version("notes.txt", "text/html")

        _, _, media_type, _ = self.service.load_file(uuid4(), uuid4(), uuid4())

        self.assertEqual(media_type, "text/plain; charset=utf-8")

    @patch("modules.sources.services.source_service.resolve_file")
    def test_active_content_is_rejected_before_file_is_loaded(self, resolve_file):
        self.version("payload.html", "text/html")

        with self.assertRaises(SourcePreviewUnsupportedError):
            self.service.load_file(uuid4(), uuid4(), uuid4())

        resolve_file.assert_not_called()

    @patch("modules.sources.services.source_service.resolve_file")
    def test_svg_preview_is_rejected(self, resolve_file):
        self.version("diagram.svg", "image/svg+xml")

        with self.assertRaises(SourcePreviewUnsupportedError):
            self.service.load_file(uuid4(), uuid4(), uuid4())

        resolve_file.assert_not_called()


if __name__ == "__main__":
    unittest.main()
