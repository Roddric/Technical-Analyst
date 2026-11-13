# Daily Technical Report — Circle Internet Group (CRCL)

- Generated: 2026-11-13T02:44:28.253821+00:00
- Latest daily market bar: 2026-11-12
- Explicit data refresh: successful
- Scope: technical analysis only; latest daily bars are not tick-level real-time quotes.

## 1. Stock overview

Price is **63.82**, versus a 2026-05-15–2026-11-12 range of 57.84–118.85. It is -46.30% from the period high and 10.34% from the period low.

## 2. Trend analysis

- SMA20 / SMA50 / SMA200: 76.58 / 83.50 / 85.90.
- Price position: SMA20 **below**, SMA50 **below**, SMA200 **below**.
- EMA20 / EMA50: 74.23 / 79.08; stack **bearish**.
- Latest SMA50/200 event: death_cross (2026-11-05).

## 3. Momentum

- RSI(14): **32.92** (neutral); divergence **none**.
- MACD / signal / histogram: -5.0139 / -3.7105 / -1.3035.
- MACD state: **bearish**, histogram **contracting**.

## 4. Volatility

- Bollinger lower / mid / upper: 61.04 / 76.58 / 92.12; %B 0.089.
- Squeeze: **False**; volatility **expanding**.
- ATR(14): 5.2586 (8.24% of price); expected daily range 5.26.

## 5. Volume

- OBV trend **falling**, strength **moderate**.
- Price confirmation: **True**; divergence **none**.

## 6. Key levels

- Quick 60-bar support / resistance: 62.77 / 103.28.
- Distance to support / resistance: 1.65% / 61.83%; range reward:risk 37.58.

**Confirmed supports**

- 58.84 (6 touches; last 2026-08-03; -7.80% from price)
- 49.90 (1 touches; last 2026-02-05; -21.81% from price)

**Confirmed resistances**

- 64.92 (1 touches; last 2025-11-20; 1.72% from price)
- 76.11 (14 touches; last 2026-11-04; 19.26% from price)
- 88.22 (13 touches; last 2026-10-21; 38.23% from price)

Dominant swing: **up**, 49.90 (2026-02-05) to 140.00 (2026-05-12). Nearest Fibonacci level is 0.786 at 69.18 (8.40% from price).

## 7. Indicator conflicts and risks

- Trend stack is **bearish** while MACD is **bearish**; disagreement here is a live trend/momentum conflict, not something to smooth over.
- RSI divergence is **none** and price/OBV confirmation is **True**.
- Bollinger squeeze is **False** while ATR-based volatility is **expanding**.
- Circle has a comparatively short public-market history; long-horizon statistics and any validation score require extra caution.

## 8. Mechanical summary and bias

The council state is **flat**, conviction **0.000**, effective breadth **0.00**, and veto **True**. The council is the only validated directional verdict; the classic indicators above remain descriptive.

```json
{
  "direction": "flat",
  "conviction": 0.0,
  "effective_breadth": 0.0,
  "entry": 63.82,
  "stop": 63.82,
  "target": 63.82,
  "long_only_suppressed": false
}
```

## 9. Seven-day report review

Compared with **5** prior report(s) from 2026-11-05 through 2026-11-12, price changed **-8.15%**. RSI ranged from 32.18 to 36.13. Council state changed 0 time(s).

| market date | price | RSI | EMA stack | MACD | council | conviction |
|---|---:|---:|---|---|---|---:|
| 2026-11-05 | 69.48 | 36.13 | bearish | bearish | flat | 0.000 |
| 2026-11-06 | 67.88 | 34.75 | bearish | bearish | flat | 0.000 |
| 2026-11-09 | 67.56 | 34.46 | bearish | bearish | flat | 0.000 |
| 2026-11-10 | 64.98 | 32.18 | bearish | bearish | flat | 0.000 |
| 2026-11-11 | 67.12 | 35.97 | bearish | bearish | flat | 0.000 |
| 2026-11-12 | 63.82 | 32.92 | bearish | bearish | flat | 0.000 |

## 10. Backtesting and validation

Archived-signal scorecard: **insufficient sample**. At a 5-bar horizon, 13 directional report(s) have matured, 0 are pending, and 62 were honest abstentions.
Observed directional hit rate is 53.85% and mean signed forward return is -1.25%.
No performance claim is made until at least 20 directional reports mature. This is prospective validation of archived calls—not a replacement for a cost-aware portfolio backtest with slippage, turnover, and benchmark comparison.
