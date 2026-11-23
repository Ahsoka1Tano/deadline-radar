# AI Engineering Lab — Радар дедлайнов

## Проверка работы

| Workflow | Успешный запуск | Что смотреть |
| --- | --- | --- |
| [Quality CI](https://github.com/Ahsoka1Tano/deadline-radar/actions/workflows/quality-ci.yml) | [Журналы проверок](https://github.com/Ahsoka1Tano/deadline-radar/actions/runs/45237864673) | Ruff и по семь тестов на Python 3.12 и 3.13. В журнале `Verify workload calculations and CSV-to-report behavior` перечислены проверки расчёта и CLI. |
| [Project CI](https://github.com/Ahsoka1Tano/deadline-radar/actions/workflows/project-ci.yml) | [Отчёт и журнал генерации](https://github.com/Ahsoka1Tano/deadline-radar/actions/runs/45237864694) | Markdown на вкладке **Summary** и [архив `deadline-report`](https://github.com/Ahsoka1Tano/deadline-radar/actions/runs/45237864694/artifacts/14850292895) с `report.md` и `report.json`. Для скачивания ZIP нужно войти в GitHub. |

Оба запуска относятся к [коммиту `d002a03`](https://github.com/Ahsoka1Tano/deadline-radar/commit/d002a03aaaa106e95cf3591c75bd1b7166a816c3) с приложением, тестами и workflow. Запуски после добавления этих ссылок доступны на [вкладке Actions](https://github.com/Ahsoka1Tano/deadline-radar/actions?query=branch%3Amain).

Инструкция по запуску и алгоритм описаны в [README.md](README.md). Использование ИИ раскрыто в [AI_MODELS.md](AI_MODELS.md).

## Как проверить результат

Отчёт строится по [демонстрационному CSV](data/demo.csv) на период 23–29 ноября 2026 года с бюджетом 90 минут в день. Ожидается одна просроченная задача, пять предстоящих, одна за пределами периода и одна выполненная. В отчёте должны быть два дня с дефицитом. На 23 ноября не хватает 15 минут, на 25 ноября не хватает 30 минут.
