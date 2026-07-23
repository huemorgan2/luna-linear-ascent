"""worldd game API: auth, creation flow, idempotency, shared frontier."""

import hashlib
import hmac
import json
import time
import uuid

import pytest

from app import db
from app.config import get_config


async def make_tenant(client, name: str) -> str:
    r = await client.post(f"/admin/tenants", json={"tenant": name},
                          headers={"X-Admin-Key": get_config().admin_key})
    if r.status_code == 409:
        pool = await db.get_pool()
        row = await pool.fetchrow(
            "SELECT secret FROM ascent_tenants WHERE tenant=$1", name)
        return row["secret"]
    assert r.status_code == 200, r.text
    return r.json()["secret"]


def signed(secret: str, tenant: str, payload: dict) -> tuple[bytes, dict]:
    body = json.dumps(payload, separators=(",", ":")).encode()
    ts = str(int(time.time()))
    sig = hmac.new(secret.encode(), f"{ts}.".encode() + body,
                   hashlib.sha256).hexdigest()
    return body, {
        "Content-Type": "application/json",
        "X-Ascent-Tenant": tenant, "X-Ascent-Ts": ts,
        "X-Ascent-Signature": sig, "X-Ascent-Api": "1",
    }


async def act(client, secret, tenant, player, option="", text="", idem=None):
    body, headers = signed(secret, tenant, {
        "player": player, "option": option, "text": text,
        "idem": idem or str(uuid.uuid4())})
    r = await client.post("/v1/act", content=body, headers=headers)
    assert r.status_code == 200, r.text
    return r.json()["scene"]


async def scene(client, secret, tenant, player):
    body, headers = signed(secret, tenant, {"player": player})
    r = await client.post("/v1/scene", content=body, headers=headers)
    assert r.status_code == 200, r.text
    return r.json()["scene"]


@pytest.fixture
async def tenant_a(client):
    return await make_tenant(client, "tenant-a")


@pytest.fixture
async def tenant_b(client):
    return await make_tenant(client, "tenant-b")


async def test_rejects_unsigned_and_bad_sig(client, tenant_a):
    r = await client.post("/v1/scene", json={"player": "x"})
    assert r.status_code in (401, 426)
    body, headers = signed(tenant_a, "tenant-a", {"player": "x"})
    headers["X-Ascent-Signature"] = "0" * 64
    r = await client.post("/v1/scene", content=body, headers=headers)
    assert r.status_code == 401


async def test_rejects_stale_timestamp(client, tenant_a):
    payload = {"player": "x"}
    body = json.dumps(payload, separators=(",", ":")).encode()
    ts = str(int(time.time()) - 4000)
    sig = hmac.new(tenant_a.encode(), f"{ts}.".encode() + body,
                   hashlib.sha256).hexdigest()
    r = await client.post("/v1/scene", content=body, headers={
        "Content-Type": "application/json",
        "X-Ascent-Tenant": "tenant-a", "X-Ascent-Ts": ts,
        "X-Ascent-Signature": sig, "X-Ascent-Api": "1"})
    assert r.status_code == 401


async def test_creation_flow_over_http(client, tenant_a):
    player = f"p-{uuid.uuid4().hex[:8]}"
    s = await scene(client, tenant_a, "tenant-a", player)
    assert "shard" in s["headline"].lower()
    s = await act(client, tenant_a, "tenant-a", player, option="dwarf")
    assert "how do you fight" in s["headline"]
    s = await act(client, tenant_a, "tenant-a", player, option="warrior")
    s = await act(client, tenant_a, "tenant-a", player, text="Borin")
    assert "Borin" in s["headline"]

    # character sheet reflects the dwarf warrior
    body, headers = signed(tenant_a, "tenant-a", {"player": player})
    r = await client.post("/v1/character", content=body, headers=headers)
    assert r.json()["race"] == "dwarf"


async def test_idempotent_act_replays_same_scene(client, tenant_a):
    player = f"p-{uuid.uuid4().hex[:8]}"
    await scene(client, tenant_a, "tenant-a", player)
    idem = str(uuid.uuid4())
    s1 = await act(client, tenant_a, "tenant-a", player,
                   option="human", idem=idem)
    s2 = await act(client, tenant_a, "tenant-a", player,
                   option="human", idem=idem)      # replay
    assert s1 == s2
    # state advanced exactly once: next distinct act still on class stage
    s3 = await act(client, tenant_a, "tenant-a", player, option="warrior")
    assert "name" in s3["headline"].lower()


async def test_frontier_is_shared_across_tenants(client, tenant_a, tenant_b):
    pool = await db.get_pool()
    await pool.execute(
        "UPDATE ascent_world SET value='4'::jsonb WHERE key='frontier'")
    player = f"p-{uuid.uuid4().hex[:8]}"
    await scene(client, tenant_b, "tenant-b", player)
    await act(client, tenant_b, "tenant-b", player, option="elf")
    await act(client, tenant_b, "tenant-b", player, option="archer")
    await act(client, tenant_b, "tenant-b", player, text="Fleet")
    s = await act(client, tenant_b, "tenant-b", player, option="gate")
    labels = [o["label"] for o in s["options"]]
    assert any("Floor 4" in l for l in labels)     # world frontier inherited
    await pool.execute(
        "UPDATE ascent_world SET value='1'::jsonb WHERE key='frontier'")


async def test_players_are_tenant_scoped(client, tenant_a, tenant_b):
    player = f"p-{uuid.uuid4().hex[:8]}"
    await scene(client, tenant_a, "tenant-a", player)
    await act(client, tenant_a, "tenant-a", player, option="halfling")
    # same player name under tenant-b starts fresh at race selection
    s = await scene(client, tenant_b, "tenant-b", player)
    assert "shard" in s["headline"].lower()
