# Выбор и запуск scanner

Читать после определения проекта и перед анализом. Предпочитать существующую
команду проекта и scanner, интегрированный с его системой сборки.

## Gradle

Проверить `build.gradle(.kts)`, conventions/plugins, Version Catalog и документацию.
Использовать wrapper и настроенную задачу `sonar`/проектный alias. Сохранить
версию `org.sonarqube`, project key/name и многомодульную конфигурацию.
Не требовать конкретную версию плагина или фиксированный набор свойств.

Выполнить нужные compile/test/coverage tasks до scanner, проверив зависимости.
Например, если в этом проекте существуют `test`, `jacocoTestReport` и `sonar`:

```bash
SONAR_TOKEN="$SONAR_TOKEN" ./gradlew test jacocoTestReport sonar \
  -Dsonar.host.url="$SONAR_HOST_URL" \
  -Dsonar.projectKey="$SONAR_PROJECT_KEY"
```

Для других проектов выбрать их реальные tasks и coverage paths; не добавлять
JaCoCo только ради совпадения с примером. Для Java анализа нужна компиляция.
Свойства scanner должны разрешаться в реальные строки/пути; Gradle Provider
нужно корректно разрешить, а не передать строку `map(...)`. При неверной
настройке сообщить требуемое исправление, не менять build молча.

## Maven

Проверить `pom.xml`, profiles и wrapper. Использовать configured/pinned
SonarScanner for Maven и проектную команду compile/test/coverage. Пример для
проекта с настроенным goal `sonar:sonar`:

```bash
SONAR_TOKEN="$SONAR_TOKEN" ./mvnw verify sonar:sonar \
  -Dsonar.host.url="$SONAR_HOST_URL" \
  -Dsonar.projectKey="$SONAR_PROJECT_KEY"
```

Без wrapper применять установленный `mvn`, если это соответствует инструкциям
проекта. Учитывать profile и multi-module prerequisites, а не считать этот
пример универсальной командой.

## Другие проекты

При наличии project-specific scanner (например, .NET) применять его
документированный цикл: для .NET begin -> build/test -> end. Проверять способ
передачи секрета у этого scanner: `SONAR_TOKEN` не поддерживается всеми.

SonarScanner CLI подходит, если нет подходящего build-specific scanner и
сервер поддерживает язык. Прочитать `sonar-project.properties`/project scripts,
определить sources/tests/exclusions, обязательные build artifacts и формат
coverage. Предпочитать установленный или закреплённый проектом scanner:

```bash
SONAR_TOKEN="$SONAR_TOKEN" sonar-scanner \
  -Dsonar.host.url="$SONAR_HOST_URL" \
  -Dsonar.projectKey="$SONAR_PROJECT_KEY"
```

Это пример после настройки scope; не сканировать весь репозиторий с догадками
о путях. Не применять CLI как универсальную замену .NET/native-build scanner.
Если запуск scanner в Docker уже настроен, сохранить его сеть и mounts:
`localhost` внутри scanner-контейнера обозначает сам контейнер. Для host-based
scanner loopback-публикация локального сервера работает напрямую.

## Metadata и полнота

Путь metadata брать из scanner output или `sonar.scanner.metadataFilePath`.
Типичные пути: Gradle `build/sonar/report-task.txt`, Maven
`target/sonar/report-task.txt`, CLI `.scannerwork/report-task.txt`.
При custom working directory или другом scanner путь отличается.

Записать фактический scanner/version, команды, scope и наличие build/coverage
artifacts. Успешный exit scanner подтверждает загрузку, а CE `SUCCESS` -
завершение серверной обработки. Ошибку build, scanner, CE, доступа или сборки
API-страниц не выдавать за чистый quality gate.

## Официальные источники

- [Gradle scanner](https://docs.sonarsource.com/sonarqube-server/analyzing-source-code/scanners/sonarscanner-for-gradle).
- [Maven scanner](https://docs.sonarsource.com/sonarqube-server/analyzing-source-code/scanners/sonarscanner-for-maven).
- [Scanner CLI](https://docs.sonarsource.com/sonarqube-server/analyzing-source-code/scanners/sonarscanner).
- [Scanner for .NET](https://docs.sonarsource.com/sonarqube-server/analyzing-source-code/scanners/dotnet/introduction).
