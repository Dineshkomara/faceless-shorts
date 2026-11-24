#!/usr/bin/env python3
"""Broadcast Queue Manager - Staged Pre-Render & Scheduled YouTube Publishing.

Implements the 'Publish-Then-Produce' broadcast architecture:
  1. At trigger time (configured local-time slots): Instantly uploads the pre-rendered video waiting in the queue.
  2. Immediately after upload: Kicks off pipeline to produce & render the video for the NEXT slot.

Usage:
  python3 broadcast_queue.py status              # Show queued videos and next slot info
  python3 broadcast_queue.py broadcast [en|te|all] # Instantly publish queued video(s)
  python3 broadcast_queue.py next-slot           # Print the next target slot identifier
"""

import argparse
import datetime
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from faceless_shorts.config import PATHS

ROOT = PATHS.root
PROJECTS = PATHS.projects
DAILY = PATHS.daily
LEDGER = DAILY / "topics-done.md"
FEEDBACK_LOG = DAILY / "feedback" / "reviews.jsonl"
SKILL = PATHS.skill
if not SKILL.is_dir():
    SKILL = Path.home() / ".config/opencode/skill/faceless-shorts"
UPLOAD_SCRIPT = SKILL / "scripts/upload_youtube.py"
PYTHON_BIN = Path(os.environ.get("PIPELINE_PYTHON", sys.executable))


def get_slot_info():
    """Return the next local-time publish slot from PUBLISH_SLOTS (default: 10,19)."""
    now = datetime.datetime.now()
    try:
        hours = sorted({int(x.strip()) for x in os.environ.get("PUBLISH_SLOTS", "10,19").split(",") if x.strip()})
    except ValueError as exc:
        raise ValueError("PUBLISH_SLOTS must be comma-separated 24-hour clock hours, such as 10,19") from exc
    if not hours or any(hour < 0 or hour > 23 for hour in hours):
        raise ValueError("PUBLISH_SLOTS must contain at least one hour from 0 to 23")

    today_slots = [now.replace(hour=h, minute=0, second=0, microsecond=0) for h in hours]
    upcoming = next((slot for slot in today_slots if slot > now), None)
    if upcoming is not None:
        next_slot = upcoming.strftime("%H:%M (Today)")
        target_hour = upcoming.hour
        passed = [slot for slot in today_slots if slot <= now]
        current_slot = passed[-1].strftime("%H:%M") if passed else "before first slot"
    else:
        target_hour = hours[0]
        next_slot = (today_slots[0] + datetime.timedelta(days=1)).strftime("%H:%M (Tomorrow)")
        current_slot = today_slots[-1].strftime("%H:%M")

    return {
        "current_time": now.strftime("%Y-%m-%d %H:%M:%S"),
        "current_slot": current_slot,
        "next_slot": next_slot,
        "target_hour": target_hour
    }


def load_uploaded_ledger():
    """Parses topics-done.md to find already uploaded project names and video IDs."""
    if not LEDGER.is_file():
        return set()

    text = LEDGER.read_text(encoding="utf-8", errors="replace")
    uploaded = set()
    for line in text.splitlines():
        if not line.startswith("- "):
            continue
        parts = [p.strip() for p in line[2:].split("|")]
        if len(parts) >= 5:
            proj_name = parts[2]
            status = parts[4]
            # If status indicates uploaded and has video ID or UPLOADED tag
            yt_id_match = re.search(r"watch\?v=([a-zA-Z0-9_-]{11})|([a-zA-Z0-9_-]{11})", line)
            if "UPLOADED" in status and yt_id_match and "THROTTLED" not in line:
                uploaded.add(proj_name)
    return uploaded


def get_queued_videos(target_channel="all"):
    """Find ready videos that also passed the strict post-render quality gate."""
    uploaded_projs = load_uploaded_ledger()
    candidates = []

    if not PROJECTS.is_dir():
        return candidates
    for p in PROJECTS.iterdir():
        if not p.is_dir() or p.name.startswith(".") or p.name in {"daily", "dashboard", "node_modules", "vendor"}:
            continue

        script_file = p / "script.json"
        if not script_file.is_file():
            continue

        try:
            meta = json.loads(script_file.read_text(encoding="utf-8"))
        except Exception:
            continue

        # Determine channel
        lang = meta.get("lang", "en")
        voice = meta.get("voice", "")
        is_telugu = (lang == "te") or ("te-IN" in voice) or ("sarvam" in voice) or p.name.endswith("-te")
        proj_channel = "te" if is_telugu else "en"

        if target_channel != "all" and proj_channel != target_channel:
            continue

        # Check for rendered MP4
        renders_dir = p / "renders"
        if not renders_dir.is_dir():
            continue

        mp4s = list(renders_dir.glob("*.mp4"))
        if not mp4s:
            continue

        # Sort MP4s by mtime (most recent)
        mp4s.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        master_mp4 = mp4s[0]

        # Check if already uploaded
        if p.name in uploaded_projs:
            continue

        # Cover check
        cover_file = p / "covers/cover.jpg"
        has_cover = cover_file.is_file()
        if not has_cover:
            continue
        # A render without a passing feedback-loop record cannot be published,
        # even if it has a cover and a completed MP4.
        if not has_quality_pass(p.name):
            continue

        candidates.append({
            "project": p.name,
            "path": str(p),
            "title": meta.get("title", p.name),
            "channel": proj_channel,
            "channel_name": "asakthi" if is_telugu else "curiography",
            "video_path": str(master_mp4),
            "video_size_mb": master_mp4.stat().st_size / (1024 * 1024),
            "mtime": master_mp4.stat().st_mtime,
            "has_cover": has_cover
        })

    # Sort candidates by mtime descending (newest first)
    candidates.sort(key=lambda c: c["mtime"], reverse=True)
    return candidates


def has_quality_pass(project_name):
    if not FEEDBACK_LOG.is_file():
        return False
    latest = None
    for line in FEEDBACK_LOG.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            row = json.loads(line)
        except Exception:
            continue
        if row.get("project") == project_name:
            latest = row
    return bool(latest and latest.get("result") == "PASS")


def broadcast_queued(target_channel="all"):
    """Instantly publishes the queued ready video(s) to YouTube."""
    slot = get_slot_info()
    lock_file = DAILY / ".broadcast.lock"
    try:
        lock_file.write_text(str(os.getpid()))
    except Exception:
        pass

    try:
        print(f"\n=======================================================", flush=True)
        print(f"📡 [BROADCAST QUEUE] Trigger Fired at {slot['current_time']}", flush=True)
        print(f"   Slot: {slot['current_slot']} | Channel Target: {target_channel.upper()}", flush=True)
        print(f"=======================================================", flush=True)

        queued = get_queued_videos(target_channel)
        if not queued:
            print(f"⚠️ [QUEUE EMPTY] No quality-approved pre-rendered videos waiting for channel: {target_channel}", flush=True)
            print("   -> Unreviewed or failed-QA renders are held; pipeline will generate the next video.", flush=True)
            return False

        # Group by channel
        to_publish = {}
        for item in queued:
            ch = item["channel"]
            if ch not in to_publish:
                to_publish[ch] = item

        success_count = 0
        for ch, item in to_publish.items():
            print(f"\n🚀 [INSTANT BROADCAST] Publishing staged video for {item['channel_name'].upper()}:", flush=True)
            print(f"   • Project: {item['project']}", flush=True)
            print(f"   • Title  : {item['title']}", flush=True)
            print(f"   • Video  : {Path(item['video_path']).name} ({item['video_size_mb']:.1f} MB)", flush=True)

            cmd = [
                str(PYTHON_BIN),
                str(UPLOAD_SCRIPT),
                item["path"],
                "--upload",
                "--force"
            ]

            try:
                env = dict(os.environ, PYTHONUNBUFFERED="1")
                proc = subprocess.Popen(
                    cmd,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )
                output_lines = []
                for line in proc.stdout:
                    output_lines.append(line)
                    print(line, end='', flush=True)
                proc.wait(timeout=300)
                output = "".join(output_lines)
                if "API THROTTLED" in output or "UPLOAD HALTED" in output or "UPLOAD PENDING" in output:
                    print(f"⏳ [PENDING] Upload throttled by YouTube/Zapier API rate limit. Staged for next slot.", flush=True)
                elif proc.returncode == 0 and ("watch?v=" in output or "VIDEO UPLOADED SUCCESSFULLY" in output or "UPLOAD SUCCESSFUL" in output):
                    print(f"✅ [PUBLISHED] Successfully uploaded {item['title']} to YouTube!", flush=True)
                    success_count += 1
                else:
                    print(f"⚠️ [UPLOAD FINISHED] Return code: {proc.returncode}", flush=True)
            except Exception as e:
                print(f"❌ [UPLOAD FAILED] Exception: {e}", flush=True)

        return success_count > 0
    finally:
        try:
            lock_file.unlink(missing_ok=True)
        except Exception:
            pass


def print_status():
    slot = get_slot_info()
    print(f"\n📊 [BROADCAST QUEUE STATUS]")
    print(f"   Current Time: {slot['current_time']}")
    print(f"   Current Slot: {slot['current_slot']}")
    print(f"   Next Slot   : {slot['next_slot']}\n")

    queued = get_queued_videos("all")
    if not queued:
        print("   Queue is currently empty (no unuploaded videos waiting).")
        return

    print(f"   📦 {len(queued)} video(s) staged and waiting to broadcast:")
    for idx, q in enumerate(queued, 1):
        ch_flag = "🇮🇳 TELUGU (Asakthi)" if q["channel"] == "te" else "🇬🇧 ENGLISH (Curiography)"
        cover_tag = "✓ Cover ready" if q["has_cover"] else "✗ Missing cover"
        print(f"   {idx}. [{ch_flag}] {q['title']}")
        print(f"      Project : {q['project']}")
        print(f"      File    : {Path(q['video_path']).name} ({q['video_size_mb']:.1f} MB) | {cover_tag}")


def main():
    parser = argparse.ArgumentParser(description="Broadcast Queue Manager")
    parser.add_argument("action", choices=["status", "broadcast", "next-slot", "json"], default="status", nargs="?")
    parser.add_argument("--channel", choices=["en", "te", "all"], default="all")
    args = parser.parse_args()

    if args.action == "status":
        print_status()
    elif args.action == "next-slot":
        slot = get_slot_info()
        print(slot["next_slot"])
    elif args.action == "json":
        slot = get_slot_info()
        queued = get_queued_videos(args.channel)
        print(json.dumps({"slot": slot, "queued": queued}, indent=2))
    elif args.action == "broadcast":
        ok = broadcast_queued(args.channel)
        sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
