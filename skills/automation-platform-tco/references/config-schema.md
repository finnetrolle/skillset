# Config Schema

Create JSON input matching this shape. Keep only fields you need.

## Minimal structure

```json
{
  "project_name": "Filin",
  "horizon_months": 6,
  "currency": "RUB",
  "reserve_rate": 0.10,
  "scope_rows": [
    {"label": "Горизонт", "value": "6 месяцев"},
    {"label": "Контур", "value": "Private cloud, prod"}
  ],
  "user_plan": {
    "active_by_month": [20, 50, 50, 100, 100, 100],
    "new_by_month": [20, 30, 0, 50, 0, 0]
  },
  "assumptions": [
    "Уже понесенная разработка исключена",
    "L1/L2 держим с первого месяца"
  ],
  "sources": [
    "Yandex Cloud pricing, 2026-06-29",
    "ЦБ РФ USD/RUB, 2026-06-27"
  ],
  "infra_proxy": {
    "enabled": true,
    "platform": "Intel Broadwell regular VM",
    "storage_type": "network HDD",
    "vcpu_hour_usd": 0.0103278672,
    "ram_gb_hour_usd": 0.0036065568,
    "hdd_gb_hour_usd": 0.000039344256,
    "usd_rub": 77.0611,
    "vat_rate": 0.20,
    "hours_per_month": 730.5,
    "resources": [
      {"name": "k8s-master", "vcpu": 4, "ram_gb": 8, "storage_gb": 10}
    ]
  },
  "monthly_costs": [
    {
      "name": "Inference: 2 x A100",
      "monthly_amount": 630000,
      "category": "external",
      "includes_vat": true,
      "vat_rate": 0.20,
      "notes": "Полная стоимость нод"
    },
    {
      "name": "L1/L2 support",
      "monthly_amount": 200000,
      "category": "internal",
      "notes": "1.0 FTE"
    },
    {
      "name": "L3 support",
      "monthly_amount": 200000,
      "category": "internal",
      "notes": "0.5 FTE"
    }
  ],
  "training": {
    "enabled": true,
    "specialist_monthly_amount": 450000,
    "hours_per_month": 168,
    "group_size": 10,
    "group_hours": 1,
    "individual_hours_per_user": 3,
    "new_users_by_month": [20, 30, 0, 50, 0, 0],
    "notes": "Считаем только труд специалиста"
  }
}
```

## Field notes

- `project_name`: title in PDF.
- `horizon_months`: used for multiplying monthly fixed costs.
- `scope_rows`: arbitrary summary rows for first section.
- All human-readable text fields are inserted into PDF verbatim. Write them in Russian if final document must be Russian.
- `user_plan.active_by_month`: active users by month.
- `user_plan.new_by_month`: new users by month for training and onboarding metrics.
- `reserve_rate`: decimal, for example `0.10`.

## `monthly_costs`

Use for any fixed monthly block:

- inference cluster
- licenses
- support FTE
- managed service contract
- external vendor support

Fields:

- `name`: row title in results.
- `monthly_amount`: monthly amount in report currency.
- `category`: `internal` or `external`.
- `includes_vat`: boolean, only meaningful for external rows.
- `vat_rate`: decimal if external amount is net and VAT must be added.
- `notes`: optional text for PDF.

## `infra_proxy`

Use when user gives footprint but not internal chargeback rates.

- `hours_per_month`: default `730.5` if omitted.
- `resources`: list with `name`, `vcpu`, `ram_gb`, `storage_gb`.
- Script calculates:
  - monthly net cost from hourly vCPU, RAM, storage rates
  - monthly gross cost with VAT
  - horizon total

## `training`

Script calculates monthly training hours as:

`ceil(new_users / group_size) * group_hours + new_users * individual_hours_per_user`

Hourly specialist rate:

`specialist_monthly_amount / hours_per_month`

Training total:

`sum(month_hours * hourly_rate)`

## Result logic

Script reports:

- monthly and total fixed costs
- infra proxy total
- training total
- baseline TCO
- reserve
- final TCO
- unit metrics:
  - cost per peak active user
  - cost per onboarded unique user
