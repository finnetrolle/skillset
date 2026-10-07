from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/System/Library/Fonts/Supplemental/Times New Roman.ttf",
    "/Library/Fonts/Arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]


def register_font() -> str:
    for path in FONT_CANDIDATES:
        if Path(path).exists():
            pdfmetrics.registerFont(TTFont("SkillPdfFont", path))
            return "SkillPdfFont"
    return "Helvetica"


FONT_NAME = register_font()


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def money(amount: float, currency: str) -> str:
    return f"{amount:,.0f} {currency}".replace(",", " ")


def pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def table(rows, widths, repeat_rows=0):
    t = Table(rows, colWidths=widths, repeatRows=repeat_rows)
    t.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), FONT_NAME),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("LEADING", (0, 0), (-1, -1), 12),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dbe7f3")),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return t


def styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "title",
            parent=base["Title"],
            fontName=FONT_NAME,
            fontSize=22,
            leading=26,
            textColor=colors.HexColor("#0f172a"),
            spaceAfter=8,
        ),
        "h2": ParagraphStyle(
            "h2",
            parent=base["Heading2"],
            fontName=FONT_NAME,
            fontSize=15,
            leading=18,
            textColor=colors.HexColor("#111827"),
            spaceBefore=8,
            spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "body",
            parent=base["BodyText"],
            fontName=FONT_NAME,
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#1f2937"),
            spaceAfter=5,
        ),
    }


def external_gross(monthly: dict) -> float:
    amount = float(monthly["monthly_amount"])
    if monthly.get("category") != "external":
        return amount
    if monthly.get("includes_vat", False):
        return amount
    vat_rate = float(monthly.get("vat_rate", 0.0))
    return amount * (1 + vat_rate)


def compute_infra(cfg: dict, currency: str) -> dict | None:
    infra = cfg.get("infra_proxy")
    if not infra or not infra.get("enabled"):
        return None
    resources = infra.get("resources", [])
    total_vcpu = sum(item.get("vcpu", 0) for item in resources)
    total_ram = sum(item.get("ram_gb", 0) for item in resources)
    total_storage = sum(item.get("storage_gb", 0) for item in resources)
    hours_per_month = float(infra.get("hours_per_month", 730.5))
    monthly_usd = (
        total_vcpu * float(infra["vcpu_hour_usd"])
        + total_ram * float(infra["ram_gb_hour_usd"])
        + total_storage * float(infra["hdd_gb_hour_usd"])
    ) * hours_per_month
    monthly_net = monthly_usd * float(infra["usd_rub"])
    monthly_gross = monthly_net * (1 + float(infra.get("vat_rate", 0.0)))
    return {
        "resources": resources,
        "total_vcpu": total_vcpu,
        "total_ram": total_ram,
        "total_storage": total_storage,
        "monthly_usd": monthly_usd,
        "monthly_net": monthly_net,
        "monthly_gross": monthly_gross,
        "total_gross": monthly_gross * int(cfg["horizon_months"]),
        "currency": currency,
        "platform": infra.get("platform", ""),
        "storage_type": infra.get("storage_type", ""),
        "usd_rub": infra.get("usd_rub"),
        "vat_rate": infra.get("vat_rate", 0.0),
    }


def compute_training(cfg: dict, currency: str) -> dict | None:
    training = cfg.get("training")
    if not training or not training.get("enabled"):
        return None
    new_users = training.get("new_users_by_month") or cfg.get("user_plan", {}).get("new_by_month", [])
    group_size = int(training["group_size"])
    group_hours = float(training["group_hours"])
    individual_hours = float(training["individual_hours_per_user"])
    specialist_monthly = float(training["specialist_monthly_amount"])
    hours_per_month = float(training["hours_per_month"])
    hourly_rate = specialist_monthly / hours_per_month
    rows = []
    total = 0.0
    for idx, users in enumerate(new_users, start=1):
        groups = math.ceil(users / group_size) if users else 0
        total_hours = groups * group_hours + users * individual_hours
        cost = total_hours * hourly_rate
        total += cost
        rows.append(
            {
                "month": idx,
                "new_users": users,
                "groups": groups,
                "hours": total_hours,
                "cost": cost,
            }
        )
    return {
        "rows": rows,
        "hourly_rate": hourly_rate,
        "total": total,
        "currency": currency,
        "notes": training.get("notes", ""),
    }


def compute(cfg: dict) -> dict:
    currency = cfg.get("currency", "RUB")
    horizon = int(cfg["horizon_months"])
    monthly_costs = cfg.get("monthly_costs", [])
    fixed_rows = []
    fixed_total = 0.0
    for item in monthly_costs:
        gross_monthly = external_gross(item)
        total = gross_monthly * horizon
        fixed_total += total
        fixed_rows.append(
            {
                "name": item["name"],
                "monthly": gross_monthly,
                "total": total,
                "notes": item.get("notes", ""),
                "category": item.get("category", "internal"),
            }
        )
    infra = compute_infra(cfg, currency)
    training = compute_training(cfg, currency)
    baseline = fixed_total
    if infra:
        baseline += infra["total_gross"]
    if training:
        baseline += training["total"]
    reserve = baseline * float(cfg.get("reserve_rate", 0.0))
    total_tco = baseline + reserve
    active = cfg.get("user_plan", {}).get("active_by_month", [])
    new_users = cfg.get("user_plan", {}).get("new_by_month", [])
    peak_active = max(active) if active else 0
    total_new = sum(new_users) if new_users else 0
    return {
        "currency": currency,
        "horizon": horizon,
        "fixed_rows": fixed_rows,
        "fixed_total": fixed_total,
        "infra": infra,
        "training": training,
        "baseline": baseline,
        "reserve": reserve,
        "total_tco": total_tco,
        "peak_active": peak_active,
        "total_new": total_new,
        "cost_per_peak_active": total_tco / peak_active if peak_active else 0.0,
        "cost_per_new_user": total_tco / total_new if total_new else 0.0,
    }


def build_pdf(cfg: dict, calc: dict, output: Path) -> None:
    st = styles()
    doc = SimpleDocTemplate(
        str(output),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=f"TCO - {cfg['project_name']}",
        author="Automation Platform TCO",
    )
    story = []
    story.append(Paragraph(f"TCO платформы: {cfg['project_name']}", st["title"]))
    story.append(
        Paragraph(
            "Документ фиксирует план расчета, собранные допущения и базовую оценку TCO по заданному горизонту.",
            st["body"],
        )
    )

    story.append(Paragraph("1. Рамка расчета", st["h2"]))
    scope_rows = [["Параметр", "Значение"]]
    scope_rows.extend([[row["label"], row["value"]] for row in cfg.get("scope_rows", [])])
    scope_rows.append(["Горизонт", f"{cfg['horizon_months']} мес."])
    scope_rows.append(["Валюта", calc["currency"]])
    scope_rows.append(["Резерв", pct(float(cfg.get("reserve_rate", 0.0)))])
    story.append(table(scope_rows, [60 * mm, 110 * mm], repeat_rows=1))

    active_by_month = cfg.get("user_plan", {}).get("active_by_month", [])
    new_by_month = cfg.get("user_plan", {}).get("new_by_month", [])
    if active_by_month:
        story.append(Paragraph("2. План пользователей", st["h2"]))
        rows = [["Месяц", "Активные пользователи", "Новые пользователи"]]
        for idx, active in enumerate(active_by_month, start=1):
            new_users = new_by_month[idx - 1] if idx - 1 < len(new_by_month) else 0
            rows.append([str(idx), str(active), str(new_users)])
        story.append(table(rows, [25 * mm, 55 * mm, 45 * mm], repeat_rows=1))

    assumptions = cfg.get("assumptions", [])
    if assumptions:
        story.append(Paragraph("3. Допущения", st["h2"]))
        for item in assumptions:
            story.append(Paragraph(f"- {item}", st["body"]))

    infra = calc["infra"]
    if infra:
        story.append(PageBreak())
        story.append(Paragraph("4. Инфраструктурный proxy", st["h2"]))
        pricing_rows = [
            ["Параметр", "Значение"],
            ["Платформа VM", infra["platform"]],
            ["Тип storage", infra["storage_type"]],
            ["Курс USD/RUB", str(infra["usd_rub"])],
            ["НДС", pct(float(infra["vat_rate"]))],
            ["Всего vCPU", str(infra["total_vcpu"])],
            ["Всего RAM, GB", str(infra["total_ram"])],
            ["Всего storage, GB", str(infra["total_storage"])],
            ["Месячная стоимость, gross", money(infra["monthly_gross"], calc["currency"])],
            ["Итого за горизонт", money(infra["total_gross"], calc["currency"])],
        ]
        story.append(table(pricing_rows, [60 * mm, 110 * mm], repeat_rows=1))

        resource_rows = [["Ресурс", "vCPU", "RAM GB", "Storage GB"]]
        for item in infra["resources"]:
            resource_rows.append(
                [item["name"], str(item["vcpu"]), str(item["ram_gb"]), str(item["storage_gb"])]
            )
        story.append(Spacer(1, 6))
        story.append(table(resource_rows, [70 * mm, 20 * mm, 25 * mm, 30 * mm], repeat_rows=1))

    if calc["fixed_rows"]:
        story.append(Paragraph("5. Фиксированные ежемесячные блоки", st["h2"]))
        rows = [["Блок", "В месяц", "За горизонт", "Примечание"]]
        for item in calc["fixed_rows"]:
            rows.append(
                [
                    item["name"],
                    money(item["monthly"], calc["currency"]),
                    money(item["total"], calc["currency"]),
                    item["notes"],
                ]
            )
        story.append(table(rows, [55 * mm, 30 * mm, 35 * mm, 50 * mm], repeat_rows=1))

    training = calc["training"]
    if training:
        story.append(Paragraph("6. Обучение", st["h2"]))
        rows = [["Месяц", "Новые", "Группы", "Часы", "Стоимость"]]
        for item in training["rows"]:
            rows.append(
                [
                    str(item["month"]),
                    str(item["new_users"]),
                    str(item["groups"]),
                    f"{item['hours']:.0f}",
                    money(item["cost"], calc["currency"]),
                ]
            )
        rows.append(["Итого", "", "", "", money(training["total"], calc["currency"])])
        story.append(table(rows, [20 * mm, 25 * mm, 20 * mm, 25 * mm, 40 * mm], repeat_rows=1))
        if training["notes"]:
            story.append(Paragraph(f"Примечание: {training['notes']}", st["body"]))

    story.append(Paragraph("7. Итог TCO", st["h2"]))
    result_rows = [["Показатель", "Значение"]]
    if infra:
        result_rows.append(["Infra proxy", money(infra["total_gross"], calc["currency"])])
    result_rows.append(["Фиксированные блоки", money(calc["fixed_total"], calc["currency"])])
    if training:
        result_rows.append(["Обучение", money(training["total"], calc["currency"])])
    result_rows.append(["Baseline TCO", money(calc["baseline"], calc["currency"])])
    result_rows.append(["Резерв", money(calc["reserve"], calc["currency"])])
    result_rows.append(["Итоговый TCO", money(calc["total_tco"], calc["currency"])])
    story.append(table(result_rows, [70 * mm, 70 * mm], repeat_rows=1))

    story.append(Paragraph("8. Unit-метрики", st["h2"]))
    metric_rows = [["Метрика", "Значение"]]
    if calc["peak_active"]:
        metric_rows.append(["Стоимость на peak active user", money(calc["cost_per_peak_active"], calc["currency"])])
    if calc["total_new"]:
        metric_rows.append(["Стоимость на onboarded user", money(calc["cost_per_new_user"], calc["currency"])])
    story.append(table(metric_rows, [70 * mm, 70 * mm], repeat_rows=1))

    sources = cfg.get("sources", [])
    if sources:
        story.append(Paragraph("9. Источники", st["h2"]))
        for src in sources:
            story.append(Paragraph(f"- {src}", st["body"]))

    doc.build(story)


def main():
    parser = argparse.ArgumentParser(description="Generate Russian TCO PDF from JSON config.")
    parser.add_argument("--input", required=True, help="Path to JSON config")
    parser.add_argument("--output", required=True, help="Path to output PDF")
    args = parser.parse_args()

    cfg = load_json(Path(args.input))
    calc = compute(cfg)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    build_pdf(cfg, calc, output)

    print(f"PDF: {output}")
    print(f"Baseline TCO: {money(calc['baseline'], calc['currency'])}")
    print(f"Total TCO: {money(calc['total_tco'], calc['currency'])}")


if __name__ == "__main__":
    main()
