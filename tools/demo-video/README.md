# Demo video

Records the three-minute walkthrough in `docs/demo-script.md` by driving the real dashboard in headless Chrome. It adds an animated cursor, captions and title cards, then encodes the frames with ffmpeg. There is no audio, so you can add a voice-over in any editor.

## Needs

- Node 22 or newer and Google Chrome (set `CHROME` to a different binary if needed).
- `ffmpeg` on the path, or set `FFMPEG` to its location. `pip install imageio-ffmpeg` provides a bundled one.
- The API and dashboard running locally, with the demo data seeded.

## Record

```bash
# from a clean demo database
python -m scripts.seed

python tools/demo-video/make_week_csv.py        # a fresh batch of 24 claims, so Overview tells a clean story
node tools/demo-video/record.mjs                # about 3 minutes, writes frames to the temp folder
OUT=hakiki-demo.mp4 python tools/demo-video/encode.py
```

Settings, all optional: `BASE` (default `http://localhost:5173`), `DEMO_EMAIL`, `DEMO_PASSWORD`, `DEMO_CSV`, `FRAMES`, `OUT`.

## Change the script

The steps are in `record.mjs`. `say("...")` shows a caption for a time based on its length, `click(selector, text)` moves the cursor and clicks, and `card(html, ms)` shows a title card. Keep the finished video under three minutes, and rerun `make_week_csv.py` and the seed before each take so the numbers on the Overview match the story.
