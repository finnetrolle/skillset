---
name: github-ai-trending-pdf
description: Generate an updated PDF report of AI-related GitHub Trending projects by merging the exact weekly and monthly Trending pages, deduplicating repositories, translating short descriptions into Russian, and exporting a union table. Use when producing a repeatable weekly or monthly GitHub AI trend report, a fresh PDF artifact, or a current list of GitHub Trending AI, LLM, agent, MCP, voice, or AI-infrastructure projects.
---

# GitHub AI Trending PDF

Use exact GitHub pages only:

- `https://github.com/trending?since=weekly`
- `https://github.com/trending?since=monthly`

Do not add `spoken_language_code` or other filters. The report from this skill must match the exact public Trending pages the user would see in the browser.

## Workflow

1. Collect a draft dataset.
   - Run:
   - `uv run --with reportlab python scripts/github_ai_trending_report.py collect --output tmp/github-ai-trending-raw.json`
   - The script fetches the exact weekly and monthly Trending pages, parses cards, merges both lists, deduplicates repositories, auto-fills `description_ru` when possible, and writes a JSON draft with `include`, `description_source`, and heuristic matches.

2. Run automatic translation again after curation when needed.
   - Run:
   - `python scripts/github_ai_trending_report.py translate --input tmp/github-ai-trending-raw.json --output tmp/github-ai-trending-raw.json`
   - Use this after changing `include` flags or when new rows were added to the final AI set.

3. Curate the final AI list.
   - Read the JSON draft.
   - Keep repositories where AI, LLM, agents, MCP, voice, AI-native workflows, or AI infrastructure are core.
   - Flip `include` to `false` for false positives.
   - Fill `description_ru` for every included row with a short factual Russian description.
   - Automatic translation should already fill most rows.
   - If the GitHub description is in English or any other non-Russian language, make sure the final `description_ru` is translated to Russian before rendering.
   - Fix awkward machine translation manually when needed.
   - Do not leave source-language descriptions in the final PDF. Keep one sentence. Remove hype.

4. Render the PDF.
   - Run:
   - `uv run --with reportlab python scripts/github_ai_trending_report.py render --input tmp/github-ai-trending-raw.json --output output/pdf/github-ai-trending-YYYY-MM-DD.pdf --preview-dir tmp/pdfs/github-ai-trending-YYYY-MM-DD`
   - Prefer a filename with the current date.

5. Validate the render.
   - Open generated PNG previews.
   - Check clipping, Cyrillic rendering, repeated table headers, page numbers, and column readability.
   - Re-render after fixes if the PDF is crowded or broken.

## Selection Guidance

- Include repositories where AI is the main product, workflow, or infrastructure layer.
- Include common buckets from this report: AI coding agents, MCP servers, AI search or memory tools, AI voice or video tools, AI skills, prompt or system-prompt tooling, OpenAI-compatible AI infra, and AI-oriented knowledge workflows.
- Exclude generic devtools, cloud tools, security tools, design tools, or infrastructure where AI is incidental rather than central.
- Treat the script heuristic as a draft, not as ground truth. Review edge cases manually before rendering.

## JSON Contract

- `include`: explicit keep or drop flag used by the renderer
- `description_source`: raw description from GitHub Trending
- `description_ru`: required Russian description shown in the PDF for every included row
- `translation_status`: how `description_ru` was produced, for example `translated`, `copied-russian`, or `failed`
- `total_stars`: current total stars from the Trending card
- `weekly_added` / `monthly_added`: nullable integers; keep `null` when the repository was absent from that list
- `url`: repository link used in the PDF

## Output Rules

- Sort the final report by `weekly_added` descending, then `monthly_added` descending, then `total_stars` descending.
- Render `null` weekly or monthly values as `—`, not `0`.
- Keep project names as `owner/repo`.
- Keep descriptions brief, factual, and always in Russian.
- Write the PDF under `output/pdf/` in the current worktree unless the user asked for a different location.

## Script

Use bundled script `scripts/github_ai_trending_report.py`.

- `collect` fetches and merges Trending data into a JSON draft and tries to auto-fill `description_ru`.
- `translate` re-runs automatic translation for included rows after manual curation.
- `render` turns curated JSON into a PDF and optional PNG previews.
