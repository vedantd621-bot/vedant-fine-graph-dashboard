# Recurring Pattern Discovery & Structural Similarity

## Overview
The Pattern Discovery Engine (`backend/app/pattern_discovery/`) identifies and catalogs recurring fraud motifs across graph structures and campaigns.

## Similarity Formula
$$\text{Sim}(P_1, P_2) = 0.40 \cdot \frac{|E_1 \cap E_2|}{|E_1 \cup E_2|} + 0.35 \cdot \frac{|S_1 \cap S_2|}{|S_1 \cup S_2|} + 0.25 \cdot \left(1.0 - \frac{|\text{Risk}_1 - \text{Risk}_2|}{100.0}\right)$$
