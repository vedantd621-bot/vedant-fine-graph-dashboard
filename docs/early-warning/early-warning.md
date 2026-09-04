# Proactive Early Warning System

## Overview
The Early Warning Engine (`backend/app/early_warning/`) flags nascent fraud patterns before severe monetary exposure occurs.

## Rule Definitions
1. **Network Growth Surge**: Graph node/edge growth $\ge 25\%$ and risk score $\ge 75$.
2. **Exposure Spike**: Network financial exposure $\ge \$100,000$.
3. **Mule Funnel Convergence**: Account risk $\ge 80$ and statistical anomaly deviation score $\ge 70$.

## Action Recommendations
All recommendations are strictly non-destructive:
- `REVIEW_NETWORK`
- `REVIEW_ACCOUNT`
- `ESCALATE_CASE`
- `MONITOR_ACTIVITY`
- `INVESTIGATE_COUNTERPARTIES`
- `REVIEW_TRANSACTION_FLOW`
