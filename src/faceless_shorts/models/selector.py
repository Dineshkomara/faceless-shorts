#!/usr/bin/env python3
"""Pick a working free model from the LIVE OpenCode catalog.

The old runner hardcoded opencode/glm-5.3-flash-free, which disappeared from the catalog and
killed every scheduled run. This asks `opencode models` what exists right now, keeps only
models that are actually free, probes them in parallel, then stores all responsive candidates.
Known free IDs are also probed when the live catalog is temporarily incomplete.

    pick_model.py               -> cached primary if fresh, else probe
    pick_model.py --refresh     -> ignore the cache and probe again
    pick_model.py --list        -> print responsive candidates from the latest probe
"""
import concurrent.futures
import os
import pathlib
import subprocess
import sys
import time
from faceless_shorts.config import PATHS

CLI = os.environ.get("OPENCODE_CLI") or __import__("shutil").which("opencode-cli") or __import__("shutil").which("opencode") or "/Applications/OpenCode.app/Contents/Resources/opencode-cli"
HERE = PATHS.daily
CACHE = PATHS.model_cache / ".model"
CANDIDATE_CACHE = PATHS.model_cache / ".model-candidates"
TTL = 15 * 60            # providers can hit quota inside a longer cache window
PROBE_TIMEOUT = 15      # seconds per probe

# Preference order: Active Google Gemini models first, then known free catalog models.
PREFERRED = [
    "google/gemini-flash-lite-latest",
    "google/gemini-3.1-flash-lite",
    "google/gemini-3.5-flash-lite",
    "google/gemini-3.5-flash",
    "google/gemini-3.6-flash",
    "google/gemini-3-flash-preview",
    "opencode/beam-free",
    "opencode/flint-40b-free",
    "opencode/hy4-flash-free",
    "opencode/iceman-free",
    "opencode/nemotron-3.5-lightning-free",
    "opencode/tidepool-alpha-free",
    "opencode/deepseek-v4.1-flash-free",
    "opencode/mimo-v2.6-flash-free",
    "opencode/longcat-2.5-free",
]

RETIRED = {
    "google/gemini-2.0-flash",
    "google/gemini-2.5-pro",
    "google/gemini-1.5-pro",
    "google/gemini-2.5-flash",
    "google/gemini-2.5-flash-lite",
    "google/gemini-2.5-computer-use-preview-10-2025",
    "opencode/gemini-2.0-flash-free",
}


def catalog():
    if not CLI or (CLI.startswith("/") and not pathlib.Path(CLI).exists()):
        raise RuntimeError("OpenCode CLI not found; set OPENCODE_CLI or install opencode-cli")
    out = subprocess.run([CLI, "models"], capture_output=True, text=True, timeout=90).stdout
    return [line.strip() for line in out.splitlines() if line.strip() and line.strip() not in RETIRED]


def free_models(models):
    # Include explicitly free models as well as active Gemini models configured in the environment
    free = [m for m in models if (m.endswith("-free") or "gemini" in m.lower()) and m not in RETIRED]
    ordered = [m for m in PREFERRED if m in free]
    ordered += [m for m in free if m not in ordered]
    return ordered


def candidates(models):
    """Use the live catalog first, then probe known free IDs if it is incomplete."""
    ordered = free_models(models)
    ordered += [m for m in PREFERRED if m not in ordered and m not in RETIRED]
    return ordered


def read_cache():
    try:
        raw = CACHE.read_text().strip().split("|")
        return raw[0], float(raw[1])
    except Exception:
        return None, 0.0


def write_cache(model):
    try:
        CACHE.write_text(f"{model}|{time.time()}\n")
    except Exception:
        pass


def read_candidate_cache():
    try:
        lines = CANDIDATE_CACHE.read_text().splitlines()
        when = float(lines[0])
        if time.time() - when < TTL:
            return lines[1:]
    except Exception:
        pass
    return None


def write_candidate_cache(models):
    try:
        CANDIDATE_CACHE.write_text(f"{time.time()}\n" + "\n".join(models) + "\n")
    except Exception:
        pass


def probe(model):
    """True when the model answers a trivial prompt. Free catalogs list models that 404 or hit quotas."""
    try:
        r = subprocess.run(
            [CLI, "run", "--model", model, "Reply with exactly: READY"],
            capture_output=True, text=True, timeout=PROBE_TIMEOUT, cwd="/tmp",
        )
        if r.returncode != 0:
            return False
        text = ((r.stdout or "") + (r.stderr or "")).lower()
        error_signals = [
            "model unavailable",
            "credit_balance",
            "usage limit",
            "rate limit",
            "quota",
            "429",
            "500 internal server error",
            "insufficient_quota",
            "free usage",
            "no longer available",
            "retry in",
        ]
        if any(sig in text for sig in error_signals):
            return False
        return "READY" in (r.stdout or "").upper()
    except Exception:
        return False


def pick(ordered):
    """Probe in parallel and return every responsive model in preference order."""
    if not ordered:
        return []
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(probe, m): m for m in ordered}
        for fut in concurrent.futures.as_completed(futures):
            m = futures[fut]
            try:
                results[m] = fut.result()
            except Exception:
                results[m] = False
    return [m for m in ordered if results.get(m)]  # preference order wins over response time


def provider_diverse(models):
    """Keep the preferred model first, then try other providers before same-provider fallbacks."""
    if len(models) < 2:
        return models
    primary_provider = models[0].split('/', 1)[0]
    other_providers = [m for m in models[1:] if m.split('/', 1)[0] != primary_provider]
    same_provider = [m for m in models[1:] if m.split('/', 1)[0] == primary_provider]
    return [models[0], *other_providers, *same_provider]


def main():
    args = set(sys.argv[1:])
    if "--list" in args:
        available = read_candidate_cache()
        if available is None:
            available = candidates(catalog())
        print("\n".join(available))
        return 0

    models = catalog()
    pool = candidates(models)

    if "--refresh" not in args:
        cached, when = read_cache()
        if cached and time.time() - when < TTL and cached in pool:
            print(cached)
            return 0

    if not pool:
        print("no candidate models are configured", file=sys.stderr)
        return 1

    available = pick(pool)
    available = provider_diverse(available)
    write_candidate_cache(available)
    if not available:
        print("every candidate model failed the availability probe", file=sys.stderr)
        return 1
    chosen = available[0]
    write_cache(chosen)
    print(chosen)
    return 0


if __name__ == "__main__":
    sys.exit(main())
