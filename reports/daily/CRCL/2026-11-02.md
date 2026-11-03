# Daily Technical Report — Circle Internet Group (CRCL)

- Generated: 2026-11-03T03:33:13.798502+00:00
- Latest daily market bar: 2026-11-02
- Explicit data refresh: successful
- Scope: technical analysis only; latest daily bars are not tick-level real-time quotes.

## 1. Stock overview

Price is **72.08**, versus a 2026-05-05–2026-11-02 range of 57.84–140.00. It is -48.51% from the period high and 24.62% from the period low.

## 2. Trend analysis

- SMA20 / SMA50 / SMA200: 82.22 / 86.95 / 86.04.
- Price position: SMA20 **below**, SMA50 **below**, SMA200 **below**.
- EMA20 / EMA50: 81.65 / 83.00; stack **bearish**.
- Latest SMA50/200 event: golden_cross (2026-10-21).

## 3. Momentum

- RSI(14): **36.54** (neutral); divergence **none**.
- MACD / signal / histogram: -2.3756 / -1.1779 / -1.1976.
- MACD state: **bearish**, histogram **expanding**.

## 4. Volatility

- Bollinger lower / mid / upper: 73.73 / 82.22 / 90.71; %B -0.097.
- Squeeze: **True**; volatility **expanding**.
- ATR(14): 5.4234 (7.52% of price); expected daily range 5.42.

## 5. Volume

- OBV trend **falling**, strength **moderate**.
- Price confirmation: **True**; divergence **none**.

## 6. Key levels

- Quick 60-bar support / resistance: 64.50 / 103.28.
- Distance to support / resistance: 10.52% / 43.29%; range reward:risk 4.12.

**Confirmed supports**

- 64.92 (1 touches; last 2025-11-20; -9.93% from price)
- 58.84 (6 touches; last 2026-08-03; -18.37% from price)
- 49.90 (1 touches; last 2026-02-05; -30.77% from price)

**Confirmed resistances**

- 76.41 (12 touches; last 2026-10-15; 6.01% from price)
- 88.22 (13 touches; last 2026-10-21; 22.39% from price)
- 101.32 (8 touches; last 2026-09-21; 40.57% from price)

Dominant swing: **up**, 49.90 (2026-02-05) to 140.00 (2026-05-12). Nearest Fibonacci level is 0.786 at 69.18 (-4.02% from price).

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
  "entry": 72.08,
  "stop": 72.08,
  "target": 72.08,
  "long_only_suppressed": false
}
```

## 9. Seven-day report review

Compared with **5** prior report(s) from 2026-10-26 through 2026-11-02, price changed **-9.72%**. RSI ranged from 36.54 to 46.50. Council state changed 0 time(s).

| market date | price | RSI | EMA stack | MACD | council | conviction |
|---|---:|---:|---|---|---|---:|
| 2026-10-26 | 79.84 | 44.10 | bullish | bullish | flat | 0.000 |
| 2026-10-27 | 81.58 | 46.33 | bullish | bearish | flat | 0.000 |
| 2026-10-28 | 81.71 | 46.50 | bullish | bearish | flat | 0.000 |
| 2026-10-29 | 79.99 | 44.47 | bearish | bearish | flat | 0.000 |
| 2026-10-30 | 72.54 | 36.95 | bearish | bearish | flat | 0.000 |
| 2026-11-02 | 72.08 | 36.54 | bearish | bearish | flat | 0.000 |

## 10. Backtesting and validation

Archived-signal scorecard: **insufficient sample**. At a 5-bar horizon, 13 directional report(s) have matured, 0 are pending, and 54 were honest abstentions.
Observed directional hit rate is 53.85% and mean signed forward return is -1.25%.
No performance claim is made until at least 20 directional reports mature. This is prospective validation of archived calls—not a replacement for a cost-aware portfolio backtest with slippage, turnover, and benchmark comparison.
