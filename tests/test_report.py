import unittest
from datetime import date

from deadline_radar.report import build_report, render_markdown
from deadline_radar.tasks import Task


class ReportTests(unittest.TestCase):
    def test_required_time_includes_overdue_and_same_day_tasks(self):
        tasks = [
            Task(
                "after", "Математика", "После периода", date(2026, 12, 1), 600, "open"
            ),
            Task("b", "Алгоритмы", "Вторая к сроку", date(2026, 11, 24), 90, "open"),
            Task("old", "Алгоритмы", "Просрочена", date(2026, 11, 20), 40, "open"),
            Task("a", "Алгоритмы", "Первая к сроку", date(2026, 11, 24), 80, "open"),
            Task("done", "Математика", "Выполнена", date(2026, 11, 23), 600, "done"),
        ]

        report = build_report(tasks, date(2026, 11, 23), days=3, daily_minutes=90)

        self.assertEqual([task.id for task in report.overdue], ["old"])
        self.assertEqual([task.id for task in report.upcoming], ["a", "b"])
        self.assertEqual((report.later_count, report.done_count), (1, 1))
        self.assertEqual([day.due_minutes for day in report.days], [0, 170, 0])
        self.assertEqual([day.required_minutes for day in report.days], [40, 210, 210])
        self.assertEqual([day.available_minutes for day in report.days], [90, 180, 270])
        self.assertEqual([day.deficit_minutes for day in report.days], [0, 30, 0])

    def test_period_includes_today_and_last_day(self):
        tasks = [
            Task("today", "Алгоритмы", "Сегодня", date(2026, 11, 23), 90, "open"),
            Task(
                "last", "Алгоритмы", "Последний день", date(2026, 11, 29), 540, "open"
            ),
            Task("after", "Алгоритмы", "Вне периода", date(2026, 11, 30), 1, "open"),
        ]

        report = build_report(tasks, date(2026, 11, 23), days=7, daily_minutes=90)

        self.assertEqual(report.through, date(2026, 11, 29))
        self.assertEqual([task.id for task in report.upcoming], ["today", "last"])
        self.assertEqual(report.later_count, 1)
        self.assertEqual(report.days[-1].required_minutes, 630)
        self.assertEqual(report.days[-1].deficit_minutes, 0)

    def test_no_tasks_with_zero_budget(self):
        report = build_report([], date(2026, 11, 23), days=1, daily_minutes=0)

        self.assertEqual(report.days[0].deficit_minutes, 0)
        self.assertIn("времени хватает", render_markdown(report))

    def test_task_text_is_escaped_in_markdown(self):
        task = Task("x", "A | B", "<b> [текст](ссылка)", date(2026, 11, 23), 1, "open")
        markdown = render_markdown(
            build_report([task], task.due, days=1, daily_minutes=0)
        )

        self.assertIn("A &#124; B", markdown)
        self.assertIn("&#60;b&#62; &#91;текст&#93;(ссылка)", markdown)
        self.assertIn("**Первый дефицит:** 2026-11-23, 1 мин.", markdown)
