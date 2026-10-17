# Daily Technical Report — Circle Internet Group (CRCL)

- Generated: 2026-10-17T00:39:42.782059+00:00
- Latest daily market bar: 2026-10-16
- Explicit data refresh: successful
- Scope: technical analysis only; latest daily bars are not tick-level real-time quotes.

## 1. Stock overview

Price is **82.22**, versus a 2026-04-20–2026-10-16 range of 57.84–140.00. It is -41.27% from the period high and 42.15% from the period low.

## 2. Trend analysis

- SMA20 / SMA50 / SMA200: 85.46 / 85.40 / 86.08.
- Price position: SMA20 **below**, SMA50 **below**, SMA200 **below**.
- EMA20 / EMA50: 84.58 / 84.09; stack **bullish**.
- Latest SMA50/200 event: death_cross (2026-06-30).

## 3. Momentum

- RSI(14): **46.93** (neutral); divergence **none**.
- MACD / signal / histogram: -1.0010 / -0.7621 / -0.2390.
- MACD state: **bearish**, histogram **contracting**.

## 4. Volatility

- Bollinger lower / mid / upper: 76.36 / 85.46 / 94.55; %B 0.322.
- Squeeze: **True**; volatility **contracting**.
- ATR(14): 5.9495 (7.24% of price); expected daily range 5.95.

## 5. Volume

- OBV trend **falling**, strength **weak**.
- Price confirmation: **True**; divergence **none**.

## 6. Key levels

- Quick 60-bar support / resistance: 57.84 / 103.28.
- Distance to support / resistance: 29.65% / 25.61%; range reward:risk 0.86.

**Confirmed supports**

- 76.52 (11 touches; last 2026-10-08; -6.93% from price)
- 64.92 (1 touches; last 2025-11-20; -21.04% from price)
- 58.84 (6 touches; last 2026-08-03; -28.44% from price)

**Confirmed resistances**

- 87.91 (11 touches; last 2026-10-09; 6.92% from price)
- 101.32 (8 touches; last 2026-09-21; 23.23% from price)
- 111.20 (1 touches; last 2026-04-17; 35.25% from price)

Dominant swing: **down**, 147.44 (2025-10-27) to 49.90 (2026-02-05). Nearest Fibonacci level is 0.382 at 87.16 (6.01% from price).

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
  "entry": 82.22,
  "stop": 82.22,
  "target": 82.22,
  "long_only_suppressed": false
}
```

## 9. Seven-day report review

Compared with **5** prior report(s) from 2026-10-09 through 2026-10-16, price changed **-2.71%**. RSI ranged from 42.61 to 52.50. Council state changed 3 time(s).

| market date | price | RSI | EMA stack | MACD | council | conviction |
|---|---:|---:|---|---|---|---:|
| 2026-10-09 | 84.51 | 48.82 | bullish | bearish | bearish / suppressed | 0.000 |
| 2026-10-12 | 83.87 | 48.01 | bullish | bearish | bearish / suppressed | 0.000 |
| 2026-10-13 | 84.27 | 48.59 | bullish | bearish | flat | 0.000 |
| 2026-10-14 | 79.55 | 42.61 | bullish | bearish | bearish / suppressed | 0.000 |
| 2026-10-15 | 86.97 | 52.50 | bullish | bearish | flat | 0.000 |
| 2026-10-16 | 82.22 | 46.93 | bullish | bearish | flat | 0.000 |

## 10. Backtesting and validation

Archived-signal scorecard: **insufficient sample**. At a 5-bar horizon, 11 directional report(s) have matured, 2 are pending, and 43 were honest abstentions.
Observed directional hit rate is 54.55% and mean signed forward return is -0.58%.
No performance claim is made until at least 20 directional reports mature. This is prospective validation of archived calls—not a replacement for a cost-aware portfolio backtest with slippage, turnover, and benchmark comparison.
