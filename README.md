# Skillset

Источник актуальных версий личного набора скиллов: 41 исходный пакет и три
адаптации Matt Pocock. Инструкции, scripts, references, assets и UI metadata
хранятся вместе. Встроенные скиллы и плагины управляются приложениями отдельно.

[Каталог по частоте использования](docs/catalog.md) ·
[Сравнение с Matt Pocock](docs/matt-pocock-comparison.md) ·
[Проверки и ограничения](docs/validation.md) ·
[Происхождение и лицензии](THIRD_PARTY_NOTICES.md)

## Начало работы

Нужны Git, Python 3.12+ и macOS или Linux. Скиллы могут требовать дополнительные
среды; менеджер их не устанавливает и не запускает код скиллов.

```sh
git clone https://github.com/finnetrolle/skillset.git
cd skillset
make setup
make check test catalog-check
make diff
make install
```

`make install` копирует весь набор в `~/.agents/skills`. Эта папка уже используется
Codex на исходной машине. Другой target задаётся явно:

```sh
make install TARGET="$HOME/.codex/skills"
```

Используй одну каноническую папку. Дубли с одинаковым именем в нескольких
источниках могут скрыть установленную версию. При необходимости обнови список
скиллов в приложении или начни новый чат.

## Ежедневное управление

```sh
make list                        # Полный список
make diff SKILL=tdd               # Отличия от установленной копии
make install SKILL=tdd            # Пакет вместе с его зависимостями
make install                     # Весь набор
make rollback                    # Последняя установка для этого target
make upstream-check              # Есть ли новый commit у Matt Pocock
make upstream-diff SKILL=tdd      # Upstream changes + локальная адаптация SKILL.md
```

Изменяй `skills/<name>/`, проверь и закоммить изменения, затем выполни install.
Push сохраняет версию на GitHub; install доставляет её на текущую машину. Эти
операции выполняются явно. Создание или редактирование скилла не запускает push
и не переписывает installed copies автоматически.

```sh
make check test
make catalog
make catalog-check
git add skills sources.lock.json docs/catalog.md
git commit -m "feat: improve skill workflow"
git push
make install SKILL=skill-name
```

При добавлении пакета зарегистрируй его в `sources.lock.json`: origin,
исходный путь или upstream source/path, исходный file manifest и зависимости.
Не изменяй baseline_files импортированных версий ради обхода конфликта: это
контроль исходного снимка, а актуальные файлы живут в skills/ и Git.
Каталог генерируется командой `make catalog`; вручную его не редактируй.

Для `upstream-diff` mappings заведены и для адаптаций, и для сопоставленных
локальных скиллов. Pin фиксирует рассмотренный upstream commit. Проверка
нового HEAD не меняет pin. Переноси полезные изменения после сравнения с
локальным контрактом, затем обновляй pin с объяснением в commit. Сохранённые
LICENSE должны оставаться в пакете.

## Защита правок и откат

Менеджер сравнивает file hashes и executable bit со своей installed manifest.
Если deployed copy редактировали вручную, install/rollback останавливаются до
замены файлов. В первый раз существующая unmanaged copy принимается только
при точном совпадении с актуальным пакетом или исходным снимком.

Предварительный просмотр ничего не создаёт в target:

```sh
.venv/bin/python scripts/manage.py install --dry-run
.venv/bin/python scripts/manage.py diff --skill tdd --full
```

Если нужно намеренно заменить местные правки, сначала перенеси нужное в
репозиторий. Для явно согласованного overwrite есть `--overwrite-edits`;
вытесняемые файлы всё равно сохраняются в backup. По умолчанию этот флаг не
используется.

Состояние и backups хранятся в `<target>/.skillset/`. Каждая изменяющая установка
имеет transaction ID, сохранённые предыдущие файлы и manifest. Повторный install
той же версии ничего не меняет. Чужие пакеты не удаляются.

```sh
.venv/bin/python scripts/manage.py rollback --transaction <id>
```

Откатывай установки от последней к предыдущим. После прерванной установки или
отката новая установка заблокирована до `rollback`, который восстанавливает
последнюю pending transaction. Backups остаются после успешного восстановления.

При первоначальном переносе можно явно убрать известные старые копии:

```sh
.venv/bin/python scripts/manage.py install --dry-run --migrate-from "$HOME/.codex/skills"
.venv/bin/python scripts/manage.py install --migrate-from "$HOME/.codex/skills"
```

Убираются только совпадающие известные пакеты, с backup для rollback. `.system`,
плагины и чужие директории сохраняются. Алиасы менеджер не заменяет: укажи их
каноническую папку. Существующие Claude symlinks на `~/.agents/skills` продолжают
работать; независимая копия `~/.claude/skills/tdd` этой миграцией не меняется.

## Формат и проверка

`scripts/manage.py` возвращает TOON по умолчанию, JSON с `--json`; ошибки и
подсказки идут в stdout. Exit codes: 0 успех, 1 ошибка проверки/операции,
2 неверные аргументы. `show`, `diff` и `upstream-diff` возвращают previews с
путём к полному чтению (`--full`); upstream patch можно сохранить `--output`.
Отсутствие команды показывает полный каталог.

CLI tests используют только временные targets и синтетические журналы.
Workflow GitHub Actions содержит те же проверки; состояние его первого запуска
и внешние ограничения записаны в [отчёте проверки](docs/validation.md).
Циклические зависимости пакетов допустимы: например, verify-changes и
two-axis-review устанавливаются вместе; это не цикл исполнения work items.

Первый commit `67df44e` сохраняет исходный снимок. История изменений отделяет
его от менеджера и последующих адаптаций. Локальные пути происхождения указаны
в sources.lock.json без пользовательских сообщений и идентификаторов задач.
В data/ лежат только агрегированные usage counts за 30 дней. Большой retained
шаблон презентации сохранён целиком в обычном Git; .venv, caches, .DS_Store и
временные artifacts исключены. Репозиторий приватный.
