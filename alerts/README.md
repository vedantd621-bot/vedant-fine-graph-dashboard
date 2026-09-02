# FinGraph Alert Engine

The alert engine continuously evaluates incoming graph events and recalculated risk scores against compliance thresholds. It manages alert deduplication, cooldown intervals, and dispatches notices across supported backends.

## Dispatch Modes
- `mock`: Default local mode. Logs structured alerts to stdout and in-memory store for development without credentials.
- `slack`: Sends JSON payload to configured Slack Webhook URL.
- `email`: Sends formatted AML alert email via SMTP.
- `webhook`: Posts alert payload to external compliance webhooks.
