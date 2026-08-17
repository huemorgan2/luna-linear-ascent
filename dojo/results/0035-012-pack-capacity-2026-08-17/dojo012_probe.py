"""dojo 012 — production probe over HMAC (throwaway tenant)."""
import hashlib, hmac, json, secrets, sys, time, urllib.request

BASE = "https://ascent-worldd.onrender.com"
UA = "dojo-probe/012"


def post(path, body, tenant=None, secret=None):
    raw = json.dumps(body).encode()
    hdr = {"content-type": "application/json", "user-agent": UA}
    if tenant:
        ts = str(int(time.time()))
        sig = hmac.new(secret.encode(), f"{ts}.".encode() + raw,
                       hashlib.sha256).hexdigest()
        hdr.update({"X-Ascent-Tenant": tenant, "X-Ascent-Ts": ts,
                    "X-Ascent-Signature": sig, "X-Ascent-Api": "1"})
    req = urllib.request.Request(BASE + path, raw, hdr)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


st, health = 0, json.loads(urllib.request.urlopen(BASE + "/health").read())
print("health", health)
st, en = post("/v1/enroll", {"install_id": "dojo012-" + secrets.token_hex(8),
                             "name_hint": "dojo012"})
print("enroll", st, en.get("tenant"))
T, S = en["tenant"], en["secret"]
P = "dojo012-player"


def act(opt="", text=""):
    st, r = post("/v1/act", {"player": P, "option": opt, "text": text,
                             "idem": secrets.token_hex(6)}, T, S)
    assert st == 200, (st, r)
    return r["scene"]


def scene():
    st, r = post("/v1/scene", {"player": P}, T, S)
    assert st == 200, (st, r)
    return r["scene"]


s = scene()
for n in range(80):
    ids = [o["id"] for o in s.get("options", [])]
    if "forge" in ids or "town" in ids:
        break
    if s.get("awaits_text"):
        s = act("", "DojoPack" + secrets.token_hex(2)); continue
    for pick in ("human", "warrior"):
        if pick in ids:
            s = act(pick); break
    else:
        s = act(ids[0] if ids else "1")
print("steps", n, "| headline:", s.get("headline"), "| opts:", [o["id"] for o in s["options"]][:9])
print("wire pack_slots:", s.get("pack_slots"),
      "| inventory:", [(i["slug"], i.get("kind"), i.get("count")) for i in s.get("inventory", [])])
if "town" in [o["id"] for o in s.get("options", [])] and "forge" not in [o["id"] for o in s["options"]]:
    s = act("town")
s = act("forge")
row = next((o for o in s["options"] if o["id"] == "buy_pack"), None)
print("forge buy_pack row:", row)
s = act("buy_pack")
print("buy_pack at level 1 → refusal:", s.get("refusal"), "| note:", s.get("shard_note"))
st, ch = post("/v1/character", {"player": P}, T, S)
print("character keys:", list(ch)[:12])
doc = ch.get("doc") or ch.get("character") or ch
for k in ("pack_slots", "gold", "level"):
    print(" ", k, doc.get(k) if isinstance(doc, dict) else None)
# medlab: buy until the pack fills, expect a pack-full refusal on the 7th kind
s = act("back"); s = act("medlab")
print("medlab rows:", [o["id"] for o in s["options"]])
print("tenant", T)
