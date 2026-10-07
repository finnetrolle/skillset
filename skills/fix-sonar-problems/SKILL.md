---
name: fix-sonar-problems
description: Исправление технодолга из реестра sonar_problems.md по одной проблеме за раз: чтение записи, fix согласно рекомендации, проверка Gradle-сборкой, обновление реестра. Использовать, когда пользователь просит "исправь технодолг из sonar_problems", "исправь проблемы из sonar_problems.md", "fix sonar problems", "закрой находки SonarQube", или invokes /fix-sonar-problems.
---

# Исправление проблем из sonar_problems.md

Задача: закрыть проблемы, зарегистрированные в `sonar_problems.md` (корень проекта), и обновить реестр. Реестр ведётся по правилам из CLAUDE.md: каждая запись - долг, гасится в тех же изменениях, что затрагивают соответствующую область.

## Шаг 1. Прочитать реестр

Прочитать `sonar_problems.md` целиком. Если открытых проблем нет (есть только раздел истории) - сообщить пользователю и остановиться.

Сортировка работ: сначала VULNERABILITY/BUG, затем CODE_SMELL; внутри типа - по серьёзности (BLOCKER > CRITICAL > MAJOR > MINOR).

## Шаг 2. Исправить по одной проблеме

Для каждой записи:

1. Прочитать затронутые файлы ДО редактирования (правило: не предлагать изменения в непрочитанном коде).
2. Выбрать вариант из разделка "Как SonarQube советует исправить". Если в записи отмечен рекомендуемый для проекта вариант - использовать его.
3. Проверить, что новый артефакт/файл не попадает под `.gitignore`.
4. Одна проблема - один цикл правка-проверка. Не править пачкой.

### TDD-граница (из CLAUDE.md)

- Изменения build-инфраструктуры (`build.gradle.kts`, `settings.gradle.kts`, `gradle/*`, Version Catalog, verification metadata) - exempt от RED-first: это metadata, не production-код. Но полный `./gradlew build` обязан быть GREEN до и после.
- Изменения production-кода (`src/`) - обязателен tdd-скилл: один behavior-тест, RED по поведенческой причине, минимальный код, GREEN. Proxy-поведение - только E2E через реальные Armeria-серверы.

## Шаг 3. Специфика известных правил

Уроки, уже полученные на этом проекте - применять, не повторять ошибки.

### kotlin:S6474 (dependency verification отсутствует)

Генерировать строго с `--refresh-dependencies`:

```bash
./gradlew --write-verification-metadata pgp,sha256 --export-keys --refresh-dependencies
```

Почему `--refresh-dependencies` обязателен: без него артефакты, уже лежащие в кеше Gradle, не резолвятся заново и НЕ попадают в metadata. Сборка при этом проходит, а позже падает с "Checksums are missing from verification metadata" (наблюдалось на `kotlinx-coroutines-bom-1.8.0.pom`).

Создаёт три файла, все коммитятся (`.gitignore` не должен исключать `gradle/`):
- `gradle/verification-metadata.xml`;
- `gradle/verification-keyring.gpg`;
- `gradle/verification-keyring.keys`.

Ключи, недоступные с keyserver, попадают в `ignored-keys` - их артефакты проверяются контрольными суммами sha256. Это допустимый fallback по рекомендации правила (integrity без authenticity).

`dependencyVerification { mode = STRICT }` в `settings.gradle.kts` не добавлять: дефолтный режим уже роняет сборку на отсутствующей записи.

Доказательство работоспособности (не пропускать):

```bash
./gradlew --refresh-dependencies build
```

Если упало "Checksums are missing" - не отключать верификацию, а регенерировать metadata командой выше. Отчёт о причине: `build/reports/dependency-verification/at-*/dependency-verification-report.html`.

### kotlin:S6624 (захардкоженные версии)

Version Catalog `gradle/libs.versions.toml`:

```toml
[versions]
armeria = "1.41.0"
hoplite = "2.9.0"

[libraries]
armeria = { module = "com.linecorp.armeria:armeria", version.ref = "armeria" }
hoplite-core = { module = "com.sksamuel.hoplite:hoplite-core", version.ref = "hoplite" }
```

- Зависимости одной семьи версий (`hoplite-core`/`hoplite-hocon`) связывать одним `version.ref`.
- Catalog подключается к `build.gradle.kts` автоматически (Gradle 8+, каталог в `gradle/libs.versions.toml`), в `settings.gradle.kts` ничего регистрировать не надо.
- Версии в блоке `plugins {}` через каталог напрямую не выражаются (нужен `pluginManagement`) - не трогать, пока правило их не флагает.
- Плагин `io.spring.dependency-management` не подходит: проект без Spring.

### Прочие правила

Если правило не из списка выше - взять рекомендацию из записи (раздел "Как SonarQube советует исправить") и действовать по ней. Для production-кода - см. TDD-границу в шаге 2.

## Шаг 4. Финальная проверка

```bash
./gradlew build
```

Обязан быть GREEN. Для изменений dependency verification - дополнительно `./gradlew --refresh-dependencies build` (см. шаг 3).

## Шаг 5. Обновить реестр

После GREEN:

1. Удалить исправленные записи из секции проблем.
2. Обновить сводную таблицу (только оставшиеся проблемы).
3. Каждое исправление записать в раздел `## История исправлений` (создать при отсутствии) строкой: дата, правило, суть исправления.
4. Если открытых проблем не осталось - в шапке написать "открытых проблем нет".
5. Стиль файла: русский, без длинных тире (только `-`), технические термины без искажений.

## Шаг 6. Отчёт пользователю

По каждой проблеме: правило, что сделано, чем проверено (команда + результат GREEN). Плюс: предложение перегенерировать реестр (шаг 7), если пользователь хочет подтверждение от SonarQube, что находки закрыты.

## Шаг 7. Перепроверка через SonarQube (по запросу пользователя)

Команды запуска и прогона встроены сюда намеренно - не искать их в других скиллах и не выводить самостоятельно. Полная процедура сбора отчёта (API, формат файла) - в скилле `analyze-via-sonar`; этот шаг только поднимает сервер и гонит анализ.

1. Проверить/поднять контейнер (порт 9000, дефолтный пароль admin/admin - только локальный одноразовый контейнер):

```bash
docker ps --filter name=vigilant-sonar --format '{{.Names}}'
# если пусто:
docker run -d --name vigilant-sonar -p 9000:9000 sonarqube:26.8.0.126808-community
```

2. Ждать готовности (старт 1-3 минуты; в 26.x статус `UP`, не `GREEN`):

```bash
curl -s http://localhost:9000/api/system/status   # {"status":"UP"}
```

3. Токен (существующий или новый; не записывать в файлы репозитория). Пароль админа брать из gitignored-файла `.claude/sonar.env` (`SONAR_ADMIN_PASSWORD`), не хардкодить:

```bash
source .claude/sonar.env
curl -s -u "admin:$SONAR_ADMIN_PASSWORD" -X POST \
  'http://localhost:9000/api/user_tokens/generate?name=vigilant-local-analysis'
```

Если 401 - файла `.claude/sonar.env` нет или пароль устарел. Спросить у пользователя актуальный пароль, записать в `.claude/sonar.env` и повторить. НЕ пересоздавать контейнер - потеряется история проекта. Существующий токен `squ_...` у пользователя тоже подходит без генерации нового.

4. Анализ (тесты + JaCoCo обязательны до `sonar`):

```bash
./gradlew test jacocoTestReport sonar \
  -Dsonar.host.url=http://localhost:9000 \
  -Dsonar.token=<TOKEN>
```

5. Дальше - шаги 5-6 скилла `analyze-via-sonar` (API-запросы, перезапись `sonar_problems.md`, отчёт). Предупредить пользователя о дефолтном пароле админа, если контейнер поднимался в этом сеансе.
