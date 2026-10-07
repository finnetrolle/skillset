---
name: landing-redline
description: Hard-nosed landing-page audit and revision workflow for marketing pages, hero sections, offers, CTAs, pricing blocks, and conversion copy. Use when critiquing, improving, rewriting, or proposing edits for a landing page or лендинг in code or rendered form, especially when all user-facing text must be inspected first to identify clarity or conversion problems before recommending or implementing targeted changes.
---

# Landing Redline

Use this skill to review a landing page like a conversion editor, not a polite design reviewer. Audit the whole page and every visible string before suggesting fixes.

## Working Sequence

1. Build context
2. Inventory copy
3. Run a hard audit
4. Propose changes
5. Edit only after the audit is explicit

## Build Context

- Find the entry page, section components, content source, and styling constraints before touching copy.
- Prefer the rendered page when available. Inspect the live preview first and inspect source next.
- Use `rg -n` to locate headlines, subheads, CTA labels, proof blocks, pricing text, FAQ copy, metadata, and footer strings across the codebase.
- Inspect content files, CMS payloads, dictionaries, JSON, and constants if the landing text is not inline.
- Preserve the existing design system unless the user asks for a redesign.
- Read [references/audit-rubric.md](references/audit-rubric.md) before evaluating a serious landing-page task.

## Inventory Copy First

- Extract all user-facing text across hero, navigation, sections, proof, pricing, FAQ, footer, forms, legal disclaimers, and CTAs.
- Build a short text inventory with section labels or file paths so nothing important is missed.
- Treat repeated microcopy, badges, buttons, labels, empty states, and form hints as part of the message.
- Do not start rewriting after reading only the hero. Finish the inventory first.

## Audit Hard

Judge the page against five questions:

1. What is this?
2. Who is it for?
3. Why trust it?
4. Why act now?
5. What should the user do next?

Pressure-test:

- clarity of offer
- specificity of outcome
- audience fit
- proof and credibility
- hierarchy and scanability
- objection handling
- CTA quality
- redundancy, jargon, filler, and vagueness
- consistency between headline, sections, and CTA

Call problems directly. Prefer `unclear`, `generic`, `unproven`, `buried`, `soft CTA`, or `benefit without proof` over diplomatic filler.

## Propose Changes After The Audit

- Rank fixes by likely conversion impact.
- Separate messaging problems, wording problems, and structural problems.
- Rewrite the minimum amount of copy needed to sharpen the page.
- Offer one to three replacement lines for high-leverage elements such as the headline, subhead, CTA, proof block, and closing section.
- Preserve the concept when the concept is strong and the wording is weak.
- Fix the offer before polishing tone when the page lacks a clear offer.
- Read [references/rewrite-patterns.md](references/rewrite-patterns.md) before rewriting hero or CTA copy from scratch.
- Read [references/output-format.md](references/output-format.md) before responding when the user asks for critique, recommendations, or copy rewrites.

## Editing Rules

- Keep the promise, CTA, and proof aligned across the page.
- Remove repetition before adding new sections.
- Prefer concrete nouns, sharp verbs, numbers, timelines, and proof over slogans.
- Replace abstract claims with mechanism, evidence, or outcome.
- Preserve brand voice only when it does not hide meaning.
- Cut or merge sections that do not explain, prove, or convert.
- Make decisive edits instead of leaving TODO comments when the user asks for implementation.

## Default Deliverable

Produce, in order:

1. Verdict
2. Key issues
3. Prioritized change plan
4. Proposed rewrites
5. Implementation notes or code edits if requested

## Guardrails

- Do not praise weak copy just because the layout looks polished.
- Do not assume the hero tells the whole story.
- Do not rewrite everything when the real problem is hierarchy or proof.
- Do not invent claims, metrics, testimonials, guarantees, or deadlines that the source material does not support.
- Do not silently edit first and explain later unless the user explicitly asks for direct changes only.
