"""010 — the Gmail door's OAuth 2.0 plumbing (authorization-code + PKCE).

Stdlib only, on purpose: worldd ships no HTTP client in requirements, so
the token exchange is a server-to-server HTTPS POST via urllib, run off
the event loop with asyncio.to_thread. The ID token comes straight back
from Google's token endpoint over TLS, so its payload is *decoded*, not
re-verified against Google's JWKS — Google's own guidance is that a token
fetched directly from the token endpoint needs no signature check. We
still assert aud, iss, exp and email_verified before trusting a claim.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request

from .config import get_config

AUTH_URI = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URI = "https://oauth2.googleapis.com/token"
SCOPE = "openid email profile"
_ISSUERS = {"accounts.google.com", "https://accounts.google.com"}


class OAuthError(Exception):
    """Any failure in the Google round-trip — the door shows a retry."""


def configured() -> bool:
    c = get_config()
    return bool(c.google_client_id and c.google_client_secret
                and c.google_redirect_uri)


def make_pkce() -> tuple[str, str]:
    """(verifier, challenge) for PKCE S256."""
    verifier = secrets.token_urlsafe(64)[:96]
    digest = hashlib.sha256(verifier.encode()).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return verifier, challenge


def auth_url(state: str, code_challenge: str) -> str:
    c = get_config()
    params = {
        "client_id": c.google_client_id,
        "redirect_uri": c.google_redirect_uri,
        "response_type": "code",
        "scope": SCOPE,
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "access_type": "online",
        # always let the player choose which Google account to use
        "prompt": "select_account",
    }
    return AUTH_URI + "?" + urllib.parse.urlencode(params)


def _b64url_json(segment: str) -> dict:
    pad = "=" * (-len(segment) % 4)
    return json.loads(base64.urlsafe_b64decode(segment + pad))


def _post_token(code: str, code_verifier: str) -> dict:
    c = get_config()
    data = urllib.parse.urlencode({
        "code": code,
        "client_id": c.google_client_id,
        "client_secret": c.google_client_secret,
        "redirect_uri": c.google_redirect_uri,
        "grant_type": "authorization_code",
        "code_verifier": code_verifier,
    }).encode()
    req = urllib.request.Request(
        TOKEN_URI, data=data, method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded",
                 "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        raise OAuthError(f"token exchange HTTP {e.code}") from e
    except Exception as e:  # network, JSON, timeout
        raise OAuthError("token exchange failed") from e


def claims_from_id_token(id_token: str) -> dict:
    """Decode + validate the ID token payload. Returns the normalized
    identity dict. Raises OAuthError on any inconsistency."""
    parts = id_token.split(".")
    if len(parts) != 3:
        raise OAuthError("malformed id_token")
    claims = _b64url_json(parts[1])
    c = get_config()
    if claims.get("aud") != c.google_client_id:
        raise OAuthError("id_token aud mismatch")
    if claims.get("iss") not in _ISSUERS:
        raise OAuthError("id_token iss mismatch")
    if int(claims.get("exp", 0)) < int(time.time()):
        raise OAuthError("id_token expired")
    sub = claims.get("sub")
    email = (claims.get("email") or "").strip().lower()
    verified = claims.get("email_verified")
    if isinstance(verified, str):
        verified = verified.lower() == "true"
    if not sub or not email:
        raise OAuthError("id_token missing sub/email")
    if not verified:
        raise OAuthError("google email not verified")
    return {
        "sub": str(sub),
        "email": email,
        "email_verified": True,
        "name": claims.get("name") or "",
        "given_name": claims.get("given_name") or "",
    }


async def exchange_code(code: str, code_verifier: str) -> dict:
    """Trade the authorization code for the verified Google identity:
    {sub, email, email_verified, name, given_name}. Raises OAuthError."""
    tok = await asyncio.to_thread(_post_token, code, code_verifier)
    id_token = tok.get("id_token")
    if not id_token:
        raise OAuthError("no id_token in token response")
    return claims_from_id_token(id_token)
