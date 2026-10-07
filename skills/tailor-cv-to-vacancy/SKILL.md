---
name: tailor-cv-to-vacancy
description: Create a truthful, vacancy-targeted CV from an existing CV and a job description. Use when adapting, rewriting, restructuring, or generating a candidate CV or resume for a specific vacancy from PDF, DOCX, RTF, TXT, Markdown, JSON, or pasted text, including producing validated JSON and an ATS-friendly DOCX without inventing experience or skills.
---

# Tailor CV to Vacancy

Transform a source CV into a vacancy-focused CV while preserving factual accuracy. Use the vacancy to prioritize evidence and terminology, never as evidence that the candidate has a skill.

## Workflow

1. Identify the source CV and vacancy. If either is missing, request only the missing input. Accept attached files, local paths, or pasted text.
2. Resolve a Python runtime. In Codex desktop, call the workspace dependency loader and use its returned Python executable for document scripts. Otherwise use an active environment containing `pdfplumber`, `python-docx`, and `striprtf`. Store that executable path in `CV_RUNTIME_PY` for the commands below.
3. Extract both inputs. Read JSON, TXT, and Markdown directly. For PDF, DOCX, or RTF, run `scripts/extract_document.py` from this skill directory. If a PDF is image-only, use OCR and flag uncertain text.
4. Read `references/cv-schema.md` before drafting.
5. Build a private evidence ledger containing only facts found in the source CV: employers, dates, positions, projects, tools, duties, achievements, education, languages, location, and interests. Do not treat the vacancy or inferred seniority as candidate evidence.
6. Map each vacancy requirement as `supported`, `adjacent`, or `missing`. Emphasize supported evidence, use adjacent evidence conservatively, and omit missing requirements from the CV.
7. Draft the canonical JSON in the source CV's language. Reorder and rewrite content for relevance, but preserve the meaning of every claim.
8. Validate the JSON:

   ```bash
   "$CV_RUNTIME_PY" <skill-directory>/scripts/validate_cv.py <targeted-cv.json>
   ```

   Fix every validation error. Then compare names, dates, employers, education, tools, metrics, and language levels against the evidence ledger.
9. Unless the user requests JSON only, render an ATS-friendly DOCX:

   ```bash
   "$CV_RUNTIME_PY" <skill-directory>/scripts/render_cv.py <targeted-cv.json> --output <targeted-cv.docx>
   ```

   If the document skill is available, render and inspect the DOCX before delivery. Create a PDF only when requested, and visually verify it with the PDF workflow.
10. Deliver the JSON and DOCX paths plus a short note listing the strongest alignment and any important vacancy gaps. Never overwrite the source CV.

## Content Rules

- Write a concise professional summary of 3–5 sentences in first-person singular and the source CV's language. Use present tense for current expertise and past tense only for completed achievements.
- Use the target job title as the headline only when the CV supports it; otherwise retain the closest truthful specialization.
- Put vacancy-relevant, evidenced skills first. Merge skills found in project stacks, but do not add tools seen only in the vacancy.
- Preserve employer names, positions, dates, chronology, education, and language levels. Never manufacture metrics, achievements, clients, certifications, or years of experience.
- Improve grammar and action wording. Keep responsibilities and achievements distinct; do not convert routine duties into unsupported achievements.
- Include hobbies only when present in the source. Exclude personal details not useful for hiring.
- Use `null` or empty arrays for missing data as defined in the schema; do not fill gaps by guessing.

## Output Location

Honor the user's requested directory. Otherwise create `output/` in the current workspace and use sanitized filenames such as `ivan_ivanov_data_analyst_cv.json` and `.docx`. Do not expose the private evidence ledger unless the user asks for an audit.
