# Architecture — Phase 16: Advanced Fraud Graph Intelligence, Predictive Risk & Network Evolution

## 1. Executive Overview

FinGraph Phase 16 transforms the platform from retrospective case investigation into a **predictive, evolving fraud graph intelligence system**.

```
                    ┌──────────────────────────────┐
                    │ Advanced Graph Intelligence  │
                    └──────────────┬───────────────┘
                                   ↓
             ┌─────────────────────┼─────────────────────┐
             ↓                     ↓                     ↓
      Network Evolution      Predictive Risk       Pattern Discovery
             ↓                     ↓                     ↓
      Entity Risk Changes    Risk Forecasting      Emerging Threats
             └─────────────────────┼─────────────────────┘
                                   ↓
                         Fraud Early Warning
                                   ↓
                         Command Center V2
```

---

## 2. Core Pillars

### A. Network Evolution & Velocity Engine (`backend/app/network_evolution/`)
- Evaluates temporal diffs over bounded windows (`5m`, `1h`, `6h`, `24h`, `7d`, `30d`).
- Calculates activity velocity per hour:
  $$V_{\text{Tx}} = \frac{\Delta \text{Transactions}}{\Delta \text{Hours}}, \quad V_{\text{Exposure}} = \frac{\Delta \text{Exposure}}{\Delta \text{Hours}}, \quad V_{\text{Risk}} = \frac{\Delta \text{Risk}}{\Delta \text{Hours}}$$
- Classifies deterministic risk momentum trajectory:
  - $\Delta \text{Risk} \le -10 \implies \text{DECREASING}$
  - $-10 < \Delta \text{Risk} < 10 \implies \text{STABLE}$
  - $10 \le \Delta \text{Risk} < 25 \implies \text{INCREASING}$
  - $\Delta \text{Risk} \ge 25 \implies \text{RAPIDLY\_INCREASING}$

### B. Predictive Risk Forecasting
- Time-series risk projections across $1\text{h}$, $6\text{h}$, $24\text{h}$, and $7\text{d}$:
  $$\text{Forecast}(h) = \min\left(100.0, \max\left(0.0, \text{CurrentRisk} + V_{\text{Risk}} \cdot h \cdot \frac{1}{1 + 0.04 \cdot h}\right)\right)$$
- If historical observations are $<2$, returns `INSUFFICIENT_HISTORY` without fabricating data.

### C. Proactive Early Warning Engine (`backend/app/early_warning/`)
- Triggers non-destructive warnings across 5 proactive criteria (rapid growth, monetary surge, mule funnel clustering, statistical anomaly deviation, detector convergence).
- Warning state machine (`ACTIVE` $\to$ `ACKNOWLEDGED` $\to$ `ESCALATED` or `DISMISSED`) with full audit trail.

### D. Pattern Discovery & Structural Similarity (`backend/app/pattern_discovery/`)
- Extracts recurring topological motifs (`CIRCULAR_LOOP`, `MULTI_INFLOW_FUNNEL`, `RAPID_DISPERSION`, `BURST_ACTIVITY`, `LAYERED_CHAIN`).
- Deterministic similarity:
  $$\text{Sim}(P_1, P_2) = 0.40 \cdot \text{Jaccard}(E_1, E_2) + 0.35 \cdot \text{Jaccard}(S_1, S_2) + 0.25 \cdot \left(1 - \frac{|\Delta \text{Risk}|}{100}\right)$$

### E. Enterprise Threat Level Scoring
- Explainable composite index ($0–100$):
  $$\text{ThreatScore} = 0.25 \cdot \text{NetworkRisk} + 0.20 \cdot \text{ExposureScore} + 0.20 \cdot \text{AlertSeverity} + 0.15 \cdot \text{EarlyWarnings} + 0.10 \cdot \text{ActiveCampaigns} + 0.10 \cdot \text{SLABreaches}$$
- Classifications: `NORMAL` (0-20), `ELEVATED` (21-40), `HIGH` (41-60), `SEVERE` (61-80), `CRITICAL` (81-100).
