"""Tests for saving original files."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.storage.files import save_original_file


class SaveOriginalFileTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)
        self.raw = self.root / "data" / "raw"
        self.source = self.root / "measurement.bin"
        self.source.write_bytes(b"\x00original\xff")
        patcher = patch("src.storage.files._RAW_DIRECTORY", self.raw)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_copy_preserves_name_contents_and_source(self) -> None:
        before = self.source.stat()
        result = save_original_file(self.source, "measurement-1")
        self.assertEqual(result, self.raw / "measurement-1" / self.source.name)
        self.assertEqual(result.read_bytes(), b"\x00original\xff")
        self.assertEqual(self.source.read_bytes(), result.read_bytes())
        self.assertEqual(self.source.stat().st_mtime_ns, before.st_mtime_ns)

    def test_missing_source(self) -> None:
        with self.assertRaisesRegex(FileNotFoundError, "Source file does not exist"):
            save_original_file(self.root / "missing.bin", "measurement-1")
        self.assertFalse(self.raw.exists())

    def test_source_directory(self) -> None:
        with self.assertRaisesRegex(IsADirectoryError, "not a regular file"):
            save_original_file(self.root, "measurement-1")

    def test_existing_measurement_directory_is_rejected(self) -> None:
        directory = self.raw / "measurement-1"
        directory.mkdir(parents=True)
        with self.assertRaises(FileExistsError):
            save_original_file(self.source, "measurement-1")
        self.assertEqual(list(directory.iterdir()), [])

    def test_existing_destination_is_preserved(self) -> None:
        destination = save_original_file(self.source, "measurement-1")
        with self.assertRaises(FileExistsError):
            save_original_file(self.source, "measurement-1")
        self.assertEqual(destination.read_bytes(), b"\x00original\xff")

    def test_copy_error_is_clear_and_source_is_preserved(self) -> None:
        with patch("src.storage.files.shutil.copyfileobj", side_effect=OSError("disk full")):
            with self.assertRaisesRegex(OSError, "Could not copy.*disk full"):
                save_original_file(self.source, "measurement-1")
        self.assertEqual(self.source.read_bytes(), b"\x00original\xff")

    def test_measurement_id_cannot_escape_raw_directory(self) -> None:
        for measurement_id in ("", ".", "..", "../outside", "/outside", "a\\b"):
            with self.subTest(measurement_id=measurement_id):
                with self.assertRaises(ValueError):
                    save_original_file(self.source, measurement_id)


if __name__ == "__main__":
    unittest.main()
