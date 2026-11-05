# Daily Technical Report — Circle Internet Group (CRCL)

- Generated: 2026-11-05T02:38:43.215595+00:00
- Latest daily market bar: 2026-11-04
- Explicit data refresh: successful
- Scope: technical analysis only; latest daily bars are not tick-level real-time quotes.

## 1. Stock overview

Price is **76.12**, versus a 2026-05-07–2026-11-04 range of 57.84–140.00. It is -45.63% from the period high and 31.60% from the period low.

## 2. Trend analysis

- SMA20 / SMA50 / SMA200: 81.54 / 86.38 / 86.04.
- Price position: SMA20 **below**, SMA50 **below**, SMA200 **below**.
- EMA20 / EMA50: 80.57 / 82.44; stack **bearish**.
- Latest SMA50/200 event: golden_cross (2026-10-21).

## 3. Momentum

- RSI(14): **42.67** (neutral); divergence **none**.
- MACD / signal / histogram: -2.6358 / -1.6935 / -0.9422.
- MACD state: **bearish**, histogram **expanding**.

## 4. Volatility

- Bollinger lower / mid / upper: 72.25 / 81.54 / 90.83; %B 0.208.
- Squeeze: **False**; volatility **expanding**.
- ATR(14): 5.3495 (7.03% of price); expected daily range 5.35.

## 5. Volume

- OBV trend **falling**, strength **weak**.
- Price confirmation: **True**; divergence **none**.

## 6. Key levels

- Quick 60-bar support / resistance: 68.81 / 103.28.
- Distance to support / resistance: 9.60% / 35.68%; range reward:risk 3.72.

**Confirmed supports**

- 76.00 (13 touches; last 2026-10-30; -0.16% from price)
- 64.92 (1 touches; last 2025-11-20; -14.71% from price)
- 58.84 (6 touches; last 2026-08-03; -22.70% from price)

**Confirmed resistances**

- 88.22 (13 touches; last 2026-10-21; 15.90% from price)
- 101.32 (8 touches; last 2026-09-21; 33.11% from price)
- 111.20 (1 touches; last 2026-04-17; 46.09% from price)

Dominant swing: **up**, 49.90 (2026-02-05) to 140.00 (2026-05-12). Nearest Fibonacci level is 0.786 at 69.18 (-9.12% from price).

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
  "entry": 76.12,
  "stop": 76.12,
  "target": 76.12,
  "long_only_suppressed": false
}
```

## 9. Seven-day report review

Compared with **5** prior report(s) from 2026-10-28 through 2026-11-04, price changed **-6.84%**. RSI ranged from 36.54 to 46.50. Council state changed 0 time(s).

| market date | price | RSI | EMA stack | MACD | council | conviction |
|---|---:|---:|---|---|---|---:|
| 2026-10-28 | 81.71 | 46.50 | bullish | bearish | flat | 0.000 |
| 2026-10-29 | 79.99 | 44.47 | bearish | bearish | flat | 0.000 |
| 2026-10-30 | 72.54 | 36.95 | bearish | bearish | flat | 0.000 |
| 2026-11-02 | 72.08 | 36.54 | bearish | bearish | flat | 0.000 |
| 2026-11-03 | 75.22 | 41.34 | bearish | bearish | flat | 0.000 |
| 2026-11-04 | 76.12 | 42.67 | bearish | bearish | flat | 0.000 |

## 10. Backtesting and validation

Archived-signal scorecard: **insufficient sample**. At a 5-bar horizon, 13 directional report(s) have matured, 0 are pending, and 56 were honest abstentions.
Observed directional hit rate is 53.85% and mean signed forward return is -1.25%.
No performance claim is made until at least 20 directional reports mature. This is prospective validation of archived calls—not a replacement for a cost-aware portfolio backtest with slippage, turnover, and benchmark comparison.
