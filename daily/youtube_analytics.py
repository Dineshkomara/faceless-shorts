#!/usr/bin/env python3
"""Import read-only YouTube Analytics into dashboard/perf.json (stdlib only)."""
import argparse
import base64
import datetime as dt
import hashlib
import json
import os
import secrets
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(os.environ.get("PIPELINE_ROOT", Path(__file__).resolve().parent.parent)).resolve()

def load_local_env():
    """Load optional repo-local settings without overriding the caller's environment."""
    env_file = ROOT / ".env"
    if not env_file.is_file():
        return
    for raw in env_file.read_text(errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

load_local_env()

DAILY = ROOT / "daily"
PERF = ROOT / "dashboard" / "perf.json"
CLIENT = Path(os.environ.get("YT_ANALYTICS_CLIENT_JSON", str(Path.home() / "Documents/yt-analytics")))
TOKEN_BASE = Path(os.environ.get("YT_ANALYTICS_TOKEN_DIR", str(Path.home() / ".config/faceless-shorts")))
SCOPE = "https://www.googleapis.com/auth/yt-analytics.readonly"
AUTH = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
REPORTS = "https://youtubeanalytics.googleapis.com/v2/reports"


def client_json():
    path = CLIENT
    if path.is_dir():
        candidates = sorted(path.glob("*.json"))
        candidates = [p for p in candidates if "client_secret" in p.name]
        if len(candidates) != 1:
            raise RuntimeError(f"Expected one OAuth client JSON in {path}; found {len(candidates)}")
        path = candidates[0]
    data = json.loads(path.read_text())
    return path, data.get("installed") or data.get("web")


def token_path(profile):
    explicit = os.environ.get("YT_ANALYTICS_TOKEN_FILE")
    if explicit and profile == "en":
        return Path(explicit)
    return TOKEN_BASE / f"youtube-analytics-{profile}-token.json"


def save_token(token, profile):
    path = token_path(profile)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(token, indent=2) + "\n")
    os.chmod(tmp, 0o600)
    tmp.replace(path)
    os.chmod(path, 0o600)


def load_token(profile):
    path = token_path(profile)
    return json.loads(path.read_text()) if path.exists() else None


def post_form(url, values):
    body = urllib.parse.urlencode(values).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req, timeout=30) as res:
        return json.loads(res.read())


def authorize(profile):
    _, client = client_json()
    if not client or not client.get("client_id"):
        raise RuntimeError("OAuth client JSON is missing installed-app client configuration")
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
    state = secrets.token_urlsafe(24)
    result = {}

    class Callback(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass
        def do_GET(self):
            query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            if query.get("state", [None])[0] != state:
                self.send_error(400, "OAuth state mismatch")
                result["error"] = "OAuth state mismatch"
                return
            result.update({k: v[0] for k, v in query.items() if v})
            message = b"Authorization received. You can close this tab and return to the pipeline."
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(message)))
            self.end_headers()
            self.wfile.write(message)

    server = HTTPServer(("127.0.0.1", 0), Callback)
    server.timeout = 240
    port = server.server_port
    redirect = f"http://127.0.0.1:{port}/"
    params = {"client_id": client["client_id"], "redirect_uri": redirect, "response_type": "code",
              "scope": SCOPE, "access_type": "offline", "prompt": "consent", "state": state,
              "code_challenge": challenge, "code_challenge_method": "S256"}
    url = AUTH + "?" + urllib.parse.urlencode(params)
    print("Opening Google sign-in. Approve read-only YouTube Analytics access in the browser.")
    if os.environ.get("YT_ANALYTICS_NO_BROWSER") == "1" or not webbrowser.open(url):
        print(url, flush=True)
    server.handle_request()
    server.server_close()
    if result.get("error"):
        raise RuntimeError("Google authorization was not completed: " + result["error"])
    if not result.get("code"):
        raise RuntimeError("Timed out waiting for Google authorization callback")
    tokens = post_form(TOKEN_URL, {"code": result["code"], "client_id": client["client_id"],
        "client_secret": client.get("client_secret", ""), "redirect_uri": redirect,
        "grant_type": "authorization_code", "code_verifier": verifier})
    if SCOPE not in tokens.get("scope", SCOPE):
        raise RuntimeError("Google did not grant the requested read-only Analytics scope")
    tokens["expires_at"] = time.time() + int(tokens.get("expires_in", 3600))
    save_token(tokens, profile)
    print(f"Read-only Analytics authorization saved for the {profile.upper()} channel profile.")


def access_token(profile):
    token = load_token(profile)
    if not token:
        raise RuntimeError("No saved authorization. Run: python3 daily/youtube_analytics.py authorize")
    if token.get("expires_at", 0) > time.time() + 60:
        return token["access_token"]
    _, client = client_json()
    if not token.get("refresh_token"):
        raise RuntimeError("Saved token has no refresh token. Reauthorize with the authorize command.")
    fresh = post_form(TOKEN_URL, {"client_id": client["client_id"], "client_secret": client.get("client_secret", ""),
        "refresh_token": token["refresh_token"], "grant_type": "refresh_token"})
    fresh["refresh_token"] = token["refresh_token"]
    fresh["expires_at"] = time.time() + int(fresh.get("expires_in", 3600))
    save_token(fresh, profile)
    return fresh["access_token"]


def api_report(access, start, end, metrics, ids, filters, dimensions="video"):
    params = {"ids": ids, "startDate": start, "endDate": end, "metrics": metrics,
              "filters": filters, "dimensions": dimensions, "maxResults": "200"}
    url = REPORTS + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + access})
    try:
        with urllib.request.urlopen(req, timeout=45) as res:
            return json.loads(res.read())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:500]
        raise RuntimeError(f"YouTube Analytics API returned HTTP {exc.code}: {detail}") from exc


def sync(profile="all"):
    if not PERF.is_file():
        raise RuntimeError(f"Dashboard performance file not found: {PERF}")
    rows = json.loads(PERF.read_text())
    records = [r for r in rows if isinstance(r, dict) and len(str(r.get("video_id", ""))) == 11]
    if not records:
        print("No uploaded video IDs found; nothing to sync.")
        return
    profiles = ("en", "te") if profile == "all" else (profile,)
    end = dt.date.today().isoformat()
    updated = 0
    for channel_profile in profiles:
        profile_records = [r for r in records if normalize_channel(r.get("channel")) == channel_profile]
        if not profile_records:
            continue
        try:
            access = access_token(channel_profile)
        except RuntimeError as exc:
            print(f"{channel_profile.upper()} Analytics skipped: {exc}", file=sys.stderr)
            continue
        ids = list(dict.fromkeys(r["video_id"] for r in profile_records))
        dates = [r.get("date") for r in profile_records if r.get("date") and str(r["date"])[:4].isdigit()]
        start = min(dates) if dates else "2005-01-01"
        video_filter = "video==" + ",".join(ids)
        stats = api_report(access, start, end, "views,likes,comments,averageViewPercentage", "channel==MINE", video_filter)
        values = {}
        for r in stats.get("rows", []):
            if len(r) >= 5:
                values[r[0]] = {"views": int(r[1]), "likes": int(r[2]), "comments": int(r[3]), "retention": round(float(r[4]), 2)}
        # Thumbnail reach metrics are available through YouTube Reporting API bulk
        # reports, not this targeted reports.query combination. Leave CTR untouched.
        for item in profile_records:
            metrics = values.get(item["video_id"])
            if not metrics:
                continue
            for key, value in metrics.items():
                item[key] = value
            item["analytics_updated_at"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
            updated += 1
    tmp = PERF.with_suffix(".tmp")
    tmp.write_text(json.dumps(rows, indent=1, ensure_ascii=False) + "\n")
    os.chmod(tmp, PERF.stat().st_mode & 0o777)
    tmp.replace(PERF)
    print(f"Synced Analytics for {updated} of {len(records)} uploaded videos.")


def normalize_channel(value):
    value = str(value or "").lower()
    return "te" if value in ("te", "telugu", "asakthi") else "en"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("authorize", "sync", "status"))
    parser.add_argument("--profile", choices=("en", "te", "all"), default="all",
                        help="Channel profile to authorize or sync (default: both)")
    args = parser.parse_args()
    try:
        if args.command == "authorize":
            if args.profile == "all":
                raise RuntimeError("Authorize one profile at a time: --profile en or --profile te")
            authorize(args.profile)
        elif args.command == "sync":
            sync(args.profile)
        else:
            for profile in ("en", "te"):
                print(f"{profile.upper()}: {'authorized' if token_path(profile).exists() else 'not authorized'}")
            print("OAuth client JSON present" if CLIENT.exists() else "OAuth client JSON not found")
    except Exception as exc:
        print(f"Analytics importer: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
