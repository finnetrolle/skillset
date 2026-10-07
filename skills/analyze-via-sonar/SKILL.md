---
name: analyze-via-sonar
description: >-
  Анализ проекта через локальный SonarQube в Docker с отчётом
  sonar_problems.md: место, причина и рекомендация по каждой проблеме.
  Использовать для "проанализируй через sonar", "проверь sonarqube",
  "analyze via sonar", при /analyze-via-sonar в Claude Code или
  $analyze-via-sonar в Codex.
---

# Анализ проекта через SonarQube

Задача: прогнать статический анализ проекта через локальный SonarQube Community (Docker) и собрать все проблемы (bugs, vulnerabilities, security hotspots, code smells) в файл `sonar_problems.md` в корне проекта.

## Шаг 1. Проверить/поднять SonarQube

```bash
docker ps --filter name=vigilant-sonar --format '{{.Names}}'
```

Сначала проверить доступность Docker daemon через `docker info` с внешним
timeout 10 секунд; зависший CLI завершить и считать infrastructure failure. Если контейнер
существует, но остановлен, запустить `docker start vigilant-sonar`. Только если
контейнера ещё нет, создать его:

```bash
docker run -d --name vigilant-sonar -p 127.0.0.1:9000:9000 \
  sonarqube:26.8.0.126808-community
```

- Порт 9000 доступен только через loopback. У свежего сервера пароль admin/admin
  по умолчанию - это допустимо только для одноразового локального контейнера.
- Ждать готовности: в SonarQube 26.x состояние `UP`, а не `GREEN`:

```bash
curl -s http://localhost:9000/api/system/status   # {"status":"UP"}
```

Старт занимает 1-3 минуты.

## Шаг 2. Токен

Авторизация для генерации токена - basic auth `admin:<пароль>`. Пароль админа лежит в gitignored-файле `.claude/sonar.env` (переменная `SONAR_ADMIN_PASSWORD`); SonarQube принудительно требует смену пароля при первом входе в web UI, и смена переживает перезапуск контейнера (данные живут внутри контейнера без volume).

Порядок:

Сначала ограничить права файла и прочитать только ожидаемые ключи. Не делать
`source .claude/sonar.env`: env-файл с секретами не должен исполняться как
shell-код. Этот блок выполнить один раз в том же shell, где пойдут команды
ниже:

```bash
chmod 600 .claude/sonar.env
sonar_env_value() {
  local key="$1" value
  value="$(awk -v key="$key" '
    index($0, key "=") == 1 { value = substr($0, length(key) + 2) }
    END { print value }
  ' .claude/sonar.env)"
  if [[ "$value" == \'*\' || "$value" == \"*\" ]]; then
    value="${value:1:${#value}-2}"
  fi
  printf '%s' "$value"
}
SONAR_ADMIN_PASSWORD="$(sonar_env_value SONAR_ADMIN_PASSWORD)"
SONAR_TOKEN="$(sonar_env_value SONAR_TOKEN)"
```

1. Если в `.claude/sonar.env` уже есть переменная `SONAR_TOKEN` - проверить её валидность и при успехе использовать без revoke/generate:

```bash
curl -fsS --connect-timeout 5 --max-time 15 -u "$SONAR_TOKEN:" \
  'http://localhost:9000/api/authentication/validate'
# {"valid":true} = токен жив; false = удалить только строку SONAR_TOKEN и продолжить
```

2. Отозвать токен прошлой сессии, если он существует (значение не персистится - повторная генерация с тем же именем без отзыва падает с `already exists`):

```bash
curl -sS --connect-timeout 5 --max-time 15 -o /dev/null -w '%{http_code}\n' \
  -u "admin:$SONAR_ADMIN_PASSWORD" -X POST \
  'http://localhost:9000/api/user_tokens/revoke?name=vigilant-local-analysis'
# 204 = отозван (тело пустое), 404 = не существовал; оба варианта нормальны
```

3. Сгенерировать свежий токен, прочитать поле `token` (`squ_...`) из ответа и сразу дописать строку `SONAR_TOKEN='<значение>'` в `.claude/sonar.env` (gitignored), чтобы следующая сессия переиспользовала его по шагу 1:

```bash
curl -fsS --connect-timeout 5 --max-time 30 \
  -u "admin:$SONAR_ADMIN_PASSWORD" -X POST \
  'http://localhost:9000/api/user_tokens/generate?name=vigilant-local-analysis'
```

4. Если 401: файл `.claude/sonar.env` отсутствует или пароль устарел. НЕ пересоздавать контейнер (сотрёт историю проекта в SonarQube) и не подбирать пароль. Спросить у пользователя актуальный пароль админа, записать его в `.claude/sonar.env` (файл gitignored; сам пароль в SKILL.md и другие файлы репозитория не писать) и повторить команды.

Токен хранить только в `.claude/sonar.env`; в файлы репозитория не записывать. Последующие API-вызовы (шаг 5) идут с токеном, а не с паролем - смена пароля на них не влияет.

Особенность curl: авторизация токеном требует двоеточия после него, иначе curl спросит пароль интерактивно: `curl -u "$TOKEN:" ...`.

## Шаг 3. Gradle-настройка

В `build.gradle.kts` уже подключено. Проверить настройки; при расхождении
остановиться и доложить, а не менять build-конфигурацию в рамках анализа:

- плагин `id("org.sonarqube") version "7.4.0.8496"`;
- блок `sonar` со свойствами: `sonar.projectKey=io.vigilant:vigilant`,
  `sonar.projectName=vigilant`,
  `sonar.coverage.jacoco.xmlReportPaths=build/reports/jacoco/test/jacocoTestReport.xml`,
  `sonar.scm.disabled=true` (pipeline сам определяет scope через Git, а не через
  SCM-сенсор SonarQube).

`sonar.coverage.jacoco.xmlReportPaths` указывать строкой-литералом: передача Gradle `Provider` превращается в `map(...)` и SonarQube её не распознаёт.

## Шаг 4. Прогнать анализ

Токен передавать через переменную окружения `SONAR_TOKEN`:

```bash
SONAR_TOKEN="$SONAR_TOKEN" ./gradlew test jacocoTestReport sonar \
  -Dsonar.host.url=http://localhost:9000
```

- Допустим и `-Dsonar.token=<TOKEN>` в командной строке: проверено 2026-08-21 на плагине 7.4.0.8496 + SonarQube 26.8 - анализ загружается (`analysisDate` в `api/project_branches/list` обновляется). Ранее фиксировался 401 на `GET /api/v2/analysis/version`; если он воспроизведётся - вернуться к `SONAR_TOKEN`.
- Тесты + JaCoCo обязательны до `sonar`, иначе отчёт покрытия не попадёт в анализ. Первый запуск скачивает плагин, повторные занимают секунды. При неизменённых входах задачи Gradle уходят в `UP-TO-DATE` (кроме самого `sonar`) - это нормально, форсировать перезапуск не нужно.

После Gradle не читать API проекта сразу: загрузка анализа асинхронна. Взять
`ceTaskUrl` и `projectKey` из `build/sonar/report-task.txt`, проверить, что
project key равен `io.vigilant:vigilant`, и опрашивать `ceTaskUrl` с токеном до
`SUCCESS`. `FAILED`, `CANCELED`, отсутствие файла или timeout 180 секунд -
infrastructure failure; старые API-данные не использовать.

## Шаг 5. Собрать результаты через API

Использовать загруженный `$SONAR_TOKEN` и следить за экранированием: в
query-параметрах `componentKeys`/`component` ключ проекта -
`io.vigilant%3Avigilant`. Все запросы выполнять с `--connect-timeout 5`,
`--max-time 30`, `--fail-with-body` и проверять JSON через `jq -e`.

1. Quality gate:

```bash
curl -sS --fail-with-body --connect-timeout 5 --max-time 30 \
  -u "$SONAR_TOKEN:" 'http://localhost:9000/api/qualitygates/project_status?projectKey=io.vigilant%3Avigilant'
```

2. Метрики (в ответе имя метрики лежит в поле `metric`, значения - в `value` или `periods`):

```bash
curl -sS --fail-with-body --connect-timeout 5 --max-time 30 \
  -u "$SONAR_TOKEN:" 'http://localhost:9000/api/measures/component?component=io.vigilant%3Avigilant&metricKeys=bugs,vulnerabilities,security_hotspots,code_smells,coverage,duplicated_lines_density,ncloc,sqale_rating,reliability_rating,security_rating'
```

3. Список проблем (важно: `ps=500` обязателен - без него лимит 100 и тишина усекает выдачу; если `total` больше числа полученных issues - добирать страницы параметром `&p=2`, `&p=3`, ...):

```bash
curl -sS --fail-with-body --connect-timeout 5 --max-time 30 \
  -u "$SONAR_TOKEN:" 'http://localhost:9000/api/issues/search?componentKeys=io.vigilant%3Avigilant&resolved=false&ps=500'
```

Из каждого issue брать: `type`, `severity`, `component` (последний сегмент после `:`), `line`, `rule`, `message`.

4. Security hotspots: в `issues/search` они НЕ попадают - отдельный endpoint. Запрашивать всегда, даже если метрика `security_hotspots = 0` (метрика берётся из снапшота анализа и должна сходиться; расхождение - повод перепроверить):

```bash
curl -sS --fail-with-body --connect-timeout 5 --max-time 30 \
  -u "$SONAR_TOKEN:" 'http://localhost:9000/api/hotspots/search?projectKey=io.vigilant%3Avigilant&ps=500'
```

Из каждого hotspot брать: `ruleKey`, `message`, `component`, `line`, `vulnerabilityProbability`, `securityCategory`, `status`. Для описания правила - тот же `api/rules/show` (шаг 5.5).

5. Описание правила (важно: текст лежит в `descriptionSections`, поля `htmlDescription`/`mdDescription` пусты):

```bash
curl -sS --fail-with-body --connect-timeout 5 --max-time 30 \
  -u "$SONAR_TOKEN:" 'http://localhost:9000/api/rules/show?key=kotlin%3AS6624'
```

Секции: `introduction`, `root_cause` (почему проблема), `how_to_fix` (рекомендация SonarQube), `resources` (CWE/OWASP/документация). HTML в `content` секций надо зачищать в текст.

## Шаг 6. Записать sonar_problems.md

Файл `sonar_problems.md` в корне проекта, на русском. Структура:

1. Шапка: дата анализа, версия сервера, ключ проекта, статус quality gate, итоговые счётчики.
2. По каждой уникальной проблеме (группировать одинаковые правила по файлу в одну секцию с таблицей вхождений):
   - таблица метаданных: правило, название правила, тип, серьёзность, где (файл:строка);
   - дословное `message` от SonarQube;
   - **Что это** - пересказ introduction/root_cause своими словами;
   - **Почему это проблема** - риски из root_cause (для уязвимостей - CWE/OWASP классификации);
   - **Как SonarQube советует исправить** - из how_to_fix, включая примеры кода и команды; если у правила несколько вариантов - перечислить все и отметить рекомендуемый для этого проекта;
   - ссылки из resources.
3. Финальная сводная таблица: правило / тип / серьёзность / количество / файл.

Если проблем 0: не выдумывать секции - шапка с метриками, строка "открытых проблем нет" и секция "История исправлений" с записью о прогоне (дата, что подтверждено, изменение метрик относительно прошлого прогона, если менялись). Существующую историю в файле сохранять.

Требования к файлу: без длинных тире (только `-`), технические термины без искажений, команды и примеры кода в блоках.

## Шаг 7. Отчёт пользователю

Кратко: статус quality gate, таблица метрик, список найденных проблем одной строкой на каждую, ссылка на `sonar_problems.md`, URL web UI (`http://localhost:9000`, проект "vigilant"). Отдельно предупреждать об уязвимостях и о дефолтном пароле админа, если контейнер поднимался в этом сеансе.
