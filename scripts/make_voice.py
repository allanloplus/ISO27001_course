"""Synthesize Allan's speech-bubble lines with a young male Taiwanese voice (edge-tts, zh-TW-YunJheNeural).

  python3 make_voice.py lines.json out_dir [--ca /path/to/ca.pem]

lines.json comes from `node scripts/render.js --events` (field "lines": [[start, end, text], ...]).
Writes out_dir/line_XX.mp3 and out_dir/voice.json with each clip's start time and duration.
"""
import asyncio, json, os, re, ssl, subprocess, sys

import edge_tts
import edge_tts.communicate as comm

VOICE = "zh-TW-YunJheNeural"

FIX = [(r"<[^>]+>", ""), (r"[\U0001F300-\U0001FAFF☀-➿️]", ""), (r"\n", ""),
       (r"P-D-C-A", "P D C A"), (r"PDCA", "P D C A"), (r"ISO", "I S O "), (r"SoA", "S O A"),
       (r"BS 7799", "B S 七七九九"), (r"4～10", "四到十"), (r"附錄A", "附錄 A"), (r"[『』]", ""), (r"～", "！")]


def say_text(line):
    text = line[4] if len(line) > 4 and line[4] else line[2]
    for a, b in FIX:
        text = re.sub(a, b, text)
    return text


def duration(path):
    import imageio_ffmpeg
    out = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-i", path], capture_output=True, text=True).stderr
    h, m, s = re.search(r"Duration: (\d+):(\d+):([\d.]+)", out).groups()
    return int(h) * 3600 + int(m) * 60 + float(s)


async def main():
    src, out_dir = sys.argv[1], sys.argv[2]
    if "--ca" in sys.argv:
        comm._SSL_CTX = ssl.create_default_context(cafile=sys.argv[sys.argv.index("--ca") + 1])
    os.makedirs(out_dir, exist_ok=True)
    lines = json.load(open(src))["lines"]
    meta = []
    for i, ln in enumerate(lines):
        window = ln[1] - ln[0] - 0.25
        path = os.path.join(out_dir, f"line_{i:02d}.mp3")
        rate = 5
        for _ in range(6):  # speed up a little if the clip would overrun its bubble
            await edge_tts.Communicate(say_text(ln), VOICE, rate=f"+{rate}%", pitch="+8Hz").save(path)
            d = duration(path)
            if d <= window or rate >= 25:
                break
            rate += 5
        meta.append({"start": ln[0], "end": ln[1], "file": os.path.basename(path), "dur": round(d, 3), "rate": rate, "text": say_text(ln)})
        print(f"{i:02d} {ln[0]:6.1f}s window {window:4.1f}s  clip {d:4.1f}s  rate +{rate}%  {say_text(ln)}")
    json.dump(meta, open(os.path.join(out_dir, "voice.json"), "w"), ensure_ascii=False, indent=1)
    with open(os.path.join(out_dir, "voice.js"), "w") as f:  # loaded by animation/index.html in voice mode
        f.write("window.VOICE_CLIPS = " + json.dumps([{"file": m["file"], "dur": m["dur"]} for m in meta]) + ";\n")


asyncio.run(main())
