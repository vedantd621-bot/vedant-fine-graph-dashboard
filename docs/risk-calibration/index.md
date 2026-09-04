# Empirical Risk Score Outcome Calibration

## Overview
Calibrates continuous 0–100 entity risk scores against actual investigation verdicts across 5 deterministic buckets.

## Outcome Buckets
* **0–20 (Very Low Risk)**: Expected confirmation rate < 5%, high false positive rate.
* **21–40 (Low Risk)**: Low yield for manual review.
* **41–60 (Medium Risk)**: Balanced operational yield.
* **61–80 (High Risk)**: Target tier for proactive queue prioritization (>70% confirmation rate).
* **81–100 (Critical Risk)**: Fast-track auto-escalation (>90% confirmation rate).
