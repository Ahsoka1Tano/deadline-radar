import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

from deadline_radar.tasks import Task

MARKDOWN_ENTITIES = str.maketrans({char: f"&#{ord(char)};" for char in "&<>\\|`*_[]~!"})


@dataclass(frozen=True)
class DailyLoad:
    day: date
    due_minutes: int
    required_minutes: int
    available_minutes: int
    deficit_minutes: int


@dataclass(frozen=True)
class Report:
    as_of: date
    through: date
    daily_minutes: int
    overdue: list[Task]
    upcoming: list[Task]
    later_count: int
    done_count: int
    days: list[DailyLoad]


def build_report(
    tasks: list[Task], as_of: date, days: int, daily_minutes: int
) -> Report:
    try:
        through = as_of + timedelta(days=days - 1)
    except OverflowError:
        raise ValueError("период выходит за пределы поддерживаемых дат") from None

    open_tasks = sorted(
        (task for task in tasks if task.status == "open"),
        key=lambda task: (task.due, task.id),
    )
    overdue = [task for task in open_tasks if task.due < as_of]
    upcoming = [task for task in open_tasks if as_of <= task.due <= through]
    minutes_by_day = Counter()
    for task in upcoming:
        minutes_by_day[task.due] += task.minutes

    required = sum(task.minutes for task in overdue)
    loads = []
    for offset in range(days):
        day = as_of + timedelta(days=offset)
        required += minutes_by_day[day]
        available = daily_minutes * (offset + 1)
        loads.append(
            DailyLoad(
                day,
                minutes_by_day[day],
                required,
                available,
                max(0, required - available),
            )
        )

    return Report(
        as_of=as_of,
        through=through,
        daily_minutes=daily_minutes,
        overdue=overdue,
        upcoming=upcoming,
        later_count=len(open_tasks) - len(overdue) - len(upcoming),
        done_count=len(tasks) - len(open_tasks),
        days=loads,
    )


def task_table(tasks: list[Task]) -> list[str]:
    if not tasks:
        return ["Нет задач."]
    rows = ["| Дедлайн | Предмет | Задача | Мин. |", "| --- | --- | --- | ---: |"]
    for task in tasks:
        subject = task.subject.translate(MARKDOWN_ENTITIES)
        title = task.title.translate(MARKDOWN_ENTITIES)
        rows.append(f"| {task.due} | {subject} | {title} | {task.minutes} |")
    return rows


def render_markdown(report: Report) -> str:
    first_deficit = next((day for day in report.days if day.deficit_minutes > 0), None)
    if first_deficit:
        headline = f"**Первый дефицит:** {first_deficit.day}, {first_deficit.deficit_minutes} мин."
    else:
        headline = "**В пределах периода времени хватает по всем дедлайнам.**"

    rows = [
        "# Радар дедлайнов",
        "",
        f"Период {report.as_of} — {report.through}. Бюджет {report.daily_minutes} мин./день.",
        "",
        headline,
        "",
        "## Нагрузка по дням",
        "",
        "В столбце «Нужно к дате» учтены просроченные и все открытые задачи со сроком к этой дате.",
        "",
        "| Дата | Срок сегодня, мин. | Нужно к дате, мин. | Доступно к дате, мин. | Дефицит, мин. |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for day in report.days:
        rows.append(
            f"| {day.day} | {day.due_minutes} | {day.required_minutes} | "
            f"{day.available_minutes} | {day.deficit_minutes} |"
        )
    rows += [
        "",
        f"## Просроченные ({len(report.overdue)})",
        "",
        *task_table(report.overdue),
        "",
        f"## Предстоящие ({len(report.upcoming)})",
        "",
        *task_table(report.upcoming),
        "",
        f"За пределами периода: {report.later_count}. Уже выполнено: {report.done_count}.",
        "",
    ]
    return "\n".join(rows)


def write_report(report: Report, directory: Path) -> None:
    markdown = render_markdown(report)
    structured = json.dumps(
        asdict(report), ensure_ascii=False, indent=2, default=date.isoformat
    )
    directory.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=directory) as temporary:
        markdown_path = Path(temporary) / "report.md"
        json_path = Path(temporary) / "report.json"
        markdown_path.write_text(markdown, encoding="utf-8", newline="\n")
        json_path.write_text(structured + "\n", encoding="utf-8", newline="\n")
        markdown_path.replace(directory / markdown_path.name)
        json_path.replace(directory / json_path.name)
