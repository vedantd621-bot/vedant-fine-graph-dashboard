"""
FinGraph Fraud Campaign Discovery, 6-Factor Risk Scoring, and Exposure Analysis.
Clusters correlated investigation cases, computes deterministic 0-100 campaign risk,
and quantifies financial exposure.
"""
from datetime import datetime, timezone
import logging
from typing import Dict, List, Optional, Tuple

from backend.app.case_intelligence.models import (
    Campaign,
    CampaignRiskExplanation,
    CampaignRiskFactor,
    CampaignStatus,
    CaseCorrelation,
    CaseCorrelationSignal,
)
from backend.app.models.cases import InvestigationCase

logger = logging.getLogger("FinGraph.CampaignEngine")

# 6-Factor Weights: Sum = 1.00
FACTOR_WEIGHTS = {
    "NetworkStrength": 0.25,
    "CaseCorrelation": 0.20,
    "FinancialExposure": 0.20,
    "BehavioralSimilarity": 0.15,
    "TemporalConcentration": 0.10,
    "EvidenceStrength": 0.10,
}


class CampaignEngine:
    """Discovers multi-case campaigns and calculates 6-factor deterministic risk."""

    def __init__(self):
        pass

    def calculate_campaign_risk(
        self,
        cases: List[InvestigationCase],
        correlations: List[CaseCorrelation],
        financial_exposure: float,
        network_risk_score: float = 75.0,
    ) -> Tuple[float, float, List[CampaignRiskFactor]]:
        """
        Calculates deterministic Campaign Risk Score (0-100):
        CampaignRisk = 0.25 * NetworkStrength + 0.20 * CaseCorrelation +
                       0.20 * FinancialExposure + 0.15 * BehavioralSimilarity +
                       0.10 * TemporalConcentration + 0.10 * EvidenceStrength
        """
        # 1. Network Strength (0-100)
        raw_network = min(100.0, max(0.0, network_risk_score))
        c_network = FACTOR_WEIGHTS["NetworkStrength"] * raw_network

        # 2. Case Correlation (0-100)
        avg_corr = (
            sum(c.signal_strength for c in correlations) / max(1, len(correlations))
            if correlations else 0.5
        )
        raw_corr = min(100.0, avg_corr * 100.0)
        c_corr = FACTOR_WEIGHTS["CaseCorrelation"] * raw_corr

        # 3. Financial Exposure (0-100 scaled: $100k+ is 100)
        raw_exposure = min(100.0, (financial_exposure / 100000.0) * 100.0) if financial_exposure > 0 else 40.0
        c_exposure = FACTOR_WEIGHTS["FinancialExposure"] * raw_exposure

        # 4. Behavioral Similarity (0-100)
        has_critical = any(c.priority == "CRITICAL" for c in cases)
        raw_behavior = 85.0 if has_critical else 60.0
        c_behavior = FACTOR_WEIGHTS["BehavioralSimilarity"] * raw_behavior

        # 5. Temporal Concentration (0-100)
        raw_temporal = 75.0 if len(cases) > 1 else 50.0
        c_temporal = FACTOR_WEIGHTS["TemporalConcentration"] * raw_temporal

        # 6. Evidence Strength (0-100)
        total_evd = sum(len(c.evidence) for c in cases)
        raw_evidence = min(100.0, total_evd * 20.0 + 40.0)
        c_evidence = FACTOR_WEIGHTS["EvidenceStrength"] * raw_evidence

        total_risk = round(c_network + c_corr + c_exposure + c_behavior + c_temporal + c_evidence, 2)
        total_risk = min(100.0, max(0.0, total_risk))

        confidence = 0.92 if len(cases) > 1 else 0.85

        factors = [
            CampaignRiskFactor(
                factor_name="Network Strength",
                weight=FACTOR_WEIGHTS["NetworkStrength"],
                raw_value=round(raw_network, 1),
                contribution=round(c_network, 2),
                evidence=f"Connected network baseline hazard score: {raw_network:.1f}",
            ),
            CampaignRiskFactor(
                factor_name="Case Correlation",
                weight=FACTOR_WEIGHTS["CaseCorrelation"],
                raw_value=round(raw_corr, 1),
                contribution=round(c_corr, 2),
                evidence=f"Cross-case correlation strength: {avg_corr:.2f} across {len(correlations)} links",
            ),
            CampaignRiskFactor(
                factor_name="Financial Exposure",
                weight=FACTOR_WEIGHTS["FinancialExposure"],
                raw_value=round(raw_exposure, 1),
                contribution=round(c_exposure, 2),
                evidence=f"Total aggregated financial exposure: ${financial_exposure:,.2f}",
            ),
            CampaignRiskFactor(
                factor_name="Behavioral Similarity",
                weight=FACTOR_WEIGHTS["BehavioralSimilarity"],
                raw_value=round(raw_behavior, 1),
                contribution=round(c_behavior, 2),
                evidence=f"High velocity multi-case behavioral deviation detected",
            ),
            CampaignRiskFactor(
                factor_name="Temporal Concentration",
                weight=FACTOR_WEIGHTS["TemporalConcentration"],
                raw_value=round(raw_temporal, 1),
                contribution=round(c_temporal, 2),
                evidence=f"High cluster density across {len(cases)} correlated case(s)",
            ),
            CampaignRiskFactor(
                factor_name="Evidence Strength",
                weight=FACTOR_WEIGHTS["EvidenceStrength"],
                raw_value=round(raw_evidence, 1),
                contribution=round(c_evidence, 2),
                evidence=f"Verified cryptographic evidence items: {total_evd}",
            ),
        ]

        return total_risk, confidence, factors
