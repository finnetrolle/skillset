---
name: grill-me
description: >-
  Уточнять план, спецификацию или задачу через интервью и проверку неоднозначностей.
  Использовать при просьбе «grill me», «опроси меня», «проверь мои допущения» или
  провести стресс-тест плана. Не начинать интервью для обычной просьбы выполнить
  уже согласованную работу.
---

# Grill Me

Reach a shared understanding that another agent can act on without reconstructing
this chat. Keep the conversation short and record the substantive decisions.

## Explore before asking

Read the artifact and the relevant repository context. Find facts in the code,
documents or primary sources rather than asking the user to repeat them. Separate
verified facts, assumptions and decisions owned by the user.

## Work the decision tree

Map the consequential decisions and their dependencies. The frontier consists of
questions whose prerequisites are settled. Choose the most consequential ready
question and ask one question at a time, with a recommendation and its reason.
An answer can expose new branches; revisit the frontier after each answer.

Do not revisit accepted decisions unless new evidence materially changes them.
When the user already provided the answer, record it and continue. Never stretch
an interview to cover low-impact implementation choices the agent can resolve.

Check these dimensions:

- Goals: the observable result and who benefits.
- Acceptance: evidence that distinguishes complete from partial work.
- Boundaries: scope and explicit non-goals.
- Alternatives: meaningful rejected options and the reason for the choice.
- Assumptions: facts the plan relies on and how they were verified.

For retrying failed work, also identify what prevents the same failure recurring.

## Show interview progress

Before each next question, show a short progress line in the user's language,
including when using an input tool. For example:

```text
Отвечено: 3; осталось примерно 4 вопроса (включая текущий).
```

Count distinct questions answered in this interview using the available history;
unanswered or skipped questions do not increase the count. Estimate the remaining
questions from the whole known decision tree, including the current question and
branches whose prerequisites are pending, rather than only the ready frontier.
Update after each answer; new branches or answers covering several decisions can
change the estimate. Briefly explain material changes.

When a useful estimate is unavailable, show the answered count and say the
remainder is not yet estimated. The counter describes progress, not ambiguity or
a question quota; completion still depends on clarity and the user's early exit.

## Close and hand off

Use freeform mode for exploration, spec mode for a full specification and ticket
mode for a single work item. In ticket mode, concentrate on the known gaps.
Read [the ambiguity rubric](references/ambiguity.md) before the final assessment;
it retains the mode thresholds and override protocol. Scores describe uncertainty,
not proof of correctness.

Summarize the accepted decisions and the remaining open questions. When the task
authorizes editing its artifact, write the decisions and ambiguity assessment
there before handing it off. Otherwise return them in the chat. Preserve the
user's right to end the interview early and label remaining uncertainty honestly.

When domain terms or significant architectural decisions need documentation,
consult [domain-modeling](../domain-modeling/SKILL.md), honoring the existing
project glossary and document-writing scope.
