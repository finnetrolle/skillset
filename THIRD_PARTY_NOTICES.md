# Происхождение и лицензии

Текущий набор содержит 27 пакетов. Происхождение импортированных версий,
исходные контрольные суммы и закреплённые upstream-коммиты записаны в
[sources.lock.json](sources.lock.json). `origin: local` означает локальный
импорт и не указывает автора или общую лицензию.

Лицензии и notices сохраняются внутри соответствующих пакетов.
Для пакетов без LICENSE отдельная лицензия в этом репозитории не назначена.

| Пакеты | Источник | Сохранённые лицензии и notices |
|---|---|---|
| diagnosing-bugs, domain-modeling, writing-for-agents | [mattpocock/skills на закреплённом коммите](https://github.com/mattpocock/skills/tree/dd400c3ad65e57c06f05e832e0aac92c7992f34d), адаптации | MIT, Copyright 2026 Matt Pocock: [diagnosing-bugs](skills/diagnosing-bugs/LICENSE), [domain-modeling](skills/domain-modeling/LICENSE), [writing-for-agents](skills/writing-for-agents/LICENSE) |
| security-best-practices | [openai/skills на закреплённом коммите](https://github.com/openai/skills/tree/49f948faa9258a0c61caceaf225e179651397431/skills/.curated/security-best-practices) | [Apache-2.0](skills/security-best-practices/LICENSE.txt) |
| archify | Локальный импорт; [tt-a1i/archify](https://github.com/tt-a1i/archify) указан в [metadata пакета](skills/archify/skill-release.json) | [MIT](skills/archify/LICENSE), Copyright 2026 tt-a1i и 2025 Cocoon AI; [notices для ресурсов](skills/archify/THIRD_PARTY_NOTICES.md) |

`security-best-practices` проверен 07.10.2026: все 13 файлов, включая
LICENSE.txt, совпадают с закреплённым первоисточником. Исходный путь локального
импорта сохранён в реестре отдельно от установленного upstream.

Остальные пакеты сохраняют происхождение `local` и исходный manifest.
Сопоставление личного скилла с аналогом Matt Pocock не меняет его происхождение.
Обновления рассматриваются явно и сохраняют лицензии вместе с материалами.
