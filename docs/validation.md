# Проверка поставки

Проверка менеджера проходит через его публичный CLI в временных каталогах.
Сценарии: ресурсы и executable modes; зависимые пакеты; idempotence; точные
backup/rollback; ручные правки; ранний отказ без частичной установки; миграция
старых копий без удаления чужих скиллов; dry-run без создания target; ошибки
аргументов и метаданных; потеря процесса во время install/rollback; повреждённый
backup; запрет замены aliases. Forced rollback также сохраняет вытесняемые
ручные правки. Upstream test использует локальный Git-репозиторий с двумя
коммитами и проверяет сохранение pin и пользовательской адаптации.

Regression test отчёта создаёт синтетические SQLite/JSONL журналы Codex и
Claude Code. Проверяет учёт .system, --all, дедупликацию и атрибуцию usage.
Реальные пользовательские журналы не используются в CI.

Независимый поведенческий прогон в изолированном fixture:

| Скилл | Сценарий | Наблюдение |
|---|---|---|
| grill-me | Уже согласован CSV import, требуется найти пробелы | Принятые решения сохранены, один вопрос о partial/atomic import. Проверен первый ход, не полный диалог. |
| domain-modeling | Совет о customer/client, CONTEXT.md существует, писать запрещено | Использован канонический customer; CONTEXT не менялся, glossary/ADR не создавались. |
| writing-for-agents | Сократить release skill с explicit-only policy и approval | Контракт сохранён, публикации и правок policy нет. |
| issue-dialogue | Записать согласованный /health header change | Локальная issue с evidence matrix без нового интервью; production fixture не менялся. |

Прогон также обнаружил неоднозначные безусловные фразы об обновлении
GLOSSARY.md. Они заменены условными инструкциями с приоритетом CONTEXT.md и
разрешённого scope. В reference writing-for-agents разделены Codex и Claude
invocation controls.

HTTP fixture baseline в sandbox не запустился из-за запрета bind localhost.
Это ограничение поведенческого прогона, не подтверждение работоспособности
реальной /health реализации. В этом репозитории она не менялась.

`make check` проверяет упаковку 44 скиллов: YAML, имена, файлы, UI icons,
прямые и транзитивно связанные Markdown references. Это не полный runtime
тест всех сторонних workflow. Некоторые скиллы требуют Docker, JVM/Gradle,
браузер, соответствующий plugin или Claude-specific hooks; их ресурсы
сохранены, но такие среды не устанавливаются менеджером.

Bundled quick_validate.py дополнительно пропустил 42 пакета. Для kdoc и lavish
его ограниченный allowlist отвергает сохранённые host-specific поля
user-invocable и argument-hint/author. Эти исходные поля не удалены ради
валидатора: собственная проверка сохраняет совместимость набора с обоими
хостами и проверяет обязательные name/description и ресурсы.
