# Daily Technical Report — Circle Internet Group (CRCL)

- Generated: 2026-10-30T02:04:03.613751+00:00
- Latest daily market bar: 2026-10-29
- Explicit data refresh: successful
- Scope: technical analysis only; latest daily bars are not tick-level real-time quotes.

## 1. Stock overview

Price is **79.99**, versus a 2026-05-01–2026-10-29 range of 57.84–140.00. It is -42.86% from the period high and 38.30% from the period low.

## 2. Trend analysis

- SMA20 / SMA50 / SMA200: 83.22 / 87.49 / 86.12.
- Price position: SMA20 **below**, SMA50 **below**, SMA200 **below**.
- EMA20 / EMA50: 83.72 / 83.89; stack **bearish**.
- Latest SMA50/200 event: golden_cross (2026-10-21).

## 3. Momentum

- RSI(14): **44.47** (neutral); divergence **none**.
- MACD / signal / histogram: -1.0016 / -0.6575 / -0.3441.
- MACD state: **bearish**, histogram **expanding**.

## 4. Volatility

- Bollinger lower / mid / upper: 77.81 / 83.22 / 88.62; %B 0.201.
- Squeeze: **True**; volatility **expanding**.
- ATR(14): 5.2354 (6.55% of price); expected daily range 5.24.

## 5. Volume

- OBV trend **rising**, strength **weak**.
- Price confirmation: **False**; divergence **bullish_accumulation**.

## 6. Key levels

- Quick 60-bar support / resistance: 60.01 / 103.28.
- Distance to support / resistance: 24.98% / 29.12%; range reward:risk 1.17.

**Confirmed supports**

- 76.41 (12 touches; last 2026-10-15; -4.48% from price)
- 64.92 (1 touches; last 2025-11-20; -18.84% from price)
- 58.84 (6 touches; last 2026-08-03; -26.44% from price)

**Confirmed resistances**

- 88.22 (13 touches; last 2026-10-21; 10.29% from price)
- 101.32 (8 touches; last 2026-09-21; 26.67% from price)
- 111.20 (1 touches; last 2026-04-17; 39.02% from price)

Dominant swing: **up**, 49.90 (2026-02-05) to 140.00 (2026-05-12). Nearest Fibonacci level is 0.618 at 84.32 (5.41% from price).

## 7. Indicator conflicts and risks

- Trend stack is **bearish** while MACD is **bearish**; disagreement here is a live trend/momentum conflict, not something to smooth over.
- RSI divergence is **none** and price/OBV confirmation is **False**.
- Bollinger squeeze is **True** while ATR-based volatility is **expanding**.
- Circle has a comparatively short public-market history; long-horizon statistics and any validation score require extra caution.

## 8. Mechanical summary and bias

The council state is **flat**, conviction **0.000**, effective breadth **0.00**, and veto **True**. The council is the only validated directional verdict; the classic indicators above remain descriptive.

```json
{
  "direction": "flat",
  "conviction": 0.0,
  "effective_breadth": 0.0,
  "entry": 79.99,
  "stop": 79.99,
  "target": 79.99,
  "long_only_suppressed": false
}
```

## 9. Seven-day report review

Compared with **5** prior report(s) from 2026-10-22 through 2026-10-29, price changed **-7.65%**. RSI ranged from 44.10 to 51.83. Council state changed 0 time(s).

| market date | price | RSI | EMA stack | MACD | council | conviction |
|---|---:|---:|---|---|---|---:|
| 2026-10-22 | 86.62 | 51.83 | bullish | bullish | flat | 0.000 |
| 2026-10-23 | 85.91 | 50.96 | bullish | bullish | flat | 0.000 |
| 2026-10-26 | 79.84 | 44.10 | bullish | bullish | flat | 0.000 |
| 2026-10-27 | 81.58 | 46.33 | bullish | bearish | flat | 0.000 |
| 2026-10-28 | 81.71 | 46.50 | bullish | bearish | flat | 0.000 |
| 2026-10-29 | 79.99 | 44.47 | bearish | bearish | flat | 0.000 |

## 10. Backtesting and validation

Archived-signal scorecard: **insufficient sample**. At a 5-bar horizon, 13 directional report(s) have matured, 0 are pending, and 52 were honest abstentions.
Observed directional hit rate is 53.85% and mean signed forward return is -1.25%.
No performance claim is made until at least 20 directional reports mature. This is prospective validation of archived calls—not a replacement for a cost-aware portfolio backtest with slippage, turnover, and benchmark comparison.
