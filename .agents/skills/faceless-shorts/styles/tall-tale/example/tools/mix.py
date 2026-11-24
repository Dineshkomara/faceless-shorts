"""Cinematic soundtrack: narration + intelligent sidechain ducking + realistic procedural foley & music.
No external samples or AI media APIs required.

  python3 tools/mix.py [project=.]          → data/mix.wav (48 kHz stereo)

Reads data/cues.json, data/narration.wav, and script.json.
Features:
- Professional -14 dB vocal sidechain ducking with smooth release (music swells between sentences).
- Cinematic foley sound effects: sub_boom, whoosh_fast, riser_cinema, impact, slam, thud, sparkle, pop, etc.
- Peak & loudness normalized for vertical mobile platforms (YouTube Shorts / TikTok / Reels).
"""
import json, subprocess, sys
from pathlib import Path
import numpy as np
from scipy import signal
from scipy.io import wavfile

P = Path(sys.argv[1] if len(sys.argv) > 1 else '.')
SR = 48000
rng = np.random.default_rng(11)
cj = json.loads((P / 'data/cues.json').read_text())
script = json.loads((P / 'script.json').read_text())
DUR = float(cj['duration'])
N = int(DUR * SR) + SR // 10


def lp(x, f, o=2):
    b, a = signal.butter(o, min(f, SR / 2 - 100) / (SR / 2), 'low')
    return signal.lfilter(b, a, x)

def hp(x, f, o=2):
    b, a = signal.butter(o, f / (SR / 2), 'high')
    return signal.lfilter(b, a, x)

def bp(x, f0, f1, o=2):
    b, a = signal.butter(o, [f0 / (SR / 2), f1 / (SR / 2)], 'band')
    return signal.lfilter(b, a, x)

def db(x):
    return 10 ** (x / 20)

def tt(d):
    return np.arange(int(d * SR)) / SR

def env(n, a=0.005, r=None):
    """attack a seconds then exponential release over the rest"""
    e = np.ones(n)
    na = max(1, int(a * SR))
    e[:na] = np.linspace(0, 1, na)
    rest = n - na
    e[na:] = np.exp(-np.linspace(0, r or 5, rest)) if rest > 0 else 1
    return e

def sweep(f0, f1, d, shape='exp'):
    t = tt(d)
    f = f0 * (f1 / f0) ** (t / d) if shape == 'exp' else f0 + (f1 - f0) * t / d
    return np.sin(2 * np.pi * np.cumsum(f) / SR)

def noise(d):
    return rng.standard_normal(int(d * SR))


# ---------- Cinematic Foley & Effects ----------
def whoosh(d=0.36, **_):
    n = noise(d); lo, hi = lp(n, 500), lp(n, 2400)
    k = np.sin(np.pi * np.linspace(0, 1, len(n)))
    x = (lo * (1 - k) + hi * k) * (k ** 1.5)
    return x / (np.abs(x).max() + 1e-9) * 0.55

def whoosh_fast(d=0.20, **_):
    """fast snappy transition whoosh for quick cuts"""
    n = noise(d)
    bp_n = bp(n, 320, 3200)
    k = np.sin(np.pi * np.linspace(0, 1, len(n))) ** 2
    return (bp_n * k) / (np.abs(bp_n).max() + 1e-9) * 0.65

def sub_boom(d=0.85, **_):
    """deep cinematic impact: sub-bass sine drop from 85 Hz -> 35 Hz with filtered rumble"""
    t = tt(d)
    f = 85 * (0.40 ** (t / d))
    sine = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(t), 0.003, 4.5)
    rumble = lp(noise(d), 95) * env(len(t), 0.005, 5.0) * 0.7
    x = np.tanh(1.5 * (sine + rumble))
    return x / (np.abs(x).max() + 1e-9) * 0.9

def riser_cinema(d=1.6, **_):
    """dramatic cinema riser building into reveals"""
    t = tt(d); k = np.linspace(0, 1, len(t)); f = 140 * (6.0 ** k)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.45 * bp(noise(d), 350, 3000)
    return lp(x, 3500) * (k ** 1.8) * 0.55

def slide(d=1.0, **_):
    n = lp(noise(d), 700); e = np.sin(np.pi * np.linspace(0, 1, len(n))) ** 2
    return n / (np.abs(n).max() + 1e-9) * e * 0.35 + sweep(260, 120, d) * e * 0.08

def pop(**_):
    x = sweep(560, 240, 0.11) * env(int(0.11 * SR), 0.002, 6)
    return lp(x, 3000) * 0.7

def plop(**_):
    x = sweep(700, 180, 0.14) * env(int(0.14 * SR), 0.002, 5)
    return lp(x, 2500) * 0.6

def gulp(**_):
    a = sweep(320, 140, 0.16) * env(int(0.16 * SR), 0.01, 4)
    b = sweep(240, 90, 0.2) * env(int(0.2 * SR), 0.01, 4)
    x = np.concatenate([a, np.zeros(int(0.04 * SR)), b])
    return lp(x, 1800) * 0.8

def boing(**_):
    d = 0.42; t = tt(d); f = 200 * (1 + 0.6 * t / d) * (1 + 0.08 * np.sin(2 * np.pi * 18 * t))
    return lp(np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(t), 0.004, 4), 2000) * 0.55

def bubbles(d=2.0, **_):
    x = np.zeros(int(d * SR))
    for _ in range(int(d * 7)):
        st = rng.integers(0, max(1, len(x) - int(0.08 * SR)))
        f = rng.uniform(380, 900)
        b = sweep(f, f * 1.6, 0.06) * env(int(0.06 * SR), 0.003, 5)
        x[st:st + len(b)] += b * rng.uniform(0.2, 0.5)
    return lp(x, 2500) * 0.5

def sizzle(d=1.0, **_):
    n = bp(noise(d), 1800, 4500)
    crack = (rng.random(len(n)) < 0.002).astype(float)
    crack = lp(crack, 300) * 40
    e = np.minimum(1, np.linspace(0, 6, len(n))) * np.linspace(1, 0.2, len(n))
    return n * (0.4 + crack) * e * 0.12

def sparkle(d=1.2, **_):
    notes = [784, 880, 1047, 1175, 1319, 1568]; x = np.zeros(int(d * SR) + SR // 2)
    for k, f in enumerate(notes):
        st = int(k * d / len(notes) * SR); n = int(0.4 * SR); t = tt(0.4)
        x[st:st + n] += (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t)) * env(n, 0.004, 6) * 0.22
    return lp(x, 4500)

def thud(**_):
    d = 0.35; t = tt(d); x = np.sin(2 * np.pi * (70 + 40 * np.exp(-t * 30)) * t) * env(len(t), 0.002, 7)
    return x * 0.9 + lp(noise(d), 220) * env(len(t), 0.001, 12) * 0.3

def slam(**_):
    d = 0.5; t = tt(d); x = np.sin(2 * np.pi * (60 + 60 * np.exp(-t * 25)) * t) * env(len(t), 0.002, 6)
    return np.tanh(1.6 * (x + lp(noise(d), 1200) * env(len(t), 0.001, 10) * 0.6)) * 0.9

def tock(**_):
    d = 0.09; t = tt(d)
    return (np.sin(2 * np.pi * 420 * t) + 0.3 * np.sin(2 * np.pi * 840 * t)) * env(len(t), 0.001, 9) * 0.35

def zip_(**_):
    d = 0.32; n = bp(noise(d), 400, 3000); k = np.linspace(0, 1, len(n))
    return (n / (np.abs(n).max() + 1e-9) * 0.35 + sweep(300, 1100, d) * 0.12) * np.sin(np.pi * k)

def alarm(d=0.8, **_):
    t = tt(d); beeps = np.sin(2 * np.pi * 880 * t) * (np.sin(2 * np.pi * 5 * t) > 0)
    return lp(beeps, 2400) * env(len(t), 0.005, 3) * 0.3

def heartbeat(d=0.7, **_):
    t = tt(d); lub = np.sin(2 * np.pi * 55 * t) * env(len(t), 0.01, 12)
    t2 = np.maximum(0, t - 0.22); dub = np.sin(2 * np.pi * 50 * t2) * env(len(t2), 0.01, 10) * (t > 0.22)
    return lp(lub * 0.85 + dub * 0.65, 180)

def inhale(d=0.6, **_):
    n = bp(noise(d), 300, 1600); k = np.linspace(0, 1, len(n))
    return n * (k ** 2) * 0.3

def river_flow(d=3.2, **_):
    """Soft broadband current for a visible river or spillway, not a generic whoosh."""
    n = bp(noise(d), 90, 1500)
    t = np.linspace(0, 1, len(n))
    swell = 0.72 + 0.20 * np.sin(2 * np.pi * (0.22 * t + 0.07 * np.sin(2 * np.pi * t)))
    return lp(n, 1900) * swell * env(len(n), 0.16, 1.7) * 0.55

def excavation(d=1.5, **_):
    """Low motor bed with a restrained granular cutting texture."""
    t = tt(d); n = bp(noise(d), 260, 2400)
    motor = np.sin(2 * np.pi * 72 * t + 0.18 * np.sin(2 * np.pi * 7 * t))
    pulse = 0.55 + 0.45 * np.sin(2 * np.pi * 3.2 * t) ** 2
    return (lp(motor * 0.42, 180) + n * 0.22) * pulse * env(len(t), 0.04, 2.2)

def concrete(d=0.75, **_):
    """Muted granular aggregate pour/placement with a short structural thump."""
    t = tt(d); grit = bp(noise(d), 180, 1900) * env(len(t), 0.015, 3.8)
    body = np.sin(2 * np.pi * (92 - 34 * t / max(d, 0.01)) * t) * env(len(t), 0.006, 5.5)
    return lp(grit * 0.42 + body * 0.68, 2200)

def machinery(d=1.8, **_):
    """Layered, quiet engine rumble and a narrow hydraulic/mechanical whine."""
    t = tt(d); n = bp(noise(d), 70, 800)
    motor = np.sin(2 * np.pi * (48 + 3 * np.sin(2 * np.pi * 0.7 * t)) * t)
    whine = sweep(310, 430, d) * (0.24 + 0.08 * np.sin(2 * np.pi * 2.1 * t))
    return lp(n * 0.28 + motor * 0.50 + whine, 1500) * env(len(t), 0.08, 1.7)

def gate_move(d=1.6, **_):
    """Slow geared rotation with hydraulic pressure and a soft end-stop."""
    t = tt(d); k = t / max(d, 0.01)
    motor = np.sin(2 * np.pi * (52 + 7 * np.sin(2 * np.pi * 0.5 * t)) * t)
    hydraulic = bp(noise(d), 320, 1250) * (0.25 + 0.45 * k)
    end = np.exp(-((k - 0.96) / 0.035) ** 2) * np.sin(2 * np.pi * (155 - 55 * k) * t)
    return lp((motor * 0.52 + hydraulic * 0.20 + end * 0.38) * env(len(t), 0.09, 0.9), 1900)

FX = dict(
    whoosh=whoosh, whoosh_fast=whoosh_fast, sub_boom=sub_boom, riser_cinema=riser_cinema,
    impact=sub_boom, riser=riser_cinema, slide=slide, pop=pop, plop=plop, gulp=gulp,
    boing=boing, bubbles=bubbles, sizzle=sizzle, sparkle=sparkle, thud=thud,
    slam=slam, tock=tock, zip=zip_, alarm=alarm, heartbeat=heartbeat, inhale=inhale,
    river_flow=river_flow, excavation=excavation, concrete=concrete,
    machinery=machinery, gate=gate_move
)

LEVEL = dict(
    whoosh=-17, whoosh_fast=-15, sub_boom=-10, impact=-10, riser_cinema=-14, riser=-16,
    slide=-19, pop=-14, plop=-15, gulp=-11, boing=-15, bubbles=-21, sizzle=-18,
    sparkle=-17, thud=-11, slam=-9, tock=-18, zip=-14, alarm=-17, heartbeat=-8, inhale=-15,
    river_flow=-25, excavation=-23, concrete=-21, machinery=-24, gate=-23
)


# ---------- Music Beds ----------
def music_bed():
    """Lush cinematic acoustic bed with warm stereo chorus and gentle pads."""
    bpm = 104; beat = 60 / bpm; bar = beat * 4
    chords = [
        [261.6, 329.6, 392.0, 523.2],  # C maj
        [220.0, 261.6, 329.6, 440.0],  # A min
        [174.6, 220.0, 261.6, 349.2],  # F maj
        [196.0, 246.9, 293.7, 392.0]   # G maj
    ]
    xl = np.zeros(N)
    xr = np.zeros(N)
    nb = int(np.ceil(DUR / bar)) + 1
    for b in range(nb):
        ch = chords[b % 4]; st = int(b * bar * SR); n = int(bar * SR)
        if st >= N: break
        t = tt(bar); e = np.minimum(1, t / 0.35) * np.minimum(1, (bar - t) / 0.35)

        # Warm pad with subtle stereo detune
        pad_l = sum(np.sin(2 * np.pi * (f * 0.998) * t) * 0.08 for f in ch) * e
        pad_r = sum(np.sin(2 * np.pi * (f * 1.002) * t) * 0.08 for f in ch) * e
        cur_n = max(0, min(n, N - st))
        xl[st:st + n] += pad_l[:cur_n]
        xr[st:st + n] += pad_r[:cur_n]

        # Gentle melodic arpeggio
        for k in range(8):
            f = ch[[0, 1, 2, 3, 2, 1, 2, 0][k]]
            ps = st + int(k * beat / 2 * SR); pn = int(0.45 * SR)
            if ps + pn >= N: continue
            pt = tt(0.45)
            pl = (np.sin(2 * np.pi * f * pt) + 0.22 * np.sin(4 * np.pi * f * pt)) * env(pn, 0.004, 6.5) * 0.09
            # Alternate slightly across stereo image
            pan = 0.35 if k % 2 == 0 else -0.35
            xl[ps:ps + pn] += pl * (1.0 - pan)
            xr[ps:ps + pn] += pl * (1.0 + pan)

    xl = lp(xl, 3800); xr = lp(xr, 3800)
    fade = np.ones(N); fo = int(1.2 * SR); fade[-fo:] = np.linspace(1, 0, fo)
    xl *= fade; xr *= fade
    m = np.column_stack([xl, xr])
    return m / (np.abs(m).max() + 1e-9)

def music_tension():
    """Low drone + slow minor pulse, for mysterious / tense explainers."""
    t = np.arange(N) / SR
    xl = np.zeros(N)
    xr = np.zeros(N)
    for f, g in [(55, 0.45), (82.4, 0.3), (110, 0.22), (130.8, 0.14)]:
        xl += np.sin(2 * np.pi * (f * 0.999) * t + np.sin(t * 0.25) * 0.4) * g
        xr += np.sin(2 * np.pi * (f * 1.001) * t + np.sin(t * 0.25) * 0.4) * g
    pulse = 0.55 + 0.45 * np.sin(2 * np.pi * t / 7.5) ** 2
    xl *= pulse; xr *= pulse

    beat = 60 / 84
    ping = lambda f: (np.sin(2 * np.pi * f * tt(1.2)) + 0.25 * np.sin(4 * np.pi * f * tt(1.2))) * env(int(1.2 * SR), 0.01, 5)
    seq = [220.0, 261.6, 196.0, 174.6]
    for k in range(int(DUR / (beat * 2))):
        i = int(k * beat * 2 * SR); pg = ping(seq[(k // 2) % 4]) * 0.30
        if i + len(pg) < N:
            xl[i:i + len(pg)] += pg * 0.8
            xr[i:i + len(pg)] += pg * 1.2
    xl = lp(xl, 2400); xr = lp(xr, 2400)
    fade = np.ones(N); fo = int(1.5 * SR); fade[-fo:] = np.linspace(1, 0, fo); fi = int(0.8 * SR); fade[:fi] *= np.linspace(0, 1, fi)
    xl *= fade; xr *= fade
    m = np.column_stack([xl, xr])
    return m / (np.abs(m).max() + 1e-9)

def music_bounce():
    """Modern punchy Shorts rhythm: warm sub-bass, snappy acoustic beat & lo-fi keys."""
    bpm = 112; beat = 60 / bpm; bar = beat * 4
    xl = np.zeros(N)
    xr = np.zeros(N)
    nb = int(np.ceil(DUR / bar)) + 1
    chords = [
        [220.0, 261.6, 329.6],  # Am
        [174.6, 220.0, 261.6],  # F
        [261.6, 329.6, 392.0],  # C
        [196.0, 246.9, 293.7]   # G
    ]
    for b in range(nb):
        ch = chords[b % 4]; st = int(b * bar * SR)
        if st >= N: break

        # Sub kick on beat 1 & 3
        for k in (0, 2):
            ks = st + int(k * beat * SR); kn = min(int(0.25 * SR), N - ks)
            if ks < N and kn > 0:
                kt = tt(kn / SR)
                kf = 110 * (0.35 ** (kt / 0.25))
                kick = np.sin(2 * np.pi * np.cumsum(kf) / SR) * env(kn, 0.002, 8.0) * 0.45
                xl[ks:ks + kn] += kick; xr[ks:ks + kn] += kick

        # Snappy rim/snap on beat 2 & 4
        for k in (1, 3):
            ss = st + int(k * beat * SR); sn = min(int(0.12 * SR), N - ss)
            if ss < N and sn > 0:
                snap = (bp(noise(sn / SR), 1200, 5000) * env(sn, 0.001, 14.0)) * 0.22
                xl[ss:ss + sn] += snap * 0.9; xr[ss:ss + sn] += snap * 1.1

        # Lo-fi Rhodes keyboard stabs
        for k in (0.5, 1.5, 2.5, 3.5):
            rs = st + int(k * beat * SR); rn = min(int(0.35 * SR), N - rs)
            if rs < N and rn > 0:
                rt = tt(rn / SR)
                stab_l = sum(np.sin(2 * np.pi * f * rt) * 0.06 for f in ch) * env(rn, 0.005, 5.0)
                stab_r = sum(np.sin(2 * np.pi * (f * 1.004) * rt) * 0.06 for f in ch) * env(rn, 0.005, 5.0)
                xl[rs:rs + rn] += stab_l; xr[rs:rs + rn] += stab_r

    xl = lp(xl, 4200); xr = lp(xr, 4200)
    fade = np.ones(N); fo = int(1.2 * SR); fade[-fo:] = np.linspace(1, 0, fo)
    xl *= fade; xr *= fade
    m = np.column_stack([xl, xr])
    return m / (np.abs(m).max() + 1e-9)

def music_engineering():
    """Evolving restrained documentary bed: warm low pads, soft pulse, sparse high notes."""
    bpm = 88; beat = 60 / bpm; bar = beat * 4
    chords = [[110.0, 164.8, 220.0, 261.6], [87.3, 130.8, 174.6, 220.0],
              [98.0, 146.8, 196.0, 246.9], [82.4, 123.5, 164.8, 196.0]]
    xl = np.zeros(N); xr = np.zeros(N)
    for b in range(int(np.ceil(DUR / bar)) + 1):
        st = int(b * bar * SR)
        if st >= N: break
        ch = chords[b % len(chords)]; n = min(int(bar * SR), N - st)
        t = np.arange(n) / SR
        edge = np.minimum(1, t / 0.8) * np.minimum(1, (bar - t) / 0.9)
        phrase = 0.82 + 0.10 * np.sin(2 * np.pi * b / 8)
        for f in ch:
            xl[st:st+n] += (np.sin(2*np.pi*f*0.999*t) + 0.22*np.sin(4*np.pi*f*0.999*t))*edge*phrase*0.045
            xr[st:st+n] += (np.sin(2*np.pi*f*1.001*t) + 0.22*np.sin(4*np.pi*f*1.001*t))*edge*phrase*0.045
        # A soft pulse once per beat keeps the build moving without sounding like a pop track.
        for k in range(4):
            ps = st + int(k * beat * SR); pn = min(int(0.20 * SR), N - ps)
            if pn <= 0: continue
            pt = np.arange(pn) / SR
            pulse = np.sin(2*np.pi*(64 - 25*pt/0.20)*pt) * np.exp(-pt*16) * 0.11
            xl[ps:ps+pn] += pulse; xr[ps:ps+pn] += pulse
        # Sparse upper-register notes enter at phrase turns, leaving narration space.
        if b % 2 == 0:
            f = ch[2] * 2; pn = min(int(0.48 * SR), N - st)
            pt = np.arange(pn) / SR
            note = (np.sin(2*np.pi*f*pt) + 0.18*np.sin(4*np.pi*f*pt))*np.exp(-pt*5.0)*0.045
            xl[st:st+pn] += note * 0.8; xr[st:st+pn] += note * 1.0
    xl = lp(xl, 2600); xr = lp(xr, 2600)
    fade = np.ones(N); fi = min(int(1.0*SR), N); fo = min(int(1.6*SR), N)
    fade[:fi] = np.linspace(0, 1, fi); fade[-fo:] *= np.linspace(1, 0, fo)
    m = np.column_stack([xl*fade, xr*fade])
    return m / (np.abs(m).max() + 1e-9)

def music_concept():
    """Warm, curious concept-explainer bed with a gentle pulse and sparse plucks."""
    bpm = 96; beat = 60 / bpm; bar = beat * 4
    chords = [[261.6, 329.6, 392.0, 523.2], [220.0, 261.6, 329.6, 440.0],
              [174.6, 220.0, 261.6, 349.2], [196.0, 246.9, 293.7, 392.0]]
    xl = np.zeros(N); xr = np.zeros(N)
    for b in range(int(np.ceil(DUR / bar)) + 1):
        st = int(b * bar * SR)
        if st >= N: break
        ch = chords[b % len(chords)]; n = min(int(bar * SR), N - st)
        t = np.arange(n) / SR
        edge = np.minimum(1, t / 0.7) * np.minimum(1, (bar - t) / 0.8)
        lift = 0.9 + 0.08 * np.sin(2 * np.pi * b / 12)
        for f in ch:
            xl[st:st+n] += np.sin(2*np.pi*f*0.998*t) * edge * lift * 0.036
            xr[st:st+n] += np.sin(2*np.pi*f*1.002*t) * edge * lift * 0.036
        # Sparse rounded plucks add movement without a busy pop beat.
        for k, note_ix in ((0.5, 2), (2.5, 1)):
            ps = st + int(k * beat * SR); pn = min(int(0.34 * SR), N - ps)
            if pn <= 0: continue
            pt = np.arange(pn) / SR; f = ch[note_ix] * 2
            pluck = (np.sin(2*np.pi*f*pt) + 0.15*np.sin(4*np.pi*f*pt)) * np.exp(-pt*10) * 0.045
            xl[ps:ps+pn] += pluck * 0.94; xr[ps:ps+pn] += pluck
        # A soft low pulse only on the first beat anchors each thought.
        pn = min(int(0.22 * SR), N - st); pt = np.arange(pn) / SR
        pulse = np.sin(2*np.pi*(72 - 22*pt/0.22)*pt) * np.exp(-pt*17) * 0.075
        xl[st:st+pn] += pulse; xr[st:st+pn] += pulse
    xl = lp(xl, 3200); xr = lp(xr, 3200)
    fade = np.ones(N); fi = min(int(0.8*SR), N); fo = min(int(1.4*SR), N)
    fade[:fi] = np.linspace(0, 1, fi); fade[-fo:] *= np.linspace(1, 0, fo)
    m = np.column_stack([xl*fade, xr*fade])
    return m / (np.abs(m).max() + 1e-9)

def load_audio(f):
    try:
        fp = Path(f)
        if not fp.exists() or not fp.is_file():
            return None
        out = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(fp), '-f', 'f32le', '-ac', '2', '-ar', str(SR), '-'], capture_output=True, check=True).stdout
        a = np.frombuffer(out, dtype=np.float32).reshape(-1, 2).astype(np.float64)
        return a
    except Exception:
        return None


mix = np.zeros((N, 2))

# 1. Voice Track (Calibrated to -17.5 dBFS RMS for clean broadcast dominance)
vf = P / 'data/narration.wav'
voice = None
if vf.exists():
    v = load_audio(vf)
    if v is not None and len(v) > 0:
        v = v[:N]
        voice = np.zeros((N, 2))
        voice[:len(v)] = v
        rms = np.sqrt(np.mean(voice ** 2) + 1e-12)
        voice *= db(-17.5) / rms
        mix += voice

# 2. Music Track with Calibrated Sidechain Ducking (-8 dB below voice)
mus = (script.get('music') or 'bed').strip().lower()
if mus and mus != 'none':
    if mus in ('concept', 'curiosity', 'explainer'):
        m = music_concept()
    elif mus in ('engineering', 'documentary', 'infrastructure'):
        m = music_engineering()
    elif mus in ('bounce', 'pop', 'upbeat', 'hiphop'):
        m = music_bounce()
    elif mus in ('tension', 'mystery', 'drone', 'dark'):
        m = music_tension()
    elif mus in ('bed', 'ambient', 'cinema', 'calm'):
        m = music_bed()
    else:
        # Check if project contains explicit custom audio file
        custom_a = load_audio(P / mus)
        if custom_a is not None and len(custom_a) > 0:
            m = np.zeros((N, 2))
            m[:len(custom_a)] = custom_a[:N]
            m /= np.abs(m).max() + 1e-9
        else:
            m = music_bed()

    # Balance music to -25.5 dBFS RMS (standard -8 dB below voice for optimal clarity)
    m_rms = np.sqrt(np.mean(m ** 2) + 1e-12)
    m *= db(-25.5 if voice is not None else -19.0) / m_rms

    if voice is not None:
        # Smooth transparent sidechain ducking (6 dB - 8 dB attenuation during vocal phrases)
        v_mono = np.abs(voice.mean(1))
        att = np.exp(-1.0 / (0.015 * SR))   # 15 ms smooth attack
        rel = np.exp(-1.0 / (0.280 * SR))   # 280 ms natural release
        env_v = np.zeros(N)
        curr = 0.0
        for i in range(N):
            val = v_mono[i]
            curr = att * curr + (1 - att) * val if val > curr else rel * curr + (1 - rel) * val
            env_v[i] = curr
        env_v /= (env_v.max() + 1e-9)

        # Smooth duck curve: drops by up to -8 dB during active voice, swells smoothly during pauses
        duck_curve = 1.0 - 0.62 * np.clip(env_v * 2.0, 0, 1)
        m *= duck_curve[:, None]

    mix += m

# 3. Sound Effects & Foley
for c in cj.get('cues', []):
    ctype = c.get('type')
    fn = FX.get(ctype)
    if not fn:
        continue
    x = fn(**({'d': c['dur']} if c.get('dur') else {}))
    x = lp(x, 5000) * db(LEVEL.get(ctype, -16)) * c.get('gain', 1.0) / (np.abs(x).max() + 1e-9) * 0.95
    i = int(c['t'] * SR); n = min(len(x), N - i)
    if n > 0 and i >= 0:
        pan = c.get('pan', 0.0)
        mix[i:i + n, 0] += x[:n] * (1 - max(0, pan))
        mix[i:i + n, 1] += x[:n] * (1 + min(0, pan))

# 4. Master: Analog warmth soft-clip & true-peak limiter (-1.2 dBFS)
mix = np.tanh(mix * 1.12) / 1.12
peak_val = np.abs(mix).max()
if peak_val > 0:
    mix *= db(-1.2) / peak_val

(P / 'data').mkdir(parents=True, exist_ok=True)
wavfile.write(P / 'data/mix.wav', SR, (mix * 32767).astype(np.int16))
print(f"data/mix.wav: {DUR:.2f} s · voice: {'yes' if voice is not None else 'NO'} · music: {mus} · {len(cj.get('cues', []))} cues")
