#!/usr/bin/env python3
"""Cinema-Grade Vocal Mastering & Audio Polish Engine.

Transforms raw synthetic speech (Edge-TTS, Piper, Kokoro) into high-end,
warm, radio-broadcast-quality narration matching professional YouTube Shorts
and documentary standards.

Acoustic Architecture:
  1. 48 kHz Ultra-High-Fidelity Resampling
  2. 80 Hz Butterworth High-Pass Filter (eliminates DC offset & sub-rumble)
  3. Gentle presence EQ and de-essing, tuned for intelligibility without a hyped/boomy tone
  4. Mild saturation and ratio-correct compression that preserves speech dynamics
  5. Peak normalization for consistent voice level
 10. Studio Vocal Booth Micro-Ambience (subtle 2.5% wet early reflections)

Usage:
  py scripts/vocal_master.py <input.wav> [output.wav] [--lang te|en]
"""

import argparse
import sys
from pathlib import Path
import numpy as np
import scipy.signal
from scipy.io import wavfile

SR = 48000


def biquad_peaking(x, f0, gain_db, q=1.0, sr=SR):
    """Parametric peaking filter."""
    if abs(gain_db) < 0.05:
        return x
    A = 10.0 ** (gain_db / 40.0)
    w0 = 2.0 * np.pi * f0 / sr
    alpha = np.sin(w0) / (2.0 * max(0.1, q))
    b0 = 1.0 + alpha * A
    b1 = -2.0 * np.cos(w0)
    b2 = 1.0 - alpha * A
    a0 = 1.0 + alpha / A
    a1 = -2.0 * np.cos(w0)
    a2 = 1.0 - alpha / A
    b = np.array([b0, b1, b2]) / a0
    a = np.array([a0, a1, a2]) / a0
    return scipy.signal.lfilter(b, a, x)


def biquad_highshelf(x, f0, gain_db, sr=SR):
    """High-shelf filter for vocal air and high-frequency sheen."""
    if abs(gain_db) < 0.05:
        return x
    A = 10.0 ** (gain_db / 40.0)
    w0 = 2.0 * np.pi * f0 / sr
    alpha = np.sin(w0) / 2.0 * np.sqrt(2.0)
    cos_w0 = np.cos(w0)
    b0 = A * ((A + 1.0) + (A - 1.0) * cos_w0 + 2.0 * np.sqrt(A) * alpha)
    b1 = -2.0 * A * ((A - 1.0) + (A + 1.0) * cos_w0)
    b2 = A * ((A + 1.0) + (A - 1.0) * cos_w0 - 2.0 * np.sqrt(A) * alpha)
    a0 = (A + 1.0) - (A - 1.0) * cos_w0 + 2.0 * np.sqrt(A) * alpha
    a1 = 2.0 * ((A - 1.0) - (A + 1.0) * cos_w0)
    a2 = (A + 1.0) - (A - 1.0) * cos_w0 - 2.0 * np.sqrt(A) * alpha
    b = np.array([b0, b1, b2]) / a0
    a = np.array([a0, a1, a2]) / a0
    return scipy.signal.lfilter(b, a, x)


def biquad_hpf(x, f0=80, sr=SR):
    """High-pass filter removing sub-bass rumble."""
    w0 = 2.0 * np.pi * f0 / sr
    alpha = np.sin(w0) / (2.0 * 0.707)
    cos_w0 = np.cos(w0)
    b0 = (1.0 + cos_w0) / 2.0
    b1 = -(1.0 + cos_w0)
    b2 = (1.0 + cos_w0) / 2.0
    a0 = 1.0 + alpha
    a1 = -2.0 * cos_w0
    a2 = 1.0 - alpha
    b = np.array([b0, b1, b2]) / a0
    a = np.array([a0, a1, a2]) / a0
    return scipy.signal.lfilter(b, a, x)


def apply_vocal_booth_ambience(x, wet_level=0.035, sr=SR):
    """Adds subtle stereo vocal booth early reflections for natural acoustic depth."""
    # Delays for left and right reflections (11ms, 19ms, 27ms)
    d1 = int(0.011 * sr)
    d2 = int(0.019 * sr)
    d3 = int(0.027 * sr)

    ref_l = np.zeros_like(x)
    ref_r = np.zeros_like(x)

    ref_l[d1:] += x[:-d1] * 0.45
    ref_l[d3:] += x[:-d3] * 0.25

    ref_r[d2:] += x[:-d2] * 0.42
    ref_r[d3:] += x[:-d3] * 0.22

    # High-cut reflections so they stay warm and don't introduce flutter
    b, a = scipy.signal.butter(2, 4500.0 / (sr / 2.0), 'low')
    ref_l = scipy.signal.lfilter(b, a, ref_l)
    ref_r = scipy.signal.lfilter(b, a, ref_r)

    out_l = x + ref_l * wet_level
    out_r = x + ref_r * wet_level
    return np.column_stack([out_l, out_r])


def master_vocal_audio(samples, sr_in, lang='te', is_stereo_out=False):
    """Applies complete professional studio vocal mastering chain.

    Args:
        samples: 1D numpy array of float audio (-1.0 to 1.0)
        sr_in: Input sample rate (e.g. 24000 or 48000)
        lang: Language code ('te' or 'en')
        is_stereo_out: If True, returns (N, 2) stereo array with booth ambience

    Returns:
        Mastered float audio array, normalized to -1.5 dBFS true-peak.
    """
    # 1. Resample to 48 kHz if needed
    if sr_in != SR:
        num_target = int(len(samples) * SR / sr_in)
        x = scipy.signal.resample(samples, num_target)
    else:
        x = np.copy(samples)

    if len(x) == 0:
        return x

    # 2. High-Pass Filter @ 80 Hz
    x = biquad_hpf(x, 80, SR)

    # 3. Parametric EQ Tuning
    if lang == 'te':
        # Keep Telugu warmth and consonant definition subtle; avoid an artificial radio EQ.
        x = biquad_peaking(x, 145, 1.6, q=1.0, sr=SR)
        x = biquad_peaking(x, 480, -1.0, q=1.2, sr=SR)
        x = biquad_peaking(x, 2800, 1.4, q=1.1, sr=SR)
        x = biquad_peaking(x, 6800, -1.3, q=2.0, sr=SR)
        x = biquad_highshelf(x, 10500, 0.8, sr=SR)
    else:
        x = biquad_peaking(x, 135, 1.4, q=1.0, sr=SR)
        x = biquad_peaking(x, 450, -0.8, q=1.2, sr=SR)
        x = biquad_peaking(x, 3000, 1.3, q=1.1, sr=SR)
        x = biquad_peaking(x, 7200, -1.2, q=2.0, sr=SR)
        x = biquad_highshelf(x, 11000, 0.8, sr=SR)

    # 4. Analog Warmth Tape Saturation (smooth even harmonics)
    x = np.tanh(1.04 * x) / 1.04

    # 5. Broadcast Dynamic Compressor & Leveler
    # Moderate attack and release preserve consonant transients and phrase dynamics.
    att = np.exp(-1.0 / (0.010 * SR))
    rel = np.exp(-1.0 / (0.120 * SR))
    env = np.zeros(len(x))
    curr = 0.0
    for i in range(len(x)):
        v = abs(x[i])
        curr = att * curr + (1.0 - att) * v if v > curr else rel * curr + (1.0 - rel) * v
        env[i] = curr

    thresh = 0.28
    ratio = 2.2
    comp_gain = np.ones(len(x))
    active_idx = env > thresh
    # Standard above-threshold compression: y = T * (x / T) ** (1 / R).
    # The old formula expanded gain before peak normalization, adding audible pumping/hardness.
    comp_gain[active_idx] = (env[active_idx] / thresh) ** (1.0 / ratio - 1.0)
    x = x * comp_gain

    # 6. Peak Normalization (-1.5 dBFS)
    peak = np.max(np.abs(x))
    if peak > 1e-6:
        x = x / peak * (10.0 ** (-1.5 / 20.0))

    # 7. Optional Studio Booth Ambience
    if is_stereo_out:
        return apply_vocal_booth_ambience(x, wet_level=0.035, sr=SR)

    return x


def master_vocal_file(in_path, out_path=None, lang='te'):
    """Reads input audio file, masters it, and saves output."""
    in_p = Path(in_path).resolve()
    out_p = Path(out_path).resolve() if out_path else in_p

    sr, data = wavfile.read(in_p)
    if data.ndim > 1:
        data = data.mean(axis=1)

    samples = data.astype(np.float64) / 32768.0
    mastered = master_vocal_audio(samples, sr, lang=lang, is_stereo_out=False)

    wavfile.write(out_p, SR, (mastered * 32767).astype(np.int16))
    print(f"[vocal_master] Mastered '{in_p.name}' -> '{out_p.name}' ({len(mastered)/SR:.2f}s @ 48kHz, lang={lang})")
    return out_p


def main():
    ap = argparse.ArgumentParser(description="Cinema-Grade Studio Vocal Mastering")
    ap.add_argument("input", help="Path to input audio file (WAV or MP3)")
    ap.add_argument("output", nargs="?", help="Path to output audio file")
    ap.add_argument("--lang", choices=["te", "en"], default="te", help="Language optimization")
    args = ap.parse_args()

    master_vocal_file(args.input, args.output, lang=args.lang)


if __name__ == '__main__':
    main()
