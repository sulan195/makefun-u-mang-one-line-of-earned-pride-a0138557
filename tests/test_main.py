"""Tests for the One Line of Earned Pride entry program.

Covers the entry line itself, validation, output-directory resolution, the
successful write path (including determinism), and every failure mode from
the Fase 2 edge-case list.
"""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import main as entry

EXPECTED_LINE = (
    "Sweat at his temple, knuckles white on the rumpled shirt, the stroke "
    "patient works the top button through and straightens his own collar."
)


class LineContentTests(unittest.TestCase):
    def test_line_is_exact_expected_text(self):
        self.assertEqual(entry.LINE, EXPECTED_LINE)

    def test_line_length_is_137_chars(self):
        self.assertEqual(len(entry.LINE), 137)

    def test_line_is_a_single_line(self):
        self.assertNotIn("\n", entry.LINE)
        self.assertNotIn("\r", entry.LINE)

    def test_line_ends_with_a_period(self):
        self.assertTrue(entry.LINE.endswith("."))


class ValidateTests(unittest.TestCase):
    def test_valid_line_passes(self):
        self.assertTrue(entry.validate(entry.LINE))

    def test_empty_string_fails(self):
        self.assertFalse(entry.validate(""))

    def test_line_over_240_chars_fails(self):
        self.assertFalse(entry.validate("x" * 241))

    def test_line_of_exactly_240_chars_passes(self):
        self.assertTrue(entry.validate("x" * 240))

    def test_single_character_passes(self):
        self.assertTrue(entry.validate("a"))

    def test_whitespace_only_fails(self):
        self.assertFalse(entry.validate("   \t  "))

    def test_internal_newline_fails(self):
        self.assertFalse(entry.validate("first line\nsecond line"))

    def test_carriage_return_fails(self):
        self.assertFalse(entry.validate("first line\rsecond line"))

    def test_tab_fails(self):
        self.assertFalse(entry.validate("word\tword"))

    def test_del_character_fails(self):
        self.assertFalse(entry.validate("word\x7fword"))

    def test_nel_control_character_fails(self):
        self.assertFalse(entry.validate("word\x85word"))

    def test_unicode_line_separator_fails(self):
        self.assertFalse(entry.validate("first line\u2028second line"))

    def test_unicode_paragraph_separator_fails(self):
        self.assertFalse(entry.validate("first line\u2029second line"))

    def test_zero_width_space_fails(self):
        self.assertFalse(entry.validate("word\u200bword"))

    def test_nbsp_only_fails(self):
        # str.strip() does strip U+00A0 (it is Unicode whitespace); this
        # test locks that behaviour — a GPT-OSS 120B finding claimed
        # otherwise, verified false.
        self.assertFalse(entry.validate("\u00a0\u00a0"))

    def test_none_fails(self):
        self.assertFalse(entry.validate(None))

    def test_integer_fails(self):
        self.assertFalse(entry.validate(123))

    def test_surrogate_fails(self):
        self.assertFalse(entry.validate("bad\ud800line"))

    def test_non_ascii_utf8_passes(self):
        self.assertTrue(entry.validate("café au lait, 6 a.m."))


class OutputDirTests(unittest.TestCase):
    def test_env_var_is_used_when_set(self):
        os.environ["MAKEFUN_OUTPUT_DIR"] = "/tmp/somewhere"
        try:
            self.assertEqual(entry.output_dir(), "/tmp/somewhere")
        finally:
            del os.environ["MAKEFUN_OUTPUT_DIR"]

    def test_falls_back_to_output_when_unset(self):
        os.environ.pop("MAKEFUN_OUTPUT_DIR", None)
        self.assertEqual(entry.output_dir(), "/output")

    def test_falls_back_when_env_is_empty(self):
        os.environ["MAKEFUN_OUTPUT_DIR"] = ""
        try:
            self.assertEqual(entry.output_dir(), "/output")
        finally:
            del os.environ["MAKEFUN_OUTPUT_DIR"]

    def test_falls_back_when_env_is_whitespace_only(self):
        os.environ["MAKEFUN_OUTPUT_DIR"] = "   \t "
        try:
            self.assertEqual(entry.output_dir(), "/output")
        finally:
            del os.environ["MAKEFUN_OUTPUT_DIR"]

    def test_env_value_is_stripped(self):
        os.environ["MAKEFUN_OUTPUT_DIR"] = "  /tmp/spaced  "
        try:
            self.assertEqual(entry.output_dir(), "/tmp/spaced")
        finally:
            del os.environ["MAKEFUN_OUTPUT_DIR"]


class MainUnitTests(unittest.TestCase):
    def test_main_writes_exact_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["MAKEFUN_OUTPUT_DIR"] = tmp
            try:
                self.assertEqual(entry.main(), 0)
                data = (Path(tmp) / "entry.txt").read_bytes()
                self.assertEqual(data, EXPECTED_LINE.encode("utf-8"))
            finally:
                del os.environ["MAKEFUN_OUTPUT_DIR"]

    def test_main_writes_world_readable_entry(self):
        # Regression test for the round-1 run_completes rejection:
        # mkstemp creates mode 0600, which the grader (reading /output
        # from the host as a different user) cannot read. entry.txt
        # must be world-readable, and no temp file may remain.
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["MAKEFUN_OUTPUT_DIR"] = tmp
            try:
                self.assertEqual(entry.main(), 0)
                target = Path(tmp) / "entry.txt"
                self.assertEqual(oct(target.stat().st_mode & 0o777), "0o644")
                self.assertEqual(sorted(p.name for p in Path(tmp).iterdir()), ["entry.txt"])
            finally:
                del os.environ["MAKEFUN_OUTPUT_DIR"]

    def test_main_returns_1_and_writes_nothing_on_invalid_line(self):
        original = entry.LINE
        entry.LINE = ""
        try:
            with tempfile.TemporaryDirectory() as tmp:
                os.environ["MAKEFUN_OUTPUT_DIR"] = tmp
                try:
                    self.assertEqual(entry.main(), 1)
                    self.assertFalse((Path(tmp) / "entry.txt").exists())
                finally:
                    del os.environ["MAKEFUN_OUTPUT_DIR"]
        finally:
            entry.LINE = original

    def test_main_returns_1_when_output_path_is_a_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            blocker = Path(tmp) / "blocker"
            blocker.write_text("x")
            os.environ["MAKEFUN_OUTPUT_DIR"] = str(blocker / "child")
            try:
                self.assertEqual(entry.main(), 1)
            finally:
                del os.environ["MAKEFUN_OUTPUT_DIR"]

    def test_main_returns_1_when_entry_path_is_a_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "entry.txt").mkdir()
            os.environ["MAKEFUN_OUTPUT_DIR"] = tmp
            try:
                self.assertEqual(entry.main(), 1)
            finally:
                del os.environ["MAKEFUN_OUTPUT_DIR"]

    def test_failed_write_keeps_previous_entry_intact(self):
        # Atomicity: a mid-write failure must not truncate an existing file.
        from unittest import mock

        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "entry.txt"
            target.write_text("previous entry", encoding="utf-8")
            os.environ["MAKEFUN_OUTPUT_DIR"] = tmp
            try:
                with mock.patch.object(
                    entry.tempfile, "mkstemp", side_effect=OSError("disk full")
                ):
                    self.assertEqual(entry.main(), 1)
                self.assertEqual(target.read_text(encoding="utf-8"), "previous entry")
            finally:
                del os.environ["MAKEFUN_OUTPUT_DIR"]


class SubprocessTests(unittest.TestCase):
    def run_entry(self, env_extra):
        env = dict(os.environ)
        env.update(env_extra)
        return subprocess.run(
            [sys.executable, str(Path(__file__).resolve().parent.parent / "main.py")],
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )

    def test_subprocess_success_writes_exact_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = self.run_entry({"MAKEFUN_OUTPUT_DIR": tmp})
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(proc.stderr, "")
            data = (Path(tmp) / "entry.txt").read_bytes()
            self.assertEqual(data, EXPECTED_LINE.encode("utf-8"))
            self.assertFalse(data.endswith(b"\n"))

    def test_subprocess_runs_are_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = Path(tmp) / "first"
            second = Path(tmp) / "second"
            first.mkdir()
            second.mkdir()
            self.assertEqual(self.run_entry({"MAKEFUN_OUTPUT_DIR": str(first)}).returncode, 0)
            self.assertEqual(self.run_entry({"MAKEFUN_OUTPUT_DIR": str(second)}).returncode, 0)
            self.assertEqual(
                (first / "entry.txt").read_bytes(),
                (second / "entry.txt").read_bytes(),
            )

    def test_subprocess_fails_when_directory_cannot_be_created(self):
        with tempfile.TemporaryDirectory() as tmp:
            blocker = Path(tmp) / "blocker"
            blocker.write_text("x")
            proc = self.run_entry({"MAKEFUN_OUTPUT_DIR": str(blocker / "child")})
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("error", proc.stderr)

    def test_subprocess_creates_missing_output_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            nested = Path(tmp) / "a" / "b"
            proc = self.run_entry({"MAKEFUN_OUTPUT_DIR": str(nested)})
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(
                (nested / "entry.txt").read_text(encoding="utf-8"), EXPECTED_LINE
            )

    def test_subprocess_fails_when_entry_path_is_a_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "entry.txt").mkdir()
            proc = self.run_entry({"MAKEFUN_OUTPUT_DIR": tmp})
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("error", proc.stderr)


if __name__ == "__main__":
    unittest.main()
