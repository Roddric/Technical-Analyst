# Daily Technical Report — Circle Internet Group (CRCL)

- Generated: 2026-11-20T03:37:38.886271+00:00
- Latest daily market bar: 2026-11-18
- Explicit data refresh: successful
- Scope: technical analysis only; latest daily bars are not tick-level real-time quotes.

## 1. Stock overview

Price is **53.31**, versus a 2026-05-21–2026-11-18 range of 52.78–118.85. It is -55.15% from the period high and 1.00% from the period low.

## 2. Trend analysis

- SMA20 / SMA50 / SMA200: 71.01 / 80.17 / 85.81.
- Price position: SMA20 **below**, SMA50 **below**, SMA200 **below**.
- EMA20 / EMA50: 68.41 / 75.78; stack **bearish**.
- Latest SMA50/200 event: death_cross (2026-11-05).

## 3. Momentum

- RSI(14): **24.87** (oversold); divergence **none**.
- MACD / signal / histogram: -7.0093 / -5.2626 / -1.7467.
- MACD state: **bearish**, histogram **expanding**.

## 4. Volatility

- Bollinger lower / mid / upper: 51.71 / 71.01 / 90.31; %B 0.041.
- Squeeze: **False**; volatility **expanding**.
- ATR(14): 4.8965 (9.18% of price); expected daily range 4.90.

## 5. Volume

- OBV trend **falling**, strength **moderate**.
- Price confirmation: **True**; divergence **none**.

## 6. Key levels

- Quick 60-bar support / resistance: 52.78 / 103.28.
- Distance to support / resistance: 0.99% / 93.73%; range reward:risk 94.28.

**Confirmed supports**

- 49.90 (1 touches; last 2026-02-05; -6.40% from price)

**Confirmed resistances**

- 55.31 (1 touches; last 2026-02-12; 3.75% from price)
- 59.54 (5 touches; last 2026-08-03; 11.69% from price)
- 76.11 (14 touches; last 2026-11-04; 42.77% from price)

Dominant swing: **up**, 49.90 (2026-02-05) to 140.00 (2026-05-12). Nearest Fibonacci level is 0.786 at 69.18 (29.77% from price).

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
  "entry": 53.31,
  "stop": 53.31,
  "target": 53.31,
  "long_only_suppressed": false
}
```

## 9. Seven-day report review

Compared with **5** prior report(s) from 2026-11-11 through 2026-11-18, price changed **-20.58%**. RSI ranged from 24.87 to 35.97. Council state changed 0 time(s).

| market date | price | RSI | EMA stack | MACD | council | conviction |
|---|---:|---:|---|---|---|---:|
| 2026-11-11 | 67.12 | 35.97 | bearish | bearish | flat | 0.000 |
| 2026-11-12 | 63.82 | 32.92 | bearish | bearish | flat | 0.000 |
| 2026-11-13 | 62.20 | 31.50 | bearish | bearish | flat | 0.000 |
| 2026-11-16 | 57.65 | 27.88 | bearish | bearish | flat | 0.000 |
| 2026-11-17 | 54.63 | 25.76 | bearish | bearish | flat | 0.000 |
| 2026-11-18 | 53.31 | 24.87 | bearish | bearish | flat | 0.000 |

## 10. Backtesting and validation

Archived-signal scorecard: **insufficient sample**. At a 5-bar horizon, 13 directional report(s) have matured, 0 are pending, and 66 were honest abstentions.
Observed directional hit rate is 53.85% and mean signed forward return is -1.25%.
No performance claim is made until at least 20 directional reports mature. This is prospective validation of archived calls—not a replacement for a cost-aware portfolio backtest with slippage, turnover, and benchmark comparison.
