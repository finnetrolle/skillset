---
name: domain-modeling
description: Уточнять предметную модель, термины, глоссарий и ADR. Использовать при проработке предметных понятий или просьбе создать либо обновить такие документы; учитывать существующие соглашения проекта.
---

# Domain Modeling

Follow the repository's existing glossary and ADR locations and formats.
`GLOSSARY.md` and `docs/adr/` below are defaults for a project without an
established convention; an existing `CONTEXT.md` may already hold the glossary.
Never rename existing documents just to match these defaults.

For discussion-only or read-only work, propose document updates in the chat.
Write them when the user's task authorizes documenting the agreed decisions.
Do not turn an unresolved assumption into an accepted term or ADR.

Actively build and sharpen the project's domain model as you design. This is the *active* discipline: challenging terms, inventing edge-case scenarios, and writing the glossary and decisions down the moment they crystallise. (Merely *reading* `GLOSSARY.md` for vocabulary is not this skill: that's a one-line habit any skill can do. This skill is for when you're changing the model, not just consuming it.)

## File structure

Most repos have a single context:

```
/
├── GLOSSARY.md
├── docs/
│   └── adr/
│       ├── 0001-event-sourced-orders.md
│       └── 0002-postgres-for-write-model.md
└── src/
```

If a `GLOSSARY-MAP.md` exists at the root, the repo has multiple contexts. The map points to where each one lives:

```
/
├── GLOSSARY-MAP.md
├── docs/
│   └── adr/                          ← system-wide decisions
├── src/
│   ├── ordering/
│   │   ├── GLOSSARY.md
│   │   └── docs/adr/                 ← context-specific decisions
│   └── billing/
│       ├── GLOSSARY.md
│       └── docs/adr/
```

Create files lazily, within the authorized documentation scope. Use the existing
glossary location, including `CONTEXT.md`. Only if none exists, create
`GLOSSARY.md` when the first term is resolved and writing it is authorized.
Create an ADR directory only when an agreed decision needs an authorized ADR.

## During the session

### Challenge against the glossary

When the user uses a term that conflicts with the existing project glossary,
surface the discrepancy. "Your glossary defines 'cancellation' as X, but you
seem to mean Y. Which is it?"

### Sharpen fuzzy language

When the user uses vague or overloaded terms, propose a precise canonical term. "You're saying 'account': do you mean the Customer or the User? Those are different things."

### Discuss concrete scenarios

When domain relationships are being discussed, stress-test them with specific scenarios. Invent scenarios that probe edge cases and force the user to be precise about the boundaries between concepts.

### Cross-reference with code

When the user states how something works, check whether the code agrees. If you find a contradiction, surface it: "Your code cancels entire Orders, but you just said partial cancellation is possible. Which is right?"

### Capture agreed terms

When a term is resolved, capture it in the existing glossary if documentation
updates are authorized; otherwise propose the entry in the chat. For a new
glossary, use [GLOSSARY-FORMAT.md](./GLOSSARY-FORMAT.md). Keep the established
format when one already exists.

Glossary entries describe domain language, not implementation decisions or
scratch notes. A broader `CONTEXT.md` may contain other sections; do not remove
or restructure those sections as part of adding a term.

### Offer ADRs sparingly

Only offer to create an ADR when all three are true:

1. **Hard to reverse**: the cost of changing your mind later is meaningful
2. **Surprising without context**: a future reader will wonder "why did they do it this way?"
3. **The result of a real trade-off**: there were genuine alternatives and you picked one for specific reasons

If any of the three is missing, skip the ADR. Use the format in [ADR-FORMAT.md](./ADR-FORMAT.md).
