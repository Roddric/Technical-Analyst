# Daily Technical Report — Circle Internet Group (CRCL)

- Generated: 2026-11-21T03:19:27.223027+00:00
- Latest daily market bar: 2026-11-20
- Explicit data refresh: successful
- Scope: technical analysis only; latest daily bars are not tick-level real-time quotes.

## 1. Stock overview

Price is **47.51**, versus a 2026-05-26–2026-11-20 range of 47.32–114.44. It is -58.48% from the period high and 0.40% from the period low.

## 2. Trend analysis

- SMA20 / SMA50 / SMA200: 67.36 / 78.54 / 85.78.
- Price position: SMA20 **below**, SMA50 **below**, SMA200 **below**.
- EMA20 / EMA50: 64.99 / 73.77; stack **bearish**.
- Latest SMA50/200 event: death_cross (2026-11-05).

## 3. Momentum

- RSI(14): **21.21** (oversold); divergence **none**.
- MACD / signal / histogram: -8.0442 / -6.1676 / -1.8766.
- MACD state: **bearish**, histogram **expanding**.

## 4. Volatility

- Bollinger lower / mid / upper: 47.12 / 67.36 / 87.59; %B 0.010.
- Squeeze: **False**; volatility **expanding**.
- ATR(14): 4.9311 (10.38% of price); expected daily range 4.93.

## 5. Volume

- OBV trend **falling**, strength **moderate**.
- Price confirmation: **True**; divergence **none**.

## 6. Key levels

- Quick 60-bar support / resistance: 47.32 / 103.28.
- Distance to support / resistance: 0.40% / 117.39%; range reward:risk 293.53.

**Confirmed supports**

No confirmed swing-pivot zones on this side.

**Confirmed resistances**

- 49.90 (1 touches; last 2026-02-05; 5.03% from price)
- 55.31 (1 touches; last 2026-02-12; 16.42% from price)
- 59.54 (5 touches; last 2026-08-03; 25.32% from price)

Dominant swing: **up**, 49.90 (2026-02-05) to 140.00 (2026-05-12). Nearest Fibonacci level is 0.786 at 69.18 (45.61% from price).

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
  "entry": 47.51,
  "stop": 47.51,
  "target": 47.51,
  "long_only_suppressed": false
}
```

## 9. Seven-day report review

Compared with **4** prior report(s) from 2026-11-13 through 2026-11-20, price changed **-23.62%**. RSI ranged from 21.21 to 31.50. Council state changed 0 time(s).

| market date | price | RSI | EMA stack | MACD | council | conviction |
|---|---:|---:|---|---|---|---:|
| 2026-11-13 | 62.20 | 31.50 | bearish | bearish | flat | 0.000 |
| 2026-11-16 | 57.65 | 27.88 | bearish | bearish | flat | 0.000 |
| 2026-11-17 | 54.63 | 25.76 | bearish | bearish | flat | 0.000 |
| 2026-11-18 | 53.31 | 24.87 | bearish | bearish | flat | 0.000 |
| 2026-11-20 | 47.51 | 21.21 | bearish | bearish | flat | 0.000 |

## 10. Backtesting and validation

Archived-signal scorecard: **insufficient sample**. At a 5-bar horizon, 13 directional report(s) have matured, 0 are pending, and 67 were honest abstentions.
Observed directional hit rate is 53.85% and mean signed forward return is -1.25%.
No performance claim is made until at least 20 directional reports mature. This is prospective validation of archived calls—not a replacement for a cost-aware portfolio backtest with slippage, turnover, and benchmark comparison.
