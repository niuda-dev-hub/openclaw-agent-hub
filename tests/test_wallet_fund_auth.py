from fastapi.testclient import TestClient

from agent_hub.main import app


def _create_agent(client: TestClient, name: str) -> dict:
    resp = client.post(
        "/api/v0.1/agents",
        json={"name": name, "agent_type": "mock", "config": {"x": 1}},
    )
    assert resp.status_code == 200
    return resp.json()


def test_wallet_fund_forbidden_when_server_token_missing(monkeypatch):
    monkeypatch.delenv("AGENT_HUB_ADMIN_FUND_TOKEN", raising=False)
    c = TestClient(app)
    agent = _create_agent(c, "agent-fund-auth-missing")

    resp = c.post(
        f"/api/v0.1/agents/{agent['id']}/wallet/fund",
        json={"amount_usd": 10.0},
    )
    assert resp.status_code == 403
    assert resp.json()["detail"] == "funding_disabled_missing_admin_token"


def test_wallet_fund_forbidden_when_token_mismatch(monkeypatch):
    monkeypatch.setenv("AGENT_HUB_ADMIN_FUND_TOKEN", "secret-123")
    c = TestClient(app)
    agent = _create_agent(c, "agent-fund-auth-mismatch")

    resp = c.post(
        f"/api/v0.1/agents/{agent['id']}/wallet/fund",
        json={"amount_usd": 10.0},
        headers={"X-Admin-Token": "wrong-token"},
    )
    assert resp.status_code == 403
    assert resp.json()["detail"] == "forbidden_admin_token"


def test_wallet_fund_success_with_bearer_token(monkeypatch):
    monkeypatch.setenv("AGENT_HUB_ADMIN_FUND_TOKEN", "secret-123")
    c = TestClient(app)
    agent = _create_agent(c, "agent-fund-auth-ok")

    resp = c.post(
        f"/api/v0.1/agents/{agent['id']}/wallet/fund",
        json={"amount_usd": 10.0},
        headers={"Authorization": "Bearer secret-123"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["balance_usd"] >= 10.0
