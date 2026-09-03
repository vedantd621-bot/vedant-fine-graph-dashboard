"""
FinGraph Fraud Pattern Detectors Package.
"""
from detection.src.detectors.base import BaseDetector
from detection.src.detectors.funnel import FunnelDetector
from detection.src.detectors.one_to_many import OneToManyDetector
from detection.src.detectors.chain import ChainDetector
from detection.src.detectors.circular import CircularFlowDetector
from detection.src.detectors.layered import LayeredNetworkDetector
from detection.src.detectors.high_degree import HighDegreeDetector
from detection.src.detectors.money_trail import MoneyTrailInvestigator

__all__ = [
    "BaseDetector",
    "FunnelDetector",
    "OneToManyDetector",
    "ChainDetector",
    "CircularFlowDetector",
    "LayeredNetworkDetector",
    "HighDegreeDetector",
    "MoneyTrailInvestigator",
]
