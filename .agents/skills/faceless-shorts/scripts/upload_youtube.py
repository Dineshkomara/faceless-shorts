#!/usr/bin/env python3
"""
upload_youtube.py - Fully automated YouTube upload & thumbnail publisher for faceless-shorts.
Uploads the rendered video to the appropriate channel (curiography or asakthi) via Zapier MCP.
"""
import sys
import os
import json
import subprocess
import glob
import re
import shutil
from pathlib import Path

PIPELINE_ROOT = Path(os.environ.get("PIPELINE_ROOT", Path(__file__).resolve().parents[4])).resolve()

def load_local_env():
    """Load non-overriding repo-local settings for direct/manual uploader calls."""
    env_file = PIPELINE_ROOT / ".env"
    if not env_file.is_file():
        return
    for raw in env_file.read_text(errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key.strip(), value)

load_local_env()

for p in ['/opt/homebrew/bin', '/usr/local/bin', os.path.expanduser('~/.local/bin'), os.path.expanduser('~/.gemini/antigravity/bin')]:
    if p not in os.environ.get('PATH', ''):
        os.environ['PATH'] = f"{p}:{os.environ.get('PATH', '')}"

FFMPEG = os.environ.get("FFMPEG_BIN") or shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"

class ApiThrottledError(Exception):
    """Raised when the YouTube or Zapier API explicitly throttles requests."""
    pass

API_THROTTLE_SIGNALS = [
    "throttled without retry",
    "this action has been throttled",
    "the user has exceeded the number of videos",
    "rate limit exceeded",
    "quotaexceeded",
    "upload limit reached",
    "daily upload limit"
]

def log(msg):
    print(f"[upload_youtube] {msg}", flush=True)

def host_file(file_path):
    if os.environ.get("ALLOW_PUBLIC_FILE_HOSTING") != "1":
        raise RuntimeError("Upload requires a public file host so Zapier can fetch the media. Review the privacy implications, then set ALLOW_PUBLIC_FILE_HOSTING=1 in the ignored .env file to enable it.")
    log(f"Hosting file: {file_path} ({os.path.getsize(file_path) / 1024 / 1024:.1f} MB)...")

    # 1. Try catbox.moe (fast, reliable direct links up to 200MB)
    try:
        res = subprocess.run([
            "curl", "-s", "--max-time", "90",
            "-F", "reqtype=fileupload",
            "-F", f"fileToUpload=@{file_path}",
            "https://catbox.moe/user/api.php"
        ], capture_output=True, text=True, timeout=95)
        url = res.stdout.strip()
        if url.startswith("http"):
            log(f"Hosted on catbox.moe: {url}")
            return url
    except Exception as e:
        log(f"catbox.moe failed: {e}")

    # 2. Try uguu.se
    try:
        res = subprocess.run([
            "curl", "-s", "--max-time", "90",
            "-F", f"files[]=@{file_path}",
            "https://uguu.se/upload"
        ], capture_output=True, text=True, timeout=95)
        data = json.loads(res.stdout)
        if data.get("success") and data.get("files"):
            url = data["files"][0]["url"]
            log(f"Hosted on uguu.se: {url}")
            return url
    except Exception as e:
        log(f"uguu.se failed: {e}")

    # 3. Try tmpfiles.org
    try:
        res = subprocess.run([
            "curl", "-s", "--max-time", "90",
            "-F", f"file=@{file_path}",
            "https://tmpfiles.org/api/v1/upload"
        ], capture_output=True, text=True, timeout=95)
        data = json.loads(res.stdout)
        if data.get("status") == "success" and data.get("data", {}).get("url"):
            raw_url = data["data"]["url"]
            # Convert https://tmpfiles.org/xyz/name.mp4 -> https://tmpfiles.org/dl/xyz/name.mp4
            dl_url = raw_url.replace("tmpfiles.org/", "tmpfiles.org/dl/")
            log(f"Hosted on tmpfiles.org: {dl_url}")
            return dl_url
    except Exception as e:
        log(f"tmpfiles.org failed: {e}")

    raise RuntimeError(f"Failed to host {file_path} across all providers.")

def get_working_models():
    return [
        "google/gemini-3.1-flash-lite",
        "google/gemini-3.5-flash-lite",
        "google/gemini-flash-lite-latest",
        "google/gemini-3.5-flash",
        "google/gemini-3.6-flash",
        "opencode/beam-free",
        "opencode/flint-40b-free",
        "opencode/hy4-flash-free",
        "opencode/iceman-free",
        "opencode/nemotron-3.5-lightning-free",
        "opencode/tidepool-alpha-free",
        "opencode/deepseek-v4.1-flash-free",
        "opencode/mimo-v2.6-flash-free"
    ]

def run_opencode_js(js_code):
    models = get_working_models()
    cli = os.environ.get("OPENCODE_CLI") or shutil.which("opencode-cli") or shutil.which("opencode") or "/Applications/OpenCode.app/Contents/Resources/opencode-cli"
    if not os.path.exists(cli):
        raise FileNotFoundError("OpenCode CLI not found; set OPENCODE_CLI or install opencode-cli")

    prompt = f"Execute the following JavaScript code directly and return the full JSON result:\n```js\n{js_code}\n```"
    last_err = None
    for m in models:
        log(f"Attempting execution with model {m}...")
        try:
            res = subprocess.run([
                cli, "run", "--auto", "--model", m, prompt
            ], capture_output=True, text=True, timeout=120)
            out = (res.stdout or "") + "\n" + (res.stderr or "")
            out_lower = out.lower()
            error_signals = [
                "limit reached",
                "quota exceeded",
                "exceeded your current quota",
                "resource has been exhausted",
                "rate limit",
                "429",
                "500 internal server error",
                "is no longer available",
                "overloaded",
                "credit_balance",
                "insufficient_quota",
                "model unavailable",
                "please update your code"
            ]
            # Immediate check: If the API itself is throttled on Zapier/YouTube side, abort model cycling immediately!
            if any(sig in out_lower for sig in API_THROTTLE_SIGNALS):
                log(f"🛑 [API THROTTLED] YouTube/Zapier rate limit hit: {out[:180].strip()}...")
                raise ApiThrottledError(out)

            if any(err in out_lower for err in error_signals):
                log(f"Model {m} returned quota or system error: {out[:120].strip()}... Trying next...")
                last_err = out
                continue

            has_video_id = bool(re.search(r'watch\?v=([a-zA-Z0-9_-]{11})|"id":\s*"([a-zA-Z0-9_-]{11})"', out))
            has_thumb_ok = ("upload_video_thumbnail" in js_code) and any(k in out for k in ['"url":', '"status":', "success", "default"])

            if has_video_id or has_thumb_ok or ('"status": "success"' in out_lower):
                log(f"Model {m} succeeded.")
                return out

            log(f"Model {m} output did not indicate success: {out[:200].strip()}...")
            last_err = out
        except ApiThrottledError:
            raise
        except Exception as e:
            log(f"Model {m} exception: {e}")
            last_err = str(e)
            continue
    raise RuntimeError(f"All OpenCode models failed. Last error: {last_err}")

def main():
    proj = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "."
    proj = os.path.abspath(proj)
    force = "--force" in sys.argv or "--upload" in sys.argv
    dry_run = ("--dry-run" in sys.argv or os.environ.get("DRY_RUN") == "1") and not force

    script_path = os.path.join(proj, "script.json")
    if not os.path.exists(script_path):
        log(f"No script.json found in {proj}")
        sys.exit(1)

    with open(script_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    title = meta.get("title", "Science Shorts")
    # Enforce title length <= 40 chars
    if len(title) > 40:
        title = title[:37] + "..."

    lang = meta.get("lang", "en")
    is_telugu = (lang == "te") or ("te-IN" in meta.get("voice", ""))
    conn_key = "YOUTUBE_CONNECTION_TE" if is_telugu else "YOUTUBE_CONNECTION_EN"
    conn_id = os.environ.get(conn_key, "").strip()
    channel_name = "asakthi" if is_telugu else "curiography"

    # Find video
    renders_dir = os.path.join(proj, "renders")
    videos = glob.glob(os.path.join(renders_dir, "*.mp4"))
    if not videos:
        log(f"No rendered mp4 found in {renders_dir}")
        sys.exit(1)

    proj_name = os.path.basename(proj)
    named_video = os.path.join(renders_dir, f"{proj_name}.mp4")
    named_web = os.path.join(renders_dir, f"{proj_name}_web.mp4")
    video_web = os.path.join(renders_dir, "video_web.mp4")
    video_mp4 = os.path.join(renders_dir, "video.mp4")

    # Select the most accurate master render file (prefer pre-optimized web render if within 35MB)
    if os.path.exists(named_web) and (os.path.getsize(named_web) / 1024 / 1024 <= 35):
        video_path = named_web
    elif os.path.exists(video_web) and (os.path.getsize(video_web) / 1024 / 1024 <= 35):
        video_path = video_web
    elif os.path.exists(named_video):
        video_path = named_video
    elif os.path.exists(video_mp4):
        video_path = video_mp4
    else:
        videos.sort(key=lambda f: os.path.getmtime(f), reverse=True)
        video_path = videos[0]

    log(f"Selected master video for upload: {os.path.basename(video_path)}")

    # Check size; if > 35MB, optimize for web upload
    size_mb = os.path.getsize(video_path) / 1024 / 1024
    if size_mb > 35:
        log(f"Video is {size_mb:.1f} MB. Optimizing for web upload...")
        opt_path = os.path.join(renders_dir, f"{proj_name}_web.mp4")
        subprocess.run([
            FFMPEG, "-y", "-v", "error", "-i", video_path,
            "-c:v", "libx264", "-crf", "22", "-preset", "fast",
            "-c:a", "copy", opt_path
        ], check=True)
        video_path = opt_path

    # Cover image
    covers_dir = os.path.join(proj, "covers")
    os.makedirs(covers_dir, exist_ok=True)
    cover_path = os.path.join(covers_dir, "cover.jpg")
    if not os.path.exists(cover_path):
        log("Generating cover image...")
        skill_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        make_cover = os.path.join(skill_dir, "scripts", "make_cover.sh")
        c_text = "SCIENCE|SHORTS" if not is_telugu else "తెలుగు|కథ"
        subprocess.run(["bash", make_cover, video_path, cover_path, "10.0", c_text, "96"])

    if dry_run:
        log(f"[DRY-RUN] Ready to upload '{title}' to {channel_name}. Exiting without upload.")
        sys.exit(0)

    if not conn_id:
        log(f"No publishing connection configured for {'Telugu' if is_telugu else 'English'}; set {conn_key} in the ignored .env file.")
        sys.exit(2)

    # 1. Host video & cover
    video_url = host_file(video_path)
    cover_url = host_file(cover_path) if os.path.exists(cover_path) else None

    # 2. Build upload script
    lines_text = " ".join([l.get("text", "") for l in meta.get("lines", [])[:2]])
    desc = f"{lines_text}\n\n#shorts #{'telugu' if is_telugu else 'science'} #viral #facts"
    tags = ["telugu", "shorts", "mythology"] if is_telugu else ["science", "biology", "facts", "shorts", "curiosity"]

    upload_params = {
        "video": video_url,
        "title": title,
        "description": desc,
        "tags": tags,
        "category_id": "23" if is_telugu else "28",
        "privacy_status": "public",
        "made_for_kids": "false",
        "embeddable": "true",
        "notify_subscribers": "true",
        "default_language": lang,
        "default_audio_language": lang,
        "license": "youtube"
    }

    conn_clause = f'connection_id: "{conn_id}",\n' if conn_id else ""
    manage_clause = f'await tools.zapier.manage_zapier_connections({{ selected_api: "YouTubeV4CLIAPI", default_connection_id: "{conn_id}" }});\n' if conn_id else ""
    js_upload = f"""
{manage_clause}const r = await tools.zapier.execute_zapier_write_action({{
  selected_api: "YouTubeV4CLIAPI",
  action: "upload_video",
  {conn_clause}params: {json.dumps(upload_params, indent=2)}
}});
return JSON.stringify(r);
"""
    log(f"Triggering YouTube upload for {channel_name}...")
    try:
        upload_res = run_opencode_js(js_upload)
    except ApiThrottledError as te:
        log(f"🛑 [UPLOAD HALTED] YouTube/Zapier API rate limit encountered. Halting retry loops.")
        log(f"   Video '{title}' remains staged in renders/ and will broadcast in the next slot.")
        ledger_path = str(Path(os.environ.get("PIPELINE_ROOT", Path(__file__).resolve().parents[4])) / "daily" / "topics-done.md")
        if os.path.exists(ledger_path):
            import datetime
            today_str = datetime.date.today().strftime("%Y-%m-%d")
            status_tag = f"UPLOAD PENDING (throttled - {channel_name})" if is_telugu else "UPLOAD PENDING (throttled)"
            style_val = meta.get("style", "tall-tale")
            ledger_line = f"- {today_str} | {title} | {proj_name} | {style_val} | {status_tag} | — | notes: YouTube upload throttled by Zapier API; video staged for broadcast\n"
            with open(ledger_path, "a", encoding="utf-8") as f:
                f.write(ledger_line)
            log(f"Ledger updated with UPLOAD PENDING in {ledger_path}")
        sys.exit(0)

    # Extract video ID
    vid_match = re.search(r'watch\?v=([a-zA-Z0-9_-]{11})|"id":\s*"([a-zA-Z0-9_-]{11})"', upload_res)
    video_id = vid_match.group(1) or vid_match.group(2) if vid_match else None

    if not video_id:
        log(f"Upload finished but could not parse video ID. Raw output:\n{upload_res}")
        sys.exit(1)

    log(f"VIDEO UPLOADED SUCCESSFULLY! Video ID: {video_id} -> https://www.youtube.com/watch?v={video_id}")

    # 3. Upload thumbnail
    if cover_url:
        log("Uploading custom thumbnail...")
        js_thumb = f"""
{manage_clause}const r = await tools.zapier.execute_zapier_write_action({{
  selected_api: "YouTubeV4CLIAPI",
  action: "upload_video_thumbnail",
  {conn_clause}params: {{
    video_id: "{video_id}",
    thumbnail: "{cover_url}"
  }}
}}).catch(e => ({{ error: e.message }}));
return JSON.stringify(r);
"""
        try:
            run_opencode_js(js_thumb)
            log("Custom thumbnail applied.")
        except Exception as e:
            log(f"Thumbnail upload error: {e}")

    # 4. Update ledger
    ledger_path = str(Path(os.environ.get("PIPELINE_ROOT", Path(__file__).resolve().parents[4])) / "daily" / "topics-done.md")
    if os.path.exists(ledger_path):
        proj_name = os.path.basename(proj)
        import datetime
        today_str = datetime.date.today().strftime("%Y-%m-%d")
        status_tag = f"UPLOADED ({channel_name})" if is_telugu else "UPLOADED"
        style_val = meta.get("style") or ("tall-tale" if is_telugu else "deep-dive")
        ledger_line = f"- {today_str} | {title} | {proj_name} | {style_val} | {status_tag} | {video_id}\n"
        with open(ledger_path, "a", encoding="utf-8") as f:
            f.write(ledger_line)
        log(f"Ledger updated in {ledger_path}")

    log("ALL UPLOAD PIPELINE STEPS COMPLETED!")

if __name__ == "__main__":
    main()
