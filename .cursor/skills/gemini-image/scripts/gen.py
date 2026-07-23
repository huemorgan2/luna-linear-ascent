#!/usr/bin/env python3
"""Generate or edit images with Google's Gemini image models (Nano Banana / Nano Banana Pro).

Stdlib only (no pip installs). Resolves the API key from, in order:
  1. --api-key
  2. $GEMINI_API_KEY
  3. ~/.cursor/mcp.json   (any GEMINI_API_KEY value, nested)
  4. ./.env or ../luna/.env  (GEMINI_API_KEY or LUNA_GEMINI_API_KEY)

Examples:
  python gen.py --list-models
  python gen.py --prompt "a luminous moon over deep space" --out out.png --aspect 16:9
  python gen.py --prompt "make the moon larger, add aurora" --ref out.png --out out2.png
"""
import argparse, base64, json, mimetypes, os, sys, urllib.request, urllib.error

API_ROOT = "https://generativelanguage.googleapis.com/v1beta"
DEFAULT_MODEL = "gemini-3-pro-image"  # Nano Banana Pro. Use gemini-2.5-flash-image for cheaper/faster.


def _find_key(o, target):
    if isinstance(o, dict):
        for k, v in o.items():
            if k == target and isinstance(v, str) and v:
                return v
            r = _find_key(v, target)
            if r:
                return r
    elif isinstance(o, list):
        for v in o:
            r = _find_key(v, target)
            if r:
                return r
    return None


def resolve_key(cli_key=None):
    if cli_key:
        return cli_key
    if os.environ.get("GEMINI_API_KEY"):
        return os.environ["GEMINI_API_KEY"]
    mcp = os.path.expanduser("~/.cursor/mcp.json")
    if os.path.isfile(mcp):
        try:
            return _find_key(json.load(open(mcp)), "GEMINI_API_KEY")
        except Exception:
            pass
    for envf in (".env", "../luna/.env"):
        if os.path.isfile(envf):
            for line in open(envf):
                line = line.strip()
                for name in ("GEMINI_API_KEY", "LUNA_GEMINI_API_KEY"):
                    if line.startswith(name + "="):
                        v = line.split("=", 1)[1].strip().strip('"').strip("'")
                        if v:
                            return v
    return None


def list_models(key):
    d = json.load(urllib.request.urlopen(f"{API_ROOT}/models?key={key}&pageSize=300"))
    for m in d.get("models", []):
        n = m["name"].replace("models/", "")
        if "image" in n.lower():
            print(n, "->", ",".join(m.get("supportedGenerationMethods", [])))


def _inline_part(path):
    mime = mimetypes.guess_type(path)[0] or "image/png"
    data = base64.b64encode(open(path, "rb").read()).decode()
    return {"inline_data": {"mime_type": mime, "data": data}}


def generate(key, model, prompt, out, refs=None, aspect=None):
    parts = [{"text": prompt}]
    for r in (refs or []):
        parts.append(_inline_part(r))
    gen_cfg = {"responseModalities": ["IMAGE"]}
    if aspect:
        gen_cfg["imageConfig"] = {"aspectRatio": aspect}
    body = {"contents": [{"parts": parts}], "generationConfig": gen_cfg}
    url = f"{API_ROOT}/models/{model}:generateContent?key={key}"
    req = urllib.request.Request(
        url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}
    )
    try:
        resp = urllib.request.urlopen(req)
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code}: {e.read().decode()[:1000]}")
    d = json.load(resp)
    cands = d.get("candidates", [])
    if not cands:
        sys.exit("No candidates returned: " + json.dumps(d)[:1000])
    cparts = cands[0].get("content", {}).get("parts", [])
    for part in cparts:
        inl = part.get("inlineData") or part.get("inline_data")
        if inl:
            raw = base64.b64decode(inl["data"])
            os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
            with open(out, "wb") as fh:
                fh.write(raw)
            print(out)
            return out
    texts = " ".join(p.get("text", "") for p in cparts)
    sys.exit("No image in response. Model returned text: " + texts[:1000])


def main():
    ap = argparse.ArgumentParser(description="Gemini image generation/editing (Nano Banana).")
    ap.add_argument("--prompt", help="Text prompt")
    ap.add_argument("--out", help="Output file path (.png/.jpg)")
    ap.add_argument("--model", default=DEFAULT_MODEL, help=f"Model id (default {DEFAULT_MODEL})")
    ap.add_argument("--ref", action="append", default=[],
                    help="Reference/base image to edit or style-match (repeatable)")
    ap.add_argument("--aspect", help="Aspect ratio, e.g. 16:9, 1:1, 4:3, 3:2, 9:16, 21:9")
    ap.add_argument("--api-key", help="Override API key")
    ap.add_argument("--list-models", action="store_true", help="List image-capable models and exit")
    a = ap.parse_args()

    key = resolve_key(a.api_key)
    if not key:
        sys.exit("No Gemini API key found (set GEMINI_API_KEY, pass --api-key, or add it to ~/.cursor/mcp.json).")
    if a.list_models:
        list_models(key)
        return
    if not a.prompt or not a.out:
        sys.exit("--prompt and --out are required (or use --list-models).")
    generate(key, a.model, a.prompt, a.out, a.ref, a.aspect)


if __name__ == "__main__":
    main()
