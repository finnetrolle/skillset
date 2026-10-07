---
name: kdoc
description: Add or fix KDoc documentation on Kotlin declarations (functions, classes, properties). Use when the user asks to document, add KDoc, add docs, or document methods/classes in Kotlin files, or invokes /kdoc. Follows official Kotlin coding conventions for KDoc.
user-invocable: true
---

# kdoc

Document Kotlin declarations with KDoc per the official Kotlin Coding Conventions
(https://kotlinlang.org/docs/coding-conventions.html#documentation-comments).

## When invoked

- `/kdoc <file>` — document all undocumented declarations in the file
- `/kdoc <file> <function>` — document one declaration
- No args — document declarations in files changed in the current session (ask if ambiguous)

## Rules

1. **Read the file first.** Understand behavior before writing docs. Never document
   from the signature alone if the body is available.

2. **KDoc format:**

```kotlin
/**
 * One-sentence summary starting with a verb, ending with a period.
 * Optional: following paragraphs with details. Use Markdown.
 *
 * @param name what it is, in lowercase prose.
 * @return what is returned, including special cases.
 * @throws IllegalArgumentException when this condition holds.
 */
```

3. **First sentence:** imperative or third-person verb ("Parses...", "Validates...",
   "Returns..."). Concise — it shows in the IDE hover and Dokka index.

4. **Tags:**
   - `@param` — every parameter that isn't trivially obvious from name + type
   - `@return` — always for non-Unit functions unless utterly obvious (`getter`)
   - `@throws`/`@exception` — document every documented exception; `require()` throws
     `IllegalArgumentException`, `check()` throws `IllegalStateException`
   - `@sample`, `@see` — optional, when helpful

5. **References:** use `[bracketed]` references to link declarations:
   `[URI]`, `[DEFAULT_PORT]`, `[main]`. IDE resolves them; Dokka hyperlinks them.

6. **Document in English** unless the user asks otherwise.

7. **What to skip:**
   - Overrides with identical behavior — use `/** */` only if adding contract info
   - Self-evident private one-liners (`fun name() = constant`) — optional
   - Never state what code trivially shows; document intent, contracts, side effects

8. **Public API = mandatory docs.** `internal`/`private` helpers: docs recommended
   but optional. When in doubt for test-visible internal functions, document them.

9. **Do not change code logic.** Comments only. Formatting of existing code stays.

10. **Property KDoc** goes above the declaration; file-level KDoc starts with
    `@file:JvmName(...)` style annotations before the package statement if used.

## Workflow

1. Read target file(s).
2. List undocumented declarations: functions, classes, objects, interfaces,
   top-level properties with non-obvious meaning.
3. Write KDoc per rules above.
4. Show summary: what was documented, what was skipped and why.
