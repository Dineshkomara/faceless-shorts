#!/usr/bin/env python3
"""Faceless-shorts Dual-Channel Pipeline Dashboard & Studio — stdlib only.

Serves on 127.0.0.1:8788 (managed by com.dinesh.facesshorts.dashboard.plist).
Supports both channels:
  1. Curiography (English) - Runnable styles (engineering-explainer, tall-tale, cinematic-what-if)
  2. Asakthi (Telugu)      - Tall-tale style with deity character rules (Ramayana, Mahabharata, traditions)
"""

import datetime
import html
import json
import os
import re
import signal
import subprocess
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from faceless_shorts.config import PATHS

for _p in ['/opt/homebrew/bin', '/usr/local/bin', str(Path.home() / '.local/bin'), str(Path.home() / '.gemini/antigravity/bin')]:
    if _p not in os.environ.get('PATH', ''):
        os.environ['PATH'] = f"{_p}:{os.environ.get('PATH', '')}"

HOME = Path.home()
ROOT = PATHS.root
PROJECTS = PATHS.projects
EN_CHANNEL_NAME = os.environ.get('EN_CHANNEL_NAME', 'Curiography')
TE_CHANNEL_NAME = os.environ.get('TE_CHANNEL_NAME', 'Asakthi')
DAILY = PATHS.daily
LOGS = DAILY / 'logs'
LEDGER = DAILY / 'topics-done.md'
RUNNER = DAILY / 'run-daily.sh'
PERF = PATHS.dashboard / 'perf.json'
SKILL = PATHS.skill
if not SKILL.is_dir():
    SKILL = HOME / '.config/opencode/skill/faceless-shorts'
PY = SKILL / 'scripts/py'
STATIC = Path(__file__).with_name('static')
TEXT_EXT = {'.json', '.js', '.mjs', '.md', '.txt', '.py', '.sh', '.css', '.html'}
SKIP_DIRS = {'node_modules', 'review', 'covers', 'renders', 'audio', '.git', '.agents'}
ANSI = re.compile(r'\x1b\[[0-9;]*[A-Za-z]')


def resolve_project(name):
    """Resolve a project name as a direct child of the configured output folder."""
    if not name:
        return None
    base = PROJECTS.resolve()
    candidate = (base / name).resolve()
    if candidate.parent != base:
        return None
    return candidate

EN_STAGES = [
    ('topic',       'Topic & Style Hunt',       [r'new_video\.sh\s+(engineering-explainer|tall-tale|cinematic-what-if)\s+daily-\d+(?!-te)', r'STYLE ROTATION', r'topic hunt', r'CRAFT 1/8']),
    ('scaffold',    'Project Scaffold',         [r'new_video\.sh\s+\S+\s+daily-\d+(?!-te)', r'daily-\d{8}\b(?!-te)']),
    ('voice',       'Voice & Casting (Neural/Sarvam)', [r'narration\.wav \(', r'kokoro', r'\[2/13\] Voiceover', r'CRAFT 2/8', r'dialogue_engine', r'sarvam']),
    ('words',       'Word Timing (Whisper)',    [r'words\.json: ', r'data/words\.txt', r'\[3/13\] Word-level timing']),
    ('characters',  'Character Design & Assets',[r'\[4/13\] Character Design', r'setup_characters\.py', r'characters\.json', r'CRAFT 3/8']),
    ('backgrounds', 'Atmospheric Environments', [r'\[5/13\] Background Setup', r'setup_backgrounds\.py', r'backgrounds\.json', r'CRAFT 4/8']),
    ('check',       'Directing & Camera Check', [r'CHECK OK', r'CHECK FAILED', r'\[6/13\] Engine check', r'CRAFT 5/8']),
    ('cues',        'Sound Cues & Foley',       [r'cues\.json: ', r'\[7/13\] Extract sound cues', r'CRAFT 6/8']),
    ('pacing',      'Pacing Gate & Cuts',       [r'PACING OK', r'PACING: ', r'\[8/13\] Pacing analysis', r'CRAFT 7/8.*pacing']),
    ('mix',         'Sound & Music Mix',        [r'mix\.wav: ', r'\[9/13\] Sound mix', r'CRAFT 6/8.*Mix']),
    ('sheet',       'QA Contact Sheet',         [r'all\.jpg \(', r'\[10/13\] QA Contact sheet', r'CRAFT 7/8.*sheet']),
    ('render',      'Render Cinema MP4',        [r'renders/\S+\.mp4', r'renders/video\.mp4', r'\[11/13\] Video render', r'CRAFT 8/8.*MP4']),
    ('cover',       'Cover Image',              [r'cover: covers/cover\.jpg', r'make_cover\.sh.*renders/daily-\d+\.mp4', r'\[12/13\] Cover generation', r'CRAFT 8/8.*Cover']),
    ('upload',      'Upload → Curiography',     [r'watch\?v=[A-Za-z0-9_-]{11}(?!.*asakthi)', r'UPLOADED(?!\s*\(asakthi\))', r'\[13/13\] Automated YouTube upload', r'CRAFT 8/8.*Upload']),
    ('comment',     'Comment Seeded',           [r'commentThreads']),
    ('ledger',      'Ledger Updated',           [r'topics-done\.md']),
    ('end',         'Run Complete',             [r'run end, exit=(\d+)', r'BUILD & UPLOAD PIPELINE COMPLETE']),
]
EN_STAGES = [(sid, title.replace('Curiography', EN_CHANNEL_NAME), pats) for sid, title, pats in EN_STAGES]

TE_STAGES = [
    ('topic',       'Topic & Visual Style',     [r'Telugu', r'asakthi', r'deity', r'DEITIES\.md', r'new_video\.sh.*-te', r'CRAFT 1/8']),
    ('scaffold',    'Project Scaffold (-te)',   [r'new_video\.sh.*-te', r'scaffold.*-te']),
    ('voice',       'Telugu Voice (Sarvam/Neural)', [r'sarvam', r'bulbul', r'te-IN-MohanNeural', r'te-IN-ShrutiNeural', r'te_IN-venkatesh', r'piper_say', r'vocal_master', r'\[2/13\] Voiceover', r'CRAFT 2/8', r'dialogue_engine']),
    ('words',       'Word Timing (Whisper te)', [r'words\.json.*-te', r'-te/data/words\.json', r'\[3/13\] Word-level timing']),
    ('characters',  'Character Design & Sprites',[r'\[4/13\] Character Design', r'setup_characters\.py', r'characters\.json', r'CRAFT 3/8']),
    ('backgrounds', 'Atmospheric Environments', [r'\[5/13\] Background Setup', r'setup_backgrounds\.py', r'backgrounds\.json', r'CRAFT 4/8']),
    ('check',       'Directing & Camera Check', [r'DEITIES\.md', r'CHECK OK.*-te', r'\[6/13\] Engine check', r'CRAFT 5/8']),
    ('cues',        'Sound Cues & Foley',       [r'cues\.json.*-te', r'-te/data/cues\.json', r'\[7/13\] Extract sound cues', r'CRAFT 6/8']),
    ('pacing',      'Pacing Gate & Cuts',       [r'PACING OK.*-te', r'\[8/13\] Pacing analysis', r'CRAFT 7/8.*pacing']),
    ('mix',         'Sound Mix',                [r'mix\.wav.*-te', r'-te/data/mix\.wav', r'\[9/13\] Sound mix', r'CRAFT 6/8.*Mix']),
    ('sheet',       'QA Contact Sheet',         [r'all\.jpg.*-te', r'-te/review/all\.jpg', r'\[10/13\] QA Contact sheet', r'CRAFT 7/8.*sheet']),
    ('render',      'Render Cinema MP4',        [r'renders/.*-te\.mp4', r'-te/renders', r'\[11/13\] Video render', r'CRAFT 8/8.*MP4']),
    ('cover',       'Cover Image (Telugu)',     [r'-te/covers/cover\.jpg', r'make_cover\.sh.*-te', r'\[12/13\] Cover generation', r'CRAFT 8/8.*Cover']),
    ('upload',      'Upload → Asakthi',         [r'asakthi.*watch\?v=', r'UPLOADED \(asakthi\)', r'\[13/13\] Automated YouTube upload', r'CRAFT 8/8.*Upload']),
    ('comment',     'Telugu Comment Seeded',    [r'commentThreads.*asakthi', r'జై\s*హనుమాన్', r'కామెంట్']),
    ('ledger',      'Ledger Updated',           [r'topics-done\.md.*asakthi']),
    ('end',         'Run Complete',             [r'run end, exit=(\d+)', r'BUILD & UPLOAD PIPELINE COMPLETE']),
]
TE_STAGES = [(sid, title.replace('Asakthi', TE_CHANNEL_NAME), pats) for sid, title, pats in TE_STAGES]


def today():
    return datetime.date.today().isoformat()


def latest_log_date():
    if not LOGS.exists():
        return today()
    run_logs = [x.stem for x in LOGS.glob('*.log') if re.fullmatch(r'\d{4}-\d{2}-\d{2}', x.stem)]
    return max(run_logs) if run_logs else today()


def block_for_date(date):
    f = LOGS / f'{date}.log'
    if not f.exists():
        return '', ''
    try:
        text = f.read_text(errors='replace')
    except Exception:
        return '', ''
    matches = list(re.finditer(r'===== .*run start.*=====', text))
    if not matches:
        return text, ''
    # Find the latest non-skipped run start block
    active_start = None
    for m in reversed(matches):
        block_sample = text[m.start():m.start() + 400]
        if 'skipped: a previous run is still active' not in block_sample:
            active_start = m.start()
            break
    if active_start is None:
        active_start = matches[-1].start()
    return text[active_start:], text


def latest_run_failure(date, is_telugu=False):
    """Summarize the latest failed run for a channel so IDLE doesn't hide a failure."""
    f = LOGS / f'{date}.log'
    if not f.exists():
        return None
    try:
        text = ANSI.sub('', f.read_text(errors='replace'))
    except Exception:
        return None
    starts = list(re.finditer(r'===== .*?run start \([^\n]*?CHANNEL=(en|te|all)[^\n]*?=====\s*', text, re.IGNORECASE))
    target = 'te' if is_telugu else 'en'
    for start in reversed(starts):
        channel = start.group(1).lower()
        if channel not in (target, 'all'):
            continue
        tail = text[start.end():]
        end = re.search(r'===== .*?run end, exit=(\d+) =====', tail)
        if not end:
            return None  # active run; report its live state instead
        code = int(end.group(1))
        if code == 0:
            return None
        segment = tail[:end.start()]
        reasons = []
        if re.search(r'quota|rate.limit|high demand|model .* unavailable|credit_balance|no model passed the availability probe|every free model failed the probe', segment, re.IGNORECASE):
            reasons.append('Model provider quota or availability stopped generation.')
        if re.search(r'new_video\.sh: No such file|scripts/new_video\.sh', segment, re.IGNORECASE):
            attempted = re.search(r'new_video\.sh[^\n]*\s(daily-\d{8}[a-z0-9-]*)', segment, re.IGNORECASE)
            target = f" {attempted.group(1)}" if attempted else ''
            reasons.append(f'Project{target} was not created because the new_video.sh path was invalid.')
        message = ' '.join(reasons) if reasons else f'Pipeline exited with code {code}. Open Live Logs for the error details.'
        return {'exit_code': code, 'message': message}
    return None


def get_uploaded_map():
    """Maps project directory names to their YouTube upload record from the ledger."""
    ledger = DAILY / 'topics-done.md'
    uploaded = {}
    if ledger.exists():
        for line in ledger.read_text(errors='replace').splitlines():
            line = line.strip()
            if not line.startswith('- '):
                continue
            parts = [p.strip() for p in line[2:].split('|')]
            if len(parts) >= 5:
                pname = parts[2]
                status = parts[4].upper()
                vid_id = parts[5].strip() if len(parts) >= 6 else ''
                vid_match = re.search(r'[a-zA-Z0-9_-]{11}', vid_id)
                actual_id = vid_match.group(0) if vid_match else None
                if 'UPLOADED' in status:
                    uploaded[pname] = {
                        'video_id': actual_id,
                        'url': f'https://www.youtube.com/watch?v={actual_id}' if actual_id else None,
                        'status': status
                    }
    return uploaded


def get_running_channels():
    """Returns {'en': bool, 'te': bool, 'any': bool} by inspecting active OS processes."""
    lock = DAILY / '.run.lock'
    lock_active = False
    if lock.exists():
        try:
            pid = int(lock.read_text().strip())
            os.kill(pid, 0)
            lock_active = True
        except (ValueError, OSError):
            pass

    running_en = False
    running_te = False

    try:
        out = subprocess.run(
            ['ps', '-eo', 'pid,ppid,args'],
            capture_output=True,
            text=True,
            errors='replace'
        )
        my_pid = os.getpid()
        lines = out.stdout.splitlines()

        for line in lines[1:]:
            parts = line.strip().split(None, 2)
            if len(parts) >= 3:
                try:
                    p = int(parts[0])
                    cmd = parts[2]
                except ValueError:
                    continue

                if p == my_pid:
                    continue
                if 'server.py' in cmd or 'grep' in cmd:
                    continue

                if any(k in cmd for k in ['run-daily.sh', 'build_pipeline.sh', 'opencode-cli run', 'capture.mjs']):
                    if 'run-daily.sh te' in cmd or 'Execute ONLY the Telugu' in cmd or '-te' in cmd or 'asakthi' in cmd:
                        running_te = True
                    elif 'run-daily.sh en' in cmd or 'Execute ONLY the English' in cmd or ('daily-' in cmd and '-te' not in cmd) or 'curiography' in cmd:
                        running_en = True
                    elif 'run-daily.sh all' in cmd or 'run-daily.sh' in cmd:
                        running_en = True
                        running_te = True
    except Exception:
        pass

    if lock_active and not (running_en or running_te):
        running_en = True
        running_te = True

    is_bc, bc_pid = is_broadcast_running()

    return {
        'en': running_en,
        'te': running_te,
        'any': running_en or running_te or is_bc,
        'broadcasting': is_bc,
        'broadcast_pid': bc_pid
    }


def is_broadcast_running():
    """Checks if a broadcast / YouTube upload process is currently executing."""
    lock = DAILY / '.broadcast.lock'
    if lock.exists():
        try:
            pid = int(lock.read_text().strip())
            os.kill(pid, 0)
            return True, pid
        except (ValueError, OSError):
            lock.unlink(missing_ok=True)

    try:
        out = subprocess.run(
            ['ps', '-eo', 'pid,args'],
            capture_output=True,
            text=True,
            errors='replace'
        )
        my_pid = os.getpid()
        for line in out.stdout.splitlines()[1:]:
            parts = line.strip().split(None, 1)
            if len(parts) >= 2:
                try:
                    p = int(parts[0])
                except ValueError:
                    continue
                cmd = parts[1]
                if p == my_pid:
                    continue
                if ('broadcast_queue.py broadcast' in cmd) or ('upload_youtube.py' in cmd):
                    return True, p
    except Exception:
        pass

    return False, None


def is_running():
    return get_running_channels()['any']


def get_ledger_entries():
    if not LEDGER.exists():
        return []
    entries = []
    for line in LEDGER.read_text(errors='replace').splitlines():
        if not line.startswith('- '):
            continue
        parts = [x.strip() for x in line[2:].split('|')]
        if len(parts) >= 5:
            date = parts[0]
            topic = parts[1]
            proj = parts[2]
            style = parts[3] if len(parts) >= 6 else ''
            status = parts[4] if len(parts) >= 6 else parts[3]
            v_id = parts[5] if len(parts) >= 6 else parts[4]
            vm = re.search(r'\b[A-Za-z0-9_-]{11}\b', v_id)
            entries.append({
                'date': date,
                'topic': topic,
                'project': proj,
                'style': style,
                'status': status,
                'video_id': vm.group(0) if vm else '',
                'channel': 'asakthi' if proj.endswith('-te') else 'curiography',
                'raw': line,
            })
    return entries


def analyze_channel(date, is_telugu=False, is_channel_running=False):
    blk, full = block_for_date(date)
    clean = ANSI.sub('', blk)
    stages_spec = TE_STAGES if is_telugu else EN_STAGES
    stages = []
    for sid, name, pats in stages_spec:
        pos = -1
        detail = ''
        for pat in pats:
            for m in re.finditer(pat, clean, re.IGNORECASE):
                if m.start() > pos:
                    pos = m.start()
                    line_start = clean.rfind('\n', 0, pos) + 1
                    detail = clean[line_start:].split('\n')[0].strip()[:140]
        stages.append({
            'id': sid,
            'name': name,
            'done': pos >= 0,
            'detail': html.unescape(detail),
        })

    # Channel-specific project directory matching
    if is_telugu:
        matches = sorted([str(p) for p in PROJECTS.glob(f'daily-{date.replace("-","")}*') if p.is_dir() and p.name.endswith('-te')])
    else:
        matches = sorted([str(p) for p in PROJECTS.glob(f'daily-{date.replace("-","")}*') if p.is_dir() and not p.name.endswith('-te')])
    P = Path(matches[-1]) if matches else None

    # Project, Style, Video ID from ledger for THIS channel only
    ledger_entries = get_ledger_entries()
    proj_name = P.name if P else None
    style_name = None
    if P and (P / 'script.json').exists():
        try:
            s_data = json.loads((P / 'script.json').read_text(errors='replace'))
            style_name = s_data.get('style') or s_data.get('assigned_style')
        except Exception:
            pass
    video_id = None
    status_str = 'RUNNING' if is_channel_running else 'IDLE'
    target_channel = 'asakthi' if is_telugu else 'curiography'

    # Match ledger entry: strictly match by project directory name first!
    if proj_name:
        for entry in reversed(ledger_entries):
            if entry['project'] == proj_name and entry['channel'] == target_channel:
                video_id = entry['video_id']
                status_str = entry['status']
                style_name = entry['style'] or style_name
                break
    elif not is_channel_running:
        for entry in reversed(ledger_entries):
            if entry['channel'] == target_channel and entry['date'] == date:
                video_id = entry['video_id']
                status_str = entry['status']
                style_name = entry['style'] or style_name
                proj_name = entry['project']
                break

    if not style_name:
        style_name = 'tall-tale' if is_telugu else 'procedural'

    # Filesystem and artifact facts check for THIS project directory only
    has_script = False
    has_narration = False
    has_words = False
    has_characters = False
    has_backgrounds = False
    has_cues = False
    has_mix = False
    has_sheet = False
    has_render = False
    has_cover = False
    if P and P.is_dir():
        has_script = (P / 'script.json').exists()
        has_narration = (P / 'data/narration.wav').exists()
        has_words = (P / 'data/words.json').exists()
        has_characters = (P / 'data/characters.json').exists() or (P / 'characters.json').exists()
        has_backgrounds = (P / 'data/backgrounds.json').exists() or (P / 'backgrounds.json').exists()
        has_cues = (P / 'data/cues.json').exists()
        has_mix = (P / 'data/mix.wav').exists()
        has_sheet = bool(list(P.glob('review/*.jpg')))
        has_render = bool(list(P.glob('renders/*.mp4')))
        has_cover = (P / 'covers/cover.jpg').exists()

        is_cinematic = (style_name in ('engineering-explainer', 'cinematic-what-if'))
        if is_channel_running:
            # During active runs, stage completion is determined strictly by project artifacts
            for s in stages:
                sid = s['id']
                if sid == 'topic':
                    s['done'] = has_script
                elif sid == 'scaffold':
                    s['done'] = True
                elif sid == 'voice':
                    s['done'] = has_narration or has_mix or has_render
                elif sid == 'words':
                    s['done'] = has_words or has_mix or has_render
                elif sid == 'characters':
                    s['done'] = has_characters or is_cinematic or has_cues or has_mix or has_render
                elif sid == 'backgrounds':
                    s['done'] = has_backgrounds or is_cinematic or has_cues or has_mix or has_render
                elif sid == 'check':
                    s['done'] = has_cues or has_mix or has_render
                elif sid == 'cues':
                    s['done'] = has_cues or has_mix or has_render
                elif sid == 'pacing':
                    s['done'] = has_mix or has_render
                elif sid == 'mix':
                    s['done'] = has_mix or has_render
                elif sid == 'sheet':
                    s['done'] = has_sheet or has_render
                elif sid == 'render':
                    s['done'] = has_render
                elif sid == 'cover':
                    s['done'] = has_cover
                elif sid == 'upload':
                    s['done'] = bool(video_id) and 'UPLOADED' in (status_str or '')
                elif sid == 'comment':
                    s['done'] = bool(video_id) and 'UPLOADED' in (status_str or '')
                elif sid == 'ledger':
                    s['done'] = bool(video_id) and 'UPLOADED' in (status_str or '')
                elif sid == 'end':
                    s['done'] = False

    if not is_channel_running:
        # Idle stages must come from this channel's artifacts, never historical log text.
        uploaded = bool(video_id) and 'UPLOADED' in (status_str or '')
        artifact_state = {
            'topic': has_script,
            'scaffold': bool(P and P.is_dir()),
            'voice': has_narration,
            'words': has_words,
            'characters': has_characters,
            'backgrounds': has_backgrounds,
            'check': has_cues,
            'cues': has_cues,
            'pacing': has_mix,
            'mix': has_mix,
            'sheet': has_sheet,
            'render': has_render,
            'cover': has_cover,
            'upload': uploaded,
            'comment': uploaded,
            'ledger': uploaded,
            'end': uploaded,
        }
        for s in stages:
            s['done'] = artifact_state.get(s['id'], False)
            s['detail'] = ''

    # Mark completed stages if video was uploaded to YouTube
    if video_id and 'UPLOADED' in (status_str or ''):
        for s in stages:
            s['done'] = True

    # Identify current active stage ONLY if this channel is running
    current = None
    if is_channel_running:
        for s in stages:
            if not s['done']:
                current = s['id']
                break
        if current is None and stages:
            current = 'working'

    return {
        'channel': target_channel,
        'channel_title': f'{TE_CHANNEL_NAME} (Telugu)' if is_telugu else f'{EN_CHANNEL_NAME} (English)',
        'running': is_channel_running,
        'project': proj_name,
        'style': style_name,
        'stages': stages,
        'current': current,
        'video_id': video_id,
        'status': status_str,
        'last_failure': None if is_channel_running else latest_run_failure(date, is_telugu),
        'has_render': bool(P and list(P.glob('renders/*.mp4'))),
        'has_cover': bool(P and (P / 'covers/cover.jpg').exists()),
        'has_sheet': bool(P and (P / 'review/all.jpg').exists()),
        'has_audio': bool(P and (P / 'data/mix.wav').exists()),
        'has_characters': has_characters,
        'has_backgrounds': has_backgrounds,
    }


def seed_perf():
    if PERF.exists():
        return
    recs = []
    for entry in get_ledger_entries():
        recs.append({
            'video_id': entry['video_id'],
            'date': entry['date'],
            'title': entry['topic'],
            'style': entry['style'],
            'status': entry['status'],
            'channel': entry['channel'],
            'views': None,
            'ctr': None,
            'retention': None,
            'likes': None,
            'comments': None,
            'hook_angle': '',
        })
    try:
        PERF.parent.mkdir(parents=True, exist_ok=True)
        PERF.write_text(json.dumps(recs, indent=1))
    except Exception:
        pass


class DashboardHandler(BaseHTTPRequestHandler):

    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype='application/json'):
        try:
            self.send_response(code)
            self.send_header('Content-Type', ctype)
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            # Browsers routinely cancel media/preview requests during navigation.
            # A disconnected client is not a server error and should not flood logs.
            return

    def _json(self, obj, code=200):
        self._send(code, json.dumps(obj).encode('utf-8'))

    def _stop_all_pipelines(self):
        stopped = []
        lock = DAILY / '.run.lock'
        if lock.exists():
            try:
                pid = int(lock.read_text().strip())
                try:
                    pgid = os.getpgid(pid)
                    os.killpg(pgid, signal.SIGTERM)
                    stopped.append(f'pgid:{pgid}')
                except Exception:
                    try:
                        os.kill(pid, signal.SIGTERM)
                        stopped.append(f'pid:{pid}')
                    except Exception:
                        pass
            except Exception:
                pass
            lock.unlink(missing_ok=True)

        b_lock = DAILY / '.broadcast.lock'
        if b_lock.exists():
            try:
                pid = int(b_lock.read_text().strip())
                try:
                    os.kill(pid, signal.SIGTERM)
                    stopped.append(f'broadcast_pid:{pid}')
                except Exception:
                    pass
            except Exception:
                pass
            b_lock.unlink(missing_ok=True)

        kill_patterns = [
            'run-daily.sh',
            'opencode.*run',
            'build_pipeline.sh',
            'upload_youtube.py',
            'broadcast_queue.py',
            'capture.mjs',
            'dialogue_engine.py',
            'blender_engine.py',
        ]
        for pat in kill_patterns:
            try:
                subprocess.run(['pkill', '-15', '-f', pat], check=False)
                stopped.append(f'pkill:{pat}')
            except Exception:
                pass

        LOGS.mkdir(parents=True, exist_ok=True)
        try:
            with open(LOGS / f'{today()}.log', 'a') as f:
                f.write(f"\n🛑 [PIPELINE STOPPED] User manually aborted all pipeline processes at {datetime.datetime.now().isoformat()}\n")
        except Exception:
            pass

        return stopped

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        p = self.path.split('?')[0]
        q = {}
        if '?' in self.path:
            q = dict(urllib.parse.parse_qsl(self.path.split('?')[1]))
        try:
            if p == '/':
                page = INDEX_HTML.replace('Curiography', html.escape(EN_CHANNEL_NAME)).replace('Asakthi', html.escape(TE_CHANNEL_NAME))
                self._send(200, page.encode('utf-8'), 'text/html; charset=utf-8')
            elif p == '/static/dashboard.css':
                self._send(200, (STATIC / 'dashboard.css').read_bytes(), 'text/css; charset=utf-8')
            elif p == '/static/dashboard.js':
                script = (STATIC / 'dashboard.js').read_text(encoding='utf-8')
                script = script.replace('Curiography', html.escape(EN_CHANNEL_NAME)).replace('Asakthi', html.escape(TE_CHANNEL_NAME))
                self._send(200, script.encode('utf-8'), 'application/javascript; charset=utf-8')
            elif p == '/api/status':
                date = q.get('date') or latest_log_date()
                running_map = get_running_channels()
                en_info = analyze_channel(date, is_telugu=False, is_channel_running=running_map['en'])
                te_info = analyze_channel(date, is_telugu=True, is_channel_running=running_map['te'])
                self._json({
                    'date': date,
                    'running': running_map['any'],
                    'running_en': running_map['en'],
                    'running_te': running_map['te'],
                    'broadcasting': running_map.get('broadcasting', False),
                    'broadcast_pid': running_map.get('broadcast_pid'),
                    'en': en_info,
                    'te': te_info,
                    'ledger_entries': get_ledger_entries()[:15],
                })
            elif p == '/api/broadcast_status':
                is_bc, bc_pid = is_broadcast_running()
                b_log_file = LOGS / 'broadcast.log'
                lines = []
                if b_log_file.exists():
                    try:
                        raw = b_log_file.read_text(errors='replace')
                        lines = ANSI.sub('', raw).splitlines()[-100:]
                    except Exception:
                        pass
                sys.path.insert(0, str(DAILY))
                try:
                    import broadcast_queue
                    slot = broadcast_queue.get_slot_info()
                    queued = broadcast_queue.get_queued_videos('all')
                except Exception:
                    slot = {}
                    queued = []
                self._json({
                    'is_running': is_bc,
                    'pid': bc_pid,
                    'lines': lines,
                    'slot': slot,
                    'queued': queued
                })
            elif p == '/api/trends':
                style = q.get('style') or None
                channel = q.get('channel') or 'en'
                category = q.get('category') or None
                count = int(q.get('count', 6))
                sys.path.insert(0, str(DAILY))
                try:
                    import trend_hunter
                    trends = trend_hunter.hunt_trends(
                        target_style=style,
                        top_n=count,
                        channel=channel,
                        category_key=category
                    )
                    self._json({'channel': channel, 'trends': trends})
                except Exception as e:
                    self._json({'channel': channel, 'trends': [], 'error': str(e)})
            elif p == '/api/queue':
                channel = q.get('channel') or 'all'
                sys.path.insert(0, str(DAILY))
                try:
                    import broadcast_queue
                    slot = broadcast_queue.get_slot_info()
                    queued = broadcast_queue.get_queued_videos(channel)
                    self._json({'slot': slot, 'queued': queued})
                except Exception as e:
                    self._json({'slot': {}, 'queued': [], 'error': str(e)})
            elif p == '/api/stop':
                self._json({'error': 'POST required'}, 405)
            elif p == '/api/projects':
                uploaded_map = get_uploaded_map()
                ledger_channels = {entry['project']: entry['channel'] for entry in get_ledger_entries()}
                projects = []
                for x in sorted(PROJECTS.iterdir(), reverse=True) if PROJECTS.is_dir() else []:
                    if not x.is_dir():
                        continue
                    mp4s = list(x.glob('renders/*.mp4'))
                    if not (x / 'script.json').is_file() and not mp4s:
                        continue
                    up_info = uploaded_map.get(x.name, {})
                    script_data = {}
                    try:
                        script_data = json.loads((x / 'script.json').read_text(errors='replace'))
                    except Exception:
                        pass
                    script_title = script_data.get('title') or x.name
                    is_te = (x.name.endswith('-te') or ledger_channels.get(x.name) == 'asakthi'
                             or script_data.get('channel') in ('te', 'asakthi')
                             or bool(re.search(r'[\u0c00-\u0c7f]', str(script_title))))
                    projects.append({
                        'name': x.name,
                        'title': script_title,
                        'channel': 'asakthi' if is_te else 'curiography',
                        'has_render': bool(mp4s),
                        'has_cover': (x / 'covers/cover.jpg').exists(),
                        'has_sheet': (x / 'review/all.jpg').exists(),
                        'has_audio': (x / 'data/mix.wav').exists(),
                        'mp4_size': mp4s[0].stat().st_size if mp4s else 0,
                        'is_uploaded': bool(up_info.get('video_id')),
                        'video_id': up_info.get('video_id'),
                        'youtube_url': up_info.get('url'),
                    })
                self._json({'projects': projects})
            elif p == '/api/project_details':
                proj_name = q.get('project', '')
                proj = resolve_project(proj_name)
                if proj is None or not proj.is_dir():
                    self._json({'error': 'Invalid project'}, 400)
                    return
                script_path = proj / 'script.json'
                script_data = {}
                if script_path.is_file():
                    try:
                        script_data = json.loads(script_path.read_text(errors='replace'))
                    except Exception:
                        pass
                shots_path = proj / 'src/shots.js'
                shots_content = shots_path.read_text(errors='replace') if shots_path.is_file() else ''
                characters_data = {}
                char_path = proj / 'data/characters.json'
                if char_path.is_file():
                    try:
                        characters_data = json.loads(char_path.read_text(errors='replace'))
                    except Exception:
                        pass
                backgrounds_data = {}
                bg_path = proj / 'data/backgrounds.json'
                if bg_path.is_file():
                    try:
                        backgrounds_data = json.loads(bg_path.read_text(errors='replace'))
                    except Exception:
                        pass
                up_info = get_uploaded_map().get(proj_name, {})
                ledger_channel = next((entry['channel'] for entry in reversed(get_ledger_entries()) if entry['project'] == proj_name), None)
                project_is_te = (proj_name.endswith('-te') or ledger_channel == 'asakthi'
                                 or script_data.get('channel') in ('te', 'asakthi')
                                 or bool(re.search(r'[\u0c00-\u0c7f]', str(script_data.get('title', '')))))
                self._json({
                    'project': proj_name,
                    'channel': 'asakthi' if project_is_te else 'curiography',
                    'script': script_data,
                    'shots_preview': shots_content[:2500],
                    'characters': characters_data,
                    'backgrounds': backgrounds_data,
                    'has_characters': bool(characters_data),
                    'has_backgrounds': bool(backgrounds_data),
                    'has_render': bool(list(proj.glob('renders/*.mp4'))),
                    'has_cover': (proj / 'covers/cover.jpg').exists(),
                    'has_sheet': (proj / 'review/all.jpg').exists(),
                    'has_mix': (proj / 'data/mix.wav').exists(),
                    'has_narration': (proj / 'data/narration.wav').exists(),
                    'is_uploaded': bool(up_info.get('video_id')),
                    'video_id': up_info.get('video_id'),
                    'youtube_url': up_info.get('url'),
                })
            elif p == '/api/log':
                date = q.get('date') or latest_log_date()
                channel = q.get('channel', 'all')
                if channel == 'broadcast' or date == 'broadcast':
                    f = LOGS / 'broadcast.log'
                else:
                    f = LOGS / f'{date}.log'
                tail = int(q.get('tail', 600))
                if not f.exists():
                    self._json({'date': date, 'channel': channel, 'lines': []})
                    return
                all_lines = ANSI.sub('', f.read_text(errors='replace')).splitlines()
                if channel == 'en':
                    filtered = [l for l in all_lines if not any(k in l for k in ['-te', 'asakthi', 'te_IN', 'piper_say', 'Telugu', 'దేవాలయం', 'హనుమంతుడు', 'తెలుగు'])]
                    lines = filtered[-tail:]
                elif channel == 'te':
                    filtered = [l for l in all_lines if any(k in l for k in ['-te', 'asakthi', 'te_IN', 'piper_say', 'Telugu', 'tall-tale daily-', 'deity', 'DEITIES', 'హనుమాన్', 'తెలుగు', 'CHANNEL RESTRICTION: Execute ONLY the Telugu'])]
                    lines = filtered[-tail:]
                else:
                    lines = all_lines[-tail:]
                self._json({'date': date, 'channel': channel, 'lines': lines})
            elif p == '/api/logs':
                run_logs = sorted((x.stem for x in LOGS.glob('*.log') if re.fullmatch(r'\d{4}-\d{2}-\d{2}', x.stem)), reverse=True)
                if (LOGS / 'broadcast.log').exists():
                    run_logs.append('broadcast')
                self._json({'logs': run_logs})
            elif p == '/api/perf':
                seed_perf()
                self._json({'records': json.loads(PERF.read_text()) if PERF.exists() else []})
            elif p == '/api/files':
                proj = resolve_project(q.get('project') or '')
                if proj is None or not proj.is_dir():
                    self._json({'files': []})
                    return
                files = []
                for f in sorted(proj.rglob('*')):
                    if any(part in SKIP_DIRS for part in f.relative_to(proj).parts):
                        continue
                    if f.is_file() and f.suffix.lower() in TEXT_EXT and f.stat().st_size < 600_000:
                        files.append(str(f.relative_to(proj)))
                self._json({'files': files})
            elif p == '/api/file':
                fp = (ROOT / q['path']).resolve()
                if not str(fp).startswith(str(ROOT)):
                    self._json({'error': 'outside root'}, 400)
                    return
                if not fp.is_file():
                    self._json({'error': 'not found'}, 404)
                    return
                self._json({'path': q['path'], 'content': fp.read_text(errors='replace')})
            elif p == '/api/vid':
                proj = resolve_project(q.get('project') or '')
                if proj is None:
                    self._json({'error': 'Invalid project'}, 400)
                    return
                renders = list(proj.glob('renders/*.mp4'))
                if not renders or not renders[0].is_file():
                    self._json({'error': 'video not found'}, 404)
                    return
                data = renders[0].read_bytes()
                self.send_response(200)
                self.send_header('Content-Type', 'video/mp4')
                self.send_header('Content-Length', str(len(data)))
                self.send_header('Cache-Control', 'no-store')
                self.end_headers()
                self.wfile.write(data)
            elif p == '/api/thumb':
                proj = resolve_project(q.get('project') or '')
                if proj is None:
                    self._json({'error': 'Invalid project'}, 400)
                    return
                f = proj / 'covers' / 'cover.jpg'
                if not f.is_file():
                    self._json({'error': 'cover not found'}, 404)
                    return
                data = f.read_bytes()
                self.send_response(200)
                self.send_header('Content-Type', 'image/jpeg')
                self.send_header('Content-Length', str(len(data)))
                self.send_header('Cache-Control', 'no-store')
                self.end_headers()
                self.wfile.write(data)
            elif p == '/api/sheet':
                proj = resolve_project(q.get('project') or '')
                if proj is None:
                    self._json({'error': 'Invalid project'}, 400)
                    return
                f = proj / 'review' / 'all.jpg'
                if not f.is_file():
                    self._json({'error': 'sheet not found'}, 404)
                    return
                data = f.read_bytes()
                self.send_response(200)
                self.send_header('Content-Type', 'image/jpeg')
                self.send_header('Content-Length', str(len(data)))
                self.send_header('Cache-Control', 'no-store')
                self.end_headers()
                self.wfile.write(data)
            elif p == '/api/audio':
                proj = resolve_project(q.get('project') or '')
                if proj is None:
                    self._json({'error': 'Invalid project'}, 400)
                    return
                kind = q.get('type', 'mix')
                f = proj / 'data' / ('narration.wav' if kind == 'narration' else 'mix.wav')
                if not f.is_file():
                    self._json({'error': 'audio not found'}, 404)
                    return
                data = f.read_bytes()
                self.send_response(200)
                self.send_header('Content-Type', 'audio/wav')
                self.send_header('Content-Length', str(len(data)))
                self.send_header('Cache-Control', 'no-store')
                self.end_headers()
                self.wfile.write(data)
            elif p == '/api/asset':
                proj = resolve_project(q.get('project') or '')
                if proj is None:
                    self._json({'error': 'Invalid project'}, 400)
                    return
                rel = q.get('path', '')
                fp = (proj / rel).resolve()
                if not str(fp).startswith(str(proj)) or not fp.is_file():
                    self._json({'error': 'asset not found'}, 404)
                    return
                ext = fp.suffix.lower()
                ctype = 'image/png' if ext == '.png' else ('image/jpeg' if ext in ('.jpg', '.jpeg') else ('image/webp' if ext == '.webp' else 'application/octet-stream'))
                data = fp.read_bytes()
                self.send_response(200)
                self.send_header('Content-Type', ctype)
                self.send_header('Content-Length', str(len(data)))
                self.send_header('Cache-Control', 'no-store')
                self.end_headers()
                self.wfile.write(data)
            else:
                self._json({'error': 'unknown route'}, 404)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            return
        except Exception as e:
            self._json({'error': str(e)}, 500)

    def do_POST(self):
        p = self.path.split('?')[0]
        try:
            n = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(n) or b'{}')
            if p == '/api/file':
                fp = (ROOT / body['path']).resolve()
                if not str(fp).startswith(str(ROOT)):
                    self._json({'error': 'outside root'}, 400)
                    return
                if fp.exists():
                    bak = fp.with_suffix(fp.suffix + '.bak')
                    bak.write_text(fp.read_text(errors='replace'))
                fp.parent.mkdir(parents=True, exist_ok=True)
                fp.write_text(body['content'])
                self._json({'ok': True, 'path': body['path']})
            elif p == '/api/perf':
                seed_perf()
                recs = json.loads(PERF.read_text()) if PERF.exists() else []
                rec = body.get('record') or {}
                vid = rec.get('video_id')
                hit = next((r for r in recs if r.get('video_id') == vid), None)
                if hit:
                    hit.update({k: v for k, v in rec.items() if k in hit})
                else:
                    recs.append(rec)
                PERF.write_text(json.dumps(recs, indent=1))
                self._json({'ok': True, 'count': len(recs)})
            elif p == '/api/perf/sync':
                script = DAILY / 'youtube_analytics.py'
                try:
                    result = subprocess.run([sys.executable, str(script), 'sync'], cwd=ROOT,
                                            capture_output=True, text=True, timeout=90)
                    self._json({'ok': result.returncode == 0, 'output': (result.stdout + result.stderr).strip()},
                               200 if result.returncode == 0 else 400)
                except subprocess.TimeoutExpired:
                    self._json({'ok': False, 'output': 'Analytics sync timed out after 90 seconds.'}, 504)
            elif p == '/api/run':
                channel = body.get('channel', 'all')
                engine = body.get('engine', '3d')
                if channel not in ('en', 'te', 'all') or engine not in ('3d', 'mpt'):
                    self._json({'ok': False, 'error': 'Choose a valid channel and production engine.'}, 400)
                    return
                active = get_running_channels()
                if active['en'] or active['te']:
                    self._json({'ok': False, 'error': 'A pipeline is already running. Wait for it to finish before starting another.'}, 409)
                    return
                dry = bool(body.get('dry'))
                topic = (body.get('topic') or '').strip()[:300]
                style = (body.get('style') or '').strip()
                format_mode = body.get('format', 'short')
                env = dict(os.environ, DRY_RUN='1' if dry else '0', CHANNEL_FILTER=channel, ENGINE_MODE=engine, PRODUCTION_FORMAT=format_mode)
                if engine == 'documentary':
                    env['FETCH_BROLL'] = '1'
                if topic:
                    env['TOPIC_OVERRIDE'] = topic
                if style and style != 'auto':
                    env['STYLE_OVERRIDE'] = style

                # Redirect output live into today's log file
                LOGS.mkdir(parents=True, exist_ok=True)
                log_f = open(LOGS / f'{today()}.log', 'a')
                log_f.write(f"\n===== [RUN TRIGGERED: channel={channel}, format={format_mode}, dry={dry}, engine={engine}, style={style or 'auto'}] at {datetime.datetime.now().isoformat()} =====\n")
                log_f.flush()

                if engine == 'mpt':
                    cmd = [
                        sys.executable,
                        str(DAILY / 'mpt_pipeline.py'),
                        '--channel', channel,
                    ]
                    if topic:
                        cmd.extend(['--topic', topic])
                    if dry:
                        cmd.append('--dry-run')
                    subprocess.Popen(
                        cmd,
                        env=dict(os.environ, PYTHONUNBUFFERED='1'),
                        stdout=log_f,
                        stderr=subprocess.STDOUT,
                        start_new_session=True,
                    )
                else:
                    subprocess.Popen(
                        ['/bin/zsh', str(RUNNER), channel],
                        env=env,
                        stdout=log_f,
                        stderr=subprocess.STDOUT,
                        start_new_session=True,
                    )
                self._json({'ok': True, 'channel': channel, 'dry': dry, 'topic': topic, 'engine': engine, 'style': style})
            elif p == '/api/broadcast':
                channel = body.get('channel') or 'all'
                sys.path.insert(0, str(DAILY))
                try:
                    is_bc, bc_pid = is_broadcast_running()
                    if is_bc:
                        self._json({'ok': False, 'error': f'Broadcast already running (PID {bc_pid})', 'pid': bc_pid})
                        return

                    LOGS.mkdir(parents=True, exist_ok=True)
                    broadcast_log_path = LOGS / 'broadcast.log'
                    today_log_path = LOGS / f'{today()}.log'

                    header = f"\n===== [BROADCAST TRIGGERED: channel={channel}] at {datetime.datetime.now().isoformat()} =====\n"
                    with open(today_log_path, 'a') as f:
                        f.write(header)

                    b_log = open(broadcast_log_path, 'w')
                    b_log.write(header)
                    b_log.flush()

                    cmd = [sys.executable, str(DAILY / 'broadcast_queue.py'), 'broadcast', '--channel', channel]
                    env = dict(os.environ, PYTHONUNBUFFERED='1')
                    proc = subprocess.Popen(
                        cmd,
                        env=env,
                        stdout=b_log,
                        stderr=subprocess.STDOUT,
                        start_new_session=True,
                    )
                    self._json({'ok': True, 'pid': proc.pid, 'channel': channel})
                except Exception as e:
                    self._json({'ok': False, 'error': str(e)})
            elif p == '/api/broadcast_stop':
                stopped = []
                b_lock = DAILY / '.broadcast.lock'
                if b_lock.exists():
                    try:
                        pid = int(b_lock.read_text().strip())
                        try:
                            os.kill(pid, signal.SIGTERM)
                            stopped.append(f'broadcast_pid:{pid}')
                        except Exception:
                            pass
                    except Exception:
                        pass
                    b_lock.unlink(missing_ok=True)
                for pat in ['broadcast_queue.py', 'upload_youtube.py']:
                    try:
                        subprocess.run(['pkill', '-15', '-f', pat], check=False)
                        stopped.append(f'pkill:{pat}')
                    except Exception:
                        pass
                self._json({'ok': True, 'stopped': stopped})
            elif p == '/api/stop':
                stopped = self._stop_all_pipelines()
                self._json({'ok': True, 'stopped': stopped})
            elif p == '/api/action':
                proj_name = body.get('project')
                action = body.get('action')
                proj = resolve_project(proj_name)
                if proj is None or not proj.is_dir():
                    self._json({'error': 'Invalid project'}, 400)
                    return

                LOGS.mkdir(parents=True, exist_ok=True)
                log_f = open(LOGS / f'{today()}.log', 'a')
                log_f.write(f"\n===== [ACTION: {action} on {proj_name}] at {datetime.datetime.now().isoformat()} =====\n")
                log_f.flush()

                if action == 'build':
                    script = SKILL / 'scripts/build_pipeline.sh'
                    cmd = ['bash', str(script), str(proj)]
                    if body.get('skip_audio'):
                        cmd.append('--skip-audio')
                    proc = subprocess.Popen(cmd, cwd=str(proj), env=os.environ, stdout=log_f, stderr=subprocess.STDOUT)
                    self._json({'ok': True, 'pid': proc.pid})
                elif action == 'render':
                    cmd = ['node', 'tools/capture.mjs', 'video', f'renders/{proj_name}.mp4']
                    proc = subprocess.Popen(cmd, cwd=str(proj), env=os.environ, stdout=log_f, stderr=subprocess.STDOUT)
                    self._json({'ok': True, 'pid': proc.pid})
                elif action == 'cover':
                    script = SKILL / 'scripts/make_cover.sh'
                    t = str(body.get('time', 1.0))
                    text = body.get('text', 'TITLE|HERE')
                    cmd = ['zsh', str(script), f'renders/{proj_name}.mp4', 'covers/cover.jpg', t, text]
                    proc = subprocess.Popen(cmd, cwd=str(proj), env=os.environ, stdout=log_f, stderr=subprocess.STDOUT)
                    self._json({'ok': True, 'pid': proc.pid})
                elif action == 'upload':
                    script = SKILL / 'scripts/upload_youtube.py'
                    force = bool(body.get('force', True))
                    cmd = [str(PY), str(script), str(proj)]
                    if force:
                        cmd.append('--force')
                    proc = subprocess.Popen(cmd, cwd=str(proj), env=os.environ, stdout=log_f, stderr=subprocess.STDOUT)
                    self._json({'ok': True, 'pid': proc.pid})
                elif action == 'stop':
                    lock = DAILY / '.run.lock'
                    if lock.exists():
                        try:
                            pid = int(lock.read_text().strip())
                            os.kill(pid, 15)
                            lock.unlink(missing_ok=True)
                        except Exception:
                            pass
                    self._json({'ok': True})
                else:
                    self._json({'error': f'Unknown action {action}'}, 400)
            else:
                self._json({'error': 'unknown route'}, 404)
        except Exception as e:
            self._json({'error': str(e)}, 500)


TEMPLATE = Path(__file__).with_name("templates") / "dashboard.html"
INDEX_HTML = TEMPLATE.read_text(encoding="utf-8")


def main(argv=None):
    """Run the local dashboard HTTP server."""
    argv = list(sys.argv[1:] if argv is None else argv)
    port = int(argv[0]) if argv else int(os.environ.get("DASHBOARD_PORT", "8788"))
    host = os.environ.get("DASHBOARD_HOST", "127.0.0.1")
    print(f"Faceless Video Pipeline dashboard: http://{host}:{port}")
    ThreadingHTTPServer((host, port), DashboardHandler).serve_forever()


if __name__ == "__main__":
    main()
