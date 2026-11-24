"""Batch Piper synthesis (run with the piper venv python, NOT the faceless venv):

  piper-venv/bin/python scripts/piper_say.py <voice.onnx> <manifest.json>

manifest: {"out": "/abs/dir", "length_scale": 0.95, "sents": {"key": "text", ...}}
writes <out>/<key>.wav (22050 Hz mono int16) — one model load for all clips.
"""
import json, sys, wave
from pathlib import Path
from piper import PiperVoice, SynthesisConfig

voice_path, man_path = sys.argv[1], sys.argv[2]
man = json.loads(Path(man_path).read_text())
v = PiperVoice.load(voice_path)
cfg = SynthesisConfig(length_scale=float(man.get('length_scale', 1.0)))
out = Path(man['out']); out.mkdir(parents=True, exist_ok=True)
for k, text in man['sents'].items():
    with wave.open(str(out / f'{k}.wav'), 'wb') as w:
        v.synthesize_wav(text, w, syn_config=cfg)
print(f'piper: {len(man["sents"])} clips -> {out}')
