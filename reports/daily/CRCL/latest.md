# Daily Technical Report — Circle Internet Group (CRCL)

- Generated: 2026-10-21T00:43:38.982302+00:00
- Latest daily market bar: 2026-10-20
- Explicit data refresh: successful
- Scope: technical analysis only; latest daily bars are not tick-level real-time quotes.

## 1. Stock overview

Price is **85.87**, versus a 2026-04-22–2026-10-20 range of 57.84–140.00. It is -38.66% from the period high and 48.46% from the period low.

## 2. Trend analysis

- SMA20 / SMA50 / SMA200: 84.36 / 86.07 / 86.10.
- Price position: SMA20 **above**, SMA50 **below**, SMA200 **below**.
- EMA20 / EMA50: 84.42 / 84.05; stack **bullish**.
- Latest SMA50/200 event: death_cross (2026-06-30).

## 3. Momentum

- RSI(14): **51.53** (neutral); divergence **none**.
- MACD / signal / histogram: -0.8388 / -0.8344 / -0.0043.
- MACD state: **bearish**, histogram **contracting**.

## 4. Volatility

- Bollinger lower / mid / upper: 77.42 / 84.36 / 91.31; %B 0.608.
- Squeeze: **True**; volatility **contracting**.
- ATR(14): 5.8446 (6.81% of price); expected daily range 5.84.

## 5. Volume

- OBV trend **falling**, strength **weak**.
- Price confirmation: **True**; divergence **none**.

## 6. Key levels

- Quick 60-bar support / resistance: 57.84 / 103.28.
- Distance to support / resistance: 32.64% / 20.27%; range reward:risk 0.62.

**Confirmed supports**

- 76.41 (12 touches; last 2026-10-15; -11.02% from price)
- 64.92 (1 touches; last 2025-11-20; -24.40% from price)
- 58.84 (6 touches; last 2026-08-03; -31.48% from price)

**Confirmed resistances**

- 87.89 (12 touches; last 2026-10-15; 2.35% from price)
- 101.32 (8 touches; last 2026-09-21; 17.99% from price)
- 111.20 (1 touches; last 2026-04-17; 29.50% from price)

Dominant swing: **down**, 147.44 (2025-10-27) to 49.90 (2026-02-05). Nearest Fibonacci level is 0.382 at 87.16 (1.50% from price).

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
  "entry": 85.87,
  "stop": 85.87,
  "target": 85.87,
  "long_only_suppressed": false
}
```

## 9. Seven-day report review

Compared with **5** prior report(s) from 2026-10-13 through 2026-10-20, price changed **1.90%**. RSI ranged from 42.61 to 52.50. Council state changed 2 time(s).

| market date | price | RSI | EMA stack | MACD | council | conviction |
|---|---:|---:|---|---|---|---:|
| 2026-10-13 | 84.27 | 48.59 | bullish | bearish | flat | 0.000 |
| 2026-10-14 | 79.55 | 42.61 | bullish | bearish | bearish / suppressed | 0.000 |
| 2026-10-15 | 86.97 | 52.50 | bullish | bearish | flat | 0.000 |
| 2026-10-16 | 82.22 | 46.93 | bullish | bearish | flat | 0.000 |
| 2026-10-19 | 81.37 | 45.98 | bullish | bearish | flat | 0.000 |
| 2026-10-20 | 85.87 | 51.53 | bullish | bearish | flat | 0.000 |

## 10. Backtesting and validation

Archived-signal scorecard: **insufficient sample**. At a 5-bar horizon, 12 directional report(s) have matured, 1 are pending, and 45 were honest abstentions.
Observed directional hit rate is 58.33% and mean signed forward return is -0.29%.
No performance claim is made until at least 20 directional reports mature. This is prospective validation of archived calls—not a replacement for a cost-aware portfolio backtest with slippage, turnover, and benchmark comparison.
