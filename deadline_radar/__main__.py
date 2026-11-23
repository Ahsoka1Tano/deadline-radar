import argparse
import sys
from datetime import date
from pathlib import Path

from deadline_radar.report import build_report, write_report
from deadline_radar.tasks import parse_date, read_tasks


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Отчёт о дедлайнах и доступном учебном времени."
    )
    parser.add_argument("csv", type=Path, help="CSV-файл со списком задач")
    parser.add_argument(
        "--as-of", metavar="ГГГГ-ММ-ДД", help="дата начала, по умолчанию сегодня"
    )
    parser.add_argument(
        "--days", type=int, default=7, help="период в днях, по умолчанию 7"
    )
    parser.add_argument(
        "--daily-minutes", type=int, default=90, help="минут в день, по умолчанию 90"
    )
    parser.add_argument(
        "--out-dir", type=Path, default=Path("dist"), help="папка для отчёта"
    )
    args = parser.parse_args()

    if not 1 <= args.days <= 366:
        parser.error("--days должно быть от 1 до 366")
    if not 0 <= args.daily_minutes <= 1440:
        parser.error("--daily-minutes должно быть от 0 до 1440")

    try:
        as_of = parse_date(args.as_of) if args.as_of is not None else date.today()
        input_path = args.csv.resolve()
        if any(
            input_path == (args.out_dir / name).resolve()
            for name in ("report.md", "report.json")
        ):
            raise ValueError(
                "файл отчёта совпадает с входным CSV, выберите другую папку"
            )
        report = build_report(
            read_tasks(args.csv), as_of, args.days, args.daily_minutes
        )
        write_report(report, args.out_dir)
    except (OSError, ValueError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 1

    print(f"Готово: {args.out_dir / 'report.md'} и {args.out_dir / 'report.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
