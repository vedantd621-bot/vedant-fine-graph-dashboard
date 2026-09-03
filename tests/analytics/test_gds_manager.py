"""
Unit tests for GDSManager projection lifecycle and algorithm execution.
"""
from unittest.mock import MagicMock
import pytest

from analytics.src.gds_manager import GDSManager
from analytics.src.models import GraphFeatures


def test_gds_manager_projection_lifecycle():
    """Verify projection existence, creation, and drop operations."""
    mock_client = MagicMock()
    # Sequence of queries:
    # 1. gds.projection_exists("fingraph") -> returns False
    # 2. gds.create_projection("fingraph") -> internal projection_exists check -> returns False
    # 3. gds.create_projection("fingraph") -> CALL gds.graph.project -> returns nodeCount 30
    # 4. gds.projection_exists("fingraph") -> returns True
    # 5. gds.drop_projection("fingraph") -> CALL gds.graph.drop -> returns graphName
    mock_client.execute_query.side_effect = [
        [{"exists": False}],                                                                            # 1
        [{"exists": False}],                                                                            # 2
        [{"graphName": "fingraph", "nodeCount": 30, "relationshipCount": 29, "projectMillis": 12}],    # 3
        [{"exists": True}],                                                                             # 4
        [{"graphName": "fingraph"}],                                                                    # 5
    ]

    gds = GDSManager(mock_client)
    assert gds.projection_exists("fingraph") is False

    res = gds.create_projection("fingraph")
    assert res["nodeCount"] == 30

    assert gds.projection_exists("fingraph") is True
    assert gds.drop_projection("fingraph") is True


def test_gds_manager_algorithms_execution():
    """Verify execution of PageRank, WCC, and Louvain algorithms."""
    mock_client = MagicMock()
    mock_client.execute_query.side_effect = [
        [{"nodePropertiesWritten": 30, "computeMillis": 8}],  # mutate PR
        [{"propertiesWritten": 30}],                           # write PR
        [{"componentCount": 5, "computeMillis": 4}],          # mutate WCC
        [{"propertiesWritten": 30}],                           # write WCC
        [{"communityCount": 6, "modularity": 0.72}],          # mutate Louvain
        [{"propertiesWritten": 30}],                           # write Louvain
    ]

    gds = GDSManager(mock_client)
    all_res = gds.run_all_algorithms("fingraph")

    assert "pagerank" in all_res
    assert "wcc" in all_res
    assert "louvain" in all_res
    assert mock_client.execute_query.call_count == 6


def test_gds_manager_extract_graph_features():
    """Verify extraction of graph features for accounts."""
    mock_client = MagicMock()
    mock_client.execute_query.return_value = [
        {
            "account_id": "A005",
            "pagerank": 0.45,
            "wcc_id": 1,
            "louvain_community_id": 2,
            "in_degree": 4,
            "out_degree": 1,
            "total_degree": 5,
            "total_volume": 71280.0,
        },
        {
            "account_id": "A001",
            "pagerank": 0.15,
            "wcc_id": 1,
            "louvain_community_id": 2,
            "in_degree": 0,
            "out_degree": 1,
            "total_degree": 1,
            "total_volume": 8500.0,
        },
    ]

    gds = GDSManager(mock_client)
    features_map = gds.extract_graph_features()

    assert len(features_map) == 2
    assert "A005" in features_map
    assert features_map["A005"].pagerank == 0.45
    assert features_map["A005"].total_degree == 5
    assert features_map["A005"].community_size == 2
