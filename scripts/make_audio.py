"""Generate the background track for the 180 s animation.

  python3 make_audio.py out.wav                        # calm ambient pad (classic version)
  python3 make_audio.py out.wav --pop events.json      # upbeat track + bubble "pop" SFX (Q-version)
  python3 make_audio.py out.wav --pop events.json --voice animation/voice   # + Allan's voice, music ducked

events.json comes from `node scripts/render.js --events events.json`
({"bubbles": [...start times], "scenes": [...start times]}).
"""
import json, sys, wave
import numpy as np

SR, DUR = 44100, 180.0
t = np.arange(int(SR * DUR)) / SR


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def add(buf, start, sig):
    i0 = int(start * SR)
    if i0 >= len(buf):
        return
    n = min(len(sig), len(buf) - i0)
    buf[i0:i0 + n] += sig[:n]


def ambient():
    scenes = [9, 18, 36, 50, 62, 78, 90, 96, 102, 114, 120, 125, 131, 136, 150, 163, 171]
    out = np.zeros_like(t)
    chords = [[48, 55, 64, 67, 71, 74], [45, 52, 60, 64, 67, 71], [41, 48, 57, 64, 67, 69], [43, 50, 59, 62, 64, 67]]
    seg = 8.0
    for k in range(int(np.ceil(DUR / seg)) + 1):
        s0 = k * seg - 1.0
        i0, i1 = max(0, int(s0 * SR)), min(len(t), int((s0 + seg + 2.0) * SR))
        if i0 >= i1:
            continue
        lt = t[i0:i1] - s0
        env = np.sin(np.clip(lt / 2.0, 0, 1) * np.clip((seg + 2.0 - lt) / 2.0, 0, 1) * np.pi / 2) ** 2
        for j, m in enumerate(chords[k % 4]):
            f = hz(m)
            sig = np.sin(2 * np.pi * f * lt + 0.3 * np.sin(2 * np.pi * 0.2 * lt + j)) + 0.15 * np.sin(2 * np.pi * 2 * f * lt)
            out[i0:i1] += (0.5 if j == 0 else 0.28) * env * sig
    for b in np.arange(0, DUR, 2.0):
        lt = np.arange(int(1.2 * SR)) / SR
        root = hz(chords[int(b // seg) % 4][0] - 12)
        add(out, b, 0.35 * np.exp(-lt * 4) * np.sin(2 * np.pi * root * lt))
    for s in scenes:
        lt = np.arange(int(2.5 * SR)) / SR
        add(out, s, sum(a * np.exp(-lt * 2.2) * np.sin(2 * np.pi * f * lt) for f, a in [(hz(84), .5), (hz(91), .3), (hz(96), .18)]))
    return out, out.copy(), 0.35


def pop(events):
    bpm = 116
    beat = 60 / bpm
    L = np.zeros_like(t)
    R = np.zeros_like(t)
    # I - V - vi - IV in C, one chord per bar
    prog = [[60, 64, 67], [55, 59, 62], [57, 60, 64], [53, 57, 60]]
    bass = [36, 43, 45, 41]

    def pluck(f, d=0.45, bright=1.0):
        lt = np.arange(int(d * SR)) / SR
        env = np.exp(-lt * 7) * np.clip(lt / 0.004, 0, 1)
        return env * (np.sin(2 * np.pi * f * lt) + 0.35 * bright * np.sin(4 * np.pi * f * lt) + 0.12 * np.sin(6 * np.pi * f * lt))

    def kick():
        lt = np.arange(int(0.25 * SR)) / SR
        f = 45 + 90 * np.exp(-lt * 30)
        return np.exp(-lt * 12) * np.sin(2 * np.pi * np.cumsum(f) / SR)

    rng = np.random.default_rng(7)

    def hat(d=0.05):
        n = int(d * SR)
        noise = rng.standard_normal(n)
        noise = np.diff(noise, prepend=0)  # crude high-pass
        return noise * np.exp(-np.arange(n) / SR * 70)

    def clap():
        n = int(0.18 * SR)
        noise = rng.standard_normal(n)
        return noise * np.exp(-np.arange(n) / SR * 22) * 0.5

    nbeats = int(DUR / beat) + 1
    arp_pat = [0, 1, 2, 1, 0, 2, 1, 2]
    for b in range(nbeats):
        tb = b * beat
        bar = b // 4
        ch = prog[bar % 4]
        intro = tb < 1.0
        if intro:
            continue
        # drums: four-on-the-floor kick, offbeat hats, clap on 2 & 4 (lighter during first 10 s)
        k = kick()
        add(L, tb, 0.55 * k); add(R, tb, 0.55 * k)
        h = hat()
        add(L, tb + beat / 2, 0.10 * h); add(R, tb + beat / 2, 0.14 * h)
        if b % 4 in (1, 3) and tb > 10:
            c = clap()
            add(L, tb, 0.16 * c); add(R, tb, 0.13 * c)
        # bass on beats
        lt = np.arange(int(beat * 0.9 * SR)) / SR
        f = hz(bass[bar % 4])
        bs = np.exp(-lt * 3) * (np.sin(2 * np.pi * f * lt) + 0.3 * np.sin(4 * np.pi * f * lt))
        add(L, tb, 0.30 * bs); add(R, tb, 0.30 * bs)
        # arpeggio in eighth notes
        for e in range(2):
            idx = arp_pat[(b * 2 + e) % 8]
            note = ch[idx] + 12
            p = pluck(hz(note))
            pan = 0.35 if e else 0.65
            add(L, tb + e * beat / 2, 0.16 * pan * 2 * p)
            add(R, tb + e * beat / 2, 0.16 * (1 - pan) * 2 * p)
        # soft chord stab each bar
        if b % 4 == 0:
            for m in ch:
                p = pluck(hz(m), d=beat * 3, bright=0.3) * 0.5
                add(L, tb, 0.10 * p); add(R, tb, 0.10 * p)

    music_env = np.clip(t / 1.5, 0, 1) * np.clip((DUR - t) / 3.0, 0, 1)
    L *= music_env
    R *= music_env

    # SFX: bubble "pop" (pitch sweep up) and scene "swoosh" (filtered noise sweep + chime)
    for s in events.get("bubbles", []):
        lt = np.arange(int(0.12 * SR)) / SR
        f = 500 + 1400 * lt / 0.12
        sig = np.exp(-lt * 30) * np.sin(2 * np.pi * np.cumsum(f) / SR)
        add(L, s, 0.45 * sig); add(R, s, 0.45 * sig)
    for s in events.get("scenes", []):
        n = int(0.45 * SR)
        lt = np.arange(n) / SR
        noise = rng.standard_normal(n)
        sm = np.convolve(noise, np.ones(8) / 8, mode="same")
        sw = sm * np.sin(np.pi * lt / 0.45) ** 2 * 0.35
        add(L, s - 0.25, sw); add(R, s - 0.2, sw)
        ch = sum(a * np.exp(-lt * 6) * np.sin(2 * np.pi * f * lt) for f, a in [(hz(88), .25), (hz(95), .15)])
        add(L, s, ch); add(R, s, ch)
    return L, R, 0.6


def load_clip(path):
    import subprocess, imageio_ffmpeg
    raw = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-loglevel", "error", "-i", path, "-f", "s16le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, "<i2").astype(np.float64) / 32767


def add_voice(L, R, vdir):
    """Mix voice clips at their bubble start times and duck the music underneath."""
    import os
    meta = json.load(open(os.path.join(vdir, "voice.json")))
    voice = np.zeros_like(t)
    duck = np.ones_like(t)
    ramp = int(0.15 * SR)
    for m in meta:
        clip = load_clip(os.path.join(vdir, m["file"]))
        add(voice, m["start"] + 0.05, clip)
        i0, i1 = int(m["start"] * SR), min(len(t), int((m["start"] + len(clip) / SR + 0.1) * SR))
        duck[i0:i1] = 0.3
    # smooth the ducking envelope
    k = np.ones(ramp) / ramp
    duck = np.convolve(duck, k, mode="same")
    voice = voice / (np.max(np.abs(voice)) + 1e-9)
    return L * duck, R * duck, voice


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "bgm.wav"
    if "--pop" in sys.argv:
        ev = json.load(open(sys.argv[sys.argv.index("--pop") + 1]))
        L, R, peak = pop(ev)
        voice = None
        if "--voice" in sys.argv:
            m = max(np.max(np.abs(L)), np.max(np.abs(R)))
            L, R = L / m * 0.45, R / m * 0.45
            L, R, voice = add_voice(L, R, sys.argv[sys.argv.index("--voice") + 1])
            L, R = L + 0.9 * voice, R + 0.9 * voice
            peak = 0.95
        d = int(0.18 * SR)
        L2, R2 = L.copy(), R.copy()
        L2[d:] += 0.18 * R[:-d]; R2[d:] += 0.18 * L[:-d]
        st = np.stack([L2, R2], 1)
    else:
        mono, _, peak = ambient()
        d = int(0.23 * SR)
        left, right = mono.copy(), mono.copy()
        left[d:] += 0.35 * mono[:-d]
        right[2 * d:] += 0.3 * mono[:-2 * d]
        st = np.stack([left, right], 1)
        st *= (np.clip(t / 2.0, 0, 1) * np.clip((DUR - t) / 4.0, 0, 1))[:, None]
    st = st / np.max(np.abs(st)) * peak
    with wave.open(out, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(st, -1, 1) * 32767).astype("<i2").tobytes())


if __name__ == "__main__":
    main()
