# Daily Technical Report — Circle Internet Group (CRCL)

- Generated: 2026-11-06T02:40:37.323070+00:00
- Latest daily market bar: 2026-11-05
- Explicit data refresh: successful
- Scope: technical analysis only; latest daily bars are not tick-level real-time quotes.

## 1. Stock overview

Price is **69.48**, versus a 2026-05-08–2026-11-05 range of 57.84–140.00. It is -50.37% from the period high and 20.12% from the period low.

## 2. Trend analysis

- SMA20 / SMA50 / SMA200: 80.97 / 85.97 / 86.02.
- Price position: SMA20 **below**, SMA50 **below**, SMA200 **below**.
- EMA20 / EMA50: 79.51 / 81.93; stack **bearish**.
- Latest SMA50/200 event: death_cross (2026-11-05).

## 3. Momentum

- RSI(14): **36.13** (neutral); divergence **none**.
- MACD / signal / histogram: -3.1805 / -1.9909 / -1.1896.
- MACD state: **bearish**, histogram **contracting**.

## 4. Volatility

- Bollinger lower / mid / upper: 70.29 / 80.97 / 91.65; %B -0.038.
- Squeeze: **False**; volatility **expanding**.
- ATR(14): 5.7752 (8.31% of price); expected daily range 5.78.

## 5. Volume

- OBV trend **falling**, strength **moderate**.
- Price confirmation: **True**; divergence **none**.

## 6. Key levels

- Quick 60-bar support / resistance: 64.81 / 103.28.
- Distance to support / resistance: 6.72% / 48.65%; range reward:risk 7.24.

**Confirmed supports**

- 64.92 (1 touches; last 2025-11-20; -6.56% from price)
- 58.84 (6 touches; last 2026-08-03; -15.31% from price)
- 49.90 (1 touches; last 2026-02-05; -28.18% from price)

**Confirmed resistances**

- 76.00 (13 touches; last 2026-10-30; 9.38% from price)
- 88.22 (13 touches; last 2026-10-21; 26.97% from price)
- 101.32 (8 touches; last 2026-09-21; 45.83% from price)

Dominant swing: **up**, 49.90 (2026-02-05) to 140.00 (2026-05-12). Nearest Fibonacci level is 0.786 at 69.18 (-0.43% from price).

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
  "entry": 69.48,
  "stop": 69.48,
  "target": 69.48,
  "long_only_suppressed": false
}
```

## 9. Seven-day report review

Compared with **5** prior report(s) from 2026-10-29 through 2026-11-05, price changed **-13.14%**. RSI ranged from 36.13 to 44.47. Council state changed 0 time(s).

| market date | price | RSI | EMA stack | MACD | council | conviction |
|---|---:|---:|---|---|---|---:|
| 2026-10-29 | 79.99 | 44.47 | bearish | bearish | flat | 0.000 |
| 2026-10-30 | 72.54 | 36.95 | bearish | bearish | flat | 0.000 |
| 2026-11-02 | 72.08 | 36.54 | bearish | bearish | flat | 0.000 |
| 2026-11-03 | 75.22 | 41.34 | bearish | bearish | flat | 0.000 |
| 2026-11-04 | 76.12 | 42.67 | bearish | bearish | flat | 0.000 |
| 2026-11-05 | 69.48 | 36.13 | bearish | bearish | flat | 0.000 |

## 10. Backtesting and validation

Archived-signal scorecard: **insufficient sample**. At a 5-bar horizon, 13 directional report(s) have matured, 0 are pending, and 57 were honest abstentions.
Observed directional hit rate is 53.85% and mean signed forward return is -1.25%.
No performance claim is made until at least 20 directional reports mature. This is prospective validation of archived calls—not a replacement for a cost-aware portfolio backtest with slippage, turnover, and benchmark comparison.
