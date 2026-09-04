# Forensic Evidence Provenance

## Overview
Evidence Provenance (`backend/app/case_intelligence/evidence_graph.py`) establishes clear, transparent audit links between raw graph anomalies, alerts, cases, and forensic decisions.

## Relationship Types
- **SUPPORTS**: Evidence directly corroborates the fraud hypothesis.
- **CONTRADICTS**: Evidence indicates benign or non-fraudulent commercial activity.
- **DERIVED_FROM**: Evidence produced as a mathematical derivative of graph algorithms (GDS, Cypher paths).
- **RELATED_TO**: Contextual association without direct polarity.
