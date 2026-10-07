#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import quote
from urllib.request import Request, urlopen


WEEKLY_URL = "https://github.com/trending?since=weekly"
MONTHLY_URL = "https://github.com/trending?since=monthly"
USER_AGENT = "Mozilla/5.0"
DEFAULT_OUTPUT_DIR = Path("output/pdf")

MANUAL_INCLUDE = {
    "microsoft/markitdown",
    "google-labs-code/design.md",
    "Leonxlnx/taste-skill",
    "mvanhorn/last30days-skill",
    "phuryn/pm-skills",
    "asgeirtj/system_prompts_leaks",
}

KEYWORD_PATTERNS: list[tuple[str, re.Pattern[str], int]] = [
    ("ai", re.compile(r"\bai\b", re.I), 3),
    ("llm", re.compile(r"\bllm\b", re.I), 3),
    ("agent", re.compile(r"\bagent(s|ic)?\b", re.I), 3),
    ("mcp", re.compile(r"\bmcp\b", re.I), 3),
    ("voice", re.compile(r"\bvoice\b", re.I), 2),
    ("speech", re.compile(r"\bspeech\b|\basr\b", re.I), 2),
    ("prompt", re.compile(r"\bprompt(s)?\b", re.I), 2),
    ("openai-compatible", re.compile(r"openai-compatible", re.I), 2),
    ("knowledge graph", re.compile(r"knowledge graph", re.I), 2),
    ("notebooklm", re.compile(r"notebook\s*lm|notebooklm", re.I), 3),
    ("coding agent", re.compile(r"coding agent|coding agents", re.I), 2),
    ("assistant", re.compile(r"\bassistant(s)?\b", re.I), 2),
    ("vector", re.compile(r"\bvector\b", re.I), 2),
    ("rag", re.compile(r"\brag\b", re.I), 2),
]


@dataclass
class TrendingItem:
    repo: str
    url: str
    description_source: str
    language: str | None
    total_stars: int | None
    weekly_added: int | None = None
    monthly_added: int | None = None
    weekly_rank: int | None = None
    monthly_rank: int | None = None


def fetch_html(url: str) -> str:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req) as response:
        return response.read().decode("utf-8", "ignore")


def strip_tags(text: str) -> str:
    text = re.sub(r"<svg[\s\S]*?</svg>", " ", text)
    text = re.sub(r"<img[\s\S]*?>", " ", text)
    text = re.sub(r"<[^>]+>", " ", text)
    return " ".join(html.unescape(text).split())


def parse_trending(period: str, url: str) -> list[TrendingItem]:
    html_text = fetch_html(url)
    items: list[TrendingItem] = []

    for rank, block in enumerate(html_text.split('<article class="Box-row">')[1:], start=1):
        block = block.split("</article>", 1)[0]
        repo_match = re.search(r'<h2 class="h3 lh-condensed">[\s\S]*?<a [^>]*href="/([^"]+)"', block)
        if not repo_match:
            continue

        repo = repo_match.group(1)
        desc_match = re.search(r'<p class="col-9 color-fg-muted my-1 tmp-pr-4">([\s\S]*?)</p>', block)
        description = strip_tags(desc_match.group(1)) if desc_match else ""
        lang_match = re.search(r'<span itemprop="programmingLanguage">([^<]+)</span>', block)
        language = lang_match.group(1).strip() if lang_match else None
        stars_match = re.search(r'href="/[^"]+/stargazers"[^>]*>([\s\S]*?)</a>', block)
        trend_match = re.search(r"([\d,]+) stars this (week|month|day)", strip_tags(block))

        total_stars = None
        if stars_match:
            stars_text = strip_tags(stars_match.group(1))
            stars_num = re.search(r"([\d,]+)", stars_text)
            if stars_num:
                total_stars = int(stars_num.group(1).replace(",", ""))

        trend_value = None
        if trend_match:
            trend_value = int(trend_match.group(1).replace(",", ""))

        item = TrendingItem(
            repo=repo,
            url=f"https://github.com/{repo}",
            description_source=description,
            language=language,
            total_stars=total_stars,
        )
        if period == "weekly":
            item.weekly_added = trend_value
            item.weekly_rank = rank
        elif period == "monthly":
            item.monthly_added = trend_value
            item.monthly_rank = rank
        else:
            raise ValueError(f"Unsupported period: {period}")
        items.append(item)

    return items


def merge_items(weekly_items: Iterable[TrendingItem], monthly_items: Iterable[TrendingItem]) -> list[dict]:
    merged: dict[str, TrendingItem] = {}

    for item in weekly_items:
        merged[item.repo] = item

    for item in monthly_items:
        if item.repo in merged:
            current = merged[item.repo]
            current.monthly_added = item.monthly_added
            current.monthly_rank = item.monthly_rank
            if current.total_stars is None:
                current.total_stars = item.total_stars
            if not current.description_source:
                current.description_source = item.description_source
            if not current.language:
                current.language = item.language
        else:
            merged[item.repo] = item

    rows: list[dict] = []
    for item in merged.values():
        include, score, matches = ai_heuristic(item.repo, item.description_source)
        rows.append(
            {
                "repo": item.repo,
                "url": item.url,
                "language": item.language,
                "total_stars": item.total_stars,
                "weekly_added": item.weekly_added,
                "monthly_added": item.monthly_added,
                "weekly_rank": item.weekly_rank,
                "monthly_rank": item.monthly_rank,
                "description_source": item.description_source,
                "description_ru": "",
                "include": include,
                "heuristic_score": score,
                "heuristic_matches": matches,
                "seen_in": [p for p, value in (("weekly", item.weekly_added), ("monthly", item.monthly_added)) if value is not None],
            }
        )

    rows.sort(key=sort_key, reverse=True)
    return rows


def ai_heuristic(repo: str, description: str) -> tuple[bool, int, list[str]]:
    haystack = f"{repo} {description}"
    score = 0
    matches: list[str] = []

    if repo in MANUAL_INCLUDE:
        score += 3
        matches.append("manual-include")

    for label, pattern, weight in KEYWORD_PATTERNS:
        if pattern.search(haystack):
            score += weight
            matches.append(label)

    include = score >= 3
    return include, score, matches


def sort_key(item: dict) -> tuple[int, int, int]:
    return (
        item.get("weekly_added") or -1,
        item.get("monthly_added") or -1,
        item.get("total_stars") or -1,
    )


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, payload: dict) -> None:
    ensure_parent(path)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def format_num(value: int | None) -> str:
    return f"{value:,}" if value is not None else "—"


def normalize_text(text: str) -> str:
    return " ".join((text or "").split())


def looks_russian(text: str) -> bool:
    text = text or ""
    cyr = len(re.findall(r"[А-Яа-яЁё]", text))
    latin = len(re.findall(r"[A-Za-z]", text))
    cjk = len(re.findall(r"[\u4e00-\u9fff]", text))
    return cyr >= 8 and cyr >= latin and cjk == 0


def translate_to_russian(text: str) -> str:
    text = normalize_text(text)
    if not text:
        return ""

    if looks_russian(text):
        return text

    url = (
        "https://translate.googleapis.com/translate_a/single"
        f"?client=gtx&sl=auto&tl=ru&dt=t&q={quote(text)}"
    )
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req) as response:
        payload = json.loads(response.read().decode("utf-8", "ignore"))

    translated_parts = []
    for part in payload[0]:
        if part and part[0]:
            translated_parts.append(part[0])
    return normalize_text("".join(translated_parts))


def populate_russian_descriptions(
    items: list[dict],
    *,
    overwrite: bool,
    strict: bool,
) -> list[str]:
    failures: list[str] = []

    for item in items:
        if not item.get("include", True):
            continue

        existing = normalize_text(item.get("description_ru") or "")
        if existing and not overwrite:
            item["translation_status"] = item.get("translation_status") or "manual"
            continue

        source = normalize_text(item.get("description_source") or "")
        if not source:
            item["translation_status"] = "failed-no-source"
            failures.append(item["repo"])
            continue

        try:
            if looks_russian(source):
                item["description_ru"] = source
                item["translation_status"] = "copied-russian"
            else:
                translated = translate_to_russian(source)
                item["description_ru"] = translated
                item["translation_status"] = "translated" if translated else "failed-empty"
                if not translated:
                    failures.append(item["repo"])
        except Exception:
            item["translation_status"] = "failed"
            failures.append(item["repo"])

    if strict and failures:
        joined = ", ".join(failures[:10])
        suffix = "" if len(failures) <= 10 else f" ... (+{len(failures) - 10})"
        raise SystemExit(f"Automatic translation failed for: {joined}{suffix}")

    return failures


def iter_render_items(payload: dict) -> list[dict]:
    if isinstance(payload, list):
        items = payload
    else:
        items = payload.get("items", [])

    filtered = [item for item in items if item.get("include", True)]
    filtered.sort(key=sort_key, reverse=True)
    return filtered


def render_pdf(input_path: Path, output_path: Path, title: str, preview_dir: Path | None) -> None:
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A3, landscape
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    except ImportError as exc:
        raise SystemExit("Install reportlab first. Example: uv run --with reportlab python ...") from exc

    payload = load_json(input_path)
    items = iter_render_items(payload)
    if not items:
        raise SystemExit("No included items to render.")

    missing_russian = [
        item["repo"]
        for item in items
        if not (item.get("description_ru") or "").strip()
    ]
    if missing_russian:
        joined = ", ".join(missing_russian[:10])
        suffix = "" if len(missing_russian) <= 10 else f" ... (+{len(missing_russian) - 10})"
        raise SystemExit(
            "Render blocked: fill description_ru in Russian for every included item first: "
            f"{joined}{suffix}"
        )

    font_candidates = [
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/Library/Fonts/Arial Unicode.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
    ]
    font_path = next((candidate for candidate in font_candidates if Path(candidate).exists()), None)
    if not font_path:
        raise SystemExit("No suitable Unicode font found for PDF rendering.")

    pdfmetrics.registerFont(TTFont("TrendingArialUnicode", font_path))

    styles = getSampleStyleSheet()
    base = ParagraphStyle(
        "base",
        parent=styles["Normal"],
        fontName="TrendingArialUnicode",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#111827"),
    )
    header = ParagraphStyle(
        "header",
        parent=base,
        fontSize=8.2,
        leading=10,
        textColor=colors.white,
        alignment=1,
    )
    title_style = ParagraphStyle(
        "title",
        parent=base,
        fontSize=18,
        leading=22,
        spaceAfter=6,
    )
    meta_style = ParagraphStyle(
        "meta",
        parent=base,
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#374151"),
    )
    link_style = ParagraphStyle(
        "link",
        parent=base,
        textColor=colors.HexColor("#0f766e"),
    )
    num_style = ParagraphStyle(
        "num",
        parent=base,
        alignment=2,
    )
    foot_style = ParagraphStyle(
        "foot",
        parent=base,
        fontSize=7.5,
        leading=9,
        textColor=colors.HexColor("#4b5563"),
    )

    page_width, _page_height = landscape(A3)
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=landscape(A3),
        leftMargin=12 * mm,
        rightMargin=12 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
    )
    usable_width = page_width - doc.leftMargin - doc.rightMargin
    col_widths = [72 * mm, 24 * mm, 24 * mm, 24 * mm, usable_width - (72 + 24 + 24 + 24) * mm]

    story = [
        Paragraph(title, title_style),
        Paragraph(
            "Источники: https://github.com/trending?since=weekly и "
            "https://github.com/trending?since=monthly. Символ “—” означает, "
            "что проект не попал в соответствующий список Trending, а не нулевой прирост.",
            meta_style,
        ),
        Spacer(1, 6 * mm),
    ]

    data = [
        [
            Paragraph("Проект", header),
            Paragraph("Всего звезд", header),
            Paragraph("За неделю", header),
            Paragraph("За месяц", header),
            Paragraph("Описание", header),
        ]
    ]

    for item in items:
        description = (item.get("description_ru") or "").strip()
        data.append(
            [
                Paragraph(
                    f'<link href="{item["url"]}" color="#0f766e">{item["repo"]}</link>',
                    link_style,
                ),
                Paragraph(format_num(item.get("total_stars")), num_style),
                Paragraph(format_num(item.get("weekly_added")), num_style),
                Paragraph(format_num(item.get("monthly_added")), num_style),
                Paragraph(description, base),
            ]
        )

    table = Table(data, colWidths=col_widths, repeatRows=1, splitByRow=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
                ("LINEBELOW", (0, 0), (-1, 0), 0.8, colors.HexColor("#0f172a")),
                ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(table)
    story.append(
        Spacer(1, 4 * mm)
    )
    story.append(
        Paragraph(
            "Отбор AI-проектов является стартовой эвристикой. Проверяйте спорные случаи вручную перед финальной отправкой.",
            foot_style,
        )
    )

    def add_page_number(canvas, document):
        canvas.setFont("TrendingArialUnicode", 8)
        canvas.setFillColor(colors.HexColor("#6b7280"))
        canvas.drawRightString(page_width - document.rightMargin, 8 * mm, f"Стр. {document.page}")

    ensure_parent(output_path)
    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)

    if preview_dir:
        preview_dir.mkdir(parents=True, exist_ok=True)
        prefix = preview_dir / output_path.stem
        subprocess.run(["pdftoppm", "-png", str(output_path), str(prefix)], check=True)


def command_collect(args: argparse.Namespace) -> None:
    weekly_items = parse_trending("weekly", args.weekly_url)
    monthly_items = parse_trending("monthly", args.monthly_url)
    rows = merge_items(weekly_items, monthly_items)
    translation_failures: list[str] = []
    if not args.skip_translate:
        translation_failures = populate_russian_descriptions(
            rows,
            overwrite=False,
            strict=False,
        )
    if args.selected_only:
        rows = [row for row in rows if row.get("include")]

    payload = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "sources": {
            "weekly": args.weekly_url,
            "monthly": args.monthly_url,
        },
        "notes": [
            "Use exact weekly and monthly Trending URLs only.",
            "Review include flags manually before final rendering.",
            "description_ru must be Russian for every included item before final delivery.",
        ],
        "translation": {
            "auto_translate_on_collect": not args.skip_translate,
            "failures": translation_failures,
        },
        "items": rows,
    }
    output_path = Path(args.output)
    write_json(output_path, payload)
    print(output_path)


def command_translate(args: argparse.Namespace) -> None:
    input_path = Path(args.input)
    payload = load_json(input_path)
    if isinstance(payload, list):
        items = payload
    else:
        items = payload.get("items", [])

    failures = populate_russian_descriptions(
        items,
        overwrite=args.overwrite,
        strict=args.strict,
    )

    if isinstance(payload, dict):
        payload["translated_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
        payload["translation"] = {
            "auto_translate_on_collect": payload.get("translation", {}).get("auto_translate_on_collect", True),
            "failures": failures,
        }

    output_path = Path(args.output or args.input)
    write_json(output_path, payload)
    print(output_path)


def command_render(args: argparse.Namespace) -> None:
    output_path = Path(args.output) if args.output else DEFAULT_OUTPUT_DIR / f"github-ai-trending-{dt.date.today().isoformat()}.pdf"
    preview_dir = Path(args.preview_dir) if args.preview_dir else None
    render_pdf(Path(args.input), output_path, args.title, preview_dir)
    print(output_path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Collect and render GitHub AI Trending PDF reports.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    collect = subparsers.add_parser("collect", help="Fetch exact Trending pages and write a JSON draft.")
    collect.add_argument("--output", required=True, help="Path to write the collected JSON draft.")
    collect.add_argument("--weekly-url", default=WEEKLY_URL, help="Exact weekly Trending URL.")
    collect.add_argument("--monthly-url", default=MONTHLY_URL, help="Exact monthly Trending URL.")
    collect.add_argument("--selected-only", action="store_true", help="Keep only heuristic matches in output.")
    collect.add_argument("--skip-translate", action="store_true", help="Skip automatic translation during collect.")
    collect.set_defaults(func=command_collect)

    translate = subparsers.add_parser("translate", help="Auto-fill Russian descriptions for included rows.")
    translate.add_argument("--input", required=True, help="Collected or curated JSON file.")
    translate.add_argument("--output", help="Path to write translated JSON. Defaults to overwriting input.")
    translate.add_argument("--overwrite", action="store_true", help="Overwrite existing description_ru values.")
    translate.add_argument("--strict", action="store_true", help="Fail if any translation could not be produced.")
    translate.set_defaults(func=command_translate)

    render = subparsers.add_parser("render", help="Render a curated JSON file to PDF.")
    render.add_argument("--input", required=True, help="Collected or curated JSON file.")
    render.add_argument("--output", help="Output PDF path. Defaults to output/pdf/github-ai-trending-YYYY-MM-DD.pdf.")
    render.add_argument("--title", default="GitHub Trending: AI-проекты за неделю и месяц", help="PDF title.")
    render.add_argument("--preview-dir", help="Optional directory for pdftoppm PNG previews.")
    render.set_defaults(func=command_render)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
