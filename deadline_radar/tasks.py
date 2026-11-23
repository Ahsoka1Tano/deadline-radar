import csv
from dataclasses import dataclass
from datetime import date
from pathlib import Path

FIELDS = ("id", "subject", "title", "due", "minutes", "status")


@dataclass(frozen=True)
class Task:
    id: str
    subject: str
    title: str
    due: date
    minutes: int
    status: str


def parse_date(value: str) -> date:
    try:
        result = date.fromisoformat(value)
    except ValueError:
        raise ValueError(f"ожидалась дата ГГГГ-ММ-ДД, получено {value!r}") from None
    if result.isoformat() != value:
        raise ValueError(f"ожидалась дата ГГГГ-ММ-ДД, получено {value!r}")
    return result


def parse_task(values: list[str], header: list[str]) -> Task:
    if len(values) != len(header):
        raise ValueError(f"ожидалось {len(header)} полей, получено {len(values)}")
    row = dict(zip(header, (value.strip() for value in values), strict=True))
    for field in FIELDS:
        if not row[field] or not row[field].isprintable():
            raise ValueError(
                f"поле {field} должно содержать непустой текст в одну строку"
            )
    if not row["minutes"].isascii() or not row["minutes"].isdecimal():
        raise ValueError("minutes должно быть положительным целым числом")
    minutes = int(row["minutes"])
    if minutes == 0:
        raise ValueError("minutes должно быть положительным целым числом")
    if row["status"] not in {"open", "done"}:
        raise ValueError(f"неизвестный status {row['status']!r}, допустимы open и done")
    return Task(
        row["id"],
        row["subject"],
        row["title"],
        parse_date(row["due"]),
        minutes,
        row["status"],
    )


def read_tasks(path: Path) -> list[Task]:
    tasks = []
    seen_ids = set()
    with path.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.reader(source, strict=True)
        try:
            header = next(reader, [])
            if len(header) != len(FIELDS) or set(header) != set(FIELDS):
                raise ValueError(f"ожидались поля {', '.join(FIELDS)}")

            for values in reader:
                if not values:
                    continue
                task = parse_task(values, header)
                if task.id in seen_ids:
                    raise ValueError(f"повторяющийся id {task.id!r}")
                seen_ids.add(task.id)
                tasks.append(task)
        except (csv.Error, ValueError) as error:
            raise ValueError(f"{path}:{max(reader.line_num, 1)}: {error}") from None
    return tasks
