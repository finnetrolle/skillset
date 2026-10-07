#!/usr/bin/env python3
"""Validate canonical targeted-CV JSON without third-party dependencies."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

TOP_LEVEL = {
    "name",
    "role",
    "location",
    "about",
    "skills",
    "experience",
    "courses",
    "education",
    "languages",
}
EXPERIENCE_FIELDS = {
    "company",
    "time",
    "position",
    "project",
    "client",
    "stack",
    "responsibilities",
    "achievements",
}
COURSE_FIELDS = {"grad_year", "name"}
EDUCATION_FIELDS = {"grad_year", "name", "direction"}
LANGUAGE_FIELDS = {"name", "level"}
LANGUAGE_LEVELS = {
    # Deliberately extended: native-language sources (e.g. Russian "Родной")
    # cannot be mapped to the CEFR-style scale.
    "Родной",
    "Elementary",
    "Pre-Intermediate",
    "Intermediate",
    "Upper-Intermediate",
    "Advanced",
    "Proficiency",
}


def check_keys(value: dict[str, Any], expected: set[str], path: str) -> list[str]:
    errors: list[str] = []
    missing = expected - value.keys()
    extra = value.keys() - expected
    if missing:
        errors.append(f"{path}: missing keys: {', '.join(sorted(missing))}")
    if extra:
        errors.append(f"{path}: unexpected keys: {', '.join(sorted(extra))}")
    return errors


def check_nullable_strings(
    value: dict[str, Any], fields: set[str], path: str
) -> list[str]:
    return [
        f"{path}.{field}: expected string or null"
        for field in fields & value.keys()
        if value[field] is not None and not isinstance(value[field], str)
    ]


def check_object_list(
    data: dict[str, Any], field: str, expected: set[str], *, nullable: bool = False
) -> list[str]:
    value = data.get(field)
    if nullable and value is None:
        return []
    if not isinstance(value, list):
        return [f"$.{field}: expected array"]

    errors: list[str] = []
    for index, item in enumerate(value):
        path = f"$.{field}[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{path}: expected object")
            continue
        errors.extend(check_keys(item, expected, path))
        string_fields = expected - {"grad_year"}
        errors.extend(check_nullable_strings(item, string_fields, path))
        if (
            "grad_year" in item
            and item["grad_year"] is not None
            and (
                not isinstance(item["grad_year"], int)
                or isinstance(item["grad_year"], bool)
            )
        ):
            errors.append(f"{path}.grad_year: expected integer or null")
    return errors


def validate_cv(data: Any) -> list[str]:
    if not isinstance(data, dict):
        return ["$: expected object"]

    errors = check_keys(data, TOP_LEVEL, "$")
    errors.extend(
        check_nullable_strings(
            data, {"name", "role", "location", "about", "skills"}, "$"
        )
    )
    errors.extend(check_object_list(data, "experience", EXPERIENCE_FIELDS))
    errors.extend(check_object_list(data, "courses", COURSE_FIELDS, nullable=True))
    errors.extend(check_object_list(data, "education", EDUCATION_FIELDS))
    errors.extend(check_object_list(data, "languages", LANGUAGE_FIELDS))

    languages = data.get("languages")
    if isinstance(languages, list):
        for index, language in enumerate(languages):
            if not isinstance(language, dict):
                continue
            level = language.get("level")
            if level is not None and level not in LANGUAGE_LEVELS:
                errors.append(
                    f"$.languages[{index}].level: unsupported level {level!r}"
                )
    return errors


def load_and_validate(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read valid JSON from {path}: {exc}") from exc

    errors = validate_cv(data)
    if errors:
        raise ValueError("CV validation failed:\n- " + "\n- ".join(errors))
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    args = parser.parse_args()
    try:
        load_and_validate(args.input)
    except ValueError as exc:
        print(exc)
        return 1
    print(f"OK: {args.input}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
