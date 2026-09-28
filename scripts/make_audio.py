"""Generate a soft ambient background track (pad + scene-change chimes) for the 180s animation."""
import sys, wave
import numpy as np

SR, DUR = 44100, 180.0
SCENES = [9, 18, 36, 50, 62, 78, 90, 96, 102, 114, 120, 125, 131, 136, 150, 163, 171]
t = np.arange(int(SR * DUR)) / SR
out = np.zeros_like(t)

def hz(m): return 440.0 * 2 ** ((m - 69) / 12)

# Cmaj9 - Am9 - Fmaj9 - G6, 8 s per chord
chords = [[48, 55, 64, 67, 71, 74], [45, 52, 60, 64, 67, 71], [41, 48, 57, 64, 67, 69], [43, 50, 59, 62, 64, 67]]
SEG = 8.0
for k in range(int(np.ceil(DUR / SEG)) + 1):
    s0 = k * SEG - 1.0
    i0, i1 = max(0, int(s0 * SR)), min(len(t), int((s0 + SEG + 2.0) * SR))
    if i0 >= i1: continue
    lt = t[i0:i1] - s0
    env = np.clip(lt / 2.0, 0, 1) * np.clip((SEG + 2.0 - lt) / 2.0, 0, 1)
    env = np.sin(env * np.pi / 2) ** 2
    for j, m in enumerate(chords[k % 4]):
        f = hz(m)
        v = 0.5 if j == 0 else 0.28
        sig = np.sin(2 * np.pi * f * lt + 0.3 * np.sin(2 * np.pi * 0.2 * lt + j)) + 0.15 * np.sin(2 * np.pi * 2 * f * lt)
        out[i0:i1] += v * env * sig

# gentle pulse on the root an octave down (heartbeat-like, every 2 s)
for b in np.arange(0, DUR, 2.0):
    i0, i1 = int(b * SR), min(len(t), int((b + 1.2) * SR))
    lt = t[i0:i1] - b
    root = hz(chords[int(b // SEG) % 4][0] - 12)
    out[i0:i1] += 0.35 * np.exp(-lt * 4) * np.sin(2 * np.pi * root * lt)

# chimes at scene changes
for s in SCENES:
    i0, i1 = int(s * SR), min(len(t), int((s + 2.5) * SR))
    lt = t[i0:i1] - s
    for f, a in [(hz(84), 0.5), (hz(91), 0.3), (hz(96), 0.18)]:
        out[i0:i1] += a * np.exp(-lt * 2.2) * np.sin(2 * np.pi * f * lt)

# simple stereo delay/reverb feel
d = int(0.23 * SR)
left, right = out.copy(), out.copy()
left[d:] += 0.35 * out[:-d]
right[2 * d:] += 0.3 * out[:-2 * d]
st = np.stack([left, right], 1)
fade = np.clip(t / 2.0, 0, 1) * np.clip((DUR - t) / 4.0, 0, 1)
st *= fade[:, None]
st = st / np.max(np.abs(st)) * 0.5
with wave.open(sys.argv[1] if len(sys.argv) > 1 else "bgm.wav", "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((st * 32767).astype("<i2").tobytes())
