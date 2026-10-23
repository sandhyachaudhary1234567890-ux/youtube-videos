#!/usr/bin/env python3
"""Render an actual continuous review excerpt, at the same 1080p60 settings."""
import argparse
import json
import subprocess
from pathlib import Path
try:
    from . import render_master_video_60fps as r
    from .cinematic_editorial import synthesize_soundtrack
except ImportError:
    import render_master_video_60fps as r
    from cinematic_editorial import synthesize_soundtrack

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--start',type=float,default=154)
    parser.add_argument('--duration',type=float,default=12)
    parser.add_argument('--output',default='videos/Cinematic_60FPS_12sec_REVIEW.mp4')
    args=parser.parse_args()
    if args.start<0 or args.duration<=0 or args.start+args.duration>600:
        parser.error('Excerpt must fit inside the 600 second timeline')
    manifest=json.loads(Path('videos/timeline_manifest.json').read_text())
    shots=r.build_shot_schedule(manifest)
    pmap={p['id']:p for p in manifest['placements']}
    start=round(args.start*r.FPS); end=start+round(args.duration*r.FPS)
    silent='/tmp/cinematic_excerpt_picture.mp4'
    r.render_chunk((start,end,silent,shots,[s['start'] for s in shots],pmap,manifest['placements']))
    fx='/tmp/cinematic_excerpt_fx.wav'
    synthesize_soundtrack(shots,manifest,fx)
    safe=pmap['05b_ncrb_telemanas']
    # Mix at original timeline timestamps, THEN trim. Safe-zone exclusion cannot shift.
    filters=(
        '[1:a]highpass=f=80,acompressor=threshold=-18dB:ratio=3:attack=10:release=120,'
        'volume=1.35,asplit=2[vo][sc];'
        '[2:a][3:a]amix=inputs=2:normalize=0[bed];'
        '[bed][sc]sidechaincompress=threshold=0.02:ratio=6:attack=25:release=280[ducked];'
        f"[ducked]volume=0:enable='between(t,{safe['start']},{safe['end']})'[safe];"
        '[vo][safe]amix=inputs=2:normalize=0,alimiter=limit=0.95:latency=1,'
        f'atrim=start={start/r.FPS}:duration={(end-start)/r.FPS},asetpts=PTS-STARTPTS[a]')
    subprocess.run([r.FFMPEG,'-y','-loglevel','error','-i',silent,
        '-i','videos/audio_stems/ai_voiceover_timed_10min.m4a',
        '-i','videos/audio_stems/bgm_and_sfx_only_10min.m4a','-i',fx,
        '-filter_complex',filters,'-map','0:v','-map','[a]',
        '-c:v','copy','-c:a','aac','-b:a','160k','-movflags','+faststart',
        '-t',str((end-start)/r.FPS),args.output],check=True)
    print(f'READY: {args.output}',flush=True)

if __name__=='__main__': main()
