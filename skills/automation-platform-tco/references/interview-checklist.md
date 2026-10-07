# Interview Checklist

Use this order by default. Ask one question at a time. Skip blocks already answered.

## 1. Scope

1. What exactly are we calculating: one platform, comparison of options, or build-vs-buy?
2. What horizon to use: 6 months, 12 months, 3 years, other?
3. What currency should the output use?
4. Include or exclude already-spent development cost?
5. Which blocks belong in scope:
   - infra
   - inference
   - licenses
   - support/ops
   - L1/L2/L3
   - training
   - security/compliance
   - reserve

## 2. Demand and rollout

1. How many active users by month?
2. Is user count cumulative?
3. How many new users are onboarded each month?
4. Does support scale with users or stay fixed from month 1?

## 3. Deployment model

1. Where does platform run: cloud, private cloud, on-prem, hybrid?
2. Are resources dedicated fully to this platform or shared?
3. If shared, what allocation share belongs to platform?

## 4. Infra pricing path

1. Do internal rates exist for vCPU, RAM, storage, GPU?
2. If no internal rates, may we proxy with official public-cloud tariffs?
3. Which official source should act as proxy?
4. Which FX source should convert foreign-currency prices?

## 5. Technical footprint

1. List non-GPU resources:
   - VM or service name
   - vCPU
   - RAM
   - storage
2. Are resources held all period or ramped by month?
3. Which storage type to proxy: HDD, SSD, object storage, other?

## 6. Inference

1. Is inference priced by capacity or by tokens/requests?
2. If by capacity:
   - how many GPU nodes/cards
   - exact monthly cost or public proxy
   - whether price already includes VAT
3. If by usage:
   - model/provider
   - unit price
   - expected monthly load

## 7. Support

1. What FTE or monthly hours to use for:
   - L1/L2
   - L3
   - separate ops role if any
2. Are rates monthly fully loaded rates?
3. Are these fixed from month 1 or proportional to adoption?

## 8. Training

1. Is training one-time or wave-based?
2. Group size?
3. Group onboarding hours per cohort?
4. Individual hours per user?
5. Specialist monthly rate and standard hours per month?
6. Count only specialist time, or user time too?

## 9. Taxes and reserve

1. Calculate with VAT or without?
2. If with VAT, which blocks get VAT:
   - all external purchases
   - only selected vendors
   - all costs
3. What reserve to apply: 0%, 10%, 15%, other?

## 10. Final control

Before calculation, confirm:

- all included cost blocks
- all excluded cost blocks
- tariff and FX source dates
- fixed overrides provided by user
- biggest uncertainty
