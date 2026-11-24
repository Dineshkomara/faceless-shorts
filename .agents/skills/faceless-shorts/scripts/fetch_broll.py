#!/usr/bin/env python3
"""Fetch realistic B-roll stock footage or photography for each shot in a faceless-short project.

Integrates OpenMontage stock sources (Wikimedia Commons, NASA, Openverse, LOC) and Pexels/Pixabay APIs.
Crops and scales media into 1080x1920 vertical shorts format and writes metadata to data/broll.json.

Usage:
  scripts/py scripts/fetch_broll.py <project_dir>
"""

import json, os, re, subprocess, sys
from pathlib import Path
import urllib.parse
import urllib.request

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
HOME = Path(os.environ.get('FACELESS_HOME', Path.home() / '.faceless-shorts'))
OPENMONTAGE_DIR = Path(os.environ.get('OPENMONTAGE_DIR', os.environ.get('PIPELINE_ROOT', Path(__file__).resolve().parents[4])))

def get_env_key(key):
    if os.environ.get(key):
        return os.environ.get(key)
    for env_path in [Path(os.environ.get("PIPELINE_ROOT", Path(__file__).resolve().parents[4])) / ".env", HOME / ".env", OPENMONTAGE_DIR / ".env"]:
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if line.startswith(f"{key}="):
                    val = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if val and not val.startswith("your-"):
                        return val
    return None

def extract_keywords(text):
    clean = re.sub(r'[^a-zA-Z0-9\s]', ' ', text).lower()
    stop_words = {
        'the', 'and', 'for', 'with', 'that', 'this', 'from', 'into', 'its', 'their', 'about',
        'over', 'under', 'while', 'during', 'your', 'you', 'our', 'are', 'was', 'were', 'have',
        'has', 'had', 'what', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few',
        'more', 'most', 'some', 'such', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 'can',
        'will', 'just', 'should', 'now', 'part', 'turns', 'keeps', 'figure', 'figured', 'because',
        'they', 'them', 'these', 'those', 'also', 'even', 'then', 'here', 'there', 'really'
    }
    tokens = [w for w in clean.split() if len(w) > 3 and w not in stop_words]
    return ' '.join(tokens[:3]) or clean.strip()[:30]

def search_wikimedia(query):
    clean_q = ' '.join([w for w in query.split() if len(w) > 2][:3])
    url = f"https://commons.wikimedia.org/w/api.php?action=query&format=json&generator=search&gsrsearch={urllib.parse.quote(clean_q)}&gsrnamespace=6&gsrlimit=15&prop=imageinfo&iiprop=url|mime|size"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            pages = data.get('query', {}).get('pages', {})
            candidates = []
            for p in pages.values():
                info = p.get('imageinfo', [{}])[0]
                mime = info.get('mime', '')
                furl = info.get('url', '')
                if furl and ('image/' in mime or 'video/' in mime):
                    if 'svg' in mime:
                        continue
                    candidates.append({
                        'url': furl,
                        'mime': mime,
                        'width': info.get('width', 0),
                        'height': info.get('height', 0),
                        'source': 'wikimedia'
                    })
            return candidates
    except Exception as e:
        print(f"  [wikimedia error: {e}]", file=sys.stderr)
        return []

def search_openmontage_sources(query):
    if not OPENMONTAGE_DIR.exists():
        return []
    try:
        if str(OPENMONTAGE_DIR) not in sys.path:
            sys.path.insert(0, str(OPENMONTAGE_DIR))
        from tools.video.stock_sources import available_sources, SearchFilters
        sources = available_sources()
        f = SearchFilters(kind='image', per_page=4)
        for s in sources:
            if s.name in ('nasa', 'openverse', 'loc'):
                try:
                    res = s.search(query, f)
                    if res:
                        cands = []
                        for r in res:
                            durl = getattr(r, 'download_url', None) or getattr(r, 'url', None)
                            if durl:
                                cands.append({
                                    'url': durl,
                                    'mime': 'image/jpeg',
                                    'width': getattr(r, 'width', 1080),
                                    'height': getattr(r, 'height', 1920),
                                    'source': f"openmontage:{s.name}"
                                })
                        if cands:
                            return cands
                except Exception:
                    pass
    except Exception:
        pass
    return []

def search_pexels(query, api_key):
    url = f"https://api.pexels.com/videos/search?query={urllib.parse.quote(query)}&orientation=portrait&per_page=5"
    req = urllib.request.Request(url, headers={"Authorization": api_key, "User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            candidates = []
            for v in data.get('videos', []):
                vfiles = v.get('video_files', [])
                if vfiles:
                    best = max(vfiles, key=lambda f: f.get('width', 0))
                    candidates.append({
                        'url': best.get('link'),
                        'mime': 'video/mp4',
                        'width': best.get('width', 0),
                        'height': best.get('height', 0),
                        'duration': v.get('duration', 0),
                        'source': 'pexels'
                    })
            return candidates
    except Exception as e:
        print(f"  [pexels error: {e}]", file=sys.stderr)
        return []

def download_file(url, out_path):
    cmd = [
        'curl', '-sL', '-f', '--max-time', '25',
        '-A', USER_AGENT,
        url, '-o', str(out_path)
    ]
    subprocess.run(cmd, check=True)

def process_media_to_vertical(in_path, out_path, is_video=False, duration=5.0):
    """Normalize input image/video to 1080x1920 vertical format with smart color grading."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if is_video:
        cmd = [
            'ffmpeg', '-y', '-i', str(in_path),
            '-t', str(duration),
            '-vf', 'scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,eq=contrast=1.05:brightness=0.01:saturation=1.10',
            '-c:v', 'libx264', '-preset', 'fast', '-crf', '21',
            '-an', str(out_path)
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    else:
        # High quality 1080x1920 JPEG still with film color grading
        cmd = [
            'ffmpeg', '-y', '-ss', '00:00:01', '-i', str(in_path),
            '-vf', 'scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,eq=contrast=1.06:saturation=1.08',
            '-frames:v', '1',
            str(out_path)
        ]
        r = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if r.returncode != 0:
            cmd2 = [
                'ffmpeg', '-y', '-i', str(in_path),
                '-vf', 'scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,eq=contrast=1.06:saturation=1.08',
                '-frames:v', '1',
                str(out_path)
            ]
            subprocess.run(cmd2, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

def main():
    if len(sys.argv) < 2:
        print("Usage: fetch_broll.py <project_dir>", file=sys.stderr)
        sys.exit(1)

    P = Path(sys.argv[1]).resolve()
    script_path = P / 'script.json'
    if not script_path.exists():
        print(f"Error: {script_path} missing", file=sys.stderr)
        sys.exit(1)

    S = json.loads(script_path.read_text())
    lines = S.get('lines', [])
    if not lines:
        print("No lines in script.json")
        return

    broll_dir = P / 'assets/broll'
    broll_dir.mkdir(parents=True, exist_ok=True)

    pexels_key = get_env_key('PEXELS_API_KEY')
    broll_manifest = []

    print(f"=== Sourcing Cinematic B-Roll for {len(lines)} shots in {P.name} ===")
    for i, line in enumerate(lines):
        query = line.get('broll') or extract_keywords(line.get('text', ''))
        print(f"Shot {i:02d}: query='{query}'...", end=" ", flush=True)

        candidates = []
        if pexels_key:
            candidates = search_pexels(query, pexels_key)

        if not candidates:
            candidates = search_wikimedia(query)

        if not candidates:
            candidates = search_openmontage_sources(query)

        if not candidates:
            topic = S.get('topic', 'science nature space psychology')
            fallback_query = extract_keywords(topic)
            candidates = search_wikimedia(fallback_query)

        success = False
        for cand in candidates:
            is_video = 'video' in cand['mime']
            raw_ext = '.mp4' if is_video else '.jpg'
            raw_file = broll_dir / f"_raw_{i:02d}{raw_ext}"
            final_img = broll_dir / f"broll_{i:02d}.jpg"
            final_vid = broll_dir / f"broll_{i:02d}.mp4" if is_video else None

            try:
                download_file(cand['url'], raw_file)
                # Ensure downloaded file is not an HTML error
                with open(raw_file, 'rb') as rf:
                    head = rf.read(512)
                    if b'<html' in head.lower() or b'<!doctype' in head.lower():
                        try: raw_file.unlink()
                        except Exception: pass
                        continue

                # Always render 1080x1920 JPEG still for fast canvas drawing
                process_media_to_vertical(raw_file, final_img, is_video=False)
                # If video, also normalize 1080x1920 MP4 clip
                if is_video and final_vid:
                    try: process_media_to_vertical(raw_file, final_vid, is_video=True)
                    except Exception: final_vid = None
                try: raw_file.unlink()
                except Exception: pass

                print(f"OK ({cand['source']}, {final_img.name})")
                entry = {
                    "shot": i,
                    "query": query,
                    "source": cand['source'],
                    "file": str(final_img.relative_to(P)),
                    "type": "image"
                }
                if is_video and final_vid and final_vid.exists():
                    entry["video_file"] = str(final_vid.relative_to(P))
                broll_manifest.append(entry)
                success = True
                break
            except Exception:
                try: raw_file.unlink()
                except Exception: pass
                continue

        if not success:
            print("No working media candidate found")

    (P / 'data').mkdir(parents=True, exist_ok=True)
    (P / 'data/broll.json').write_text(json.dumps(broll_manifest, indent=2))
    print(f"=== B-roll complete: {len(broll_manifest)} clips saved to {broll_dir} ===")

if __name__ == '__main__':
    main()
