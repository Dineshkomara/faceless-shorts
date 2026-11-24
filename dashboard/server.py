#!/usr/bin/env python3
"""Faceless-shorts Dual-Channel Pipeline Dashboard & Studio — stdlib only.

Serves on 127.0.0.1:8788 (managed by com.dinesh.facesshorts.dashboard.plist).
Supports both channels:
  1. Curiography (English) - Runnable styles (engineering-explainer, tall-tale, cinematic-what-if)
  2. Asakthi (Telugu)      - Tall-tale style with deity character rules (Ramayana, Mahabharata, traditions)
"""

import datetime
import glob
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

for _p in ['/opt/homebrew/bin', '/usr/local/bin', str(Path.home() / '.local/bin'), str(Path.home() / '.gemini/antigravity/bin')]:
    if _p not in os.environ.get('PATH', ''):
        os.environ['PATH'] = f"{_p}:{os.environ.get('PATH', '')}"

HOME = Path.home()
ROOT = Path(os.environ.get('PIPELINE_ROOT', Path(__file__).resolve().parent.parent)).resolve()
EN_CHANNEL_NAME = os.environ.get('EN_CHANNEL_NAME', 'Curiography')
TE_CHANNEL_NAME = os.environ.get('TE_CHANNEL_NAME', 'Asakthi')
DAILY = ROOT / 'daily'
LOGS = DAILY / 'logs'
LEDGER = DAILY / 'topics-done.md'
RUNNER = DAILY / 'run-daily.sh'
PERF = ROOT / 'dashboard' / 'perf.json'
SKILL = Path(os.environ.get('SKILL_DIR', ROOT / '.agents/skills/faceless-shorts'))
if not SKILL.is_dir():
    SKILL = HOME / '.config/opencode/skill/faceless-shorts'
PY = SKILL / 'scripts/py'
TEXT_EXT = {'.json', '.js', '.mjs', '.md', '.txt', '.py', '.sh', '.css', '.html'}
SKIP_DIRS = {'node_modules', 'review', 'covers', 'renders', 'audio', '.git', '.agents'}
ANSI = re.compile(r'\x1b\[[0-9;]*[A-Za-z]')

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
        matches = sorted([p for p in glob.glob(str(ROOT / f'daily-{date.replace("-","")}*')) if p.endswith('-te')])
    else:
        matches = sorted([p for p in glob.glob(str(ROOT / f'daily-{date.replace("-","")}*')) if not p.endswith('-te')])
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
                for x in sorted(ROOT.iterdir(), reverse=True):
                    if not x.is_dir() or x.name in ('daily', 'dashboard', 'review', '.git', '.agents'):
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
                proj = (ROOT / proj_name).resolve()
                if not proj.is_dir() or proj.parent != ROOT:
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
                proj = ROOT / (q.get('project') or '')
                if not proj.is_dir() or proj.resolve().parent != ROOT:
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
                proj = ROOT / (q.get('project') or '')
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
                proj = ROOT / (q.get('project') or '')
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
                proj = ROOT / (q.get('project') or '')
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
                proj = ROOT / (q.get('project') or '')
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
                proj = ROOT / (q.get('project') or '')
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
                proj = (ROOT / proj_name).resolve()
                if not proj.is_dir() or proj.parent != ROOT:
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


INDEX_HTML = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>🎬 Faceless Shorts Studio</title>
<style>
:root {
  --bg: #090d16;
  --surface: #111827;
  --surface-hover: #1f2937;
  --border: #232f3e;
  --border-focus: #3b82f6;
  --text: #f3f4f6;
  --text-dim: #9ca3af;
  --en-accent: #38bdf8;
  --en-bg: rgba(56, 189, 248, 0.12);
  --te-accent: #fbbf24;
  --te-bg: rgba(251, 191, 36, 0.12);
  --ok: #22c55e;
  --warn: #eab308;
  --err: #ef4444;
  --radius: 12px;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--bg);
  color: var(--text);
  font: 14px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  -webkit-font-smoothing: antialiased;
}
header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 28px;
  background: rgba(17, 24, 39, 0.85);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--border);
  position: sticky;
  top: 0;
  z-index: 100;
}
.brand { display: flex; align-items: center; gap: 14px; }
.brand h1 { margin: 0; font-size: 17px; font-weight: 700; letter-spacing: -0.02em; }
.brand .pill {
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
}
.pill.idle { background: rgba(34, 197, 94, 0.15); color: var(--ok); }
.pill.run { background: rgba(234, 179, 8, 0.2); color: var(--warn); animation: pulse 1.5s infinite; }
.pill.err { background: rgba(239, 68, 68, 0.2); color: var(--err); }
.run-failure { display:flex; align-items:center; gap:10px; flex-wrap:wrap; margin:0 0 12px; padding:10px 12px; border:1px solid rgba(239,68,68,.35); border-radius:9px; background:rgba(239,68,68,.08); color:var(--err); font-size:12px; }
.run-failure span { color:var(--text); flex:1; min-width:200px; }
@keyframes pulse { 50% { opacity: 0.5; } }

.top-actions { display: flex; align-items: center; gap: 10px; }
.btn {
  background: var(--surface);
  color: var(--text);
  border: 1px solid var(--border);
  padding: 7px 14px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  transition: all 0.15s ease;
}
.btn:hover { background: var(--surface-hover); border-color: var(--text-dim); }
.btn.primary { background: #2563eb; border-color: #3b82f6; color: #fff; }
.btn.primary:hover { background: #1d4ed8; }
.btn.en { background: var(--en-bg); border-color: var(--en-accent); color: var(--en-accent); }
.btn.te { background: var(--te-bg); border-color: var(--te-accent); color: var(--te-accent); }
.btn.danger { background: rgba(239, 68, 68, 0.15); border-color: var(--err); color: var(--err); }

nav {
  display: flex;
  gap: 6px;
  padding: 8px 28px;
  background: var(--surface);
  border-bottom: 1px solid var(--border);
}
nav button {
  background: none;
  border: 1px solid transparent;
  color: var(--text-dim);
  padding: 7px 16px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  transition: all 0.15s;
}
nav button:hover { color: var(--text); }
nav button.active {
  color: #fff;
  background: var(--bg);
  border-color: var(--border);
}

main { padding: 24px 28px; max-width: 1400px; margin: 0 auto; }
.grid-2 { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 20px; }
@media (max-width: 1024px) { .grid-2 { grid-template-columns: 1fr; } }
@media (max-width: 1400px) {
  header { align-items: flex-start; flex-direction: column; gap: 12px; padding: 12px 18px; }
  .brand { flex-wrap: wrap; gap: 8px 12px; }
  .top-actions { width: 100%; justify-content: flex-start; flex-wrap: wrap; }
  nav { overflow-x: auto; white-space: nowrap; padding: 8px 16px; scrollbar-width: thin; gap:4px; }
  nav button { flex: 0 0 auto; padding:7px 11px; font-size:12px; }
}
@media (max-width: 700px) {
  .card-header { align-items: flex-start; flex-direction: column; }
  .project-controls { display: grid; grid-template-columns: 1fr; }
  .queue-grid { grid-template-columns: 1fr !important; }
  .queue-actions { width: 100%; flex-wrap: wrap; }
  .inspect-layout { flex-direction: column; }
  .inspect-sidebar { width: 100% !important; max-width: 260px; }
  .inspect-main { min-width: 0; }
  .topic-details { margin: 10px 0; }
  main { padding: 16px 12px; }
  header { padding: 12px; }
  .top-actions { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }
  .top-actions > * { min-width: 0; }
  .top-actions select, .top-actions label { grid-column: 1 / -1; width: 100%; }
  .top-actions > .btn { justify-content: center; text-align: center; white-space: normal; }
  .media-preview-box { grid-template-columns: 1fr; }
  .media-preview-box > div:first-child { max-width: 220px; }
  .step { align-items: flex-start; gap: 8px; }
  .step-title { min-width: 0; width: 38%; flex: 0 0 38%; }
  .step-detail { white-space: normal; overflow-wrap: anywhere; }
  table { display: block; overflow-x: auto; white-space: nowrap; }
  .modal-content { width: calc(100vw - 24px); max-width: none; padding: 18px 14px; }
}

.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 18px 20px;
  position: relative;
}
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border);
}
.card-header h2 {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 8px;
}
.channel-tag {
  font-size: 11px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 6px;
  text-transform: uppercase;
}
.channel-tag.en { background: var(--en-bg); color: var(--en-accent); }
.channel-tag.te { background: var(--te-bg); color: var(--te-accent); }

.sub-nav {
  display: flex;
  gap: 8px;
  margin-bottom: 18px;
  align-items: center;
  flex-wrap: wrap;
}
.sub-nav button {
  background: var(--surface);
  border: 1px solid var(--border);
  color: var(--text-dim);
  padding: 6px 14px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 12.5px;
  font-weight: 600;
  transition: all 0.15s ease;
}
.sub-nav button:hover {
  background: var(--surface-hover);
  color: var(--text);
}
.sub-nav button.active {
  background: rgba(59, 130, 246, 0.15);
  border-color: #3b82f6;
  color: #fff;
}
.sub-nav button.active.en {
  background: var(--en-bg);
  border-color: var(--en-accent);
  color: var(--en-accent);
}
.sub-nav button.active.te {
  background: var(--te-bg);
  border-color: var(--te-accent);
  color: var(--te-accent);
}

.channel-section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  border-radius: 8px;
  margin: 16px 0 12px 0;
}
.channel-section-header.en {
  background: rgba(56, 189, 248, 0.08);
  border-left: 4px solid var(--en-accent);
}
.channel-section-header.te {
  background: rgba(251, 191, 36, 0.08);
  border-left: 4px solid var(--te-accent);
}
.channel-section-header h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 8px;
}

.stepper { display: flex; flex-direction: column; gap: 6px; }
.step {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 7px 10px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid transparent;
  font-size: 13px;
}
.step.done { color: var(--text); }
.step.done .dot { background: var(--ok); }
.step.current {
  background: rgba(234, 179, 8, 0.08);
  border-color: rgba(234, 179, 8, 0.3);
  color: var(--warn);
  font-weight: 600;
}
.step.current .dot { background: var(--warn); animation: pulse 1s infinite; }
.step.pending { color: var(--text-dim); }
.step.pending .dot { background: #374151; }
.dot { width: 9px; height: 9px; border-radius: 50%; flex-shrink: 0; }
.step-title { min-width: 170px; font-weight: 600; }
.step-detail { min-width: 0; color: var(--text-dim); font-size: 12px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.media-preview-box {
  display: grid;
  grid-template-columns: 200px 1fr;
  gap: 16px;
  background: var(--bg);
  padding: 14px;
  border-radius: 10px;
  border: 1px solid var(--border);
  margin-top: 14px;
}
video.preview-vid {
  width: 100%;
  aspect-ratio: 9/16;
  border-radius: 8px;
  background: #000;
  border: 1px solid var(--border);
}
img.preview-cover {
  width: 100%;
  aspect-ratio: 9/16;
  object-fit: cover;
  border-radius: 8px;
  border: 1px solid var(--border);
  cursor: pointer;
}
audio { width: 100%; margin-top: 8px; height: 36px; }

.toolbar { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 12px; }
.project-controls { display:flex; gap:10px; align-items:center; flex-wrap:wrap; margin: 4px 0 16px; }
.project-controls input, .project-controls select { min-height:38px; background:var(--bg); color:var(--text); border:1px solid var(--border); border-radius:8px; padding:8px 11px; }
.project-controls input { flex:1 1 240px; }
.project-controls select { min-width:190px; }
.count-note { color:var(--text-dim); font-size:12px; }
.project-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(220px,1fr)); gap:16px; margin-bottom:28px; }
.project-card[hidden], [data-project-section][hidden], .project-grid[hidden] { display:none !important; }
.project-card:focus-visible { outline:2px solid var(--border-focus); outline-offset:2px; }
.queue-grid { display:grid; grid-template-columns:1fr 1fr; gap:14px; }
.queue-actions { display:flex; gap:8px; }
.inspect-layout { display:flex; gap:20px; max-width:960px; }
.inspect-sidebar { width:280px; flex-shrink:0; }
.inspect-main { flex-grow:1; min-width:0; }
.topic-details { color:var(--text-dim); font-size:12px; }
.topic-details summary { cursor:pointer; font-weight:600; color:#cbd5e1; padding:7px 0; }
.modal-backdrop {
  position: fixed; inset: 0; background: rgba(0,0,0,0.85); backdrop-filter: blur(6px);
  display: none; align-items: center; justify-content: center; z-index: 999;
}
.modal-backdrop.active { display: flex; }
.modal-content {
  background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius);
  max-width: 90vw; max-height: 90vh; overflow: auto; padding: 24px; position: relative;
}
.close-btn { position: absolute; top: 12px; right: 14px; background: none; border: none; color: #fff; font-size: 20px; cursor: pointer; }

table { width: 100%; border-collapse: collapse; font-size: 13px; }
.table-wrap { width:100%; overflow-x:auto; }
.performance-table { min-width:900px; }
.trend-controls { display:flex; gap:10px; align-items:center; }
th, td { padding: 9px 12px; text-align: left; border-bottom: 1px solid var(--border); }
th { color: var(--text-dim); font-size: 12px; text-transform: uppercase; }
tr:hover td { background: rgba(255, 255, 255, 0.02); }

textarea.code-editor {
  display:block; width:100%; min-height:60vh; resize:vertical; background:#070a10; color:#e2e8f0;
  border:1px solid var(--border); border-radius:10px; padding:16px; font:12px/1.65 ui-monospace, Menlo, monospace;
  tab-size:2; white-space:pre; overflow:auto; outline:none;
}
textarea.code-editor:focus { border-color:var(--border-focus); box-shadow:0 0 0 3px rgba(99,102,241,.12); }
#log-terminal {
  background: #05070c; border: 1px solid var(--border); border-radius: 8px; padding: 14px;
  font: 11.5px/1.6 ui-monospace, Menlo, monospace; height: 600px; overflow: auto; white-space: pre-wrap; word-break: break-all;
}

.btn:disabled { opacity:.45; cursor:not-allowed; filter:saturate(.45); }
button:focus-visible, a:focus-visible, select:focus-visible, input:focus-visible, summary:focus-visible { outline:2px solid var(--border-focus); outline-offset:2px; }
@media (max-width: 700px) {
  .card-header { align-items:flex-start; flex-direction:column; gap:10px; }
  .trend-controls { width:100%; display:grid; grid-template-columns:1fr; }
  .trend-controls select, .trend-controls button { width:100%; }
  .project-controls { display:grid; grid-template-columns:1fr; }
  .queue-grid { grid-template-columns:1fr; }
  .queue-actions { width:100%; flex-wrap:wrap; }
  .inspect-layout { flex-direction:column; }
  .inspect-sidebar { width:100%; max-width:260px; }
  .inspect-main { min-width:0; }
  .top-actions { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); }
  .top-actions select, .top-actions label { grid-column:1/-1; width:100%; }
  .top-actions > .btn { justify-content:center; text-align:center; white-space:normal; }
  .media-preview-box { grid-template-columns:1fr; }
  .media-preview-box > div:first-child { max-width:220px; }
  .step { align-items:flex-start; gap:8px; }
  .step-title { min-width:0; width:38%; flex:0 0 38%; }
  .step-detail { white-space:normal; overflow-wrap:anywhere; }
  table { display:block; overflow-x:auto; white-space:nowrap; }
  .modal-content { width:calc(100vw - 24px); max-width:none; padding:18px 14px; }
}
.playbook-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(230px,1fr)); gap:14px; }
.playbook-card { background:var(--bg); padding:16px; }
.playbook-card h3 { margin:4px 0 8px; font-size:14px; }
.playbook-card p { margin:0; color:var(--text-dim); font-size:12px; line-height:1.6; }
.playbook-icon { font-size:24px; }
.playbook-note { margin-top:16px; padding:12px 14px; border-radius:8px; background:rgba(56,189,248,.08); border:1px solid rgba(56,189,248,.18); color:#cbd5e1; font-size:12px; }
@media (max-width:700px) {
  .card-header { align-items:flex-start; flex-direction:column; gap:10px; }
  .project-controls { display:grid; grid-template-columns:1fr; }
  .queue-grid { grid-template-columns:1fr; }
  .queue-actions { width:100%; flex-wrap:wrap; }
  .inspect-layout { flex-direction:column; }
  .inspect-sidebar { width:100%; max-width:260px; }
  .inspect-main { min-width:0; }
  .top-actions { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); }
  .top-actions select, .top-actions label { grid-column:1/-1; width:100%; }
  .top-actions > .btn { justify-content:center; text-align:center; white-space:normal; }
  .media-preview-box { grid-template-columns:1fr; }
  .media-preview-box > div:first-child { max-width:220px; }
  .step { align-items:flex-start; gap:8px; }
  .step-title { min-width:0; width:38%; flex:0 0 38%; }
  .step-detail { white-space:normal; overflow-wrap:anywhere; }
  table { display:block; overflow-x:auto; white-space:nowrap; }
  .modal-content { width:calc(100vw - 24px); max-width:none; padding:18px 14px; }
}
</style>
</head>
<body>

<header>
  <div class="brand">
    <h1>🎬 Faceless Shorts Studio</h1>
    <span id="state-pill" class="pill idle">IDLE</span>
    <span id="active-slot" style="color:var(--text-dim); font-size:12px;"></span>
  </div>
  <div class="top-actions">
    <select id="engine-select" onchange="updateEngineControls()" style="background:#0b1320; border:1px solid #1e293b; color:#f3f4f6; font-size:12px; padding:6px 10px; border-radius:6px; cursor:pointer;" title="Production Engine">
      <option value="3d" selected>🚀 Three.js 3D WebGL Cinema</option>
      <option value="mpt">🎥 MoneyPrinterTurbo (stock-footage video)</option>
    </select>
    <select id="style-select" style="background:#0b1320; border:1px solid #1e293b; color:#f3f4f6; font-size:12px; padding:6px 10px; border-radius:6px; cursor:pointer;" title="Visual Style Standard; Cinematic What If applies to English only">
      <option value="auto" selected>🎯 Auto by channel (current channel styles)</option>
      <option value="engineering-explainer">🏗️ Engineering Explainer (3D art direction)</option>
      <option value="tall-tale">🛕 Tall Tale (3D storybook renderer)</option>
      <option value="cinematic-what-if">🎭 Cinematic What If (2D ink-vector; English only)</option>
    </select>
    <label style="color:var(--text-dim); font-size:12px; display:flex; align-items:center; gap:6px; cursor:pointer;">
      <input type="checkbox" id="dry-run-check"> DRY-RUN (No Upload)
    </label>
    <button id="run-en-btn" class="btn en" onclick="triggerRun('en')">▶ Run English</button>
    <button id="run-te-btn" class="btn te" onclick="triggerRun('te')">▶ Run Telugu</button>
    <button id="run-all-btn" class="btn primary" onclick="triggerRun('all')">▶ Run Both</button>
    <button id="stop-btn" class="btn danger" onclick="stopPipeline()" disabled title="Stops active generation and upload workers">🛑 Stop</button>
  </div>
</header>

<nav>
  <button data-tab="pipeline" class="active">⚡ Live Pipelines</button>
  <button data-tab="crafts">🎬 Production Guide</button>
  <button data-tab="projects">📁 Projects & Media</button>
  <button data-tab="trends">🔥 Trending Topics</button>
  <button data-tab="performance">📊 Performance Hub</button>
  <button data-tab="ledger">📖 Ledger (topics-done)</button>
  <button data-tab="logs">📜 Live Logs</button>
</nav>

<main id="app-content"></main>

<div id="modal" class="modal-backdrop" onclick="closeModal(event)">
  <div class="modal-content" onclick="event.stopPropagation()">
    <button class="close-btn" onclick="closeModal()">&times;</button>
    <div id="modal-body"></div>
  </div>
</div>

<script>
let currentTab = 'pipeline';
let pipelineRenderKey = '';
let refreshInFlight = false;
let statusData = null;
let queueData = null;
let projectFilterChannel = 'all';
let projectStatusFilter = 'all';
let projectSearchQuery = '';
let currentTrendChannel = 'en';
let currentTrendCategory = 'all';
let selectedStyleFilter = 'all';
let trendsLoading = false;
let trendsData = [];
let currentLogChannel = 'all';

async function api(path, options = {}) {
  try {
    const res = await fetch(path, options);
    const data = await res.json();
    if (!res.ok && !data.error) data.error = `Request failed (${res.status})`;
    return data;
  } catch (err) {
    console.error('API Error:', err);
    return { error: String(err) };
  }
}

function updateEngineControls() {
  const engine = document.getElementById('engine-select')?.value || '3d';
  const style = document.getElementById('style-select');
  if (style) {
    style.disabled = engine === 'mpt';
    style.title = engine === 'mpt' ? 'Visual styles apply to the Three.js engine; MPT uses stock footage.' : 'Visual style for the selected channel';
  }
}

function escapeHtml(s) {
  return (s || '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

function openModal(html) {
  document.getElementById('modal-body').innerHTML = html;
  document.getElementById('modal').classList.add('active');
}
function closeModal() {
  document.getElementById('modal').classList.remove('active');
}

document.querySelectorAll('nav button').forEach(btn => {
  btn.onclick = () => {
    document.querySelectorAll('nav button').forEach(b => b.classList.toggle('active', b === btn));
    currentTab = btn.dataset.tab;
    renderTab();
  };
});

async function refreshStatus() {
  if (refreshInFlight) return;
  refreshInFlight = true;
  try {
  statusData = await api('/api/status');
  if (statusData.error) return;
  queueData = await api('/api/queue');
  const pill = document.getElementById('state-pill');
  if (statusData.running_en && statusData.running_te) {
    pill.textContent = 'BOTH RUNNING';
    pill.className = 'pill run';
  } else if (statusData.running_en) {
    pill.textContent = 'ENGLISH RUNNING';
    pill.className = 'pill run';
  } else if (statusData.running_te) {
    pill.textContent = 'TELUGU RUNNING';
    pill.className = 'pill run';
  } else if (statusData.broadcasting) {
    pill.textContent = 'BROADCASTING';
    pill.className = 'pill run';
  } else if (statusData.te?.last_failure) {
    pill.textContent = 'TELUGU RUN FAILED';
    pill.className = 'pill err';
  } else if (statusData.en?.last_failure) {
    pill.textContent = 'ENGLISH RUN FAILED';
    pill.className = 'pill err';
  } else {
    pill.textContent = 'IDLE';
    pill.className = 'pill idle';
  }
  document.getElementById('active-slot').textContent = `${statusData.date} · Scheduled runs 10:00 & 19:00 IST`;
  const stopButton = document.getElementById('stop-btn');
  ['run-en-btn', 'run-te-btn', 'run-all-btn'].forEach(id => {
    const button = document.getElementById(id);
    if (button) button.disabled = !!statusData.running;
  });
  if (stopButton) {
    stopButton.disabled = !(statusData.running || statusData.broadcasting);
    stopButton.title = stopButton.disabled ? 'No pipeline or broadcast is active' : 'Stop active generation and upload workers';
  }

  if (currentTab === 'pipeline') {
    renderPipelineTab();
  }
  } finally {
    refreshInFlight = false;
  }
}

function renderTab() {
  if (currentTab === 'pipeline') { pipelineRenderKey = ''; renderPipelineTab(); }
  else if (currentTab === 'crafts') renderCraftsTab();
  else if (currentTab === 'projects') renderProjectsTab();
  else if (currentTab === 'trends') renderTrendsTab();
  else if (currentTab === 'performance') renderPerformanceTab();
  else if (currentTab === 'ledger') renderLedgerTab();
  else if (currentTab === 'logs') renderLogsTab();
}

function renderCraftsTab() {
  document.getElementById('app-content').innerHTML = `
    <div class="card">
      <div class="card-header">
        <div>
          <h2 style="margin:0 0 4px;">🎬 Production Playbook</h2>
          <div style="font-size:12px; color:var(--text-dim);">A quick guide to what each run creates and what to review before release.</div>
        </div>
        <span class="pill idle">English + Telugu</span>
      </div>
      <div class="playbook-grid">
        <article class="card playbook-card"><div class="playbook-icon">✍️</div><h3>Story & facts</h3><p>Keep the channels in their own language and topic lane. Start with one clear question, explain the answer in connected spoken sentences, and keep on-screen text short.</p></article>
        <article class="card playbook-card"><div class="playbook-icon">🎥</div><h3>Visual direction</h3><p>For a 60–90 second video, aim for 18–24 purposeful shots across 3–5 topic-specific sets. Mix wide views, action, close detail, and changed camera angles.</p></article>
        <article class="card playbook-card"><div class="playbook-icon">🎙️</div><h3>Voice & sound</h3><p>Use one natural native-language narrator. Keep music low under speech, preserve pauses, and use only a few soft effects when an action needs emphasis.</p></article>
        <article class="card playbook-card"><div class="playbook-icon">🔎</div><h3>Review & release</h3><p>Check the contact sheet, captions, key scenes, and ending. Preview the mix and export before using the upload or broadcast controls.</p></article>
      </div>
      <div class="playbook-note"><b>Run controls:</b> choose a production engine and style above, then start one channel or both. DRY-RUN keeps the run from uploading. The Stop button is available only while work is active.</div>
    </div>
  `;
}

function renderPipelineTab() {
  if (!statusData) return;
  const en = statusData.en || {};
  const te = statusData.te || {};
  const renderKey = JSON.stringify({
    running: [en.running, te.running, statusData.broadcasting],
    channels: [en, te].map(ch => ({ project: ch.project, style: ch.style, status: ch.status, current: ch.current, last_failure: ch.last_failure,
      stages: (ch.stages || []).map(stage => [stage.id, stage.done]),
      media: [ch.has_render, ch.has_cover, ch.has_sheet, ch.has_audio, ch.video_id] })),
    slot: queueData?.slot?.next_slot_name,
    queue: (queueData?.queued || []).map(item => [item.project, item.video_id, item.has_cover]),
  });
  if (renderKey === pipelineRenderKey) return;
  pipelineRenderKey = renderKey;

  const makeStepper = (ch) => {
    if (!ch.stages) return '<div style="color:var(--text-dim); padding:10px;">No stages loaded</div>';
    return ch.stages.map(s => {
      // Strictly require that THIS specific channel is running before showing current movement
      const isCur = ch.running && ch.current === s.id;
      const cls = isCur ? 'current' : (s.done ? 'done' : 'pending');
      return `<div class="step ${cls}">
        <span class="dot"></span>
        <span class="step-title">${escapeHtml(s.name)}</span>
        <span class="step-detail">${escapeHtml(s.detail || '')}</span>
      </div>`;
    }).join('');
  };

  const makeFailureNotice = (ch) => ch.last_failure ? `<div class="run-failure" role="status"><b>Last run failed</b><span>${escapeHtml(ch.last_failure.message)}</span><button class="btn" onclick="document.querySelector('[data-tab=logs]').click()">Open logs</button></div>` : '';

  const makePreviewBox = (ch) => {
    if (!ch.project) return '<div style="color:var(--text-dim); padding:12px;">No active project generated yet today.</div>';
    return `<div class="media-preview-box">
      <div>
        ${ch.has_render ? `
          <video class="preview-vid" controls preload="metadata" src="/api/vid?project=${ch.project}"></video>
        ` : (ch.has_cover ? `<img class="preview-cover" src="/api/thumb?project=${ch.project}" onclick="openImage('/api/thumb?project=${ch.project}')">` : '<div style="aspect-ratio:9/16; background:#000; border-radius:8px; display:flex; align-items:center; justify-content:center; color:var(--text-dim);">No render yet</div>')}
      </div>
      <div>
        <div style="font-weight:700; font-size:15px; margin-bottom:4px;">${escapeHtml(ch.project)}</div>
        <div style="color:var(--text-dim); font-size:12px; margin-bottom:10px;">
          Style: <b style="color:var(--text);">${escapeHtml(ch.style || 'auto')}</b> · Status: <span style="color:var(--ok); font-weight:600;">${escapeHtml(ch.status || 'READY')}</span>
        </div>
        ${ch.video_id ? `<div style="margin-bottom:8px;">🔗 <a href="https://youtu.be/${ch.video_id}" target="_blank" style="color:var(--en-accent); font-weight:700;">youtu.be/${ch.video_id}</a> <span style="color:var(--ok); font-size:11px; margin-left:6px;">✓ Uploaded</span></div>` : (ch.has_render ? '<div style="margin-bottom:8px;"><span style="color:#f59e0b; font-size:12px; font-weight:700;">⚡ Unuploaded (Render Ready)</span></div>' : '')}
        ${ch.has_audio ? `
          <label style="font-size:11px; color:var(--text-dim);">Sound & Music Mix (mix.wav):</label>
          <audio controls src="/api/audio?project=${ch.project}&type=mix"></audio>
        ` : ''}
        <div class="toolbar">
          ${ch.has_sheet ? `<button class="btn" onclick="openImage('/api/sheet?project=${ch.project}')">🔍 QA Sheet</button>` : ''}
          ${ch.has_render && !ch.video_id ? `<button class="btn primary" style="background:linear-gradient(135deg, #dc2626, #b91c1c); color:#fff; font-weight:700;" onclick="uploadProject('${ch.project}', true)">🚀 Upload to YouTube</button>` : (ch.video_id ? `<a class="btn" href="https://youtu.be/${ch.video_id}" target="_blank" style="background:#059669; color:#fff; text-decoration:none; font-weight:600;">▶ Watch on YouTube</a>` : '')}
          <button class="btn" onclick="inspectProject('${ch.project}')">Inspect Project</button>
        </div>
      </div>
    </div>`;
  };

  const makeQueueBanner = () => {
    const queueSlot = queueData?.slot || {};
    const queuedItems = queueData?.queued || [];
    const enQueued = queuedItems.find(q => q.channel === 'en');
    const teQueued = queuedItems.find(q => q.channel === 'te');

    return `
      <div class="card" style="margin-bottom: 20px; border-left: 4px solid #f59e0b; background: linear-gradient(180deg, rgba(245, 158, 11, 0.05) 0%, var(--panel) 100%);">
        <div class="card-header" style="border-bottom: 1px solid var(--border); padding-bottom: 12px; margin-bottom: 14px;">
          <div>
            <h2 style="display:flex; align-items:center; gap:8px; font-size:16px;">
              <span>📡 Broadcast Staging Queue</span>
              <span class="pill" style="background:#f59e0b20; color:#f59e0b; border:1px solid #f59e0b60;">Next Slot: ${escapeHtml(queueSlot.next_slot_name || '10:00 AM')}</span>
              ${statusData.broadcasting ? `
                <span class="pill" style="background:#10b98125; color:#10b981; border:1px solid #10b981; animation: pulse 1.5s infinite; cursor:pointer;" onclick="openBroadcastModal()">
                  📡 Broadcasting Live (PID: ${statusData.broadcast_pid}) — Click to Observe
                </span>
              ` : ''}
            </h2>
            <div style="font-size:12px; color:var(--text-dim); margin-top:4px;">
              <b>Publish-Then-Produce:</b> When 10:00 AM or 7:00 PM triggers fire, queued videos upload instantly, then pre-production runs for the next slot.
            </div>
          </div>
          <div class="queue-actions">
            <button class="btn" onclick="refreshStatus()" title="Refresh queue">🔄 Refresh</button>
            ${statusData.broadcasting ? `
              <button class="btn primary" style="background:linear-gradient(135deg, #2563eb, #1d4ed8); font-weight:700;" onclick="openBroadcastModal()">📡 View Live Broadcast</button>
              <button class="btn" style="background:#dc2626; color:#fff; font-weight:700;" onclick="stopBroadcast()">🛑 Stop Broadcast</button>
            ` : `
              <button class="btn primary" style="background:linear-gradient(135deg, #10b981, #059669); font-weight:700;" onclick="triggerBroadcast('all')">⚡ Broadcast Now (All)</button>
            `}
          </div>
        </div>
        <div class="queue-grid">
          <!-- English Queue Box -->
          <div style="background:var(--bg); border:1px solid var(--border); border-radius:8px; padding:12px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
              <span class="channel-tag en">🇬🇧 Curiography (English)</span>
              ${enQueued ? `<span style="font-size:11px; color:#10b981; font-weight:700;">✓ Ready for Next Slot</span>` : `<span style="font-size:11px; color:var(--text-dim);">⏳ No Staged Video</span>`}
            </div>
            ${enQueued ? `
              <div style="font-weight:700; font-size:13px; margin-bottom:4px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${escapeHtml(enQueued.title)}</div>
              <div style="font-size:11.5px; color:var(--text-dim); margin-bottom:8px;">
                Project: <code>${escapeHtml(enQueued.project)}</code> · ${(enQueued.video_size_mb || enQueued.size_mb || 0).toFixed(1)} MB · ${enQueued.has_cover ? '✓ Cover OK' : '⚠ Missing Cover'}
              </div>
              <button class="btn" style="width:100%; font-size:11.5px;" onclick="triggerBroadcast('en')">🚀 Broadcast English Now</button>
            ` : `
              <div style="font-size:12px; color:var(--text-dim); padding:8px 0;">No pre-rendered English short waiting. Run pipeline to stage next video.</div>
              <button class="btn" style="width:100%; font-size:11.5px;" onclick="triggerRun('en')">▶ Pre-produce English Video</button>
            `}
          </div>

          <!-- Telugu Queue Box -->
          <div style="background:var(--bg); border:1px solid var(--border); border-radius:8px; padding:12px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
              <span class="channel-tag te">🇮🇳 Asakthi (Telugu)</span>
              ${teQueued ? `<span style="font-size:11px; color:#10b981; font-weight:700;">✓ Ready for Next Slot</span>` : `<span style="font-size:11px; color:var(--text-dim);">⏳ No Staged Video</span>`}
            </div>
            ${teQueued ? `
              <div style="font-weight:700; font-size:13px; margin-bottom:4px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${escapeHtml(teQueued.title)}</div>
              <div style="font-size:11.5px; color:var(--text-dim); margin-bottom:8px;">
                Project: <code>${escapeHtml(teQueued.project)}</code> · ${(teQueued.video_size_mb || teQueued.size_mb || 0).toFixed(1)} MB · ${teQueued.has_cover ? '✓ Cover OK' : '⚠ Missing Cover'}
              </div>
              <button class="btn" style="width:100%; font-size:11.5px;" onclick="triggerBroadcast('te')">🚀 Broadcast Telugu Now</button>
            ` : `
              <div style="font-size:12px; color:var(--text-dim); padding:8px 0;">No pre-rendered Telugu short waiting. Run pipeline to stage next video.</div>
              <button class="btn" style="width:100%; font-size:11.5px;" onclick="triggerRun('te')">▶ Pre-produce Telugu Video</button>
            `}
          </div>
        </div>
      </div>
    `;
  };

  document.getElementById('app-content').innerHTML = `
    ${makeQueueBanner()}
    <div class="grid-2">
      <div class="card">
        <div class="card-header">
          <h2>
            🇬🇧 Curiography <span class="channel-tag en">English</span>
            <span class="pill ${en.running ? 'run' : (en.last_failure ? 'err' : 'idle')}" style="margin-left:6px;">${en.running ? 'RUNNING' : (en.last_failure ? 'FAILED' : 'IDLE')}</span>
          </h2>
          <span style="font-size:12px; color:var(--text-dim);">${en.project || 'Pending today'}</span>
        </div>
        ${makeFailureNotice(en)}
        <div class="stepper">${makeStepper(en)}</div>
        ${makePreviewBox(en)}
      </div>

      <div class="card">
        <div class="card-header">
          <h2>
            🇮🇳 Asakthi <span class="channel-tag te">Telugu</span>
            <span class="pill ${te.running ? 'run' : (te.last_failure ? 'err' : 'idle')}" style="margin-left:6px;">${te.running ? 'RUNNING' : (te.last_failure ? 'FAILED' : 'IDLE')}</span>
          </h2>
          <span style="font-size:12px; color:var(--text-dim);">${te.project || 'Pending today'}</span>
        </div>
        ${makeFailureNotice(te)}
        <div class="stepper">${makeStepper(te)}</div>
        ${makePreviewBox(te)}
      </div>
    </div>
  `;
}

async function renderProjectsTab() {
  const data = await api('/api/projects');
  const allProjects = data.projects || [];
  const enProjects = allProjects.filter(p => p.channel === 'curiography');
  const teProjects = allProjects.filter(p => p.channel === 'asakthi');

  const renderProjectCard = (p) => {
    const projectArg = encodeURIComponent(p.name);
    const projectState = p.is_uploaded ? 'uploaded' : (p.has_render ? 'ready' : 'draft');
    return `
    <div class="card project-card" data-project-card data-project-name="${escapeHtml((p.name + ' ' + (p.title || '')).toLowerCase())}" data-project-channel="${p.channel === 'asakthi' ? 'te' : 'en'}" data-project-state="${projectState}" role="button" tabindex="0" style="padding:14px; background:var(--bg); border-color:var(--border); cursor:pointer;" onclick="inspectProject(decodeURIComponent('${projectArg}'))" onkeydown="if(event.key==='Enter'||event.key===' '){event.preventDefault();inspectProject(decodeURIComponent('${projectArg}'))}">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
        <span class="channel-tag ${p.channel === 'asakthi' ? 'te' : 'en'}">${p.channel === 'asakthi' ? '🇮🇳 Telugu' : '🇬🇧 English'}</span>
        <span style="font-size:11px; color:var(--text-dim);">${(p.mp4_size / 1024 / 1024).toFixed(1)} MB</span>
      </div>
      <div style="font-weight:700; font-size:14px; margin-bottom:2px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;" title="${escapeHtml(p.title || p.name)}">${escapeHtml(p.title || p.name)}</div>
      <div style="font-size:11px; color:var(--text-dim); margin-bottom:6px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${escapeHtml(p.name)}</div>
      <div style="font-size:11.5px; margin-bottom:8px;">
        ${p.is_uploaded ? `<span style="color:#10b981; font-weight:700;">✓ Uploaded</span> <a href="${p.youtube_url || ('https://youtu.be/' + p.video_id)}" target="_blank" onclick="event.stopPropagation();" style="color:var(--en-accent); font-size:11px; margin-left:4px;">${p.video_id}</a>` : (p.has_render ? '<span style="color:#f59e0b; font-weight:700;">⚡ Unuploaded (Ready)</span>' : '<span style="color:var(--text-dim);">⏳ No render</span>')}
      </div>
      ${p.has_cover ? `<img src="/api/thumb?project=${projectArg}" style="width:100%; height:190px; object-fit:contain; background:#000; border-radius:6px; margin-bottom:8px;">` : '<div style="height:190px; background:#000; border-radius:6px; display:flex; align-items:center; justify-content:center; color:var(--text-dim); margin-bottom:8px;">No cover</div>'}
      <div style="display:flex; justify-content:space-between; font-size:11px; color:var(--text-dim); margin-bottom:8px;">
        <span>${p.has_render ? '🎬 Rendered' : '⏳ No render'}</span>
        <span>${p.has_audio ? '🎵 Audio' : 'No mix'}</span>
      </div>
      ${p.has_render && !p.is_uploaded ? `
        <button class="btn primary" style="width:100%; padding:6px 10px; font-size:12px; background:linear-gradient(135deg, #dc2626, #b91c1c); color:#fff; font-weight:700;" onclick="event.stopPropagation(); uploadProject(decodeURIComponent('${projectArg}'), true)">🚀 Upload to YouTube</button>
      ` : (p.is_uploaded ? `
        <a class="btn" style="width:100%; padding:6px 10px; font-size:12px; display:block; text-align:center; box-sizing:border-box; background:#059669; color:#fff; text-decoration:none; font-weight:600;" href="${p.youtube_url || ('https://youtu.be/' + p.video_id)}" target="_blank" onclick="event.stopPropagation();">▶ Watch on YouTube</a>
      ` : '')}
    </div>
  `;
  };

  document.getElementById('app-content').innerHTML = `
    <div class="card">
      <div class="card-header">
        <div>
          <h2 style="margin:0 0 4px 0;">📁 Projects & Media Archive</h2>
          <div style="font-size:12px; color:var(--text-dim);">
            Isolated channels · English (Curiography) and Telugu (Asakthi)
          </div>
        </div>
        <div style="font-size:12px; color:var(--text-dim);">
          Total: <b>${allProjects.length}</b> (🇬🇧 ${enProjects.length} · 🇮🇳 ${teProjects.length})
        </div>
      </div>

      <div class="project-controls">
        <input id="project-search" type="search" placeholder="Search project or title…" aria-label="Search projects" value="${escapeHtml(projectSearchQuery)}" oninput="projectSearchQuery=this.value;filterProjectCards()">
        <select id="project-state-filter" onchange="projectStatusFilter=this.value;filterProjectCards()" aria-label="Filter project status">
          <option value="all">All statuses</option><option value="ready">Ready to upload</option><option value="uploaded">Uploaded</option><option value="draft">In progress / no render</option>
        </select>
        <span id="project-visible-count" class="count-note">${allProjects.length} projects</span>
      </div>
      <div class="sub-nav">
        <button class="${projectFilterChannel === 'all' ? 'active' : ''}" onclick="setProjectChannelFilter('all')">
          📂 All Projects (${allProjects.length})
        </button>
        <button class="en ${projectFilterChannel === 'en' ? 'active en' : ''}" onclick="setProjectChannelFilter('en')">
          🇬🇧 English Archive (Curiography) · ${enProjects.length}
        </button>
        <button class="te ${projectFilterChannel === 'te' ? 'active te' : ''}" onclick="setProjectChannelFilter('te')">
          🇮🇳 Telugu Archive (Asakthi) · ${teProjects.length}
        </button>
      </div>

      ${(projectFilterChannel === 'all' || projectFilterChannel === 'en') ? `
        <div class="channel-section-header en" data-project-section="en">
          <h3>🇬🇧 Curiography Video Archive (English Sci/Tech Procedurals)</h3>
          <span style="font-size:12px; font-weight:700; color:var(--en-accent);">${enProjects.length} videos</span>
        </div>
        <div class="project-grid" data-project-grid="en">
          ${enProjects.length > 0 ? enProjects.map(renderProjectCard).join('') : '<div style="color:var(--text-dim); padding:20px;">No English projects found.</div>'}
        </div>
      ` : ''}

      ${(projectFilterChannel === 'all' || projectFilterChannel === 'te') ? `
        <div class="channel-section-header te" data-project-section="te">
          <h3>🇮🇳 Asakthi Video Archive (Telugu Mythology, Lore & Traditions)</h3>
          <span style="font-size:12px; font-weight:700; color:var(--te-accent);">${teProjects.length} videos</span>
        </div>
        <div class="project-grid" data-project-grid="te">
          ${teProjects.length > 0 ? teProjects.map(renderProjectCard).join('') : '<div style="color:var(--text-dim); padding:20px;">No Telugu projects found.</div>'}
        </div>
      ` : ''}
    </div>
  `;
  filterProjectCards();
}

function setProjectChannelFilter(filter) {
  projectFilterChannel = filter;
  renderProjectsTab();
}

function filterProjectCards() {
  const query = projectSearchQuery.trim().toLowerCase();
  let visible = 0;
  document.querySelectorAll('[data-project-card]').forEach(card => {
    const channelOk = projectFilterChannel === 'all' || card.dataset.projectChannel === projectFilterChannel;
    const queryOk = !query || card.dataset.projectName.includes(query);
    const statusOk = projectStatusFilter === 'all' || card.dataset.projectState === projectStatusFilter;
    const show = channelOk && queryOk && statusOk;
    card.hidden = !show;
    if (show) visible++;
  });
  document.querySelectorAll('[data-project-section]').forEach(section => {
    const channel = section.dataset.projectSection;
    const grid = document.querySelector(`[data-project-grid="${channel}"]`);
    const sectionVisible = !!grid && [...grid.querySelectorAll('[data-project-card]')].some(card => !card.hidden);
    section.hidden = !sectionVisible;
    if (grid) grid.hidden = !sectionVisible;
  });
  const count = document.getElementById('project-visible-count');
  if (count) count.textContent = `${visible} project${visible === 1 ? '' : 's'}`;
}

async function renderTrendsTab() {
  const container = document.getElementById('app-content');
  const isTe = currentTrendChannel === 'te';

  container.innerHTML = `
    <div class="card">
      <div class="card-header">
        <div>
          <h2 style="margin:0 0 4px 0;">
            🔥 ${isTe ? '🇮🇳 Telugu Lore, Temple Mysteries & Traditions (Asakthi)' : '🇬🇧 Viral Science & Curiosity Trend Hunter (Curiography)'}
          </h2>
          <div style="font-size:12px; color:var(--text-dim);">
            ${isTe ? 'Sanatana Dharma temple mysteries, epic Puranic feats, Telugu cultural heritage & tradition science' : 'Real-time breaking science from Google Trends US, ScienceDaily & Phys.org · Curiosity ranked'}
          </div>
        </div>
        <div class="trend-controls">
          ${!isTe ? `
            <select id="trend-style-select" class="btn" onchange="changeTrendStyle(this.value)">
              <option value="all" ${selectedStyleFilter === 'all' ? 'selected' : ''}>All Styles</option>
              <option value="engineering-explainer" ${selectedStyleFilter === 'engineering-explainer' ? 'selected' : ''}>Engineering Explainer</option>
              <option value="engineering-explainer" ${selectedStyleFilter === 'engineering-explainer' ? 'selected' : ''}>Engineering Explainer (3D)</option>
              <option value="tall-tale" ${selectedStyleFilter === 'tall-tale' ? 'selected' : ''}>Tall Tale (3D storybook)</option>
              <option value="cinematic-what-if" ${selectedStyleFilter === 'cinematic-what-if' ? 'selected' : ''}>Cinematic What If (2D Ink Vector)</option>
            </select>
          ` : `
            <select id="trend-category-select" class="btn te" onchange="changeTrendCategory(this.value)">
              <option value="all" ${currentTrendCategory === 'all' ? 'selected' : ''}>అన్ని విభాగాలు (All Categories)</option>
              <option value="storybooks" ${currentTrendCategory === 'storybooks' ? 'selected' : ''}>చందమామ & తెలుగు కథల పుస్తకాలు (Storybooks & Chandamama)</option>
              <option value="epics" ${currentTrendCategory === 'epics' ? 'selected' : ''}>హిందూ పురాణ గాథలు (Hindu Epics & Mythology)</option>
              <option value="temples" ${currentTrendCategory === 'temples' ? 'selected' : ''}>దేవాలయ అద్భుతాలు (Temple Marvels)</option>
              <option value="science_tradition" ${currentTrendCategory === 'science_tradition' ? 'selected' : ''}>సంప్రదాయ విజ్ఞానం (Tradition Science)</option>
              <option value="legends" ${currentTrendCategory === 'legends' ? 'selected' : ''}>చారిత్రక చమత్కారాలు (Historical Legends)</option>
            </select>
            <select id="trend-style-select" class="btn te" onchange="changeTrendStyle(this.value)">
              <option value="all" ${selectedStyleFilter === 'all' ? 'selected' : ''}>అన్ని శైలులు (All Styles)</option>
              <option value="tall-tale" ${selectedStyleFilter === 'tall-tale' ? 'selected' : ''}>Tall Tale (పురాణ గాథలు)</option>
            </select>
          `}
          <button class="btn primary" onclick="fetchAndRenderTrends(true)" id="trends-refresh-btn">
            🔄 ${isTe ? 'Refresh Topics' : 'Scan Breaking Feeds'}
          </button>
        </div>
      </div>

      <div class="sub-nav">
        <button class="en ${currentTrendChannel === 'en' ? 'active en' : ''}" onclick="setTrendChannel('en')">
          🇬🇧 English Viral Science (Curiography)
        </button>
        <button class="te ${currentTrendChannel === 'te' ? 'active te' : ''}" onclick="setTrendChannel('te')">
          🇮🇳 Telugu Lore & Traditions (Asakthi)
        </button>
      </div>

      <div id="trends-list">
        ${trendsLoading ? '<div style="padding:40px; text-align:center; color:var(--text-dim);">📡 Scanning topics and filtering against ledger...</div>' : ''}
      </div>
    </div>
  `;

  if (!trendsLoading && trendsData.length === 0) {
    await fetchAndRenderTrends(false);
  } else if (!trendsLoading) {
    renderTrendsList();
  }
}

async function setTrendChannel(ch) {
  if (currentTrendChannel === ch) return;
  currentTrendChannel = ch;
  selectedStyleFilter = 'all';
  currentTrendCategory = 'all';
  trendsData = [];
  await fetchAndRenderTrends(true);
}

async function changeTrendCategory(cat) {
  currentTrendCategory = cat;
  await fetchAndRenderTrends(true);
}

async function changeTrendStyle(val) {
  selectedStyleFilter = val;
  await fetchAndRenderTrends(true);
}

async function fetchAndRenderTrends(force = false) {
  trendsLoading = true;
  const listEl = document.getElementById('trends-list');
  if (listEl) {
    listEl.innerHTML = '<div style="padding:40px; text-align:center; color:var(--text-dim);">📡 Loading channel topics...</div>';
  }

  let query = `?channel=${currentTrendChannel}&count=9`;
  if (selectedStyleFilter !== 'all') {
    query += `&style=${selectedStyleFilter}`;
  }
  if (currentTrendChannel === 'te' && currentTrendCategory !== 'all') {
    query += `&category=${currentTrendCategory}`;
  }

  const data = await api('/api/trends' + query);
  trendsData = data.trends || [];
  trendsLoading = false;
  renderTrendsList();
}

function renderTrendsList() {
  const listEl = document.getElementById('trends-list');
  if (!listEl) return;

  if (trendsData.length === 0) {
    listEl.innerHTML = `
      <div style="padding:40px; text-align:center; color:var(--text-dim);">
        No topics found matching this criteria, or candidates are already covered in ledger.
        <br><br>
        <button class="btn" onclick="fetchAndRenderTrends(true)">Force Re-scan</button>
      </div>
    `;
    return;
  }

  const isTe = currentTrendChannel === 'te';

  listEl.innerHTML = `
    <div style="display:grid; grid-template-columns: repeat(auto-fill, minmax(min(340px, 100%), 1fr)); gap:18px; margin-top:10px;">
      ${trendsData.map((t) => `
        <div class="card" style="background:var(--bg); border:1px solid var(--border); display:flex; flex-direction:column; justify-content:space-between; padding:16px;">
          <div>
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
              <span class="channel-tag ${isTe ? 'te' : 'en'}" style="background:${isTe ? 'rgba(251,191,36,0.15)' : 'rgba(56,189,248,0.15)'};">
                🔥 ${t.curiosity_score || 9}/10 Curiosity
              </span>
              <span style="font-size:11px; color:var(--text-dim); text-transform:uppercase;">
                ${escapeHtml(t.source || (isTe ? 'Telugu Heritage' : 'Breaking News'))}
              </span>
            </div>

            <h3 style="margin:0 0 4px 0; font-size:15px; line-height:1.4;">
              ${escapeHtml(t.title)}
            </h3>

            ${t.english_title ? `
              <div style="font-size:11.5px; color:var(--text-dim); margin-bottom:8px; font-style:italic;">
                ${escapeHtml(t.english_title)}
              </div>
            ` : ''}

            <div style="font-size:11px; margin-bottom:12px; display:flex; gap:6px; flex-wrap:wrap;">
              <span class="channel-tag ${isTe ? 'te' : 'en'}" style="font-size:10px;">
                🎯 Style: ${escapeHtml(t.assigned_style || 'auto')}
              </span>
              ${t.deity ? `<span class="channel-tag te" style="font-size:10px;">🛕 ${escapeHtml(t.deity)}</span>` : ''}
              ${t.location ? `<span class="channel-tag" style="background:rgba(59,130,246,0.12); color:#60a5fa; font-size:10px;">📍 ${escapeHtml(t.location)}</span>` : ''}
              ${t.map_region ? `<span class="channel-tag" style="background:rgba(234,179,8,0.12); color:#facc15; font-size:10px;">🗺️ ${escapeHtml(t.map_region)}</span>` : ''}
              ${t.category ? `<span class="channel-tag" style="background:rgba(255,255,255,0.06); color:var(--text-dim); font-size:10px;">${escapeHtml(t.category)}</span>` : ''}
            </div>

            <details class="topic-details">
              <summary>Research notes, structure and hook ideas</summary>
              <p style="font-size:12px; color:var(--text-dim); line-height:1.5; margin:10px 0 14px;">
                ${escapeHtml(t.summary || '')}
              </p>

            ${(t.engineering_steps && t.engineering_steps.breakthrough) ? `
              <div style="font-size:11px; color:#10b981; background:rgba(16,185,129,0.08); border:1px solid rgba(16,185,129,0.2); border-radius:6px; padding:6px 8px; margin-bottom:12px; line-height:1.4;">
                <strong style="color:#34d399;">⚙️ Structural Breakthrough:</strong> ${escapeHtml(t.engineering_steps.breakthrough)}
              </div>
            ` : ''}

            ${(t.hook_angles && t.hook_angles.length > 0) ? `
              <div style="background:var(--surface); border:1px solid var(--border); border-radius:6px; padding:10px; margin-bottom:14px;">
                <div style="font-size:11px; font-weight:700; color:var(--text-dim); margin-bottom:6px;">VIRAL HOOK ANGLES:</div>
                ${t.hook_angles.map(h => `
                  <div style="font-size:11px; color:var(--text); padding:4px 0; border-bottom:1px dashed rgba(255,255,255,0.05); cursor:pointer;" onclick="promptCreateShortWithTopic('${escapeHtml(h).replace(/'/g, "\\'")}', '${t.assigned_style}', '${isTe ? 'te' : 'en'}')" title="Click to create video with this hook">
                    ⚡ "${escapeHtml(h)}"
                  </div>
                `).join('')}
              </div>
            ` : ''}
            </details>
          </div>

          <div style="padding-top:10px; border-top:1px solid var(--border);">
            <button class="btn ${isTe ? 'te' : 'primary'}" style="width:100%; font-size:12px;" onclick="promptCreateShortWithTopic('${escapeHtml(t.title).replace(/'/g, "\\'")}', '${t.assigned_style}', '${isTe ? 'te' : 'en'}')">
              🎬 Create Short For ${isTe ? 'Asakthi (Telugu)' : 'Curiography (English)'}
            </button>
          </div>
        </div>
      `).join('')}
    </div>
  `;
}

function promptCreateShortWithTopic(topic, style, targetChannel = 'en') {
  const globalStyle = document.getElementById('style-select')?.value || 'auto';
  const recommendedStyle = (style && style !== 'auto') ? style : (globalStyle !== 'auto' ? globalStyle : (targetChannel === 'en' ? 'engineering-explainer' : 'tall-tale'));
  const preferredEngine = document.getElementById('engine-select')?.value || '3d';
  openModal(`
    <div style="max-width:460px;">
      <h3 style="margin-top:0;">Launch Short Creation</h3>
      <p style="font-size:13px; color:var(--text-dim); line-height:1.4;">
        Start automated short-form generation for this topic:
      </p>
      <div style="background:var(--bg); border:1px solid var(--border); padding:10px; border-radius:6px; font-weight:600; font-size:13px; margin-bottom:14px;">
        ${escapeHtml(topic)}
      </div>
      <div style="font-size:12px; margin-bottom:14px; background:#0b1320; border:1px solid #1e293b; padding:10px; border-radius:6px;">
        <label style="font-weight:600; display:block; margin-bottom:6px; color:#f3f4f6;">Production Engine:</label>
        <label style="display:flex; align-items:center; gap:6px; margin-bottom:6px; font-size:12px; cursor:pointer;">
          <input type="radio" name="engine-mode" value="3d" ${preferredEngine === '3d' ? 'checked' : ''} onchange="document.getElementById('modal-style-select').disabled=false"> 🚀 <b>Three.js 3D WebGL Cinema</b> (Procedural 3D + Neural Voice + Foley)
        </label>
        <label style="display:flex; align-items:center; gap:6px; margin-bottom:10px; font-size:12px; cursor:pointer;">
          <input type="radio" name="engine-mode" value="mpt" ${preferredEngine === 'mpt' ? 'checked' : ''} onchange="document.getElementById('modal-style-select').disabled=true"> 🎥 <b>MoneyPrinterTurbo Engine</b> (stock B-roll draft; simpler visuals)
        </label>
        <label style="font-weight:600; display:block; margin-bottom:6px; color:#f3f4f6;">Visual Style:</label>
        <select id="modal-style-select" ${preferredEngine === 'mpt' ? 'disabled' : ''} style="width:100%; background:var(--surface); border:1px solid var(--border); color:var(--text); font-size:12px; padding:6px; border-radius:6px;">
          <option value="${recommendedStyle}">🎯 Recommended: ${escapeHtml(recommendedStyle)}</option>
          <option value="engineering-explainer">🏗️ 3D Engineering Explainer (maps, cutaways, construction steps)</option>
          <option value="tall-tale">🛕 Tall Tale (3D storybook renderer)</option>
          <option value="cinematic-what-if">🎭 Cinematic What If (2D ink-vector; English only)</option>
        </select>
      </div>
      <div style="display:flex; flex-direction:column; gap:10px;">
        ${targetChannel === 'en' ? `
          <button class="btn en" onclick="startGenerationForTopic('${encodeURIComponent(topic)}', 'en')">▶ Generate for English (Curiography)</button>
        ` : `
          <button class="btn te" onclick="startGenerationForTopic('${encodeURIComponent(topic)}', 'te')">▶ Generate for Telugu (Asakthi)</button>
        `}
        <button class="btn" onclick="startGenerationForTopic('${encodeURIComponent(topic)}', '${targetChannel === 'te' ? 'en' : 'te'}')">▶ Generate for Other Channel</button>
      </div>
    </div>
  `);
}

async function startGenerationForTopic(encodedTopic, channel) {
  const topic = decodeURIComponent(encodedTopic);
  const dry = document.getElementById('dry-run-check')?.checked || false;
  const engine = document.querySelector('input[name="engine-mode"]:checked')?.value || '3d';
  const style = document.getElementById('modal-style-select')?.value || 'auto';
  closeModal();

  const res = await api('/api/run', {
    method: 'POST',
    body: JSON.stringify({ channel, dry, topic, engine, style, format: 'short' })
  });

  if (res.ok) {
    alert(`Pipeline (${engine.toUpperCase()}) triggered for "${topic}" (${channel.toUpperCase()})`);
    currentTab = 'pipeline';
    document.querySelectorAll('nav button').forEach(b => b.classList.toggle('active', b.dataset.tab === 'pipeline'));
    refreshStatus().then(renderPipelineTab);
  } else {
    alert('Failed to start run: ' + res.error);
  }
}

async function inspectProject(projName) {
  const data = await api('/api/project_details?project=' + projName);
  const script = data.script || {};
  const lines = script.lines || [];
  const cast = script.cast || {};

  openModal(`
    <div class="inspect-layout">
      <div class="inspect-sidebar">
        ${data.has_render ? `
          <video class="preview-vid" controls src="/api/vid?project=${projName}"></video>
        ` : (data.has_cover ? `<img class="preview-cover" src="/api/thumb?project=${projName}">` : '')}
        ${data.has_mix ? `
          <div style="margin-top:10px;">
            <label style="font-size:11px; color:var(--text-dim);">Audio Mix:</label>
            <audio controls src="/api/audio?project=${projName}&type=mix"></audio>
          </div>
        ` : ''}
        ${data.has_sheet ? `
          <button class="btn" style="width:100%; margin-top:10px;" onclick="openImage('/api/sheet?project=${projName}')">🔍 View QA Contact Sheet</button>
        ` : ''}
      </div>
      <div class="inspect-main">
        <div style="display:flex; align-items:center; gap:10px; margin-bottom:12px;">
          <h2 style="margin:0; font-size:18px;">${escapeHtml(projName)}</h2>
          <span class="channel-tag ${data.channel === 'asakthi' ? 'te' : 'en'}">${data.channel}</span>
          ${data.is_uploaded ? `
            <span class="pill ok" style="margin-left:4px;">✓ UPLOADED</span>
          ` : (data.has_render ? `
            <span class="pill run" style="margin-left:4px; background:rgba(245,158,11,0.15); color:#f59e0b; border-color:rgba(245,158,11,0.3);">⚡ UNUPLOADED (READY)</span>
          ` : '')}
        </div>
        <div style="background:var(--bg); padding:12px; border-radius:8px; border:1px solid var(--border); margin-bottom:16px;">
          <div style="font-size:15px; font-weight:700; color:#fff; margin-bottom:6px;">${escapeHtml(script.title || 'Untitled')}</div>
          <div style="font-size:12px; color:var(--text-dim);">
            Voice: ${escapeHtml(script.voice || '—')} · Speed: ${script.speed || 1.0} · Music: ${escapeHtml(script.music || 'bed')}
          </div>
          ${Object.keys(cast).length > 0 ? `
            <div style="margin-top:10px; padding:8px 10px; background:rgba(168,85,247,0.08); border:1px solid rgba(168,85,247,0.25); border-radius:6px; font-size:11.5px;">
              <div style="font-weight:700; color:var(--purple); margin-bottom:6px;">👥 Cast Ensemble (${Object.keys(cast).length} Roles)</div>
              <div style="display:flex; flex-wrap:wrap; gap:8px;">
                ${Object.entries(cast).map(([id, c]) => {
                  const ccol = c.color || '#a855f7';
                  return `
                    <span style="background:var(--surface); border:1px solid var(--border); padding:3px 8px; border-radius:4px; font-size:11px;">
                      <span style="display:inline-block; width:8px; height:8px; border-radius:50%; background:${ccol}; margin-right:4px;"></span>
                      <b>${escapeHtml(c.name || id)}</b>: ${escapeHtml(c.voice || 'default')} (${c.pitch || '0Hz'})
                    </span>
                  `;
                }).join('')}
              </div>
            </div>
          ` : ''}
        </div>
        <div style="max-height:240px; overflow:auto; border:1px solid var(--border); border-radius:8px; padding:10px; background:var(--bg);">
          <div style="font-size:12px; font-weight:700; color:var(--text-dim); margin-bottom:8px;">SCENE BREAKDOWN (${lines.length} cuts)</div>
          ${lines.map((l, i) => {
            const spkKey = l.speaker || '';
            const spkObj = cast[spkKey] || {};
            const spkName = l.speaker_name || spkObj.name || spkKey;
            const spkCol = l.speaker_color || spkObj.color || '#38bdf8';
            return `
              <div style="padding:6px 0; border-bottom:1px dashed var(--border); font-size:12px;">
                <div style="display:flex; align-items:center; gap:6px; margin-bottom:3px;">
                  <b>#${i+1}</b>
                  ${spkName ? `<span style="font-size:10.5px; font-weight:700; padding:1px 6px; border-radius:4px; background:${spkCol}22; color:${spkCol}; border:1px solid ${spkCol}55;">🎭 ${escapeHtml(spkName)}</span>` : ''}
                </div>
                <div>${escapeHtml(l.text)}</div>
                <div style="color:var(--text-dim); font-size:11px; font-family:monospace; margin-top:2px;">${escapeHtml(l.caps || '')}</div>
              </div>
            `;
          }).join('')}
        </div>
        ${(() => {
          const charList = Array.isArray(data.characters?.characters) ? data.characters.characters : (Array.isArray(data.characters) ? data.characters : Object.values(data.characters || {}));
          if (!charList || charList.length === 0) return '';
          return `
            <div style="margin-top:12px; background:var(--bg); border:1px solid var(--border); border-radius:8px; padding:10px;">
              <div style="font-size:11.5px; font-weight:700; color:var(--text-dim); margin-bottom:6px;">🎭 CHARACTER SPRITES & CARDS (${charList.length})</div>
              <div style="display:flex; gap:10px; overflow-x:auto; padding-bottom:4px;">
                ${charList.map(c => {
                  const cid = c.id || 'char';
                  const cname = c.name || c.canonical || cid;
                  const csprite = c.sprite || ('assets/characters/' + cid + '.png');
                  const ccard = c.card || ('assets/characters/card_' + cid + '.jpg');
                  const cols = Array.isArray(c.palette) ? c.palette : Object.values(c.colors || {});
                  return `
                    <div style="width:110px; flex-shrink:0; background:var(--surface); border:1px solid var(--border); border-radius:6px; padding:6px; text-align:center;">
                      <img src="/api/asset?project=${projName}&path=${csprite}" style="width:56px; height:56px; object-fit:contain; border-radius:50%; background:rgba(255,255,255,0.06); margin:0 auto 4px auto; display:block; cursor:pointer;" onclick="openImage('/api/asset?project=${projName}&path=${ccard}')" title="Click to view reference card">
                      <div style="font-size:11px; font-weight:700; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${escapeHtml(cname)}</div>
                      <div style="display:flex; justify-content:center; gap:2px; margin-top:3px;">
                        ${cols.slice(0, 4).map(col => `<span style="width:8px; height:8px; border-radius:2px; background:${col}; display:inline-block; border:1px solid rgba(255,255,255,0.2);" title="${col}"></span>`).join('')}
                      </div>
                    </div>
                  `;
                }).join('')}
              </div>
            </div>
          `;
        })()}
        ${(() => {
          const bgList = Array.isArray(data.backgrounds?.backgrounds) ? data.backgrounds.backgrounds : (Array.isArray(data.backgrounds) ? data.backgrounds : []);
          if (!bgList || bgList.length === 0) return '';
          return `
            <div style="margin-top:12px; background:var(--bg); border:1px solid var(--border); border-radius:8px; padding:10px;">
              <div style="font-size:11.5px; font-weight:700; color:var(--text-dim); margin-bottom:6px;">🌄 ATMOSPHERIC BACKGROUNDS (${bgList.length})</div>
              <div style="display:flex; gap:10px; overflow-x:auto; padding-bottom:4px;">
                ${bgList.map(bg => {
                  const bgPath = bg.file || ('assets/backgrounds/bg_' + bg.id + '.jpg');
                  const bgLabel = bg.setting || bg.id;
                  const bgAtm = bg.atmosphere || '';
                  return `
                    <div style="width:130px; flex-shrink:0; background:var(--surface); border:1px solid var(--border); border-radius:6px; padding:6px; text-align:center;">
                      <img src="/api/asset?project=${projName}&path=${bgPath}" style="width:100%; aspect-ratio:9/16; object-fit:cover; border-radius:4px; margin-bottom:4px; cursor:pointer;" onclick="openImage('/api/asset?project=${projName}&path=${bgPath}')" title="Click to view full background">
                      <div style="font-size:11px; font-weight:700; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${escapeHtml(bgLabel)}</div>
                      <div style="font-size:10px; color:var(--text-dim); overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${escapeHtml(bgAtm)}</div>
                    </div>
                  `;
                }).join('')}
              </div>
            </div>
          `;
        })()}
        <div class="toolbar" style="margin-top:16px;">
          <button class="btn primary" onclick="runAction('${projName}', 'build')">🔄 Run Build Pipeline</button>
          <button class="btn" onclick="runAction('${projName}', 'render')">🎬 Re-render MP4</button>
          ${data.has_render && !data.is_uploaded ? `
            <button class="btn primary" style="background:linear-gradient(135deg, #dc2626, #b91c1c); color:#fff; font-weight:700;" onclick="uploadProject('${projName}', true)">🚀 Upload to YouTube (${data.channel === 'asakthi' ? '🇮🇳 Asakthi' : '🇬🇧 Curiography'})</button>
          ` : (data.is_uploaded ? `
            <a class="btn" href="${data.youtube_url || ('https://youtu.be/' + data.video_id)}" target="_blank" style="background:#059669; color:#fff; text-decoration:none; font-weight:600;">▶ Watch on YouTube</a>
            <button class="btn" onclick="uploadProject('${projName}', true)">🔄 Re-Upload</button>
          ` : '')}
        </div>
      </div>
    </div>
  `);
}

function openImage(url) {
  openModal(`<img src="${url}" style="max-width:88vw; max-height:85vh; object-fit:contain; border-radius:8px;">`);
}

async function renderPerformanceTab() {
  const data = await api('/api/perf');
  const records = (data.records || []).slice().sort((a, b) => (b.date || '').localeCompare(a.date || ''));

  document.getElementById('app-content').innerHTML = `
    <div class="card">
      <div class="card-header">
        <h2>📊 YouTube Performance Hub (${records.length} videos logged)</h2>
        <button class="btn" onclick="syncYouTubeAnalytics(this)">↻ Sync YouTube Analytics</button>
      </div>
      <div class="table-wrap"><table class="performance-table">
        <thead>
          <tr>
            <th>Date</th>
            <th>Channel</th>
            <th>Title</th>
            <th>Views</th>
            <th>CTR</th>
            <th>Retention</th>
            <th>Likes</th>
            <th>Comments</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          ${records.length ? '' : '<tr><td colspan="9" style="text-align:center; color:var(--text-dim); padding:24px;">No performance records yet. Uploaded videos will appear here; use Edit to add YouTube Studio metrics.</td></tr>'}
          ${records.map((r, idx) => `
            <tr>
              <td>${escapeHtml(r.date)}</td>
              <td><span class="channel-tag ${r.channel === 'asakthi' ? 'te' : 'en'}">${r.channel === 'asakthi' ? 'TELUGU' : (r.channel === 'curiography' ? 'ENGLISH' : (r.channel || 'ENGLISH'))}</span></td>
              <td><b>${escapeHtml((r.title || '').slice(0, 45))}</b></td>
              <td>${r.views != null ? r.views.toLocaleString() : '—'}</td>
              <td>${r.ctr != null ? r.ctr + '%' : '—'}</td>
              <td>${r.retention != null ? r.retention + '%' : '—'}</td>
              <td>${r.likes != null ? r.likes : '—'}</td>
              <td>${r.comments != null ? r.comments : '—'}</td>
              <td><button class="btn" style="padding:4px 8px; font-size:11px;" onclick="editPerfRecord(${idx})">Edit</button></td>
            </tr>
          `).join('')}
        </tbody>
      </table></div>
    </div>
  `;
  window._perfRecords = records;
}

async function syncYouTubeAnalytics(button) {
  const old = button.textContent;
  button.disabled = true;
  button.textContent = 'Syncing…';
  try {
    const result = await api('/api/perf/sync', { method: 'POST', body: '{}' });
    if (!result.ok) throw new Error(result.output || 'Sync failed');
    alert(result.output || 'Analytics synced.');
    renderPerformanceTab();
  } catch (error) {
    alert(error.message || 'Analytics sync failed.');
  } finally {
    button.disabled = false;
    button.textContent = old;
  }
}

function editPerfRecord(idx) {
  const r = window._perfRecords[idx];
  openModal(`
    <div style="max-width:400px;">
      <h3 style="margin-top:0;">Log Performance for "${escapeHtml(r.title || r.video_id)}"</h3>
      <div style="display:flex; flex-direction:column; gap:10px; margin-top:14px;">
        <label>Views: <input id="inp-views" type="number" class="btn" style="width:100%;" value="${r.views || ''}"></label>
        <label>CTR (%): <input id="inp-ctr" type="number" step="0.1" class="btn" style="width:100%;" value="${r.ctr || ''}"></label>
        <label>Retention (%): <input id="inp-ret" type="number" step="0.1" class="btn" style="width:100%;" value="${r.retention || ''}"></label>
        <label>Likes: <input id="inp-likes" type="number" class="btn" style="width:100%;" value="${r.likes || ''}"></label>
        <label>Comments: <input id="inp-comments" type="number" class="btn" style="width:100%;" value="${r.comments || ''}"></label>
        <button class="btn primary" style="margin-top:10px;" onclick="savePerfRecord('${r.video_id}')">💾 Save Metrics</button>
      </div>
    </div>
  `);
}

async function savePerfRecord(videoId) {
  const rec = {
    video_id: videoId,
    views: parseFloat(document.getElementById('inp-views').value) || null,
    ctr: parseFloat(document.getElementById('inp-ctr').value) || null,
    retention: parseFloat(document.getElementById('inp-ret').value) || null,
    likes: parseInt(document.getElementById('inp-likes').value) || null,
    comments: parseInt(document.getElementById('inp-comments').value) || null,
  };
  await api('/api/perf', { method: 'POST', body: JSON.stringify({ record: rec }) });
  closeModal();
  renderPerformanceTab();
}

async function renderLedgerTab() {
  const data = await api('/api/file?path=daily/topics-done.md');
  document.getElementById('app-content').innerHTML = `
    <div class="card">
      <div class="card-header">
        <div><h2>📖 Topic Ledger</h2><div class="subtle">Topics already used by either channel. Keep one entry per completed or staged video.</div></div>
        <div class="ledger-actions"><span id="ledger-state" class="subtle">Saved · backup created on save</span><button id="ledger-save" class="btn primary" onclick="saveLedger()">💾 Save ledger</button></div>
      </div>
      <textarea id="ledger-text" class="code-editor" aria-label="Topic ledger" spellcheck="false">${escapeHtml(data.content || '')}</textarea>
    </div>
  `;
  const editor = document.getElementById('ledger-text');
  editor.addEventListener('input', () => {
    const state = document.getElementById('ledger-state');
    state.textContent = 'Unsaved changes'; state.style.color = 'var(--warning, #fbbf24)';
  });
}

async function saveLedger() {
  const content = document.getElementById('ledger-text').value;
  const button = document.getElementById('ledger-save');
  const state = document.getElementById('ledger-state');
  button.disabled = true; button.textContent = 'Saving…';
  const res = await api('/api/file', {
    method: 'POST',
    body: JSON.stringify({ path: 'daily/topics-done.md', content })
  });
  button.disabled = false; button.textContent = '💾 Save ledger';
  if (res.ok) { state.textContent = 'Saved · backup created'; state.style.color = 'var(--success, #34d399)'; }
  else { state.textContent = 'Save failed: ' + (res.error || 'unknown error'); state.style.color = 'var(--danger, #fb7185)'; }
}

async function renderLogsTab() {
  const logsList = await api('/api/logs');
  const logs = logsList.logs || [];

  document.getElementById('app-content').innerHTML = `
    <div class="card">
      <div class="card-header">
        <div>
          <h2 style="margin:0 0 4px 0;">📜 Live Execution Logs</h2>
          <div style="font-size:12px; color:var(--text-dim);">
            Real-time stdout/stderr stream from run-daily.sh, build pipeline, and rendering
          </div>
        </div>
        <div style="display:flex; gap:10px; align-items:center;">
          <select id="log-select" class="btn" onchange="loadLogContent()">
            ${logs.map(l => `<option value="${l}">${l}.log</option>`).join('')}
          </select>
          <label style="font-size:12px; color:var(--text-dim); display:flex; align-items:center; gap:6px;">
            <input type="checkbox" id="auto-tail" checked> Auto-tail (5s poll)
          </label>
        </div>
      </div>

      <div class="sub-nav">
        <button class="${currentLogChannel === 'all' ? 'active' : ''}" onclick="setLogChannel('all')">
          All Logs
        </button>
        <button class="en ${currentLogChannel === 'en' ? 'active en' : ''}" onclick="setLogChannel('en')">
          🇬🇧 English Stream
        </button>
        <button class="te ${currentLogChannel === 'te' ? 'active te' : ''}" onclick="setLogChannel('te')">
          🇮🇳 Telugu Stream
        </button>
        <button class="${currentLogChannel === 'broadcast' ? 'active' : ''}" style="color:#10b981; font-weight:700;" onclick="setLogChannel('broadcast')">
          📡 Broadcast Stream
        </button>
        <button class="btn" style="margin-left:auto; padding:4px 10px; font-size:11px;" onclick="loadLogContent()">
          🔄 Refresh Log Now
        </button>
      </div>

      <div id="log-terminal">Loading live log stream...</div>
    </div>
  `;
  loadLogContent();
}

function setLogChannel(ch) {
  currentLogChannel = ch;
  renderLogsTab();
}

async function loadLogContent() {
  const date = document.getElementById('log-select')?.value;
  if (!date) return;
  const data = await api(`/api/log?date=${date}&tail=800&channel=${currentLogChannel}`);
  const term = document.getElementById('log-terminal');
  if (term) {
    term.textContent = (data.lines && data.lines.length > 0) ? data.lines.join('\n') : '(No log entries for this channel filter yet)';
    if (document.getElementById('auto-tail')?.checked) {
      term.scrollTop = term.scrollHeight;
    }
  }
}

async function triggerRun(channel) {
  const dry = document.getElementById('dry-run-check').checked;
  const engine = document.getElementById('engine-select')?.value || '3d';
  const style = document.getElementById('style-select')?.value || 'auto';
  const chName = channel === 'en' ? 'English (Curiography)' : (channel === 'te' ? 'Telugu (Asakthi)' : 'Both Channels');
  const engineLabel = engine === 'mpt' ? 'MoneyPrinterTurbo (Real B-Roll + Pop Captions)' : 'Three.js 3D Cinema';
  if (!confirm(`Trigger ${engineLabel} Pipeline run for ${chName}? (DRY_RUN=${dry ? '1' : '0'})`)) return;

  const res = await api('/api/run', {
    method: 'POST',
    body: JSON.stringify({ channel, dry, engine, style, format: 'short' })
  });
  if (res.ok) {
    alert(`Pipeline (${engine.toUpperCase()}) triggered for ${chName}!`);
    setTimeout(refreshStatus, 2000);
  } else {
    alert('Failed to trigger run: ' + res.error);
  }
}

let broadcastPollInterval = null;

async function openBroadcastModal(channel = 'all', pid = null) {
  const chLabel = channel === 'en' ? 'English (Curiography)' : (channel === 'te' ? 'Telugu (Asakthi)' : 'All Channels');

  openModal(`
    <div style="width:min(850px, 82vw); max-width:100%;">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; border-bottom:1px solid var(--border); padding-bottom:10px;">
        <div style="display:flex; align-items:center; gap:10px;">
          <span style="font-size:22px;">📡</span>
          <div>
            <h3 style="margin:0; font-size:16px;">Live Broadcast Monitor</h3>
            <div style="font-size:12px; color:var(--text-dim);" id="bc-subtext">Publishing queued video for: <b>${escapeHtml(chLabel)}</b></div>
          </div>
        </div>
        <div style="display:flex; align-items:center; gap:8px;">
          <span id="bc-badge" class="pill" style="background:#10b98125; color:#10b981; border:1px solid #10b981; font-weight:700;">
            ● RUNNING ${pid ? `(PID: ${pid})` : ''}
          </span>
          <button class="btn" style="background:#dc2626; color:#fff; font-size:12px; font-weight:700;" onclick="stopBroadcast()">🛑 Stop Broadcast</button>
          <button class="btn" style="font-size:12px;" onclick="closeBroadcastModal()">✖ Close</button>
        </div>
      </div>

      <div style="margin-bottom:10px; display:flex; justify-content:space-between; align-items:center;">
        <span style="font-size:12px; color:var(--text-dim);">Live terminal output (updating in real time):</span>
        <label style="font-size:12px; color:var(--text-dim); display:flex; align-items:center; gap:6px;">
          <input type="checkbox" id="bc-autoscroll" checked> Auto-scroll to latest
        </label>
      </div>

      <div id="bc-log-viewer" style="
        background:#070a12;
        border:1px solid var(--border);
        border-radius:8px;
        padding:12px 14px;
        height:340px;
        overflow-y:auto;
        font:11.5px/1.5 ui-monospace, Menlo, monospace;
        color:#34d399;
        white-space:pre-wrap;
        word-break:break-all;
      ">Loading broadcast process output...</div>

      <div style="margin-top:12px; display:flex; justify-content:space-between; align-items:center; font-size:12px; color:var(--text-dim);">
        <div>Tip: Closing this window will NOT stop the upload. It continues safely in the background.</div>
        <button class="btn" style="font-size:11.5px;" onclick="closeBroadcastModal(); currentTab='logs'; renderLogsTab();">📜 Open in Full Live Logs Tab</button>
      </div>
    </div>
  `);

  if (broadcastPollInterval) clearInterval(broadcastPollInterval);

  async function pollBroadcast() {
    try {
      const data = await api('/api/broadcast_status');
      const box = document.getElementById('bc-log-viewer');
      const badge = document.getElementById('bc-badge');
      if (!box) {
        clearInterval(broadcastPollInterval);
        return;
      }
      if (data.lines && data.lines.length > 0) {
        box.textContent = data.lines.join('\n');
        if (document.getElementById('bc-autoscroll')?.checked) {
          box.scrollTop = box.scrollHeight;
        }
      } else {
        box.textContent = 'Waiting for broadcast process to emit log lines...';
      }

      if (data.is_running) {
        if (badge) {
          badge.innerHTML = `● RUNNING (PID: ${data.pid})`;
          badge.style.background = '#10b98125';
          badge.style.color = '#10b981';
          badge.style.borderColor = '#10b981';
        }
      } else {
        if (badge) {
          badge.innerHTML = `✓ IDLE / FINISHED`;
          badge.style.background = '#374151';
          badge.style.color = '#9ca3af';
          badge.style.borderColor = '#4b5563';
        }
      }
    } catch (e) {
      console.error(e);
    }
  }

  pollBroadcast();
  broadcastPollInterval = setInterval(pollBroadcast, 1500);
}

function closeBroadcastModal() {
  if (broadcastPollInterval) clearInterval(broadcastPollInterval);
  closeModal();
}

async function triggerBroadcast(channel = 'all') {
  const chLabel = channel === 'en' ? 'English (Curiography)' : (channel === 'te' ? 'Telugu (Asakthi)' : 'All Channels');
  if (!confirm(`🚀 Manually trigger instant broadcast for ${chLabel}?\n\nThis will publish pre-rendered videos waiting in the queue to YouTube in the background.`)) return;

  const res = await api('/api/broadcast', {
    method: 'POST',
    body: JSON.stringify({ channel })
  });

  if (res.ok) {
    // Immediately open Live Broadcast Monitor!
    openBroadcastModal(channel, res.pid);
    refreshStatus();
  } else {
    alert('Failed to trigger broadcast: ' + (res.error || 'Unknown error'));
  }
}

async function stopBroadcast() {
  if (!confirm('🛑 STOP CURRENT BROADCAST PROCESS?\n\nThis will immediately terminate running upload and broadcast workers.')) return;
  const res = await api('/api/broadcast_stop', { method: 'POST' });
  if (res.ok) {
    alert('🛑 Broadcast stopped!');
    refreshStatus();
  } else {
    alert('Failed to stop broadcast: ' + (res.error || 'Unknown error'));
  }
}

async function stopPipeline() {
  if (!confirm('⚠️ STOP ALL ACTIVE PIPELINES?\n\nThis will immediately kill running generation scripts, terminate upload retry loops, and remove lock files.')) return;
  const res = await api('/api/stop', { method: 'POST' });
  if (res.ok) {
    alert('🛑 Pipeline stopped! All active generation and upload processes have been terminated.');
    await refreshStatus();
    if (typeof renderPipelineTab === 'function') renderPipelineTab();
  } else {
    alert('Failed to stop pipeline: ' + (res.error || 'Unknown error'));
  }
}

async function runAction(project, action) {
  if (!confirm(`Execute action "${action}" on project "${project}"?`)) return;
  const res = await api('/api/action', {
    method: 'POST',
    body: JSON.stringify({ project, action })
  });
  if (res.ok) {
    alert(`Action ${action} initiated (pid: ${res.pid})`);
    closeModal();
    currentTab = 'logs';
    document.querySelectorAll('nav button').forEach(b => b.classList.toggle('active', b.dataset.tab === 'logs'));
    renderLogsTab();
  } else {
    alert('Error: ' + res.error);
  }
}

async function uploadProject(project, force = true) {
  if (!confirm(`🚀 Upload video for project "${project}" to YouTube? This will bypass dry-run mode and publish live.`)) return;
  const res = await api('/api/action', {
    method: 'POST',
    body: JSON.stringify({ project, action: 'upload', force: force })
  });
  if (res.ok) {
    alert(`YouTube upload started for "${project}" (pid: ${res.pid})! Switching to live logs...`);
    if (typeof closeModal === 'function') closeModal();
    currentTab = 'logs';
    document.querySelectorAll('nav button').forEach(b => b.classList.toggle('active', b.dataset.tab === 'logs'));
    renderLogsTab();
  } else {
    alert('Upload initiation failed: ' + res.error);
  }
}

// Refresh dashboard state without interrupting media playback.
setInterval(() => {
  refreshStatus();
  if (currentTab === 'logs' && document.getElementById('auto-tail')?.checked) {
    loadLogContent();
  }
}, 5000);

updateEngineControls();
refreshStatus().then(renderTab);
</script>
</body>
</html>
'''

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else int(os.environ.get('DASHBOARD_PORT', '8788'))
    host = os.environ.get('DASHBOARD_HOST', '127.0.0.1')
    print(f'Faceless Video Pipeline dashboard: http://{host}:{port}')
    ThreadingHTTPServer((host, port), DashboardHandler).serve_forever()
