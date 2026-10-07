# Сравнение с Matt Pocock

Сравнение выполнено 7 октября 2026 года по всему дереву
[mattpocock/skills](https://github.com/mattpocock/skills) на коммите
[`dd400c3`](https://github.com/mattpocock/skills/tree/dd400c3ad65e57c06f05e832e0aac92c7992f34d).
В дереве найдено 38 скиллов: 20 engineering, 7 productivity, 7 in-progress,
4 misc. Основной manifest содержит 27 скиллов и версию 1.3.1; ветка
in-progress не считается стабильным комплектом для автоматической установки.

Отчёт фиксирует первоначальное сравнение. Последующие решения о составе набора
записываются в [реестре аудита](../data/skill-audit.json).

| Ваш скилл | Аналог Matt | Решение и причина |
|---|---|---|
| tdd | tdd | Сохранён ваш behavior-first контракт: regression/E2E, concurrency, независимый oracle и режимы по риску. Добавлена совместимость с существующим GLOSSARY.md. Строгий одинаковый цикл Matt для любой задачи не перенесён. |
| grill-me | grill-me / grilling | Сохранены пять измерений неоднозначности, thresholds и право закончить интервью. Добавлены дерево решений, проверка фактов до вопросов и уважение уже принятых решений. Большая рубрика перенесена в reference; удалены отсутствующие max/bugbook callers. |
| issue-dialogue | to-spec | Сохранены короткий диалог и подробная issue. Добавлен синтез уже согласованного разговора без нового интервью; domain-modeling вызывается по необходимости. |
| epic-to-issues | to-tickets | Сохранён: tracer-bullet slices, dependency graph и границы публикации уже присутствуют. Замена не даёт подтверждённого выигрыша. |
| arch-review-to-epic | improve-codebase-architecture | Сохранён: ваш обзор проверяет нормативную спецификацию и переводит нарушения в backlog. У Matt полезна идея deep modules, но она не заменяет соответствие проектному контракту. |
| two-axis-review / verify-changes | code-review | Сохранены две независимые оси, evidence contract, полный scope текущих изменений и delta review. Универсальный цикл повторных ревью committed diff не перенесён. |
| implement | implement / implement-spec | Сохранены exact source, readiness и evidence ledger. Убраны жёсткие имена моделей; routing описывает риск и необходимые возможности. Проектный WORK_ITEMS-адаптер вынесен в reference. |
| skill-usage-report | Прямого аналога нет | Сохранён. Исправлено чтение .system; добавлен --all для работы вне репозиториев, с явным scope. |
| minto-explain / fix-sonar-problems | Прямого аналога нет | Исправлены относительная ссылка на caveman и невалидный YAML description соответственно. Поведение сохранено. |
| Остальные 30 исходных скиллов | Прямые аналоги отсутствуют либо покрывают другую границу | Сохранён полный снимок с ресурсами. Частота помогает выбрать следующие улучшения, но отсутствие наблюдений не означает ненужность. |

Остальные 30: analyze-pitest, analyze-via-sonar, archify,
removed-presentation-template, automation-platform-tco, axi, cavecrew,
caveman, caveman-commit, caveman-compress, caveman-help, caveman-review,
caveman-stats, commit-push, find-skills, frontend-skill, github-ai-trending-pdf,
how-would-you-do-it, jira-repo-excel-matrix, kdoc, landing-redline, lavish, pdf,
platform-release-notes, playwright, security-best-practices, sync-agent-skills,
tailor-cv-to-vacancy, what-next, workshop-thesis-factcheck.

Добавлены три самостоятельных пакета с MIT-лицензией Matt Pocock:

| Новый скилл | Что взято | Адаптация |
|---|---|---|
| diagnosing-bugs | Воспроизведение, минимизация, проверяемые гипотезы, loop template | Масштаб процесса по сложности бага; существующие E2E runners имеют приоритет; instrumentation и стресс-проверки ограничены scope и budget. |
| domain-modeling | Ubiquitous language, glossary, ADR templates | Существующие CONTEXT/GLOSSARY/ADR и принятые термины имеют приоритет; обсуждение не разрешает автоматически менять документы. |
| writing-for-agents | Точность указателей, условные references, стоимость лишнего контекста | Сохраняются intent, approval и invocation policy; host-specific Codex/Claude механизмы разделены; краткость не оправдывает удаление контракта. |

Оставлены кандидатами без установки: research, wayfinder, retro, handoff,
teach, triage, prototype, codebase-design, pr, to-questionnaire, wait-what,
grill-with-docs, wizard, ask-matt, setup-matt-pocock-skills. Их польза требует
отдельного рабочего сценария; setup не нужен при собственном менеджере.
Misc и in-progress не импортированы. Поэтому в наборе нет второго перекрывающего
пайплайна спецификаций, реализации и ревью.

Сверка локальных источников дала 31 одинаковую общую копию, 9 Codex-only
скиллов и tdd с одинаковыми рабочими инструкциями, но разными UI metadata.
Снимок tdd взят из Codex с сохранением UI. .DS_Store исключён. Claude aliases
на общую папку сохраняются; отдельная копия Claude tdd не меняется этой поставкой.

## Как обновлять сравнение

`make upstream-check` проверяет HEAD upstream, не меняя pin и установленный
набор. `make upstream-diff SKILL=tdd` показывает изменения пакета upstream
между закреплённым и актуальным коммитами, а также вашу адаптацию SKILL.md
относительно закреплённой версии. По умолчанию выводятся previews, `--full`
возвращает полные diff; дополнительные локальные resources сверяй отдельно.
Не заменяй адаптацию целым
файлом upstream. После принятия полезных изменений обнови pin и provenance,
проверь поведение и установи новую версию явной командой.

Первоначальный импорт после очистки истории доступен в первом коммите.
Из него исключён удалённый корпоративный шаблон презентации. Числа в этом
историческом сравнении описывают исходный набор до очистки.

## Доработка epic-to-issues после аудита

Повторная сверка выполнена на upstream-коммите
[`f3fc563`](https://github.com/mattpocock/skills/tree/f3fc5632f401156837ee3872f14fe33ccf1024ea).
Пакет `to-tickets` не изменился относительно исходного pin. Пользователь
согласовал четыре доработки своей версии:

- Единая готовность задач: Draft и Blocked исключены из runnable frontier;
  готовая задача с незавершёнными блокировками ожидает их выполнения.
- Для behavioral acceptance используется контракт уже сохранённого
  issue-dialogue; структурные критерии получают применимые способы проверки.
  Записывается план проверки, а не заявление о пройденных тестах.
- Expand, migrate, contract раскрыт по этапам, зависимостям и проверкам.
  Общая integration branch допускается после согласования, с сохранением
  правил верификации и завершения задач проекта.
- Согласование явно проверяет размер задач, блокировки и необходимость
  объединения или разделения. Публикация идёт в порядке зависимостей с
  заменой proposal IDs фактическими ссылками.

Карта исследования, нормативный эпик, оценки, покрытие требований и правила
вызова сохранены. Зависимость от issue-dialogue зарегистрирована для доставки
канонического контракта вместе со скиллом. Upstream pin не менялся.
