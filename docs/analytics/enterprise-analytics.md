# FinGraph Enterprise Analytics Engine & Posture Analysis

---

## 1. Multi-Tenant KPI Sets

The Enterprise Analytics Engine evaluates 5 distinct operational KPI dimensions:

1. **Fraud KPIs**:
   * `fraud_rate`: Proportion of transactions flagged as fraudulent ($0.0–1.0$).
   * `confirmed_fraud`: Cases confirmed as true fraud by human investigators.
   * `false_positives`: Intercepted transactions cleared after review.
   * `blocked_transactions`: Proactively blocked transactions.
   * `escalations`: Incidents escalated to senior squads.
2. **Financial KPIs**:
   * `suspicious_volume`: Total financial volume flagged by detectors.
   * `confirmed_fraud_exposure`: Verified exposure on confirmed fraud accounts.
   * `prevented_loss`: Value preserved through proactive freezing and blocking.
   * `estimated_loss`: Unrecoverable capital losses.
   * `average_case_exposure`: Mean exposure per active investigation.
3. **Operations KPIs**:
   * `open_cases`: Currently active investigation cases.
   * `investigation_backlog`: Cases pending assignment or evidence review.
   * `avg_investigation_hours` & `median_investigation_hours`: Turnaround metrics.
   * `sla_compliance_rate`: Percentage of cases triaged within target SLA window.
   * `queue_depth`: Total alerts awaiting investigator triage.
4. **Detection KPIs**:
   * `precision_proxy`: Confirmed detections divided by total closed detections.
   * `false_positive_rate`: Normal behavior incorrectly flagged.
   * `detector_drift`: Trajectory change in detector firing frequency.
5. **Network KPIs**:
   * `active_fraud_networks`: Number of active Louvain/WCC collusive clusters.
   * `emerging_networks`: Newly identified rings formed within last 72 hours.
   * `campaign_count`: Multi-case coordinated syndicates.

---

## 2. 0–100 Executive Fraud Posture Index

The composite posture score evaluates organizational security posture:

$$\text{PostureScore} = w_{\text{threat}} T + w_{\text{exp}} E + w_{\text{backlog}} B + w_{\text{drift}} D$$

Positive and negative drivers are attributed deterministically to provide non-technical, explainable executive summaries.
