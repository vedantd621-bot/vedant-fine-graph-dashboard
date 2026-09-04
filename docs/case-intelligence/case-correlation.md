# Cross-Case Correlation Engine

## Overview
The Cross-Case Correlation Engine (`backend/app/case_intelligence/correlation.py`) provides deterministic cross-case intelligence by identifying shared entities, flow topologies, and temporal proximity.

## Signal Classifications
1. **SHARED_ACCOUNT**: Identifies cases referencing the same internal bank accounts.
2. **FINANCIAL_FLOW**: Identifies cases sharing direct transaction flows and counterparties.
3. **SHARED_DETECTOR**: Identifies cases triggered by identical topological fraud patterns (e.g. Circular, Funnel).
4. **TEMPORAL_CLUSTERING**: Identifies cases opened within 48 hours sharing secondary connections.

## Signal Strength & Confidence Formulation
$$\text{Strength}_{\text{Account}} = \min\left(1.0, 0.40 + 0.60 \cdot \frac{|A_1 \cap A_2|}{\min(|A_1|, |A_2|)}\right)$$
