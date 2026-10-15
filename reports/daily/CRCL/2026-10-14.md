# Daily Technical Report — Circle Internet Group (CRCL)

- Generated: 2026-10-15T00:40:46.034369+00:00
- Latest daily market bar: 2026-10-14
- Explicit data refresh: successful
- Scope: technical analysis only; latest daily bars are not tick-level real-time quotes.

## 1. Stock overview

Price is **79.55**, versus a 2026-04-16–2026-10-14 range of 57.84–140.00. It is -43.18% from the period high and 37.53% from the period low.

## 2. Trend analysis

- SMA20 / SMA50 / SMA200: 85.84 / 84.55 / 86.04.
- Price position: SMA20 **below**, SMA50 **below**, SMA200 **below**.
- EMA20 / EMA50: 84.60 / 84.05; stack **bullish**.
- Latest SMA50/200 event: death_cross (2026-06-30).

## 3. Momentum

- RSI(14): **42.61** (neutral); divergence **none**.
- MACD / signal / histogram: -1.2938 / -0.6471 / -0.6467.
- MACD state: **bearish**, histogram **contracting**.

## 4. Volatility

- Bollinger lower / mid / upper: 76.48 / 85.84 / 95.20; %B 0.164.
- Squeeze: **True**; volatility **contracting**.
- ATR(14): 5.3677 (6.75% of price); expected daily range 5.37.

## 5. Volume

- OBV trend **rising**, strength **weak**.
- Price confirmation: **False**; divergence **bullish_accumulation**.

## 6. Key levels

- Quick 60-bar support / resistance: 57.84 / 103.28.
- Distance to support / resistance: 27.29% / 29.83%; range reward:risk 1.09.

**Confirmed supports**

- 76.52 (11 touches; last 2026-10-08; -3.81% from price)
- 64.92 (1 touches; last 2025-11-20; -18.39% from price)
- 58.84 (6 touches; last 2026-08-03; -26.03% from price)

**Confirmed resistances**

- 87.91 (11 touches; last 2026-10-09; 10.51% from price)
- 101.32 (8 touches; last 2026-09-21; 27.37% from price)
- 111.20 (1 touches; last 2026-04-17; 39.79% from price)

Dominant swing: **down**, 147.44 (2025-10-27) to 49.90 (2026-02-05). Nearest Fibonacci level is 0.236 at 72.92 (-8.33% from price).

## 7. Indicator conflicts and risks

- Trend stack is **bullish** while MACD is **bearish**; disagreement here is a live trend/momentum conflict, not something to smooth over.
- RSI divergence is **none** and price/OBV confirmation is **False**.
- Bollinger squeeze is **True** while ATR-based volatility is **contracting**.
- Circle has a comparatively short public-market history; long-horizon statistics and any validation score require extra caution.

## 8. Mechanical summary and bias

The council state is **flat position; bearish evidence suppressed by long-only policy**, conviction **0.000**, effective breadth **1.00**, and veto **True**. The council is the only validated directional verdict; the classic indicators above remain descriptive.

```json
{
  "direction": "flat",
  "conviction": 0.0,
  "effective_breadth": 1.0,
  "entry": 79.55,
  "stop": 79.55,
  "target": 79.55,
  "long_only_suppressed": true
}
```

## 9. Seven-day report review

Compared with **5** prior report(s) from 2026-10-07 through 2026-10-14, price changed **-1.60%**. RSI ranged from 42.61 to 48.82. Council state changed 2 time(s).

| market date | price | RSI | EMA stack | MACD | council | conviction |
|---|---:|---:|---|---|---|---:|
| 2026-10-07 | 80.84 | 43.78 | bullish | bearish | bearish / suppressed | 0.000 |
| 2026-10-08 | 80.84 | 43.78 | bullish | bearish | bearish / suppressed | 0.000 |
| 2026-10-09 | 84.51 | 48.82 | bullish | bearish | bearish / suppressed | 0.000 |
| 2026-10-12 | 83.87 | 48.01 | bullish | bearish | bearish / suppressed | 0.000 |
| 2026-10-13 | 84.27 | 48.59 | bullish | bearish | flat | 0.000 |
| 2026-10-14 | 79.55 | 42.61 | bullish | bearish | bearish / suppressed | 0.000 |

## 10. Backtesting and validation

Archived-signal scorecard: **insufficient sample**. At a 5-bar horizon, 9 directional report(s) have matured, 4 are pending, and 41 were honest abstentions.
Observed directional hit rate is 55.56% and mean signed forward return is -0.17%.
No performance claim is made until at least 20 directional reports mature. This is prospective validation of archived calls—not a replacement for a cost-aware portfolio backtest with slippage, turnover, and benchmark comparison.
