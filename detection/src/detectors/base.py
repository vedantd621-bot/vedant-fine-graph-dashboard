"""
FinGraph Base Fraud Pattern Detector.
Defines common interface and utility methods for all Cypher graph detectors.
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from neo4j.src.client import Neo4jClient
from detection.src.models import DetectionResult


class BaseDetector(ABC):
    """Abstract base class for all topological fraud pattern detectors."""

    def __init__(self, client: Neo4jClient):
        self.client = client

    @abstractmethod
    def detect(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        **kwargs,
    ) -> List[DetectionResult]:
        """Executes Cypher detection query and returns structured DetectionResult objects."""
        pass
