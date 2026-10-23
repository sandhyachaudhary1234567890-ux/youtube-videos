#!/usr/bin/env python3
"""
One-command Voice Replacement Tool for Aryan Chaudhary Extra!
Usage:
    .venv/bin/python scripts/replace_voice.py your_recorded_voice.wav
"""
import sys
import os
import subprocess
import imageio_ffmpeg
import json
try:
    from .cinematic_editorial import audio_mix_filter
except ImportError:
    from cinematic_editorial import audio_mix_filter

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
MASTER_VIDEO = "videos/Tum_Hi_Se_Baat_Kar_Raha_Hoon_10min_MASTER.mp4"
BGM_SFX_STEM = "videos/audio_stems/bgm_and_sfx_only_10min.m4a"


def main():
    if len(sys.argv) < 2:
        print("Usage: .venv/bin/python scripts/replace_voice.py <your_voice.wav|mp3|m4a> [output.mp4]")
        sys.exit(1)
    user_vo = sys.argv[1]
    out_mp4 = sys.argv[2] if len(sys.argv) >= 3 else "videos/Tum_Hi_Se_Baat_Kar_Raha_Hoon_MY_VOICE.mp4"
    with open("videos/timeline_manifest.json", encoding="utf-8") as f:
        safe = next(p for p in json.load(f)["placements"] if p["id"] == "05b_ncrb_telemanas")
    cmd = [
        FFMPEG, "-y",
        "-i", MASTER_VIDEO, "-i", user_vo, "-i", BGM_SFX_STEM,
        "-filter_complex",
        audio_mix_filter(safe['start'], safe['end'], with_fx=False),
        "-map", "0:v:0", "-map", "[aout]",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", out_mp4,
    ]
    subprocess.run(cmd, check=True)
    print(f"Done! Custom-voiced video ready: {out_mp4}")


if __name__ == "__main__":
    main()
