# Daily Technical Report — Circle Internet Group (CRCL)

- Generated: 2026-10-31T01:43:08.884213+00:00
- Latest daily market bar: 2026-10-30
- Explicit data refresh: successful
- Scope: technical analysis only; latest daily bars are not tick-level real-time quotes.

## 1. Stock overview

Price is **72.54**, versus a 2026-05-04–2026-10-30 range of 57.84–140.00. It is -48.19% from the period high and 25.41% from the period low.

## 2. Trend analysis

- SMA20 / SMA50 / SMA200: 82.78 / 87.27 / 86.06.
- Price position: SMA20 **below**, SMA50 **below**, SMA200 **below**.
- EMA20 / EMA50: 82.66 / 83.44; stack **bearish**.
- Latest SMA50/200 event: golden_cross (2026-10-21).

## 3. Momentum

- RSI(14): **36.95** (neutral); divergence **none**.
- MACD / signal / histogram: -1.7626 / -0.8785 / -0.8841.
- MACD state: **bearish**, histogram **expanding**.

## 4. Volatility

- Bollinger lower / mid / upper: 75.68 / 82.78 / 89.89; %B -0.221.
- Squeeze: **True**; volatility **expanding**.
- ATR(14): 5.5036 (7.59% of price); expected daily range 5.50.

## 5. Volume

- OBV trend **falling**, strength **weak**.
- Price confirmation: **True**; divergence **none**.

## 6. Key levels

- Quick 60-bar support / resistance: 64.50 / 103.28.
- Distance to support / resistance: 11.08% / 42.38%; range reward:risk 3.82.

**Confirmed supports**

- 64.92 (1 touches; last 2025-11-20; -10.50% from price)
- 58.84 (6 touches; last 2026-08-03; -18.89% from price)
- 49.90 (1 touches; last 2026-02-05; -31.21% from price)

**Confirmed resistances**

- 76.41 (12 touches; last 2026-10-15; 5.33% from price)
- 88.22 (13 touches; last 2026-10-21; 21.62% from price)
- 101.32 (8 touches; last 2026-09-21; 39.67% from price)

Dominant swing: **up**, 49.90 (2026-02-05) to 140.00 (2026-05-12). Nearest Fibonacci level is 0.786 at 69.18 (-4.63% from price).

## 7. Indicator conflicts and risks

- Trend stack is **bearish** while MACD is **bearish**; disagreement here is a live trend/momentum conflict, not something to smooth over.
- RSI divergence is **none** and price/OBV confirmation is **True**.
- Bollinger squeeze is **True** while ATR-based volatility is **expanding**.
- Circle has a comparatively short public-market history; long-horizon statistics and any validation score require extra caution.

## 8. Mechanical summary and bias

The council state is **flat**, conviction **0.000**, effective breadth **0.00**, and veto **True**. The council is the only validated directional verdict; the classic indicators above remain descriptive.

```json
{
  "direction": "flat",
  "conviction": 0.0,
  "effective_breadth": 0.0,
  "entry": 72.54,
  "stop": 72.54,
  "target": 72.54,
  "long_only_suppressed": false
}
```

## 9. Seven-day report review

Compared with **5** prior report(s) from 2026-10-23 through 2026-10-30, price changed **-15.56%**. RSI ranged from 36.95 to 50.96. Council state changed 0 time(s).

| market date | price | RSI | EMA stack | MACD | council | conviction |
|---|---:|---:|---|---|---|---:|
| 2026-10-23 | 85.91 | 50.96 | bullish | bullish | flat | 0.000 |
| 2026-10-26 | 79.84 | 44.10 | bullish | bullish | flat | 0.000 |
| 2026-10-27 | 81.58 | 46.33 | bullish | bearish | flat | 0.000 |
| 2026-10-28 | 81.71 | 46.50 | bullish | bearish | flat | 0.000 |
| 2026-10-29 | 79.99 | 44.47 | bearish | bearish | flat | 0.000 |
| 2026-10-30 | 72.54 | 36.95 | bearish | bearish | flat | 0.000 |

## 10. Backtesting and validation

Archived-signal scorecard: **insufficient sample**. At a 5-bar horizon, 13 directional report(s) have matured, 0 are pending, and 53 were honest abstentions.
Observed directional hit rate is 53.85% and mean signed forward return is -1.25%.
No performance claim is made until at least 20 directional reports mature. This is prospective validation of archived calls—not a replacement for a cost-aware portfolio backtest with slippage, turnover, and benchmark comparison.
