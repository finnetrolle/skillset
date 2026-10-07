# Skillset

Публичный источник актуальных версий личного набора из **27 скиллов**:
23 локальных импорта, три адаптации Matt Pocock и один пакет OpenAI.
Инструкции, скрипты, справочники, ресурсы и UI metadata хранятся вместе.
Встроенные скиллы и плагины управляются приложениями отдельно.

[Каталог по частоте использования](docs/catalog.md) ·
[Сравнение с Matt Pocock](docs/matt-pocock-comparison.md) ·
[Проверки и ограничения](docs/validation.md) ·
[Происхождение и лицензии](THIRD_PARTY_NOTICES.md)

Все текущие пакеты согласованы; решения и доработки записаны в
[реестре аудита](data/skill-audit.json). В `grill-me` есть счётчик прогресса
интервью, в `epic-to-issues` - готовность задач и зависимости миграций,
в `analyze-via-sonar` - настройки текущего проекта, в `cavecrew` -
самодостаточные роли и выбор доступного механизма делегации.

## Начало работы

Нужны Git, Python 3.12+ и macOS или Linux. Дополнительные среды конкретного
скилла описаны в его `SKILL.md`; менеджер не устанавливает эти среды и не
запускает рабочие сценарии скиллов.

```sh
git clone https://github.com/finnetrolle/skillset.git
cd skillset
make setup
make check test catalog-check
make diff
make install
```

`make install` копирует весь набор в `~/.agents/skills`. Эта папка используется
Codex на основной машине. Другой target задаётся явно:

```sh
make install TARGET="$HOME/.codex/skills"
```

Используй одну каноническую папку: копии с одинаковым именем в нескольких
источниках могут скрыть нужную версию. Claude Code на основной машине использует
26 ссылок на общие пакеты и самостоятельную копию `tdd`. Менеджер не создаёт
Claude aliases автоматически и не заменяет эту самостоятельную копию.

## Ежедневное управление

```sh
make list                        # Каталог текущего набора
make diff SKILL=tdd               # Отличия от установленной копии
make install SKILL=tdd            # Пакет вместе с зависимостями
make install                     # Весь набор
make rollback                    # Последняя установка в этот target
make upstream-check              # Новые коммиты зарегистрированных источников
make upstream-diff SKILL=tdd      # Upstream и локальная адаптация SKILL.md
```

Редактируй `skills/<name>/`, проверяй результат и сохраняй его в Git.
Push публикует версию на GitHub, install доставляет её на текущую машину.
Обе операции выполняются по команде: редактирование файлов не запускает их.

```sh
make check test
make catalog
make catalog-check
git add skills sources.lock.json docs/catalog.md
git commit -m "docs: improve skill instructions"
git push
make install SKILL=grill-me
```

При добавлении пакета зарегистрируй его в `sources.lock.json`: происхождение,
исходный путь или upstream source/path, исходный manifest файлов и зависимости.
`baseline_files` хранит контрольные суммы импортированной версии; актуальные
файлы находятся в `skills/` и Git. Не меняй baseline ради обхода конфликта.
Каталог пересоздаётся через `make catalog`; вручную его не редактируй.
Правила документации конкретного проекта задаются в его `AGENTS.md` или
`CLAUDE.md`.

## Обновление из первоисточников

`sources.lock.json` содержит закреплённые коммиты и сопоставления пакетов.
По умолчанию `upstream-diff` использует Matt Pocock. Для официального пакета
OpenAI источник выбирается явно:

```sh
.venv/bin/python scripts/manage.py upstream-diff --source openai --skill security-best-practices
```

Проверка нового HEAD не меняет pin, рабочие файлы или установленные копии.
Сопоставляй изменения upstream с локальным контрактом, переноси полезные
правки и затем обновляй pin с объяснением в коммите. Сохраняй LICENSE и notices.
Проверяемые сопоставления описаны в [сравнении](docs/matt-pocock-comparison.md).

## Защита правок и откат

Менеджер сравнивает контрольные суммы и executable bit с установленным manifest.
Ручные правки в target блокируют install и rollback до замены файлов.
При первом переносе существующая копия принимается только при точном
совпадении с текущим пакетом или исходным снимком.

```sh
.venv/bin/python scripts/manage.py install --dry-run
.venv/bin/python scripts/manage.py diff --skill tdd --full
```

Dry-run ничего не создаёт в target. Для согласованной замены местных правок
есть `--overwrite-edits`; сначала перенеси нужные изменения в репозиторий.
Вытесняемые файлы сохраняются в резервной копии.

Состояние, manifests и backups находятся в `<target>/.skillset/`.
У изменяющей установки есть transaction ID. Повторная установка той же версии
ничего не меняет; другие пакеты в target сохраняются.

```sh
.venv/bin/python scripts/manage.py rollback --transaction <id>
```

Откатывай установки от последней к предыдущим. После прерванного install
или rollback новые установки заблокированы до восстановления pending transaction
командой rollback. Резервные копии остаются после восстановления.

Для переноса совпадающих текущих пакетов из другой папки:

```sh
.venv/bin/python scripts/manage.py install --dry-run --migrate-from "$HOME/.codex/skills"
.venv/bin/python scripts/manage.py install --migrate-from "$HOME/.codex/skills"
```

Миграция проверяет содержимое и сохраняет backup для rollback.
`.system`, плагины и другие директории остаются на месте. Target должен быть
канонической папкой: менеджер отклоняет замену aliases.

## Формат и проверка

`scripts/manage.py` возвращает TOON по умолчанию, JSON с `--json`.
Ошибки и подсказки идут в stdout. Exit codes: 0 - успех, 1 - ошибка проверки
или операции, 2 - неверные аргументы. Без команды выводится каталог.
`show`, `diff` и `upstream-diff` показывают previews; `--full` возвращает
полный текст, `--output` сохраняет upstream patch.

`make check test catalog-check` проверяет упаковку, CLI и актуальность каталога.
Тесты используют временные targets и синтетические журналы.
GitHub Actions отключены; проверки выполняются локально.

Зависимости пакетов обеспечивают доставку общих контрактов. Например,
`verify-changes` и `two-axis-review` устанавливаются вместе.
Это зависимости файлов, а не порядок выполнения задач.

В `data/` находятся согласования текущего набора и агрегированная статистика
его использования. Сырые журналы и сообщения не публикуются.
Происхождение и исходные хеши записаны в `sources.lock.json`.
`.venv`, caches, `.DS_Store` и временные файлы исключены из Git.
