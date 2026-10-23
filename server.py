#!/usr/bin/env python3
"""
Live Video Player & Asset Download Studio (bound to 0.0.0.0:8000).
Supports HTTP 206 Partial Content Byte-Range streaming so the 10:00 1080p MP4
plays, scrubs, and downloads smoothly in any browser!
"""
import os
import re
import mimetypes
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import unquote, urlparse, parse_qs

PORT = int(os.environ.get("PORT", "8000"))
ROOT = os.path.abspath(os.path.dirname(__file__))

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Aryan Chaudhary Extra — 10:00 Master Video Studio</title>
<style>
  :root {
    --bg: #06060a; --panel: #11131d; --border: #25283a;
    --yellow: #ffd600; --magenta: #ff1e8a; --cyan: #00e5ff; --green: #00e676; --text: #f6f7fb; --muted: #9da4b8;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: var(--bg); color: var(--text); font-family: system-ui, -apple-system, sans-serif; line-height: 1.5; padding: 24px; }
  .wrap { max-width: 1180px; margin: 0 auto; }
  header { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 16px; margin-bottom: 20px; border-bottom: 1px solid var(--border); padding-bottom: 16px; }
  .badge { display: inline-block; background: rgba(255,30,138,0.16); border: 1px solid var(--magenta); color: #ff69b4; font-weight: 700; font-size: 12px; padding: 4px 10px; border-radius: 999px; letter-spacing: 0.06em; margin-bottom: 6px; }
  h1 { font-size: 26px; font-weight: 800; letter-spacing: -0.02em; }
  h1 span { color: var(--yellow); }
  .actions { display: flex; flex-wrap: wrap; gap: 10px; }
  .btn { display: inline-flex; align-items: center; gap: 8px; text-decoration: none; font-weight: 800; font-size: 14px; padding: 12px 20px; border-radius: 10px; transition: transform 0.12s ease; cursor: pointer; border: none; }
  .btn:hover { transform: translateY(-1px); }
  .btn-primary { background: var(--yellow); color: #08080c; box-shadow: 0 0 24px rgba(255,214,0,0.3); }
  .btn-secondary { background: var(--panel); color: var(--text); border: 1px solid var(--cyan); }
  .player-card { background: var(--panel); border: 1px solid var(--border); border-radius: 16px; overflow: hidden; box-shadow: 0 20px 50px rgba(0,0,0,0.65); margin-bottom: 24px; }
  video { width: 100%; display: block; aspect-ratio: 16 / 9; background: #000; }
  .chapters { padding: 16px 20px; border-top: 1px solid var(--border); display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
  .chapters strong { font-size: 13px; color: var(--muted); margin-right: 6px; }
  .chip { background: #191c2b; border: 1px solid #2e334d; color: var(--text); padding: 6px 12px; border-radius: 8px; font-size: 12px; font-weight: 600; cursor: pointer; }
  .chip:hover { border-color: var(--yellow); color: var(--yellow); }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 18px; margin-bottom: 28px; }
  .card { background: var(--panel); border: 1px solid var(--border); border-radius: 14px; overflow: hidden; padding: 16px; }
  .card img { width: 100%; border-radius: 10px; margin-bottom: 12px; border: 1px solid #2b2f45; display: block; }
  .card h3 { font-size: 16px; margin-bottom: 6px; color: var(--yellow); }
  .card p { font-size: 13px; color: var(--muted); margin-bottom: 12px; }
  .stem-box { background: #0c0e16; border: 1px solid #23273b; border-radius: 10px; padding: 12px; margin-top: 10px; }
  audio { width: 100%; margin-top: 8px; height: 36px; }
  code { background: #090a10; color: var(--green); padding: 8px 12px; border-radius: 8px; display: block; font-size: 12px; margin-top: 8px; overflow-x: auto; border: 1px solid #1e2a24; }
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div>
      <div class="badge">ARYAN CHAUDHARY EXTRA • VIDEO #01 • 10:00 FULL HD</div>
      <h1>Tum Hi Se Baat Kar Raha Hoon — <span>Master MP4</span></h1>
    </div>
    <div class="actions">
      <a class="btn btn-primary" href="/videos/Tum_Hi_Se_Baat_Kar_Raha_Hoon_10min_MASTER.mp4?download=1" download>⬇ Download 10:00 Master MP4 (1080p)</a>
      <a class="btn btn-secondary" href="/videos/audio_stems/bgm_and_sfx_only_10min.m4a?download=1" download>⬇ Music + SFX Only (Replace Your Voice)</a>
    </div>
  </header>

  <div class="player-card">
    <video id="vid" controls preload="metadata" poster="/thumbnails/01_MRBEAST_2_SAAL_MAIN.jpg">
      <source src="/videos/Tum_Hi_Se_Baat_Kar_Raha_Hoon_10min_MASTER.mp4" type="video/mp4" />
    </video>
    <div class="chapters">
      <strong>JUMP TO CHAPTER:</strong>
      <button class="chip" onclick="jump(0)">0:00 Hook (2 Saal)</button>
      <button class="chip" onclick="jump(11)">0:11 Tumhara Din</button>
      <button class="chip" onclick="jump(42)">0:42 5 Problems</button>
      <button class="chip" onclick="jump(138)">2:18 Face-Cam Reset</button>
      <button class="chip" onclick="jump(151)">2:31 The 2-Year Math</button>
      <button class="chip" onclick="jump(244)">4:04 Tele-MANAS 14416</button>
      <button class="chip" onclick="jump(305)">5:05 Influencer Lie</button>
      <button class="chip" onclick="jump(412)">6:52 2036 Two Futures</button>
      <button class="chip" onclick="jump(505)">8:25 5 Tonight Steps</button>
      <button class="chip" onclick="jump(566)">9:26 Quiet Close & Loop</button>
    </div>
  </div>

  <h2 style="margin-bottom:14px;font-size:20px;">MrBeast / Tycoon-Level High-CTR Thumbnails (1920×1080)</h2>
  <div class="grid">
    <div class="card">
      <img src="/thumbnails/01_MRBEAST_2_SAAL_MAIN.jpg" alt="Thumbnail 1" />
      <h3>Option 1 (Recommended Winner): 2 SAAL BARBAAD!</h3>
      <p>Title: <em>Tumhari Zindagi Ke 2 Saal Kahan Ja Rahe Hain?</em></p>
      <a class="btn btn-primary" style="padding:8px 14px;font-size:13px;" href="/thumbnails/01_MRBEAST_2_SAAL_MAIN.jpg?download=1" download>⬇ Download 1080p JPG</a>
    </div>
    <div class="card">
      <img src="/thumbnails/02_DIRECT_CALLOUT_TUMSE_HI.jpg" alt="Thumbnail 2" />
      <h3>Option 2: TUMSE HI — RUKO 1 MIN!</h3>
      <p>Title: <em>Ye Video Tumse Hi Baat Kar Raha Hai (10 Minute Ka Sach)</em></p>
      <a class="btn btn-secondary" style="padding:8px 14px;font-size:13px;" href="/thumbnails/02_DIRECT_CALLOUT_TUMSE_HI.jpg?download=1" download>⬇ Download 1080p JPG</a>
    </div>
    <div class="card">
      <img src="/thumbnails/03_TYCOON_EXPOSED_TUM_MAAL_HO.jpg" alt="Thumbnail 3" />
      <h3>Option 3: TUM MAAL HO — KADWA SACH</h3>
      <p>Title: <em>Reels, Fake Courses Aur Tumhara Future: Kadwa Hisaab</em></p>
      <a class="btn btn-secondary" style="padding:8px 14px;font-size:13px;" href="/thumbnails/03_TYCOON_EXPOSED_TUM_MAAL_HO.jpg?download=1" download>⬇ Download 1080p JPG</a>
    </div>
  </div>

  <div class="grid">
    <div class="card">
      <h3>Swap AI Voice With Your Own Voice</h3>
      <p>Clean 10:00 Music + SFX stem (zero AI voice) so you can drop your real voiceover right on top in CapCut/Premiere or run one command:</p>
      <div class="stem-box">
        <strong style="font-size:12px;color:var(--cyan);">Clean Music + SFX Bed (10:00):</strong>
        <audio controls preload="none" src="/videos/audio_stems/bgm_and_sfx_only_10min.m4a"></audio>
      </div>
      <div class="stem-box">
        <strong style="font-size:12px;color:var(--magenta);">Isolated Timed AI Voice Guide (10:00):</strong>
        <audio controls preload="none" src="/videos/audio_stems/ai_voiceover_timed_10min.m4a"></audio>
      </div>
      <code>.venv/bin/python scripts/replace_voice.py your_recorded_voice.wav</code>
    </div>
    <div class="card">
      <h3>Master Production Package (A–G)</h3>
      <p>Full scored hooks, 1,325-word timestamped script table, 5 Face-Cam shooting guides, SFX cue sheet, chapters, verified sources, and 5 Shorts cut-downs:</p>
      <a class="btn btn-secondary" style="margin-top:8px;" href="/docs/MASTER_PRODUCTION_PACKAGE_A_TO_G.md?download=1" download>⬇ Download Full Script & Production Package (.md)</a>
    </div>
  </div>
</div>
<script>
  function jump(sec) {
    const v = document.getElementById('vid');
    v.currentTime = sec;
    v.play();
  }
</script>
</body>
</html>
"""


class RangeRequestHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Accept-Ranges", "bytes")
        super().end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        rel = unquote(parsed.path).lstrip("/")
        qs = parse_qs(parsed.query)

        if rel == "" or rel == "index.html":
            body = HTML_PAGE.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        full = os.path.abspath(os.path.join(ROOT, rel))
        if not full.startswith(ROOT) or not os.path.isfile(full):
            self.send_error(404, "File not found")
            return

        fsize = os.path.getsize(full)
        ctype = mimetypes.guess_type(full)[0] or "application/octet-stream"
        force_dl = "download" in qs

        range_hdr = self.headers.get("Range")
        if range_hdr and not force_dl:
            m = re.match(r"bytes=(\d+)-(\d*)", range_hdr)
            if m:
                start = int(m.group(1))
                end = int(m.group(2)) if m.group(2) else fsize - 1
                end = min(end, fsize - 1)
                if start >= fsize:
                    self.send_error(416, "Requested Range Not Satisfiable")
                    return
                length = end - start + 1
                self.send_response(206)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Range", f"bytes {start}-{end}/{fsize}")
                self.send_header("Content-Length", str(length))
                self.end_headers()
                with open(full, "rb") as f:
                    f.seek(start)
                    rem = length
                    while rem > 0:
                        chunk = f.read(min(65536, rem))
                        if not chunk:
                            break
                        self.wfile.write(chunk)
                        rem -= len(chunk)
                return

        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(fsize))
        if force_dl:
            self.send_header("Content-Disposition", f'attachment; filename="{os.path.basename(full)}"')
        self.end_headers()
        with open(full, "rb") as f:
            while True:
                chunk = f.read(65536)
                if not chunk:
                    break
                self.wfile.write(chunk)


if __name__ == "__main__":
    print(f"Studio server listening on http://0.0.0.0:{PORT}")
    ThreadingHTTPServer(("0.0.0.0", PORT), RangeRequestHandler).serve_forever()
