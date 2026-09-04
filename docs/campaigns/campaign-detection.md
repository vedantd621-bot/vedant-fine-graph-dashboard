# Fraud Campaign Discovery & 6-Factor Risk Scoring

## Overview
The Campaign Engine (`backend/app/case_intelligence/campaigns.py`) groups strongly correlated cases into enterprise-wide fraud campaigns.

## 6-Factor Mathematical Formulation
$$\text{Risk} = 0.25 \cdot S_{\text{Network}} + 0.20 \cdot S_{\text{Correlation}} + 0.20 \cdot S_{\text{Exposure}} + 0.15 \cdot S_{\text{Behavior}} + 0.10 \cdot S_{\text{Temporal}} + 0.10 \cdot S_{\text{Evidence}}$$

| Factor | Weight | Evaluation Method |
| :--- | :--- | :--- |
| **Network Strength** | 25% | Baseline topological hazard score of connected graph components |
| **Case Correlation** | 20% | Mean signal strength across all cross-case correlations |
| **Financial Exposure** | 20% | Scaled logarithmic/linear financial impact ($100k+ = 100) |
| **Behavioral Similarity** | 15% | High-velocity multi-case baseline deviation detection |
| **Temporal Concentration**| 10% | Cluster density across time windows |
| **Evidence Strength** | 10% | Count of verified cryptographic SHA-256 evidence items |
