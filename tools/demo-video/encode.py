import json
import os
import subprocess
import tempfile
from pathlib import Path

FRAMES = Path(os.environ.get("FRAMES", Path(tempfile.gettempdir()) / "hk-frames"))
OUTPUT = Path(os.environ.get("OUT", "hakiki-demo.mp4"))
FFMPEG = os.environ.get("FFMPEG", "ffmpeg")
LAST_FRAME_SECONDS = 3.0

frames = json.loads((FRAMES / "index.json").read_text())
lines = ["ffconcat version 1.0"]
for index, frame in enumerate(frames):
    following = frames[index + 1]["ts"] if index + 1 < len(frames) else None
    duration = (following - frame["ts"]) if following else LAST_FRAME_SECONDS
    lines += [f"file '{frame['name']}'", f"duration {max(duration, 1 / 60):.4f}"]
lines.append(f"file '{frames[-1]['name']}'")
playlist = FRAMES / "list.txt"
playlist.write_text("\n".join(lines) + "\n")

subprocess.run(
    [FFMPEG, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(playlist),
     "-vf", "fps=30,scale=1280:720,format=yuv420p", "-c:v", "libx264", "-preset", "slow",
     "-crf", "23", "-movflags", "+faststart", str(OUTPUT)],
    check=True,
)
print(f"{OUTPUT} written from {len(frames)} frames")
