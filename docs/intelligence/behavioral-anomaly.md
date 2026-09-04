# FinGraph Behavioral Anomaly Detection & Entity Similarity

## 1. Statistical Baseline Profiles
For each entity, FinGraph establishes a rolling 30-day statistical baseline:
- $\mu_{\text{amount}}$, $\sigma_{\text{amount}}$: Historical mean and standard deviation of transaction amounts.
- $\text{Max}_{\text{amount}}$: Historical peak single transaction amount.
- $V_{\text{avg}}$: Average transaction velocity per hour.
- $R_{\text{in}}, R_{\text{out}}$: Directional ratio of incoming vs outgoing volume.
- $N_{\text{counterparties}}$: Unique historical transaction counterparties.

---

## 2. Multi-Window Temporal Deviation Analysis
Configurable sliding temporal analysis windows: `5m`, `1h`, `24h`, `7d`, `30d`.

### Evaluated Anomaly Signals:
1. **VOLUME_SPIKE**: Observed window volume exceeds expected baseline by $>3.0\times$.
2. **VELOCITY_BURST**: Observed transaction frequency exceeds historical hourly rate by $>3.0\times$.
3. **COUNTERPARTY_BURST**: Sudden influx of new counterparties ($>2.5\times$ baseline unique count).
4. **UNUSUAL_OUTGOING_RATIO**: Outgoing volume ratio abruptly surges $>0.85$ when baseline is balanced.
5. **HIGH_VALUE_DEVIATION**: Single transaction amount exceeds historical maximum by $>2.5\times$.

---

## 3. Explainable Suspect Entity Similarity
Calculates mathematical similarity ($0.0 - 1.0$) between a target entity and suspect peers:

$$\text{Similarity}(A, B) = 0.40 \cdot J_{\text{counterparties}}(A, B) + 0.25 \cdot \mathbf{1}_{\text{same community}} + 0.20 \cdot \left(1 - \frac{|R_A - R_B|}{100}\right) + 0.15 \cdot \frac{\min(V_A, V_B)}{\max(V_A, V_B)}$$
