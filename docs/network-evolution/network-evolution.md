# Network Evolution & Velocity Engine

## Overview
The Network Evolution Engine (`backend/app/network_evolution/`) tracks how fraud networks expand and mutate over bounded time windows (`5m`, `1h`, `6h`, `24h`, `7d`, `30d`).

## Formulas
- **Growth Rate**: $\text{Growth} = \frac{\text{NodeCount}_{\text{curr}} - \text{NodeCount}_{\text{prev}}}{\text{NodeCount}_{\text{prev}}} \times 100\%$
- **Velocity**: $V = \frac{\Delta \text{Metric}}{\Delta \text{Hours}}$ (guarded against division by zero with $\Delta \text{Hours} \ge 0.001\text{h}$)
- **Emergence Score**: $\text{Emergence} = 0.35 \cdot \text{Growth} + 0.35 \cdot \text{Risk} + 0.20 \cdot V_{\text{Tx}} + 0.10 \cdot \text{ExposureScore}$
