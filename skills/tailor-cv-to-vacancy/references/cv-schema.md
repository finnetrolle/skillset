# Canonical CV Schema

Create UTF-8 JSON with exactly these top-level keys:

```json
{
  "name": "Candidate Name",
  "role": "Targeted but supported role",
  "location": "City or null",
  "about": "Three to five concise sentences or null",
  "skills": "Comma-separated evidenced skills or null",
  "experience": [
    {
      "company": "Company or null",
      "time": "Source date range or null",
      "position": "Source position or null",
      "project": "Relevant project summary or null",
      "client": "Client or null",
      "stack": "Comma-separated evidenced tools or null",
      "responsibilities": "One item per line or null",
      "achievements": "One item per line or null"
    }
  ],
  "courses": [
    {
      "grad_year": 2025,
      "name": "Course name or null"
    }
  ],
  "education": [
    {
      "grad_year": 2020,
      "name": "Institution or null",
      "direction": "Program or null"
    }
  ],
  "languages": [
    {
      "name": "English",
      "level": "Upper-Intermediate"
    }
  ]
}
```

## Type and Null Rules

- Permit strings or `null` for scalar fields.
- Always use arrays for `experience`, `education`, and `languages`; use `[]` when absent. Permit either an array or `null` for `courses` to remain compatible with the existing application output.
- Use an integer or `null` for `grad_year`. Do not infer a year.
- Restrict language levels to `Elementary`, `Pre-Intermediate`, `Intermediate`, `Upper-Intermediate`, `Advanced`, `Proficiency`, or `null`. Preserve a source's wording only when it cannot be mapped safely; put that wording in `level` only after extending the validator deliberately.
- Keep every top-level and nested key even when its value is empty.

## Adaptation Boundary

The vacancy controls ordering, emphasis, vocabulary, and selection. The source CV controls all factual claims. Safe transformations include shortening, grammatical repair, grouping repeated duties, translating an evidenced synonym into the vacancy's terminology, and promoting relevant items. Unsafe transformations include adding tools from the vacancy, upgrading proficiency, changing job titles or dates, inventing metrics, and presenting adjacent experience as direct experience.
