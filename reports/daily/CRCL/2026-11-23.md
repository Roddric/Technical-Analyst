# Daily Technical Report — Circle Internet Group (CRCL)

- Generated: 2026-11-24T06:13:04.996783+00:00
- Latest daily market bar: 2026-11-23
- Explicit data refresh: successful
- Scope: technical analysis only; latest daily bars are not tick-level real-time quotes.

## 1. Stock overview

Price is **51.34**, versus a 2026-05-27–2026-11-23 range of 47.32–114.44. It is -55.14% from the period high and 8.50% from the period low.

## 2. Trend analysis

- SMA20 / SMA50 / SMA200: 65.93 / 77.61 / 85.75.
- Price position: SMA20 **below**, SMA50 **below**, SMA200 **below**.
- EMA20 / EMA50: 63.69 / 72.89; stack **bearish**.
- Latest SMA50/200 event: death_cross (2026-11-05).

## 3. Momentum

- RSI(14): **28.80** (oversold); divergence **none**.
- MACD / signal / histogram: -8.1191 / -6.5579 / -1.5612.
- MACD state: **bearish**, histogram **contracting**.

## 4. Volatility

- Bollinger lower / mid / upper: 45.40 / 65.93 / 86.46; %B 0.145.
- Squeeze: **False**; volatility **expanding**.
- ATR(14): 5.1068 (9.95% of price); expected daily range 5.11.

## 5. Volume

- OBV trend **falling**, strength **moderate**.
- Price confirmation: **True**; divergence **none**.

## 6. Key levels

- Quick 60-bar support / resistance: 47.32 / 103.28.
- Distance to support / resistance: 7.83% / 101.17%; range reward:risk 12.92.

**Confirmed supports**

- 49.90 (1 touches; last 2026-02-05; -2.80% from price)

**Confirmed resistances**

- 58.84 (6 touches; last 2026-08-03; 14.61% from price)
- 76.11 (14 touches; last 2026-11-04; 48.25% from price)
- 88.22 (13 touches; last 2026-10-21; 71.83% from price)

Dominant swing: **up**, 49.90 (2026-02-05) to 140.00 (2026-05-12). Nearest Fibonacci level is 0.786 at 69.18 (34.75% from price).

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
  "entry": 51.34,
  "stop": 51.34,
  "target": 51.34,
  "long_only_suppressed": false
}
```

## 9. Seven-day report review

Compared with **4** prior report(s) from 2026-11-16 through 2026-11-23, price changed **-10.95%**. RSI ranged from 21.21 to 28.80. Council state changed 0 time(s).

| market date | price | RSI | EMA stack | MACD | council | conviction |
|---|---:|---:|---|---|---|---:|
| 2026-11-16 | 57.65 | 27.88 | bearish | bearish | flat | 0.000 |
| 2026-11-17 | 54.63 | 25.76 | bearish | bearish | flat | 0.000 |
| 2026-11-18 | 53.31 | 24.87 | bearish | bearish | flat | 0.000 |
| 2026-11-20 | 47.51 | 21.21 | bearish | bearish | flat | 0.000 |
| 2026-11-23 | 51.34 | 28.80 | bearish | bearish | flat | 0.000 |

## 10. Backtesting and validation

Archived-signal scorecard: **insufficient sample**. At a 5-bar horizon, 13 directional report(s) have matured, 0 are pending, and 68 were honest abstentions.
Observed directional hit rate is 53.85% and mean signed forward return is -1.25%.
No performance claim is made until at least 20 directional reports mature. This is prospective validation of archived calls—not a replacement for a cost-aware portfolio backtest with slippage, turnover, and benchmark comparison.
