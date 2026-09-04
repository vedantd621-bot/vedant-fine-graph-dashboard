# SLA Compliance & Deadline Engine Guide

## 1. SLA Configuration

| Priority Tier | Target SLA Deadline | At-Risk Threshold |
| :--- | :--- | :--- |
| **`P0_CRITICAL`** | 15 minutes | $< 3.75	ext{ minutes remaining}$ |
| **`P1_HIGH`** | 60 minutes | $< 15	ext{ minutes remaining}$ |
| **`P2_MEDIUM`** | 240 minutes (4 hours) | $< 60	ext{ minutes remaining}$ |
| **`P3_LOW`** | 1440 minutes (24 hours) | $< 360	ext{ minutes remaining}$ |

---

## 2. Lifecycle Statuses

- **`WITHIN_SLA`**: Time remaining $> 25\%$ of configured SLA window.
- **`AT_RISK`**: Time remaining $\le 25\%$ of configured SLA window; highlighted in amber pulse.
- **`BREACHED`**: Deadline exceeded without resolution; highlighted in red pulse and dispatches `SLA_BREACHED` WebSocket events.
- **`RESOLVED`**: Alert transitioned to `CONFIRMED_FRAUD`, `FALSE_POSITIVE`, or `CLOSED`.
