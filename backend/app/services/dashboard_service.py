"""
FinGraph Dashboard Aggregate Business Service.
Aggregates real-time metrics, risk distribution breakdowns, alert trends, and top risk candidates.
"""
from datetime import datetime, timezone
from typing import Dict, List, Optional

from neo4j.src.client import Neo4jClient
from analytics.src.models import RiskLevel
from backend.app.models.accounts import AccountSummary
from backend.app.models.alerts import AlertSummary
from backend.app.models.dashboard import (
    AlertTrendPoint,
    DashboardSummary,
    RiskDistribution,
)
from backend.app.services.account_service import AccountService
from backend.app.services.alert_service import AlertService


class DashboardService:
    """Service aggregating metrics across Neo4j graph and risk engine."""

    def __init__(
        self,
        client: Neo4jClient,
        account_service: AccountService,
        alert_service: AlertService,
    ):
        self.client = client
        self.account_service = account_service
        self.alert_service = alert_service

    def get_summary(self) -> DashboardSummary:
        """Retrieves core executive KPI metrics from Neo4j."""
        cypher_acc = "MATCH (a:Account) RETURN count(a) AS total_accounts"
        records_acc = self.client.execute_query(cypher_acc)
        acc_cnt = int(records_acc[0].get("total_accounts", 0)) if records_acc else 0

        cypher_tx = """
        MATCH ()-[r:TRANSFERRED_TO]->()
        RETURN
            count(r) AS total_transactions,
            coalesce(sum(r.amount), 0.0) AS total_volume
        """
        records_tx = self.client.execute_query(cypher_tx)
        tx_row = records_tx[0] if records_tx else {}
        total_tx = int(tx_row.get("total_transactions", tx_row.get("total_tx", 0)))
        total_vol = float(tx_row.get("total_volume", tx_row.get("total_vol", 0.0)))

        # Query all accounts to get accurate risk counts
        accounts, _ = self.account_service.list_accounts(page=1, page_size=1000)
        high_risk_count = sum(1 for a in accounts if a.risk_level == RiskLevel.HIGH)
        crit_risk_count = sum(1 for a in accounts if a.risk_level == RiskLevel.CRITICAL)

        # Query alerts
        alerts, _ = self.alert_service.list_alerts(page=1, page_size=1000)
        open_count = sum(1 for a in alerts if getattr(a.status, "value", a.status) == "OPEN")
        inv_count = sum(1 for a in alerts if getattr(a.status, "value", a.status) == "INVESTIGATING")
        res_count = sum(1 for a in alerts if getattr(a.status, "value", a.status) == "RESOLVED")

        return DashboardSummary(
            total_accounts=acc_cnt,
            total_transactions=total_tx,
            open_alerts=open_count,
            investigating_alerts=inv_count,
            resolved_alerts=res_count,
            high_risk_accounts=high_risk_count,
            critical_risk_accounts=crit_risk_count,
            total_transaction_volume=total_vol,
            currency="USD",
            updated_at=datetime.now(timezone.utc),
        )

    def get_risk_distribution(self) -> RiskDistribution:
        """Calculates categorical count distribution across risk levels."""
        accounts, _ = self.account_service.list_accounts(page=1, page_size=1000)

        low = sum(1 for a in accounts if a.risk_level == RiskLevel.LOW)
        medium = sum(1 for a in accounts if a.risk_level == RiskLevel.MEDIUM)
        high = sum(1 for a in accounts if a.risk_level == RiskLevel.HIGH)
        critical = sum(1 for a in accounts if a.risk_level == RiskLevel.CRITICAL)

        return RiskDistribution(
            low=low,
            medium=medium,
            high=high,
            critical=critical,
            total=len(accounts),
        )

    def get_alert_trends(self) -> List[AlertTrendPoint]:
        """Calculates chronological trend of generated alerts."""
        alerts, _ = self.alert_service.list_alerts(page=1, page_size=1000)

        trends_map: Dict[str, Dict[str, Any]] = {}
        for a in alerts:
            bucket_key = a.created_at.strftime("%Y-%m-%d %H:00")
            if bucket_key not in trends_map:
                trends_map[bucket_key] = {"count": 0, "severities": {}}

            trends_map[bucket_key]["count"] += 1
            sev_str = a.severity.value
            trends_map[bucket_key]["severities"][sev_str] = (
                trends_map[bucket_key]["severities"].get(sev_str, 0) + 1
            )

        points: List[AlertTrendPoint] = []
        for k, val in sorted(trends_map.items()):
            points.append(
                AlertTrendPoint(
                    timestamp=k,
                    count=val["count"],
                    severity_breakdown=val["severities"],
                )
            )

        return points

    def get_dashboard_summary(self) -> DashboardSummary:
        """Alias for get_summary."""
        return self.get_summary()

    def get_alert_trend(self) -> List[AlertTrendPoint]:
        """Alias for get_alert_trends."""
        return self.get_alert_trends()

    def get_top_risk_accounts(self, limit: int = 10) -> List[AccountSummary]:
        """Returns top accounts ordered by calculated risk score."""
        accounts, _ = self.account_service.list_accounts(
            page=1,
            page_size=limit,
            sort="risk_score",
            order="desc",
        )
        return accounts
