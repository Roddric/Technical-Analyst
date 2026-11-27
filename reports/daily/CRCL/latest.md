# Daily Technical Report — Circle Internet Group (CRCL)

- Generated: 2026-11-27T04:23:28.692122+00:00
- Latest daily market bar: 2026-11-25
- Explicit data refresh: successful
- Scope: technical analysis only; latest daily bars are not tick-level real-time quotes.

## 1. Stock overview

Price is **48.27**, versus a 2026-05-29–2026-11-25 range of 43.11–114.44. It is -57.82% from the period high and 11.97% from the period low.

## 2. Trend analysis

- SMA20 / SMA50 / SMA200: 62.57 / 76.20 / 85.63.
- Price position: SMA20 **below**, SMA50 **below**, SMA200 **below**.
- EMA20 / EMA50: 60.85 / 70.98; stack **bearish**.
- Latest SMA50/200 event: death_cross (2026-11-05).

## 3. Momentum

- RSI(14): **27.29** (oversold); divergence **none**.
- MACD / signal / histogram: -8.4344 / -7.2238 / -1.2107.
- MACD state: **bearish**, histogram **contracting**.

## 4. Volatility

- Bollinger lower / mid / upper: 42.41 / 62.57 / 82.72; %B 0.145.
- Squeeze: **False**; volatility **expanding**.
- ATR(14): 5.0743 (10.51% of price); expected daily range 5.07.

## 5. Volume

- OBV trend **falling**, strength **moderate**.
- Price confirmation: **True**; divergence **none**.

## 6. Key levels

- Quick 60-bar support / resistance: 43.11 / 103.28.
- Distance to support / resistance: 10.69% / 113.96%; range reward:risk 10.66.

**Confirmed supports**

No confirmed swing-pivot zones on this side.

**Confirmed resistances**

- 49.90 (1 touches; last 2026-02-05; 3.38% from price)
- 58.84 (6 touches; last 2026-08-03; 21.90% from price)
- 76.11 (14 touches; last 2026-11-04; 57.68% from price)

Dominant swing: **up**, 49.90 (2026-02-05) to 140.00 (2026-05-12). Nearest Fibonacci level is 0.786 at 69.18 (43.32% from price).

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
  "entry": 48.27,
  "stop": 48.27,
  "target": 48.27,
  "long_only_suppressed": false
}
```

## 9. Seven-day report review

Compared with **4** prior report(s) from 2026-11-18 through 2026-11-25, price changed **-9.45%**. RSI ranged from 21.21 to 28.80. Council state changed 0 time(s).

| market date | price | RSI | EMA stack | MACD | council | conviction |
|---|---:|---:|---|---|---|---:|
| 2026-11-18 | 53.31 | 24.87 | bearish | bearish | flat | 0.000 |
| 2026-11-20 | 47.51 | 21.21 | bearish | bearish | flat | 0.000 |
| 2026-11-23 | 51.34 | 28.80 | bearish | bearish | flat | 0.000 |
| 2026-11-24 | 47.72 | 26.23 | bearish | bearish | flat | 0.000 |
| 2026-11-25 | 48.27 | 27.29 | bearish | bearish | flat | 0.000 |

## 10. Backtesting and validation

Archived-signal scorecard: **insufficient sample**. At a 5-bar horizon, 13 directional report(s) have matured, 0 are pending, and 70 were honest abstentions.
Observed directional hit rate is 53.85% and mean signed forward return is -1.25%.
No performance claim is made until at least 20 directional reports mature. This is prospective validation of archived calls—not a replacement for a cost-aware portfolio backtest with slippage, turnover, and benchmark comparison.
