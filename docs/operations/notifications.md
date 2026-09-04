# In-App Notification Center Guide

## 1. Notification Classifications

- `CRITICAL_ALERT`: High-risk P0 syndicates flagged by streaming pipeline.
- `SLA_WARNING`: Active alert entering the `AT_RISK` window.
- `SLA_BREACH`: Active alert breaching SLA resolution deadline.
- `ALERT_ASSIGNED`: Alert assigned to current investigator.
- `ALERT_REASSIGNED`: Alert transferred to new investigator.
- `CASE_ESCALATED`: Investigation case elevated to management review.
- `NETWORK_DISCOVERY`: Newly discovered laundering ring or mule community.

---

## 2. Real-Time Delivery

Notifications are broadcast instantly over WebSocket connections and stored in the in-app notification repository for offline viewing, role-based filtering, and read tracking.
