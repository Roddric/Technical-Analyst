# Daily Technical Report — Circle Internet Group (CRCL)

- Generated: 2026-11-10T04:14:13.652036+00:00
- Latest daily market bar: 2026-11-09
- Explicit data refresh: successful
- Scope: technical analysis only; latest daily bars are not tick-level real-time quotes.

## 1. Stock overview

Price is **67.56**, versus a 2026-05-12–2026-11-09 range of 57.84–140.00. It is -51.74% from the period high and 16.80% from the period low.

## 2. Trend analysis

- SMA20 / SMA50 / SMA200: 79.32 / 85.05 / 85.99.
- Price position: SMA20 **below**, SMA50 **below**, SMA200 **below**.
- EMA20 / EMA50: 77.37 / 80.84; stack **bearish**.
- Latest SMA50/200 event: death_cross (2026-11-05).

## 3. Momentum

- RSI(14): **34.46** (neutral); divergence **none**.
- MACD / signal / histogram: -4.0881 / -2.6836 / -1.4045.
- MACD state: **bearish**, histogram **expanding**.

## 4. Volatility

- Bollinger lower / mid / upper: 66.32 / 79.32 / 92.33; %B 0.048.
- Squeeze: **False**; volatility **expanding**.
- ATR(14): 5.5450 (8.21% of price); expected daily range 5.54.

## 5. Volume

- OBV trend **falling**, strength **moderate**.
- Price confirmation: **True**; divergence **none**.

## 6. Key levels

- Quick 60-bar support / resistance: 64.81 / 103.28.
- Distance to support / resistance: 4.07% / 52.87%; range reward:risk 13.00.

**Confirmed supports**

- 64.92 (1 touches; last 2025-11-20; -3.91% from price)
- 58.84 (6 touches; last 2026-08-03; -12.91% from price)
- 49.90 (1 touches; last 2026-02-05; -26.14% from price)

**Confirmed resistances**

- 76.11 (14 touches; last 2026-11-04; 12.66% from price)
- 88.22 (13 touches; last 2026-10-21; 30.58% from price)
- 101.32 (8 touches; last 2026-09-21; 49.97% from price)

Dominant swing: **up**, 49.90 (2026-02-05) to 140.00 (2026-05-12). Nearest Fibonacci level is 0.786 at 69.18 (2.40% from price).

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
  "entry": 67.56,
  "stop": 67.56,
  "target": 67.56,
  "long_only_suppressed": false
}
```

## 9. Seven-day report review

Compared with **5** prior report(s) from 2026-11-02 through 2026-11-09, price changed **-6.27%**. RSI ranged from 34.46 to 42.67. Council state changed 0 time(s).

| market date | price | RSI | EMA stack | MACD | council | conviction |
|---|---:|---:|---|---|---|---:|
| 2026-11-02 | 72.08 | 36.54 | bearish | bearish | flat | 0.000 |
| 2026-11-03 | 75.22 | 41.34 | bearish | bearish | flat | 0.000 |
| 2026-11-04 | 76.12 | 42.67 | bearish | bearish | flat | 0.000 |
| 2026-11-05 | 69.48 | 36.13 | bearish | bearish | flat | 0.000 |
| 2026-11-06 | 67.88 | 34.75 | bearish | bearish | flat | 0.000 |
| 2026-11-09 | 67.56 | 34.46 | bearish | bearish | flat | 0.000 |

## 10. Backtesting and validation

Archived-signal scorecard: **insufficient sample**. At a 5-bar horizon, 13 directional report(s) have matured, 0 are pending, and 59 were honest abstentions.
Observed directional hit rate is 53.85% and mean signed forward return is -1.25%.
No performance claim is made until at least 20 directional reports mature. This is prospective validation of archived calls—not a replacement for a cost-aware portfolio backtest with slippage, turnover, and benchmark comparison.
