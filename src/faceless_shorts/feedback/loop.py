#!/usr/bin/env python3
"""Strict visual/content QA gate and per-channel learning notes for scheduled videos."""
import argparse
import json
import re
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path
from faceless_shorts.config import PATHS

ROOT = PATHS.projects
DAILY = PATHS.daily
LOG = DAILY / "feedback" / "reviews.jsonl"
PERF = PATHS.dashboard / "perf.json"
LIBRARY_INDEX = PATHS.asset_library / "index.json"
SCORE_KEYS = ("hook", "concept_clarity", "evidence", "pacing", "visual_cleanliness",
              "caption_legibility", "shot_variety", "audio_naturalness", "payoff")
CHECK_KEYS = ("visual_noise_pass", "no_collisions", "mobile_safe_area", "narration_clear",
              "music_below_narration", "clipping_free", "facts_supported",
              "story_is_factual_or_labeled_illustration", "export_valid", "cover_matches_video")


def under_root(path):
    resolved = Path(path).resolve()
    if resolved != ROOT and ROOT not in resolved.parents:
        raise ValueError(f"Project must be inside the configured project directory {ROOT}: {resolved}")
    return resolved


def records():
    if not LOG.is_file():
        return []
    out = []
    for line in LOG.read_text(errors="replace").splitlines():
        try:
            out.append(json.loads(line))
        except Exception:
            continue
    return out


def append_record(rec):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def path_exists(project, rel):
    if not isinstance(rel, str) or not rel:
        return False
    path = (project / rel).resolve()
    return (path == project or project in path.parents) and path.is_file()


def check_report(project):
    errors = []
    report_path = project / "review" / "quality_review.json"
    if not report_path.is_file():
        return None, ["Missing review/quality_review.json"]
    try:
        review = json.loads(report_path.read_text())
    except Exception as e:
        return None, [f"Cannot parse quality review JSON: {e}"]

    evidence = review.get("evidence", {})
    board_path = project / "review" / "production_board.md"
    if not board_path.is_file():
        errors.append("The detailed review/production_board.md is missing")
    else:
        board = board_path.read_text(errors="replace")
        shot_source = project / "src" / "shots.js"
        if shot_source.is_file():
            shot_ids = set(re.findall(r"\bid\s*:\s*['\"]([A-Za-z0-9_-]+)['\"]", shot_source.read_text(errors="replace")))
            missing_shots = sorted(shot_id for shot_id in shot_ids if shot_id not in board)
            if not shot_ids:
                errors.append("src/shots.js contains no stable shot IDs to audit against the production board")
            elif missing_shots:
                errors.append("Production board is missing shot IDs: " + ", ".join(missing_shots))
    if not path_exists(project, evidence.get("contact_sheet")):
        errors.append("The final review contact sheet is missing")
    if not list((project / "renders").glob("*.mp4")):
        errors.append("The final rendered MP4 is missing")
    if not path_exists(project, "covers/cover.jpg"):
        errors.append("The final cover is missing")
    frames = evidence.get("reviewed_frames", [])
    valid_frames = [f for f in frames if path_exists(project, f)] if isinstance(frames, list) else []
    if len(valid_frames) < 5:
        errors.append("Record at least five existing full-size frames reviewed from distinct beats/sets")
    for key in ("narration_checked", "mix_checked"):
        if evidence.get(key) is not True:
            errors.append(f"evidence.{key} must be true after listening to the final audio")

    scores = review.get("scores", {})
    valid_scores = []
    for key in SCORE_KEYS:
        value = scores.get(key)
        if not isinstance(value, (int, float)) or isinstance(value, bool) or not 1 <= value <= 5:
            errors.append(f"scores.{key} must be a number from 1 to 5")
        else:
            valid_scores.append(float(value))
            if value < 4:
                errors.append(f"scores.{key} is below the strict minimum of 4/5")
    if isinstance(scores.get("visual_cleanliness"), (int, float)) and scores["visual_cleanliness"] != 5:
        errors.append("visual_cleanliness must be 5/5; simplify any busy frame and inspect again")
    if valid_scores and statistics.mean(valid_scores) < 4.5:
        errors.append("Average quality score must be at least 4.5/5")

    checks = review.get("checks", {})
    for key in CHECK_KEYS:
        if checks.get(key) is not True:
            errors.append(f"checks.{key} must pass")
    if review.get("major_issues") != []:
        errors.append("major_issues must be an empty list; fix blocking issues before staging")

    script_path = project / "script.json"
    try:
        script = json.loads(script_path.read_text())
    except Exception as e:
        script = {}
        errors.append(f"Cannot read script.json sources: {e}")
    sources = script.get("sources", [])
    valid_sources = [s for s in sources if isinstance(s, dict) and s.get("title") and s.get("url", "").startswith(("https://", "http://"))] if isinstance(sources, list) else []
    if len({s["url"] for s in valid_sources}) < 2:
        errors.append("script.json needs at least two distinct source objects with title and direct URL")

    assets = review.get("asset_library", {})
    if not isinstance(assets.get("queries"), list) or not assets["queries"]:
        errors.append("Record at least one asset-library search query")
    try:
        known = {a.get("id") for a in json.loads(LIBRARY_INDEX.read_text()).get("assets", [])}
    except Exception:
        known = set()
    for key in ("reused_ids", "archived_ids"):
        ids = assets.get(key, [])
        if not isinstance(ids, list):
            errors.append(f"asset_library.{key} must be a list")
            continue
        missing = [x for x in ids if x not in known]
        if missing:
            errors.append(f"asset_library.{key} references IDs not in the library: {', '.join(missing)}")

    lesson = review.get("next_improvement", "").strip()
    if len(lesson) < 16:
        errors.append("next_improvement must name one specific action for the next video")
    return review, errors


def record_qa(args):
    project = under_root(args.project)
    review, errors = check_report(project)
    passed = not errors
    if review is None:
        review = {}
    review["gate_status"] = "PASS" if passed else "FAIL"
    review["gate_checked_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    if not passed:
        review["gate_failures"] = errors
    else:
        review.pop("gate_failures", None)
    (project / "review").mkdir(exist_ok=True)
    (project / "review" / "quality_review.json").write_text(json.dumps(review, indent=2, ensure_ascii=False) + "\n")
    rec = {
        "project": project.name, "channel": args.channel, "result": "PASS" if passed else "FAIL",
        "checked_at": review["gate_checked_at"], "next_improvement": review.get("next_improvement", ""),
        "scores": review.get("scores", {}), "failures": errors,
    }
    append_record(rec)
    if passed:
        print(f"QUALITY GATE PASS: {project.name}. Approved for staging.")
    else:
        print(f"QUALITY GATE FAIL: {project.name}. Do not stage or broadcast.")
        for issue in errors:
            print(f"- {issue}")
    return 0 if passed else 1


def perf_data(channel):
    if not PERF.is_file():
        return []
    try:
        items = json.loads(PERF.read_text())
    except Exception:
        return []
    rows = []
    for row in items if isinstance(items, list) else []:
        ch = row.get("channel") or ("te" if "asakthi" in row.get("status", "").lower() or row.get("title", "").startswith("తెలుగు") else "en")
        if ch in ("asakthi", "telugu"):
            ch = "te"
        elif ch in ("curiography", "english"):
            ch = "en"
        if ch != channel or not row.get("video_id"):
            continue
        metrics = {k: row.get(k) for k in ("views", "ctr", "retention", "likes", "comments")}
        if any(isinstance(v, (int, float)) for v in metrics.values()):
            rows.append({"video_id": row["video_id"], "title": row.get("title", ""), "metrics": metrics})
    return rows


def sync_ledger_to_performance():
    """Seed missing uploaded videos while preserving any metrics entered in the Dashboard."""
    if not PERF.exists():
        rows = []
    else:
        try:
            rows = json.loads(PERF.read_text())
        except Exception:
            rows = []
    if not isinstance(rows, list):
        rows = []
    seen = {r.get("video_id"): r for r in rows if isinstance(r, dict) and r.get("video_id")}
    if not (DAILY / "topics-done.md").is_file():
        return
    changed = False
    for line in (DAILY / "topics-done.md").read_text(errors="replace").splitlines():
        if not line.startswith("- "):
            continue
        parts = [p.strip() for p in line[2:].split("|")]
        if len(parts) < 5:
            continue
        match = re.search(r"\b[A-Za-z0-9_-]{11}\b", line)
        if not match:
            continue
        vid = match.group(0)
        project = parts[2]
        channel = "te" if project.endswith("-te") else "en"
        status = next((p for p in parts[3:] if "UPLOADED" in p.upper()), "UPLOADED")
        rec = seen.get(vid)
        if rec is None:
            rec = {"video_id": vid, "date": parts[0], "title": parts[1], "project": project,
                   "style": parts[3] if len(parts) >= 6 else "", "status": status,
                   "channel": channel, "views": None, "ctr": None, "retention": None,
                   "likes": None, "comments": None, "hook_angle": ""}
            rows.append(rec); seen[vid] = rec; changed = True
        else:
            # Update metadata only; never erase a metric entered in the UI.
            for key, value in (("title", parts[1]), ("project", project), ("status", status), ("channel", channel)):
                if value and rec.get(key) != value:
                    rec[key] = value; changed = True
    if changed:
        PERF.parent.mkdir(parents=True, exist_ok=True)
        temp = PERF.with_suffix(".tmp")
        temp.write_text(json.dumps(rows, indent=1, ensure_ascii=False) + "\n")
        temp.replace(PERF)


def guidance(args):
    sync_ledger_to_performance()
    all_records = [r for r in records() if r.get("channel") == args.channel]
    latest = all_records[-1] if all_records else None
    print(f"Channel: {args.channel}; reviewed projects on record: {len(all_records)}")
    if latest:
        print(f"Latest QA: {latest.get('project')} — {latest.get('result')}")
        if latest.get("failures"):
            print("Fix these previous blockers first: " + "; ".join(latest["failures"][:4]))
        if latest.get("next_improvement"):
            print("Carry forward this single improvement: " + latest["next_improvement"])
    else:
        print("No QA history yet; use a strict first-run baseline and write the first next_improvement.")
    data = perf_data(args.channel)
    if len(data) >= 3:
        latest_metrics = data[-1]
        print(f"Audience data ({len(data)} videos with manually entered metrics): latest is {latest_metrics['title'] or latest_metrics['video_id']} {latest_metrics['metrics']}.")
        for metric, action in (("retention", "tighten the mid-video visual/story transitions"), ("ctr", "test a more concrete title/cover promise")):
            values = [d["metrics"].get(metric) for d in data[-6:]]
            values = [float(v) for v in values if isinstance(v, (int, float))]
            if len(values) >= 3 and values[-1] < statistics.median(values[:-1]) * 0.9:
                print(f"Data-led focus: latest {metric} is more than 10% below the recent median; {action}.")
                break
        else:
            print("No clear retention/CTR regression versus this channel's recent median; do not overfit a small sample.")
    else:
        print("Audience performance is not yet sufficient for trend claims. Enter views/CTR/retention in the Dashboard Performance tab; use the QA review until at least three videos have metrics.")
    if latest is None or latest.get("result") == "PASS":
        print("Required before render release: all nine scores >=4/5, visual_cleanliness=5/5, no major issues, evidence+mix listened, two source URLs, 5 reviewed frames, and an asset-library search.")
    return 0


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    q = sub.add_parser("record-qa", help="Validate and log a strict post-render quality review")
    q.add_argument("--project", required=True)
    q.add_argument("--channel", choices=["en", "te"], required=True)
    q.set_defaults(func=record_qa)
    g = sub.add_parser("guidance", help="Summarize past quality and audience signals for the next run")
    g.add_argument("--channel", choices=["en", "te"], required=True)
    g.set_defaults(func=guidance)
    args = p.parse_args()
    try:
        sys.exit(args.func(args))
    except Exception as e:
        print(f"feedback-loop: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
