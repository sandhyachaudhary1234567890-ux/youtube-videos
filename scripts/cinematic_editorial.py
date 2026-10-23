"""Original editorial rules and deterministic sound design; no downloaded audio."""
import math
import wave
from pathlib import Path
import numpy as np

SAMPLE_RATE = 48000

def refine_shots(shots, placements):
    """Use motion for emphasis, clean cuts for continuity, silence for care."""
    face_ids = {p['id'] for p in placements if p.get('face_cam')}
    previous = None
    for shot in shots:
        chapter_change = previous is not None and previous['seg_id'] != shot['seg_id']
        safe = shot['seg_id'] == '05b_ncrb_telemanas'
        adjacent_safe = previous is not None and previous['seg_id'] == '05b_ncrb_telemanas'
        face = shot['seg_id'] in face_ids or shot['id'] == 0
        if safe or adjacent_safe:
            shot['trans_type'] = 'fade'
        elif face:
            shot['trans_type'] = 'cut'
        elif chapter_change:
            shot['trans_type'] = 'zoom' if 'math' in shot['seg_id'] else 'wipe'
        elif shot['id'] % 5 == 0:
            shot['trans_type'] = 'whip'
        elif shot['id'] % 7 == 0:
            shot['trans_type'] = 'leak'
        else:
            shot['trans_type'] = 'cut'
        # No arbitrary clock faces, code or rain over unrelated subject matter.
        plate = shot['plate']
        if face or safe:
            shot['env'] = 'none'
        elif any(k in plate for k in ('rain', 'puddle', 'bus')):
            shot['env'] = 'rain'
        elif any(k in plate for k in ('coding', 'server', 'editing')):
            shot['env'] = 'code'
        elif any(k in plate for k in ('metro', 'bokeh', 'street')):
            shot['env'] = 'bokeh'
        else:
            shot['env'] = 'dust'
        shot['camera_strength'] = 0.18 if face else (0.08 if safe else 1.0)
        previous = shot
    return shots

def sound_cues(shots, manifest):
    safe = next(p for p in manifest['placements'] if p['id'] == '05b_ncrb_telemanas')
    existing = [s['time'] for s in manifest.get('sfx_cue_sheet', [])]
    cues = []
    for shot in shots[1:]:
        t = shot['start']
        if shot['trans_type'] in ('cut', 'fade'):
            continue
        if safe['start'] - 1.0 <= t <= safe['end'] + 1.0:
            continue
        if any(abs(t - x) < 1.0 for x in existing):
            continue
        if cues and t - cues[-1]['time'] < 6.0:
            continue
        cues.append({'time': round(t, 4), 'kind': shot['trans_type'], 'gain_db': -29,
                     'duration': 0.36 if shot['trans_type'] == 'whip' else 0.6})
    return cues

def synthesize_soundtrack(shots, manifest, output):
    """Quiet band-limited air sweeps, not repetitive loud impacts. PCM testable."""
    sr = SAMPLE_RATE
    bed = np.zeros(round(manifest['total_duration_sec'] * sr), dtype=np.float32)
    rng = np.random.default_rng(2026)
    cues = sound_cues(shots, manifest)
    for cue in cues:
        n = round(cue['duration'] * sr)
        t = np.arange(n, dtype=np.float32) / sr
        noise = rng.normal(0, 1, n).astype(np.float32)
        # Smooth noise; suppress harsh top-end before laying underneath speech.
        air = np.convolve(noise, np.ones(24, dtype=np.float32) / 24, mode='same')
        envelope = np.sin(np.linspace(0, math.pi, n)) ** 2
        if cue['kind'] == 'zoom':
            tone = np.sin(2 * math.pi * (100*t + 70*t*t)) * .12
            air += tone
        elif cue['kind'] == 'leak':
            air *= .6
        sound = air * envelope
        peak = max(float(np.max(np.abs(sound))), 1e-6)
        sound *= 10 ** (cue['gain_db']/20) / peak
        # Small audio lead-in anticipates the visual cut.
        start = max(0, round((cue['time'] - .12) * sr))
        end = min(len(bed), start+n)
        bed[start:end] += sound[:end-start]
    # Sample-accurate hard exclusion, after all envelopes/tails have been summed.
    safe = next(p for p in manifest['placements'] if p['id'] == '05b_ncrb_telemanas')
    bed[math.floor(safe['start']*sr):math.ceil(safe['end']*sr)] = 0
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(output), 'wb') as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(sr)
        f.writeframes((np.clip(bed, -1, 1)*32767).astype('<i2').tobytes())
    return cues

def audio_mix_filter(safe_start, safe_end, *, with_fx=True):
    """Shared mix for master, excerpts and voice replacement. Inputs: VO=1, bed=2."""
    bed = '[2:a][3:a]amix=inputs=2:normalize=0[bed];' if with_fx else '[2:a]anull[bed];'
    return (
        '[1:a]highpass=f=80,acompressor=threshold=-18dB:ratio=3:attack=10:release=120,'
        'volume=1.35,asplit=2[vo][sc];' + bed +
        '[bed][sc]sidechaincompress=threshold=0.02:ratio=6:attack=25:release=280[ducked];'
        f"[ducked]volume=0:enable='between(t,{safe_start},{safe_end})'[safe];"
        '[vo][safe]amix=inputs=2:normalize=0,alimiter=limit=0.95:latency=1[aout]')
