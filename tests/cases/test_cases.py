"""
Case Management & Forensic Evidence Unit / Integration Tests.
Tests full case lifecycle, status transitions, note threads, cryptographic evidence hashing,
alert/account linking, and RBAC permission enforcement.
"""
from fastapi.testclient import TestClient
import pytest

from backend.app.main import app
from backend.app.models.cases import CasePriority, CaseStatus, EvidenceType
from backend.app.security.jwt import create_access_token


def get_auth_token(role: str = "INVESTIGATOR", username: str = "investigator") -> str:
    """Helper to generate JWT bearer tokens for test personas."""
    return create_access_token({"sub": f"usr_{username}", "username": username, "role": role})


@pytest.fixture
def client():
    return TestClient(app)


def test_case_creation_and_retrieval(client):
    """Verify creating an investigation case and retrieving its full record."""
    inv_token = get_auth_token("INVESTIGATOR", "investigator")
    headers = {"Authorization": f"Bearer {inv_token}"}

    create_payload = {
        "title": "Layered Smurfing Syndicate Alpha",
        "description": "Multi-hop layering network with fan-in aggregation and rapid outbound dispersal.",
        "priority": "HIGH",
        "assigned_investigator": "investigator",
        "linked_alerts": ["ALT-LAYERED-01"],
        "linked_accounts": ["A001", "A002", "A003"],
        "linked_transactions": ["TX_101", "TX_102"],
    }

    # 1. Create Case
    res = client.post("/api/v1/cases", json=create_payload, headers=headers)
    assert res.status_code == 201
    created_case = res.json()
    case_id = created_case["case_id"]
    assert case_id.startswith("CASE-")
    assert created_case["title"] == create_payload["title"]
    assert created_case["status"] == "OPEN"
    assert created_case["priority"] == "HIGH"
    assert len(created_case["linked_accounts"]) == 3

    # 2. Get Case Detail
    get_res = client.get(f"/api/v1/cases/{case_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["case_id"] == case_id

    # 3. List Cases with search
    list_res = client.get(f"/api/v1/cases?search=Layered", headers=headers)
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total_items"] >= 1
    assert any(c["case_id"] == case_id for c in list_data["data"])


def test_case_status_transitions_and_validation(client):
    """Verify legal and illegal state transitions for case status."""
    inv_token = get_auth_token("INVESTIGATOR", "investigator")
    headers = {"Authorization": f"Bearer {inv_token}"}

    # Create Case
    res = client.post(
        "/api/v1/cases",
        json={"title": "State Transition Test", "description": "Testing lifecycle transitions", "priority": "MEDIUM"},
        headers=headers,
    )
    case_id = res.json()["case_id"]

    # Valid transition: OPEN -> IN_PROGRESS
    patch_res = client.patch(
        f"/api/v1/cases/{case_id}",
        json={"status": "IN_PROGRESS"},
        headers=headers,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "IN_PROGRESS"

    # Valid transition: IN_PROGRESS -> ESCALATED
    esc_res = client.patch(
        f"/api/v1/cases/{case_id}",
        json={"status": "ESCALATED", "priority": "CRITICAL"},
        headers=headers,
    )
    assert esc_res.status_code == 200
    assert esc_res.json()["status"] == "ESCALATED"
    assert esc_res.json()["priority"] == "CRITICAL"


def test_case_assignment_and_notes(client):
    """Verify investigator assignment and appending notes to case feed."""
    inv_token = get_auth_token("INVESTIGATOR", "investigator")
    headers = {"Authorization": f"Bearer {inv_token}"}

    # Create Case
    res = client.post(
        "/api/v1/cases",
        json={"title": "Case Notes & Assign Test", "description": "Testing note threads", "priority": "LOW"},
        headers=headers,
    )
    case_id = res.json()["case_id"]

    # 1. Assign to another investigator
    assign_res = client.post(
        f"/api/v1/cases/{case_id}/assign",
        json={"assigned_investigator": "lead_detective"},
        headers=headers,
    )
    assert assign_res.status_code == 200
    assert assign_res.json()["assigned_investigator"] == "lead_detective"

    # 2. Add Note
    note_res = client.post(
        f"/api/v1/cases/{case_id}/notes",
        json={"content": "Counterparty subpoena request sent to intermediary bank."},
        headers=headers,
    )
    assert note_res.status_code == 201
    note = note_res.json()
    assert note["note_id"].startswith("NOTE-")
    assert note["author_name"] == "investigator"

    # 3. Verify note appears in case detail
    detail_res = client.get(f"/api/v1/cases/{case_id}", headers=headers)
    assert len(detail_res.json()["notes"]) == 1
    assert detail_res.json()["notes"][0]["note_id"] == note["note_id"]


def test_evidence_attachment_with_integrity_hash(client):
    """Verify registering evidence and verifying SHA-256 integrity hash."""
    inv_token = get_auth_token("INVESTIGATOR", "investigator")
    headers = {"Authorization": f"Bearer {inv_token}"}

    res = client.post(
        "/api/v1/cases",
        json={"title": "Evidence Registry Test", "description": "Testing cryptographic evidence attachment", "priority": "HIGH"},
        headers=headers,
    )
    case_id = res.json()["case_id"]

    evd_payload = {
        "type": "TRANSACTION",
        "source": "Apache Kafka Ingestion",
        "related_entity": "TX_998877",
        "title": "High Velocity Inflow Transaction",
        "description": "Settled wire transfer of $85,000 USD from shell entity.",
        "data": {"amount": 85000.0, "currency": "USD", "channel": "wire"},
    }

    attach_res = client.post(f"/api/v1/cases/{case_id}/evidence", json=evd_payload, headers=headers)
    assert attach_res.status_code == 201
    evd = attach_res.json()
    assert evd["evidence_id"].startswith("EVD-")
    assert evd["integrity_hash"] is not None
    assert len(evd["integrity_hash"]) == 64  # SHA-256 hex string length


def test_case_link_unlink_entities(client):
    """Verify linking and unlinking alerts and accounts to a case."""
    inv_token = get_auth_token("INVESTIGATOR", "investigator")
    headers = {"Authorization": f"Bearer {inv_token}"}

    res = client.post(
        "/api/v1/cases",
        json={"title": "Link Unlink Test", "description": "Testing association management", "priority": "MEDIUM"},
        headers=headers,
    )
    case_id = res.json()["case_id"]

    # Link alert
    l_alt = client.post(f"/api/v1/cases/{case_id}/alerts", json={"alert_id": "ALT-999"}, headers=headers)
    assert l_alt.status_code == 200
    assert "ALT-999" in l_alt.json()["linked_alerts"]

    # Unlink alert
    u_alt = client.delete(f"/api/v1/cases/{case_id}/alerts/ALT-999", headers=headers)
    assert u_alt.status_code == 200
    assert "ALT-999" not in u_alt.json()["linked_alerts"]

    # Link account
    l_acc = client.post(f"/api/v1/cases/{case_id}/accounts", json={"account_id": "A999"}, headers=headers)
    assert l_acc.status_code == 200
    assert "A999" in l_acc.json()["linked_accounts"]

    # Unlink account
    u_acc = client.delete(f"/api/v1/cases/{case_id}/accounts/A999", headers=headers)
    assert u_acc.status_code == 200
    assert "A999" not in u_acc.json()["linked_accounts"]


def test_case_timeline_endpoint(client):
    """Verify case timeline endpoint returns chronological events."""
    inv_token = get_auth_token("INVESTIGATOR", "investigator")
    headers = {"Authorization": f"Bearer {inv_token}"}

    res = client.post(
        "/api/v1/cases",
        json={"title": "Timeline Test Case", "description": "Testing event chronology", "priority": "LOW"},
        headers=headers,
    )
    case_id = res.json()["case_id"]

    # Add a note
    client.post(f"/api/v1/cases/{case_id}/notes", json={"content": "Chronological note 1"}, headers=headers)

    # Get Timeline
    tl_res = client.get(f"/api/v1/cases/{case_id}/timeline", headers=headers)
    assert tl_res.status_code == 200
    tl_data = tl_res.json()
    assert tl_data["entity_id"] == case_id
    assert tl_data["total_events"] >= 2  # Case opened + note added


def test_case_rbac_restrictions(client):
    """Verify ANALYST is blocked (403 Forbidden) from creating or mutating cases."""
    analyst_token = get_auth_token("ANALYST", "analyst")
    headers = {"Authorization": f"Bearer {analyst_token}"}

    # 1. Analyst CAN read cases
    list_res = client.get("/api/v1/cases", headers=headers)
    assert list_res.status_code == 200

    # 2. Analyst CANNOT create a case -> 403 Forbidden
    create_res = client.post(
        "/api/v1/cases",
        json={"title": "Unauthorized Case", "description": "Analyst should not be able to create this", "priority": "HIGH"},
        headers=headers,
    )
    assert create_res.status_code == 403

    # 3. Analyst CANNOT mutate case -> 403 Forbidden
    patch_res = client.patch(
        "/api/v1/cases/CASE-2026-001",
        json={"status": "CLOSED"},
        headers=headers,
    )
    assert patch_res.status_code == 403
