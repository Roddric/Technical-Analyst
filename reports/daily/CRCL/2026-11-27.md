# Daily Technical Report — Circle Internet Group (CRCL)

- Generated: 2026-11-28T04:03:34.043547+00:00
- Latest daily market bar: 2026-11-27
- Explicit data refresh: successful
- Scope: technical analysis only; latest daily bars are not tick-level real-time quotes.

## 1. Stock overview

Price is **49.29**, versus a 2026-06-01–2026-11-27 range of 43.11–109.50. It is -54.99% from the period high and 14.34% from the period low.

## 2. Trend analysis

- SMA20 / SMA50 / SMA200: 61.03 / 75.48 / 85.59.
- Price position: SMA20 **below**, SMA50 **below**, SMA200 **below**.
- EMA20 / EMA50: 59.75 / 70.13; stack **bearish**.
- Latest SMA50/200 event: death_cross (2026-11-05).

## 3. Momentum

- RSI(14): **29.32** (oversold); divergence **none**.
- MACD / signal / histogram: -8.3043 / -7.4399 / -0.8644.
- MACD state: **bearish**, histogram **contracting**.

## 4. Volatility

- Bollinger lower / mid / upper: 41.76 / 61.03 / 80.30; %B 0.195.
- Squeeze: **False**; volatility **expanding**.
- ATR(14): 4.9047 (9.95% of price); expected daily range 4.90.

## 5. Volume

- OBV trend **falling**, strength **moderate**.
- Price confirmation: **True**; divergence **none**.

## 6. Key levels

- Quick 60-bar support / resistance: 43.11 / 103.28.
- Distance to support / resistance: 12.54% / 109.54%; range reward:risk 8.74.

**Confirmed supports**

No confirmed swing-pivot zones on this side.

**Confirmed resistances**

- 49.90 (1 touches; last 2026-02-05; 1.24% from price)
- 55.31 (1 touches; last 2026-02-12; 12.21% from price)
- 59.54 (5 touches; last 2026-08-03; 20.80% from price)

Dominant swing: **up**, 49.90 (2026-02-05) to 140.00 (2026-05-12). Nearest Fibonacci level is 0.786 at 69.18 (40.35% from price).

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
  "entry": 49.29,
  "stop": 49.29,
  "target": 49.29,
  "long_only_suppressed": false
}
```

## 9. Seven-day report review

Compared with **4** prior report(s) from 2026-11-20 through 2026-11-27, price changed **3.75%**. RSI ranged from 21.21 to 29.32. Council state changed 0 time(s).

| market date | price | RSI | EMA stack | MACD | council | conviction |
|---|---:|---:|---|---|---|---:|
| 2026-11-20 | 47.51 | 21.21 | bearish | bearish | flat | 0.000 |
| 2026-11-23 | 51.34 | 28.80 | bearish | bearish | flat | 0.000 |
| 2026-11-24 | 47.72 | 26.23 | bearish | bearish | flat | 0.000 |
| 2026-11-25 | 48.27 | 27.29 | bearish | bearish | flat | 0.000 |
| 2026-11-27 | 49.29 | 29.32 | bearish | bearish | flat | 0.000 |

## 10. Backtesting and validation

Archived-signal scorecard: **insufficient sample**. At a 5-bar horizon, 13 directional report(s) have matured, 0 are pending, and 71 were honest abstentions.
Observed directional hit rate is 53.85% and mean signed forward return is -1.25%.
No performance claim is made until at least 20 directional reports mature. This is prospective validation of archived calls—not a replacement for a cost-aware portfolio backtest with slippage, turnover, and benchmark comparison.
