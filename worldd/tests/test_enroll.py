"""Self-service enrollment: idempotency, usability of minted creds, limits."""

import hashlib
import hmac as hmaclib
import json
import time
import uuid


def _signed(secret: str, tenant: str, body: dict) -> tuple[bytes, dict]:
    raw = json.dumps(body).encode()
    ts = str(int(time.time()))
    sig = hmaclib.new(secret.encode(), f"{ts}.".encode() + raw,
                      hashlib.sha256).hexdigest()
    return raw, {"X-Ascent-Tenant": tenant, "X-Ascent-Ts": ts,
                 "X-Ascent-Signature": sig, "X-Ascent-Api": "1",
                 "Content-Type": "application/json"}


async def test_enroll_mints_usable_tenant(client):
    install = uuid.uuid4().hex
    r = await client.post("/v1/enroll", json={
        "install_id": install, "name_hint": "roys-luna"})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["tenant"].startswith("roys-luna-")
    assert len(d["secret"]) == 64 and d["existing"] is False

    # the minted credentials immediately work against the game API
    raw, headers = _signed(d["secret"], d["tenant"], {"player": "p1"})
    r = await client.post("/v1/scene", content=raw, headers=headers)
    assert r.status_code == 200, r.text


async def test_enroll_is_idempotent_per_install(client):
    install = uuid.uuid4().hex
    a = (await client.post("/v1/enroll", json={"install_id": install})).json()
    b = (await client.post("/v1/enroll", json={"install_id": install})).json()
    assert b["existing"] is True
    assert (a["tenant"], a["secret"]) == (b["tenant"], b["secret"])


async def test_enroll_validates_input(client):
    r = await client.post("/v1/enroll", json={"install_id": "short"})
    assert r.status_code == 422
    r = await client.post("/v1/enroll", json={
        "install_id": uuid.uuid4().hex, "name_hint": "bad/hint!"})
    assert r.status_code == 422
