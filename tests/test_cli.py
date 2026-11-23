import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CliTests(unittest.TestCase):
    def run_cli(self, source: Path, output: Path, *options: str):
        return subprocess.run(
            [
                sys.executable,
                "-X",
                "utf8",
                "-m",
                "deadline_radar",
                str(source),
                "--as-of",
                "2026-11-23",
                "--out-dir",
                str(output),
                *options,
            ],
            cwd=ROOT,
            capture_output=True,
            encoding="utf-8",
            check=False,
        )

    def test_demo_creates_reproducible_reports(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "result"
            result = self.run_cli(ROOT / "data" / "demo.csv", output)
            self.assertEqual(result.returncode, 0, result.stderr)
            raw_json = (output / "report.json").read_bytes()
            raw_markdown = (output / "report.md").read_bytes()
            report = json.loads(raw_json)

            self.assertEqual(report["as_of"], "2026-11-23")
            self.assertEqual(report["through"], "2026-11-29")
            self.assertEqual(
                [day["deficit_minutes"] for day in report["days"]],
                [15, 0, 30, 0, 0, 0, 0],
            )
            self.assertEqual(len(report["overdue"]), 1)
            self.assertEqual(len(report["upcoming"]), 5)
            self.assertEqual((report["later_count"], report["done_count"]), (1, 1))
            markdown = raw_markdown.decode("utf-8")
            self.assertIn("**Первый дефицит:** 2026-11-23, 15 мин.", markdown)
            self.assertIn("Составить запросы: JOIN, GROUP BY", markdown)

            rerun = self.run_cli(ROOT / "data" / "demo.csv", output)
            self.assertEqual(rerun.returncode, 0, rerun.stderr)
            self.assertEqual((output / "report.json").read_bytes(), raw_json)
            self.assertEqual((output / "report.md").read_bytes(), raw_markdown)

    def test_bad_csv_returns_line_and_leaves_no_report(self):
        cases = {
            "date": ("t,Math,Proof,2026-02-30,15,open\n", "дата"),
            "minutes": ("t,Math,Proof,2026-11-23,0,open\n", "minutes"),
            "status": ("t,Math,Proof,2026-11-23,15,new\n", "status"),
            "short row": ("t,Math,Proof,2026-11-23,15\n", "ожидалось 6 полей"),
            "duplicate": (
                "t,Math,Proof,2026-11-23,15,open\nt,Math,Read,2026-11-24,20,open\n",
                "повторяющийся id",
            ),
        }
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "tasks.csv"
            output = Path(temporary) / "result"
            for label, (records, message) in cases.items():
                with self.subTest(label=label):
                    source.write_text(
                        "id,subject,title,due,minutes,status\n" + records, "utf-8-sig"
                    )

                    result = self.run_cli(source, output)

                    self.assertEqual(result.returncode, 1)
                    error_line = 1 + len(records.splitlines())
                    self.assertIn(f"tasks.csv:{error_line}:", result.stderr)
                    self.assertIn(message, result.stderr)
                    self.assertFalse(output.exists())

    def test_invalid_budget_fails_before_processing(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "result"
            result = self.run_cli(
                ROOT / "data" / "demo.csv", output, "--daily-minutes", "-1"
            )

            self.assertEqual(result.returncode, 2)
            self.assertIn("--daily-minutes должно быть от 0 до 1440", result.stderr)
            self.assertFalse(output.exists())
