# Daily Technical Report — Circle Internet Group (CRCL)

- Generated: 2026-10-28T01:31:27.211513+00:00
- Latest daily market bar: 2026-10-27
- Explicit data refresh: successful
- Scope: technical analysis only; latest daily bars are not tick-level real-time quotes.

## 1. Stock overview

Price is **81.58**, versus a 2026-04-29–2026-10-27 range of 57.84–140.00. It is -41.73% from the period high and 41.04% from the period low.

## 2. Trend analysis

- SMA20 / SMA50 / SMA200: 83.39 / 87.26 / 86.15.
- Price position: SMA20 **below**, SMA50 **below**, SMA200 **below**.
- EMA20 / EMA50: 84.37 / 84.14; stack **bullish**.
- Latest SMA50/200 event: golden_cross (2026-10-21).

## 3. Momentum

- RSI(14): **46.33** (neutral); divergence **none**.
- MACD / signal / histogram: -0.6477 / -0.5208 / -0.1268.
- MACD state: **bearish**, histogram **contracting**.

## 4. Volatility

- Bollinger lower / mid / upper: 78.21 / 83.39 / 88.56; %B 0.325.
- Squeeze: **True**; volatility **contracting**.
- ATR(14): 5.5991 (6.86% of price); expected daily range 5.60.

## 5. Volume

- OBV trend **falling**, strength **weak**.
- Price confirmation: **True**; divergence **none**.

## 6. Key levels

- Quick 60-bar support / resistance: 59.12 / 103.28.
- Distance to support / resistance: 27.53% / 26.60%; range reward:risk 0.97.

**Confirmed supports**

- 76.41 (12 touches; last 2026-10-15; -6.34% from price)
- 64.92 (1 touches; last 2025-11-20; -20.42% from price)
- 58.84 (6 touches; last 2026-08-03; -27.87% from price)

**Confirmed resistances**

- 88.22 (13 touches; last 2026-10-21; 8.14% from price)
- 101.32 (8 touches; last 2026-09-21; 24.20% from price)
- 111.20 (1 touches; last 2026-04-17; 36.31% from price)

Dominant swing: **up**, 49.90 (2026-02-05) to 140.00 (2026-05-12). Nearest Fibonacci level is 0.618 at 84.32 (3.36% from price).

## 7. Indicator conflicts and risks

- Trend stack is **bullish** while MACD is **bearish**; disagreement here is a live trend/momentum conflict, not something to smooth over.
- RSI divergence is **none** and price/OBV confirmation is **True**.
- Bollinger squeeze is **True** while ATR-based volatility is **contracting**.
- Circle has a comparatively short public-market history; long-horizon statistics and any validation score require extra caution.

## 8. Mechanical summary and bias

The council state is **flat**, conviction **0.000**, effective breadth **0.00**, and veto **True**. The council is the only validated directional verdict; the classic indicators above remain descriptive.

```json
{
  "direction": "flat",
  "conviction": 0.0,
  "effective_breadth": 0.0,
  "entry": 81.58,
  "stop": 81.58,
  "target": 81.58,
  "long_only_suppressed": false
}
```

## 9. Seven-day report review

Compared with **5** prior report(s) from 2026-10-20 through 2026-10-27, price changed **-5.00%**. RSI ranged from 44.10 to 55.70. Council state changed 0 time(s).

| market date | price | RSI | EMA stack | MACD | council | conviction |
|---|---:|---:|---|---|---|---:|
| 2026-10-20 | 85.87 | 51.53 | bullish | bearish | flat | 0.000 |
| 2026-10-21 | 89.71 | 55.70 | bullish | bullish | flat | 0.000 |
| 2026-10-22 | 86.62 | 51.83 | bullish | bullish | flat | 0.000 |
| 2026-10-23 | 85.91 | 50.96 | bullish | bullish | flat | 0.000 |
| 2026-10-26 | 79.84 | 44.10 | bullish | bullish | flat | 0.000 |
| 2026-10-27 | 81.58 | 46.33 | bullish | bearish | flat | 0.000 |

## 10. Backtesting and validation

Archived-signal scorecard: **insufficient sample**. At a 5-bar horizon, 13 directional report(s) have matured, 0 are pending, and 50 were honest abstentions.
Observed directional hit rate is 53.85% and mean signed forward return is -1.25%.
No performance claim is made until at least 20 directional reports mature. This is prospective validation of archived calls—not a replacement for a cost-aware portfolio backtest with slippage, turnover, and benchmark comparison.
