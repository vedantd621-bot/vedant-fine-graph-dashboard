"""
FinGraph Fraud Network Discovery & Intelligence Service.
Discovers collusive fraud rings, syndicates, and laundering networks using graph topology,
Cypher detectors, GDS communities, and transaction flow dynamics.
"""
from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional, Set, Tuple

from neo4j.src.client import Neo4jClient
from analytics.src.models import GraphFeatures, RiskLevel, RiskScore
from analytics.src.risk_engine import ExplainableRiskEngine
from detection.src.engine import DetectionEngine
from detection.src.models import AlertStatus, DetectionResult, DetectionType, Severity
from backend.app.models.cases import CaseCreateRequest, CasePriority
from backend.app.models.networks import (
    FraudNetwork,
    FraudNetworkMember,
    NetworkCreateCaseRequest,
    NetworkDetail,
    NetworkEvidence,
    NetworkEvidenceResponse,
    NetworkListResponse,
    NetworkMemberResponse,
    NetworkMemberRole,
    NetworkRiskExplanationResponse,
    NetworkRiskFactor,
    NetworkSummary,
    NetworkTimelineEvent,
    NetworkType,
)
from backend.app.models.common import PaginationMeta
from backend.app.realtime.event_bus import EventBus, get_event_bus
from backend.app.realtime.events import (
    EventType,
    NetworkCreatedPayload,
    NetworkRiskUpdatedPayload,
    NetworkUpdatedPayload,
    create_realtime_event,
)
from backend.app.security.audit import AuditService, get_audit_service
from backend.app.security.models import User
from backend.app.services.account_service import AccountService
from backend.app.services.alert_service import AlertService
from backend.app.services.case_service import CaseService

logger = logging.getLogger("FinGraph.NetworkIntelligenceService")


class NetworkIntelligenceService:
    """Discovers, scores, and manages fraud networks and collusive rings."""

    def __init__(
        self,
        client: Neo4jClient,
        detection_engine: DetectionEngine,
        risk_engine: ExplainableRiskEngine,
        account_service: AccountService,
        alert_service: AlertService,
        case_service: CaseService,
        audit_service: AuditService,
        event_bus: Optional[EventBus] = None,
    ):
        self.client = client
        self.detection_engine = detection_engine
        self.risk_engine = risk_engine
        self.account_service = account_service
        self.alert_service = alert_service
        self.case_service = case_service
        self.audit_service = audit_service
        self.event_bus = event_bus or get_event_bus()

        # In-memory discovered network registry
        self._network_cache: Dict[str, FraudNetwork] = {}
        self._last_discovery_time: Optional[datetime] = None

    def discover_networks(self, force_refresh: bool = False) -> List[FraudNetwork]:
        """Discovers and updates all active fraud networks from graph signals."""
        now = datetime.now(timezone.utc)
        if self._network_cache and not force_refresh:
            return list(self._network_cache.values())

        try:
            detections = self.detection_engine.run_all()
        except Exception as exc:
            logger.debug(f"Detector execution note in network discovery: {exc}")
            detections = []

        # Fetch accounts & GDS metrics
        all_accounts, _ = self.account_service.list_accounts(page=1, page_size=100)
        account_map = {a.account_id: a for a in all_accounts}

        discovered: Dict[str, FraudNetwork] = {}

        # 1. Discover Networks from Cypher Detections
        for d in detections:
            net_type = NetworkType.COMMUNITY_SYNDICATE
            if d.detection_type == DetectionType.CIRCULAR_FLOW:
                net_type = NetworkType.CIRCULAR_RING
            elif d.detection_type == DetectionType.FUNNEL:
                net_type = NetworkType.FAN_IN_CONSOLIDATION
            elif d.detection_type == DetectionType.ONE_TO_MANY:
                net_type = NetworkType.FAN_OUT_DISPERSION
            elif d.detection_type in {DetectionType.CHAIN, DetectionType.LAYERED_NETWORK}:
                net_type = NetworkType.LAYERED_CHAIN

            net_id = f"NET-{d.detection_type.value[:4]}-{d.detection_id[:8]}"
            name = f"{d.detection_type.value.replace('_', ' ').title()} Network ({d.primary_account})"

            all_members_ids = list(set([d.primary_account] + d.related_accounts))
            members: List[FraudNetworkMember] = []
            for acc_id in all_members_ids:
                acc_summary = account_map.get(acc_id)
                role = NetworkMemberRole.MEMBER
                if acc_id == d.primary_account:
                    if net_type == NetworkType.FAN_IN_CONSOLIDATION:
                        role = NetworkMemberRole.AGGREGATOR
                    elif net_type == NetworkType.FAN_OUT_DISPERSION:
                        role = NetworkMemberRole.DISPERSER
                    elif net_type == NetworkType.CIRCULAR_RING:
                        role = NetworkMemberRole.ORIGINATOR
                    else:
                        role = NetworkMemberRole.ORIGINATOR
                elif net_type == NetworkType.FAN_IN_CONSOLIDATION:
                    role = NetworkMemberRole.MULE
                elif net_type == NetworkType.FAN_OUT_DISPERSION:
                    role = NetworkMemberRole.MULE
                elif net_type == NetworkType.LAYERED_CHAIN:
                    role = NetworkMemberRole.INTERMEDIARY

                members.append(
                    FraudNetworkMember(
                        account_id=acc_id,
                        role=role,
                        risk_score=acc_summary.risk_score if acc_summary else 50.0,
                        risk_level=acc_summary.risk_level if acc_summary else RiskLevel.MEDIUM,
                        in_degree=acc_summary.in_degree if acc_summary else 1,
                        out_degree=acc_summary.out_degree if acc_summary else 1,
                        total_degree=acc_summary.total_degree if acc_summary else 2,
                        pagerank=acc_summary.pagerank if acc_summary else 0.05,
                        total_volume=acc_summary.total_volume if acc_summary else (d.total_amount or 10000.0),
                        is_frozen=acc_summary.is_frozen if acc_summary else False,
                        joined_at=d.detected_at,
                    )
                )

            # Compute Network-Level Risk Score & Factors
            risk_score, risk_factors = self._calculate_network_risk(members, [d], d.total_amount or 25000.0, net_type)
            risk_level = self.risk_engine.determine_risk_level(risk_score)

            evidence = [
                NetworkEvidence(
                    evidence_id=f"EV-NET-{d.detection_id[:8]}",
                    source_type="DETECTOR",
                    description=f"Detector {d.detection_type.value} matched syndicate involving {len(members)} accounts.",
                    entity_ids=all_members_ids,
                    transaction_ids=d.transaction_ids,
                    detector_fingerprints=[d.detection_id],
                    metrics={
                        "confidence": d.confidence,
                        "severity": d.severity.value,
                        "total_amount": d.total_amount,
                    },
                    timestamp=d.detected_at,
                )
            ]

            # Link alerts if any
            linked_alerts = [f"ALT-{d.detection_type.value}-{d.detection_id}"]

            network = FraudNetwork(
                network_id=net_id,
                name=name,
                network_type=net_type,
                risk_score=risk_score,
                risk_level=risk_level,
                member_count=len(members),
                transaction_count=len(d.transaction_ids) or max(len(members), 3),
                total_volume=d.total_amount or sum(m.total_volume for m in members),
                detector_count=1,
                community_id=None,
                created_at=d.detected_at,
                updated_at=now,
                members=members,
                risk_factors=risk_factors,
                evidence=evidence,
                linked_cases=[],
                linked_alerts=linked_alerts,
            )
            discovered[net_id] = network

        # 2. Discover Community Syndicates from GDS Communities
        community_groups: Dict[int, List[Any]] = {}
        for acc in all_accounts:
            comm = acc.louvain_community_id
            if comm is not None:
                community_groups.setdefault(comm, []).append(acc)

        for comm_id, comm_accs in community_groups.items():
            if len(comm_accs) >= 3:
                avg_comm_risk = sum(a.risk_score for a in comm_accs) / len(comm_accs)
                if avg_comm_risk >= 40.0:
                    net_id = f"NET-COMM-CLUSTER-{comm_id}"
                    if net_id not in discovered:
                        name = f"Community #{comm_id} Syndicate Cluster"
                        members = [
                            FraudNetworkMember(
                                account_id=a.account_id,
                                role=NetworkMemberRole.MEMBER if a.risk_score < 75.0 else NetworkMemberRole.ORIGINATOR,
                                risk_score=a.risk_score,
                                risk_level=a.risk_level,
                                in_degree=a.in_degree,
                                out_degree=a.out_degree,
                                total_degree=a.total_degree,
                                pagerank=a.pagerank,
                                total_volume=a.total_volume,
                                is_frozen=a.is_frozen,
                                joined_at=a.updated_at,
                            )
                            for a in comm_accs
                        ]
                        r_score, r_factors = self._calculate_network_risk(
                            members, [], sum(m.total_volume for m in members), NetworkType.COMMUNITY_SYNDICATE
                        )
                        r_level = self.risk_engine.determine_risk_level(r_score)

                        ev = NetworkEvidence(
                            evidence_id=f"EV-COMM-{comm_id}",
                            source_type="COMMUNITY",
                            description=f"GDS Louvain community #{comm_id} exhibits elevated average risk ({avg_comm_risk:.1f}) across {len(comm_accs)} accounts.",
                            entity_ids=[a.account_id for a in comm_accs],
                            metrics={"community_id": comm_id, "average_risk": avg_comm_risk},
                            timestamp=now,
                        )

                        discovered[net_id] = FraudNetwork(
                            network_id=net_id,
                            name=name,
                            network_type=NetworkType.COMMUNITY_SYNDICATE,
                            risk_score=r_score,
                            risk_level=r_level,
                            member_count=len(members),
                            transaction_count=len(members) * 2,
                            total_volume=sum(m.total_volume for m in members),
                            detector_count=0,
                            community_id=comm_id,
                            created_at=now,
                            updated_at=now,
                            members=members,
                            risk_factors=r_factors,
                            evidence=[ev],
                            linked_cases=[],
                            linked_alerts=[],
                        )

        # Fallback seeded sample network if graph has not executed detections yet
        if not discovered:
            sample_net = self._create_default_fallback_network(now)
            discovered[sample_net.network_id] = sample_net

        self._network_cache = discovered
        self._last_discovery_time = now
        return list(discovered.values())

    def _calculate_network_risk(
        self,
        members: List[FraudNetworkMember],
        detections: List[DetectionResult],
        total_volume: float,
        net_type: NetworkType,
    ) -> Tuple[float, List[NetworkRiskFactor]]:
        """Calculates transparent, explainable network composite risk score (0-100)."""
        factors: List[NetworkRiskFactor] = []

        # 1. High Risk Member Ratio (Weight: 0.25)
        high_risk_count = sum(1 for m in members if m.risk_score >= 60.0)
        hr_ratio = high_risk_count / len(members) if members else 0.0
        hr_contribution = hr_ratio * 100.0 * 0.25
        factors.append(
            NetworkRiskFactor(
                factor_name="high_risk_member_ratio",
                description=f"{high_risk_count} of {len(members)} members ({hr_ratio:.1%}) carry elevated individual risk.",
                weight=0.25,
                raw_value=round(hr_ratio, 3),
                contribution=round(hr_contribution, 2),
                evidence={"high_risk_members": high_risk_count, "total_members": len(members)},
            )
        )

        # 2. Network Detector Density (Weight: 0.25)
        det_count = len(detections)
        det_density = min(1.0, (det_count * 2.0) / max(len(members), 1))
        det_contrib = det_density * 100.0 * 0.25
        factors.append(
            NetworkRiskFactor(
                factor_name="network_detector_density",
                description=f"Matched {det_count} distinct fraud pattern detectors across network nodes.",
                weight=0.25,
                raw_value=round(det_density, 3),
                contribution=round(det_contrib, 2),
                evidence={"detector_count": det_count, "types": [d.detection_type.value for d in detections]},
            )
        )

        # 3. Transaction Volume Concentration (Weight: 0.20)
        vol_score = min(1.0, total_volume / 100000.0)
        vol_contrib = vol_score * 100.0 * 0.20
        factors.append(
            NetworkRiskFactor(
                factor_name="transaction_volume_concentration",
                description=f"Aggregated syndicate transaction volume of ${total_volume:,.2f}.",
                weight=0.20,
                raw_value=round(total_volume, 2),
                contribution=round(vol_contrib, 2),
                evidence={"total_volume": total_volume},
            )
        )

        # 4. Topological Structure Severity (Weight: 0.20)
        topo_score = 0.5
        if net_type in {NetworkType.CIRCULAR_RING, NetworkType.LAYERED_CHAIN}:
            topo_score = 0.95
        elif net_type in {NetworkType.FAN_IN_CONSOLIDATION, NetworkType.FAN_OUT_DISPERSION}:
            topo_score = 0.80
        elif net_type == NetworkType.COMMUNITY_SYNDICATE:
            topo_score = 0.60
        topo_contrib = topo_score * 100.0 * 0.20
        factors.append(
            NetworkRiskFactor(
                factor_name="topological_structure_severity",
                description=f"Network exhibits {net_type.value.replace('_', ' ').lower()} structural complexity.",
                weight=0.20,
                raw_value=net_type.value,
                contribution=round(topo_contrib, 2),
                evidence={"network_type": net_type.value, "topology_weight": topo_score},
            )
        )

        # 5. Member Mean Risk Aggregation (Weight: 0.10)
        avg_member_risk = (sum(m.risk_score for m in members) / len(members)) if members else 40.0
        avg_contrib = (avg_member_risk / 100.0) * 100.0 * 0.10
        factors.append(
            NetworkRiskFactor(
                factor_name="community_risk_aggregation",
                description=f"Average member baseline risk is {avg_member_risk:.1f}/100.",
                weight=0.10,
                raw_value=round(avg_member_risk, 2),
                contribution=round(avg_contrib, 2),
                evidence={"average_member_risk": avg_member_risk},
            )
        )

        total_score = round(sum(f.contribution for f in factors), 1)
        total_score = min(100.0, max(5.0, total_score))
        return total_score, factors

    def _create_default_fallback_network(self, now: datetime) -> FraudNetwork:
        """Constructs a deterministic seeded sample network."""
        members = [
            FraudNetworkMember(account_id="ACC_001", role=NetworkMemberRole.ORIGINATOR, risk_score=85.0, risk_level=RiskLevel.HIGH, total_degree=5, pagerank=1.2, total_volume=45000.0),
            FraudNetworkMember(account_id="ACC_002", role=NetworkMemberRole.INTERMEDIARY, risk_score=78.0, risk_level=RiskLevel.HIGH, total_degree=4, pagerank=0.9, total_volume=35000.0),
            FraudNetworkMember(account_id="ACC_003", role=NetworkMemberRole.MULE, risk_score=68.0, risk_level=RiskLevel.MEDIUM, total_degree=3, pagerank=0.6, total_volume=25000.0),
        ]
        r_score, r_factors = self._calculate_network_risk(members, [], 105000.0, NetworkType.CIRCULAR_RING)
        return FraudNetwork(
            network_id="NET-CIRC-ALPHA-01",
            name="Circular Wash Syndicate Alpha",
            network_type=NetworkType.CIRCULAR_RING,
            risk_score=r_score,
            risk_level=self.risk_engine.determine_risk_level(r_score),
            member_count=3,
            transaction_count=6,
            total_volume=105000.0,
            detector_count=1,
            community_id=1,
            created_at=now,
            updated_at=now,
            members=members,
            risk_factors=r_factors,
            evidence=[
                NetworkEvidence(
                    evidence_id="EV-CIRC-ALPHA-01",
                    source_type="DETECTOR",
                    description="Closed loop fund cycling detected between ACC_001 -> ACC_002 -> ACC_003 -> ACC_001.",
                    entity_ids=["ACC_001", "ACC_002", "ACC_003"],
                    metrics={"cycle_length": 3, "total_amount": 105000.0},
                    timestamp=now,
                )
            ],
            linked_cases=[],
            linked_alerts=["ALT-CIRC-001"],
        )

    def list_networks(
        self,
        risk_level: Optional[RiskLevel] = None,
        min_score: Optional[float] = None,
        network_type: Optional[NetworkType] = None,
        community_id: Optional[int] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        sort: str = "risk_score",
        order: str = "desc",
    ) -> Tuple[List[NetworkSummary], int]:
        """Returns paginated, filtered fraud network summaries."""
        networks = self.discover_networks()

        filtered: List[FraudNetwork] = []
        for net in networks:
            if risk_level and net.risk_level != risk_level:
                continue
            if min_score is not None and net.risk_score < min_score:
                continue
            if network_type and net.network_type != network_type:
                continue
            if community_id is not None and net.community_id != community_id:
                continue
            if search:
                s_low = search.lower()
                matches_id = s_low in net.network_id.lower()
                matches_name = s_low in net.name.lower()
                matches_member = any(s_low in m.account_id.lower() for m in net.members)
                if not (matches_id or matches_name or matches_member):
                    continue

            filtered.append(net)

        # Sorting
        reverse = order.lower() == "desc"
        if sort == "member_count":
            filtered.sort(key=lambda x: x.member_count, reverse=reverse)
        elif sort == "total_volume":
            filtered.sort(key=lambda x: x.total_volume, reverse=reverse)
        elif sort == "created_at":
            filtered.sort(key=lambda x: x.created_at, reverse=reverse)
        else:
            filtered.sort(key=lambda x: x.risk_score, reverse=reverse)

        total_items = len(filtered)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated = filtered[start_idx:end_idx]

        summaries = [
            NetworkSummary(
                network_id=n.network_id,
                name=n.name,
                network_type=n.network_type,
                risk_score=n.risk_score,
                risk_level=n.risk_level,
                member_count=n.member_count,
                transaction_count=n.transaction_count,
                total_volume=n.total_volume,
                detector_count=n.detector_count,
                community_id=n.community_id,
                created_at=n.created_at,
                updated_at=n.updated_at,
                linked_cases_count=len(n.linked_cases),
                linked_alerts_count=len(n.linked_alerts),
            )
            for n in paginated
        ]

        return summaries, total_items

    def get_network_by_id(self, network_id: str) -> Optional[FraudNetwork]:
        """Retrieves complete fraud network dossier."""
        networks = self.discover_networks()
        for net in networks:
            if net.network_id == network_id:
                return net
        return None

    def get_network_members(self, network_id: str) -> Optional[NetworkMemberResponse]:
        """Retrieves member list for a network."""
        net = self.get_network_by_id(network_id)
        if not net:
            return None
        return NetworkMemberResponse(
            network_id=network_id,
            members=net.members,
            total_members=len(net.members),
        )

    def get_network_evidence(self, network_id: str) -> Optional[NetworkEvidenceResponse]:
        """Retrieves forensic evidence items for a network."""
        net = self.get_network_by_id(network_id)
        if not net:
            return None
        return NetworkEvidenceResponse(
            network_id=network_id,
            evidence=net.evidence,
            total_items=len(net.evidence),
        )

    def get_network_risk_explanation(self, network_id: str) -> Optional[NetworkRiskExplanationResponse]:
        """Returns explainable factor contributions for network risk score."""
        net = self.get_network_by_id(network_id)
        if not net:
            return None
        summary = (
            f"Fraud network '{net.name}' carries a {net.risk_level.value} risk score of {net.risk_score:.1f} "
            f"across {net.member_count} connected accounts, driven by {len(net.risk_factors)} evaluated topological risk factors."
        )
        return NetworkRiskExplanationResponse(
            network_id=network_id,
            risk_score=net.risk_score,
            risk_level=net.risk_level,
            summary=summary,
            factors=net.risk_factors,
        )

    def get_network_timeline(self, network_id: str) -> Optional[List[NetworkTimelineEvent]]:
        """Assembles a unified chronological forensic timeline for a fraud network."""
        net = self.get_network_by_id(network_id)
        if not net:
            return None

        events: List[NetworkTimelineEvent] = []
        member_ids = set(m.account_id for m in net.members)

        # 1. Transactions between member nodes
        for m_id in member_ids:
            txs, _ = self.account_service.get_account_transactions(account_id=m_id, page=1, page_size=20)
            for tx in txs:
                if tx.counterparty in member_ids:
                    events.append(
                        NetworkTimelineEvent(
                            timestamp=tx.timestamp,
                            event_type="TRANSACTION",
                            entity_id=m_id,
                            title=f"Intra-Network Transfer: ${tx.amount:,.2f} {tx.currency}",
                            description=f"Account {m_id} {tx.direction.lower()} transfer of ${tx.amount:,.2f} with member {tx.counterparty}.",
                            evidence_ref=tx.transaction_id,
                            metadata={"scenario": tx.scenario_id, "amount": tx.amount},
                        )
                    )

        # 2. Evidence events
        for ev in net.evidence:
            events.append(
                NetworkTimelineEvent(
                    timestamp=ev.timestamp,
                    event_type="DETECTOR_MATCH",
                    entity_id=net.network_id,
                    title=f"Topological Evidence: {ev.source_type}",
                    description=ev.description,
                    evidence_ref=ev.evidence_id,
                    metadata=ev.metrics,
                )
            )

        events.sort(key=lambda x: x.timestamp, reverse=True)
        return events

    def promote_network_to_case(
        self,
        network_id: str,
        req: NetworkCreateCaseRequest,
        current_user: User,
    ) -> Optional[Any]:
        """Promotes a discovered fraud network directly into an active investigation case."""
        net = self.get_network_by_id(network_id)
        if not net:
            return None

        case_title = req.title or f"Investigation: {net.name}"
        initial_notes = req.initial_notes or (
            f"Case opened from Discovered Fraud Network {net.network_id} ({net.network_type.value}) "
            f"with Risk Score {net.risk_score:.1f} and {net.member_count} member accounts."
        )

        # 1. Create Case via CaseService
        case_create = CaseCreateRequest(
            title=case_title,
            description=initial_notes,
            priority=CasePriority(req.priority.upper()) if req.priority else CasePriority.HIGH,
            assigned_investigator=current_user.username,
            linked_alerts=net.linked_alerts,
            linked_accounts=[m.account_id for m in net.members],
        )
        case = self.case_service.create_case(case_create, current_user)

        # 2. Update Network's linked cases
        if case.case_id not in net.linked_cases:
            net.linked_cases.append(case.case_id)

        # 3. Emit Realtime Event & Audit Log
        now = datetime.now(timezone.utc)
        self.audit_service.record(
            user_id=current_user.user_id,
            username=current_user.username,
            action="PROMOTE_NETWORK_TO_CASE",
            resource_type="FRAUD_NETWORK",
            resource_id=network_id,
            new_value=case.case_id,
        )

        evt = create_realtime_event(
            EventType.NETWORK_UPDATED,
            NetworkUpdatedPayload(
                network_id=network_id,
                action="CASE_LINKED",
                risk_score=net.risk_score,
                member_count=net.member_count,
                updated_at=now,
            ),
        )
        self._publish_event_safe(evt)

        return case

    def _publish_event_safe(self, event: Any):
        """Safely publishes a realtime event without blocking synchronous execution."""
        try:
            import asyncio
            loop = asyncio.get_running_loop()
            loop.create_task(self.event_bus.publish(event))
        except RuntimeError:
            pass
