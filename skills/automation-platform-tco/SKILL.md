---
name: automation-platform-tco
description: Estimate TCO for internal automation, AI, agent, or workflow platforms, especially pilots, first production launches, and private-cloud deployments. Use when the workflow must interview the user one question at a time, collect assumptions for infra, inference, support, training, VAT, and reserve, convert the answers into a reusable cost model, and generate a Russian-language PDF with the plan and итоговый TCO.
---

Use one-question-at-a-time interview unless user explicitly asks for batch mode.

## Workflow

1. Fix scope first.
   Ask whether the task is one platform or a comparison, what horizon to use, whether sunk development cost is excluded, and which cost blocks belong in scope.

2. Drive interview from `references/interview-checklist.md`.
   Ask only unanswered questions.
   Keep a running assumption register.
   Prefer direct monthly cost overrides when the user has them.

3. Build a JSON input file before calculating.
   Read `references/config-schema.md`.
   Normalize user answers into that schema.

4. Price conservatively when internal unit economics are missing.
   For private cloud or on-prem footprints, use official public-cloud proxies only if the user agrees.
   Record exact tariff date, FX source, VAT rule, and every override.

5. Generate Russian PDF through script.
   Run:

   ```bash
   python3 scripts/generate_tco_pdf.py --input /path/to/config.json --output /path/to/result.pdf
   ```

6. Sanity-check result before delivery.
   Verify monthly fixed costs, training logic, reserve, VAT treatment, and total.
   Call out biggest uncertainty and excluded blocks.

## Output Rules

- Write final document in Russian.
- Normalize free-text fields to Russian before building JSON config. This includes `scope_rows`, `assumptions`, `sources`, and `notes`.
- Keep tables concise and executive-friendly.
- Show assumptions explicitly; do not hide pricing proxies.
- Separate internal costs from external purchases with VAT impact.
- Report both baseline TCO and TCO with reserve.

## References

- Read `references/interview-checklist.md` when running discovery interview.
- Read `references/config-schema.md` when drafting config or extending calculator.
