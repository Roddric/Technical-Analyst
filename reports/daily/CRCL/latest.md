# Daily Technical Report — Circle Internet Group (CRCL)

- Generated: 2026-11-12T03:12:20.364727+00:00
- Latest daily market bar: 2026-11-11
- Explicit data refresh: successful
- Scope: technical analysis only; latest daily bars are not tick-level real-time quotes.

## 1. Stock overview

Price is **67.12**, versus a 2026-05-14–2026-11-11 range of 57.84–132.44. It is -49.32% from the period high and 16.04% from the period low.

## 2. Trend analysis

- SMA20 / SMA50 / SMA200: 77.74 / 84.00 / 85.94.
- Price position: SMA20 **below**, SMA50 **below**, SMA200 **below**.
- EMA20 / EMA50: 75.33 / 79.70; stack **bearish**.
- Latest SMA50/200 event: death_cross (2026-11-05).

## 3. Momentum

- RSI(14): **35.97** (neutral); divergence **none**.
- MACD / signal / histogram: -4.6936 / -3.3846 / -1.3090.
- MACD state: **bearish**, histogram **contracting**.

## 4. Volatility

- Bollinger lower / mid / upper: 62.73 / 77.74 / 92.75; %B 0.146.
- Squeeze: **False**; volatility **expanding**.
- ATR(14): 5.3285 (7.94% of price); expected daily range 5.33.

## 5. Volume

- OBV trend **falling**, strength **moderate**.
- Price confirmation: **True**; divergence **none**.

## 6. Key levels

- Quick 60-bar support / resistance: 63.56 / 103.28.
- Distance to support / resistance: 5.30% / 53.87%; range reward:risk 10.16.

**Confirmed supports**

- 64.92 (1 touches; last 2025-11-20; -3.28% from price)
- 58.84 (6 touches; last 2026-08-03; -12.34% from price)
- 49.90 (1 touches; last 2026-02-05; -25.66% from price)

**Confirmed resistances**

- 76.11 (14 touches; last 2026-11-04; 13.39% from price)
- 88.22 (13 touches; last 2026-10-21; 31.44% from price)
- 101.32 (8 touches; last 2026-09-21; 50.95% from price)

Dominant swing: **up**, 49.90 (2026-02-05) to 140.00 (2026-05-12). Nearest Fibonacci level is 0.786 at 69.18 (3.07% from price).

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
  "entry": 67.12,
  "stop": 67.12,
  "target": 67.12,
  "long_only_suppressed": false
}
```

## 9. Seven-day report review

Compared with **5** prior report(s) from 2026-11-04 through 2026-11-11, price changed **-11.82%**. RSI ranged from 32.18 to 42.67. Council state changed 0 time(s).

| market date | price | RSI | EMA stack | MACD | council | conviction |
|---|---:|---:|---|---|---|---:|
| 2026-11-04 | 76.12 | 42.67 | bearish | bearish | flat | 0.000 |
| 2026-11-05 | 69.48 | 36.13 | bearish | bearish | flat | 0.000 |
| 2026-11-06 | 67.88 | 34.75 | bearish | bearish | flat | 0.000 |
| 2026-11-09 | 67.56 | 34.46 | bearish | bearish | flat | 0.000 |
| 2026-11-10 | 64.98 | 32.18 | bearish | bearish | flat | 0.000 |
| 2026-11-11 | 67.12 | 35.97 | bearish | bearish | flat | 0.000 |

## 10. Backtesting and validation

Archived-signal scorecard: **insufficient sample**. At a 5-bar horizon, 13 directional report(s) have matured, 0 are pending, and 61 were honest abstentions.
Observed directional hit rate is 53.85% and mean signed forward return is -1.25%.
No performance claim is made until at least 20 directional reports mature. This is prospective validation of archived calls—not a replacement for a cost-aware portfolio backtest with slippage, turnover, and benchmark comparison.
