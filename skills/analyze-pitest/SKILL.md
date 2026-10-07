---
name: analyze-pitest
description: >-
  Мутационный анализ JVM-проекта через pitest: прогон, разбор mutations.xml,
  фильтрация Kotlin-шума и классификация SURVIVED/NO_COVERAGE с рекомендациями.
  Использовать только по явному запросу "мутационный анализ", "analyze
  pitest", "проверь мутантов", при /analyze-pitest в Claude Code или
  $analyze-pitest в Codex. Не входит в build, verifyAll или CI.
---

# Мутационный анализ pitest (on-demand)

Pitest медленный (десятки минут на E2E-тяжёлых проектах), поэтому вынесен из
регулярных проверок и запускается только этим скиллом по явному запросу.

Применим к JVM-проектам с настроенным плагином pitest (в vigilant:
`targetClasses = io.vigilant.*`, junit5). Если `./gradlew tasks` не показывает
задачу `pitest` - сообщить пользователю, что скилл неприменим, и остановиться.

## Шаг 1. Прогон

```bash
./gradlew pitest
```

Запускать как долгий процесс штатным механизмом хоста: background task в Claude
Code или yielded exec session в Codex. Не делать частый polling; сообщать
пользователю о ходе работы не реже, чем требует хост. Exit-код 1 при выживших
мутантах (если задан `mutationThreshold`) не означает сломанный билд - это вход
для анализа на шаге 2.

## Шаг 2. Парсинг отчёта

Читать `build/reports/pitest/mutations.xml` (надёжнее HTML). Скрипт-парсер:

```bash
python3 - <<'EOF'
import xml.etree.ElementTree as ET
from collections import Counter
t = ET.parse('build/reports/pitest/mutations.xml')
c = Counter(m.get('status') for m in t.getroot().iter('mutation'))
print(dict(c))
for m in t.getroot().iter('mutation'):
    if m.get('status') in ('SURVIVED', 'NO_COVERAGE'):
        print(m.get('status'), m.find('mutatedClass').text,
              '::', m.find('mutatedMethod').text,
              'line', m.find('lineNumber').text, '-',
              m.find('description').text)
EOF
```

## Шаг 3. Классификация (LLM-суждение)

Каждый `SURVIVED`/`NO_COVERAGE` мутант отнести к одному из классов:

1. **Шум Kotlin (игнорировать)** - `kotlin/jvm/internal/Intrinsics::checkNotNull*`
   и подобные compiler-интринсики; `replaced return value with null` на
   Unit-лямбдах логгеров. Типично для Kotlin+pitest без Arcmutate kotlin plugin.
2. **Реальная дыра в тестах (чинить)** - мутированная condition/арифметика/return
   на data path не поймана тестами: negated conditional, changed boundary,
   replaced return с осмысленным значением. Рекомендация: один убивающий RED-тест
   на мутанта через существующий документированный seam (в vigilant - E2E через
   реальные Armeria servers).
3. **Непрактично тестируемо (принять, объяснить)** - например, точные значения
   длительностей в E2E (мутация арифметики nanos→ms переживает `>= 0`-ассерты).
   Явно назвать причину, не маскировать под шум.

`TIMED_OUT` считать эквивалентом killed (мутант сломал тест бесконечным
ожиданием). `NO_COVERAGE` отдельно от survived: код вообще не исполняется
тестами - кандидат либо на тест, либо на удаление мёртвого кода.

## Шаг 4. Отчёт

Формат: сводка счётчиков, затем построчно `file:line: класс - мутация ->
действие`. Классы 2 и 3 не смешивать: "чинить" и "принять" - разные решения.
После отчёта спросить пользователя: чинить ли находки класса 2 сейчас
(TDD: RED-тест → минимальный фикс → GREEN) или только зафиксировать.

## Ограничения

- Ничего не править в коде без явного решения пользователя на шаге 4.
- Не добавлять pitest обратно в build/verifyAll/CI - он здесь именно потому,
  что вынесен из регулярных проверок.
