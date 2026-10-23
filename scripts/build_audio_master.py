#!/usr/bin/env python3
"""
Builds the complete 10:00 (600.00s) Sound Design + Timed Voiceover Master.
Automatically scales inter-segment breathing pauses so the final spoken word
always lands cleanly at ~596.0s inside the 600.00s (10:00) timeline!
"""
import os
import json
import subprocess
import numpy as np
from scipy.signal import butter, lfilter
import imageio_ffmpeg

SR = 44100
TOTAL_SEC = 600.0
N_SAMPLES = int(SR * TOTAL_SEC)
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

os.makedirs("videos/audio_stems", exist_ok=True)


def load_mp3_mono(path: str) -> np.ndarray:
    cmd = [FFMPEG, "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"]
    raw = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()


def find_best_valley(wav: np.ndarray, approx_sec: float, search_radius: float = 1.3) -> int:
    c = int(approx_sec * SR)
    r = int(search_radius * SR)
    lo = max(0, c - r)
    hi = min(len(wav), c + r)
    win = int(0.04 * SR)
    if hi - lo <= win * 2:
        return min(len(wav) - 1, max(0, c))
    seg = wav[lo:hi]
    n = len(seg) // win
    rms = np.sqrt(np.mean(seg[: n * win].reshape(n, win) ** 2, axis=1))
    return lo + int(np.argmin(rms)) * win + win // 2


def fade_edges(seg: np.ndarray, ms: float = 12.0) -> np.ndarray:
    out = seg.copy()
    k = min(int(SR * ms / 1000.0), len(out) // 4)
    if k > 1:
        ramp = np.linspace(0.0, 1.0, k, dtype=np.float32)
        out[:k] *= ramp
        out[-k:] *= ramp[::-1]
    return out


def place_mono(buf_l: np.ndarray, buf_r: np.ndarray, sig: np.ndarray, start_s: float, gain_l=1.0, gain_r=1.0):
    i0 = int(round(start_s * SR))
    if i0 >= N_SAMPLES or i0 + len(sig) <= 0:
        return
    s0 = max(0, -i0)
    d0 = max(0, i0)
    n = min(len(sig) - s0, N_SAMPLES - d0)
    if n > 0:
        chunk = sig[s0 : s0 + n]
        buf_l[d0 : d0 + n] += chunk * gain_l
        buf_r[d0 : d0 + n] += chunk * gain_r


rng = np.random.default_rng(20261023)


def sfx_sub_impact(dur=0.95, freq_start=115.0, freq_end=34.0, amp=0.68):
    t = np.linspace(0, dur, int(SR * dur), endpoint=False, dtype=np.float32)
    phase = 2 * np.pi * (freq_end * t + (freq_start - freq_end) * (1 - np.exp(-t * 9.0)) / 9.0)
    sub = np.sin(phase) * np.exp(-t * 3.6)
    punch = np.sin(2 * np.pi * 180 * t) * np.exp(-t * 28.0) * 0.45
    click = rng.normal(0, 1, len(t)).astype(np.float32) * np.exp(-t * 55.0) * 0.22
    return fade_edges((sub + punch + click) * amp, 4.0)


def sfx_whoosh(dur=0.34, bright=1600.0, amp=0.26):
    t = np.linspace(0, dur, int(SR * dur), endpoint=False, dtype=np.float32)
    noise = rng.normal(0, 1, len(t)).astype(np.float32)
    b, a = butter(2, [280 / (SR / 2), min(0.9, bright / (SR / 2))], btype="band")
    filt = lfilter(b, a, noise).astype(np.float32)
    return fade_edges(filt * (np.sin(np.pi * (t / dur)) ** 1.8) * amp, 5.0)


def sfx_riser(dur=2.0, amp=0.30):
    t = np.linspace(0, dur, int(SR * dur), endpoint=False, dtype=np.float32)
    f = 140.0 * (4.2 ** (t / dur))
    phase = 2 * np.pi * np.cumsum(f) / SR
    tone = (np.sin(phase) * 0.55 + np.sin(phase * 1.5) * 0.25).astype(np.float32)
    noise = rng.normal(0, 1, len(t)).astype(np.float32) * 0.35
    b, a = butter(2, 2400 / (SR / 2), btype="low")
    return fade_edges((tone + lfilter(b, a, noise).astype(np.float32)) * ((t / dur) ** 2.3) * amp, 10.0)


def sfx_tick(amp=0.22):
    t = np.linspace(0, 0.045, int(SR * 0.045), endpoint=False, dtype=np.float32)
    return ((np.sin(2 * np.pi * 2100 * t) + 0.5 * np.sin(2 * np.pi * 4300 * t)) * np.exp(-t * 95.0) * amp).astype(np.float32)


def sfx_notif_ping(amp=0.28):
    t = np.linspace(0, 0.28, int(SR * 0.28), endpoint=False, dtype=np.float32)
    n1 = int(0.08 * SR)
    sig = np.zeros_like(t)
    sig[:n1] = np.sin(2 * np.pi * 1046.5 * t[:n1]) * np.exp(-t[:n1] * 18.0)
    sig[n1:] = np.sin(2 * np.pi * 1318.5 * (t[n1:] - t[n1])) * np.exp(-(t[n1:] - t[n1]) * 14.0)
    return fade_edges(sig * amp, 4.0)


def sfx_phone_buzz(dur=0.42, amp=0.26):
    t = np.linspace(0, dur, int(SR * dur), endpoint=False, dtype=np.float32)
    pulse = (np.sin(2 * np.pi * 9.0 * t) > -0.2).astype(np.float32)
    return fade_edges((np.sin(2 * np.pi * 142 * t) + 0.45 * np.sin(2 * np.pi * 284 * t)) * pulse * amp, 10.0)


def sfx_alarm(dur=0.85, amp=0.30):
    t = np.linspace(0, dur, int(SR * dur), endpoint=False, dtype=np.float32)
    gate = (np.sin(2 * np.pi * 6.0 * t) > 0).astype(np.float32)
    return fade_edges((np.sin(2 * np.pi * 880 * t) + 0.5 * np.sin(2 * np.pi * 1760 * t)) * gate * amp, 8.0)


def sfx_record_scratch(dur=0.42, amp=0.35):
    t = np.linspace(0, dur, int(SR * dur), endpoint=False, dtype=np.float32)
    f = 950.0 * np.exp(-t * 5.2) + 80.0 * np.sin(2 * np.pi * 14 * t)
    phase = 2 * np.pi * np.cumsum(np.maximum(40.0, f)) / SR
    grit = rng.normal(0, 0.25, len(t)).astype(np.float32)
    return fade_edges((np.tanh(np.sin(phase) * 2.2) + grit) * np.exp(-t * 3.2) * amp, 5.0)


def sfx_brass_stab(dur=0.75, amp=0.42):
    t = np.linspace(0, dur, int(SR * dur), endpoint=False, dtype=np.float32)
    sig = np.zeros_like(t)
    for k, f in enumerate([73.42, 146.83, 220.0, 293.66]):
        for h in range(1, 6):
            sig += (1.0 / h) * np.sin(2 * np.pi * f * h * t) * (0.55 / (k + 1))
    b, a = butter(2, 1400 / (SR / 2), btype="low")
    env = np.minimum(1.0, t / 0.02) * np.exp(-t * 3.4)
    return fade_edges(lfilter(b, a, sig).astype(np.float32) * env * amp, 6.0)


def sfx_glitch(dur=0.18, amp=0.26):
    t = np.linspace(0, dur, int(SR * dur), endpoint=False, dtype=np.float32)
    chop = (np.sin(2 * np.pi * 38.0 * t) > 0).astype(np.float32)
    sig = (np.sign(np.sin(2 * np.pi * 620 * t)) * 0.5 + rng.normal(0, 0.5, len(t)).astype(np.float32)) * chop
    return fade_edges(sig * amp, 3.0)


def sfx_lock_click(amp=0.36):
    t = np.linspace(0, 0.14, int(SR * 0.14), endpoint=False, dtype=np.float32)
    c1 = np.sin(2 * np.pi * 1650 * t) * np.exp(-t * 65.0)
    c2 = np.zeros_like(t)
    s2 = int(0.045 * SR)
    c2[s2:] = np.sin(2 * np.pi * 2480 * (t[s2:] - t[s2])) * np.exp(-(t[s2:] - t[s2]) * 55.0)
    return fade_edges((c1 + c2) * amp, 2.0)


def write_aac(path: str, left: np.ndarray, right: np.ndarray, bitrate="128k"):
    stereo = np.stack([np.clip(left, -0.99, 0.99), np.clip(right, -0.99, 0.99)], axis=1).astype(np.float32)
    cmd = [FFMPEG, "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", "-c:a", "aac", "-b:a", bitrate, path]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    proc.stdin.write(stereo.tobytes())
    proc.stdin.close()
    proc.wait()


def main():
    vo_l = np.zeros(N_SAMPLES, dtype=np.float32)
    vo_r = np.zeros(N_SAMPLES, dtype=np.float32)

    clips = {i: load_mp3_mono(f"assets/vo_raw/vo_{i:02d}_" + name) for i, name in [
        (1, "hook_and_day.mp3"),
        (2, "problems_1_to_3.mp3"),
        (3, "problems_4_5_reset.mp3"),
        (4, "reality_math_screens.mp3"),
        (5, "reality_jobs_human_country.mp3"),
        (6, "influencer_lie_part1.mp3"),
        (7, "influencer_sebi_study.mp3"),
        (8, "two_futures_2036.mp3"),
        (9, "country_scale_steps_1_3.mp3"),
        (10, "steps_4_5_and_close.mp3"),
    ]}

    # Split proportional to clip lengths at natural silence valleys
    c3_s = find_best_valley(clips[3], len(clips[3]) / SR * 0.72, 1.4)
    c4_s = find_best_valley(clips[4], len(clips[4]) / SR * 0.36, 1.4)
    c5_s1 = find_best_valley(clips[5], len(clips[5]) / SR * 0.30, 1.4)
    c5_s2 = find_best_valley(clips[5], len(clips[5]) / SR * 0.70, 1.6)
    c6_s = find_best_valley(clips[6], len(clips[6]) / SR * 0.59, 1.4)
    c8_s = find_best_valley(clips[8], len(clips[8]) / SR * 0.85, 1.4)
    c9_s1 = find_best_valley(clips[9], len(clips[9]) / SR * 0.48, 1.4)
    c9_s2 = find_best_valley(clips[9], len(clips[9]) / SR * 0.54, 1.4)
    c10_s1 = find_best_valley(clips[10], len(clips[10]) / SR * 0.50, 1.4)
    c10_s2 = find_best_valley(clips[10], len(clips[10]) / SR * 0.92, 1.3)

    raw_parts = [
        ("01_hook_and_day", fade_edges(clips[1]), 1.4, False, False),
        ("02_problems_1_to_3", fade_edges(clips[2]), 0.9, False, False),
        ("03a_problems_4_5", fade_edges(clips[3][:c3_s]), 1.1, False, False),
        ("03b_facecam_reset", fade_edges(clips[3][c3_s:]), 0.9, True, False),
        ("04a_math_build", fade_edges(clips[4][:c4_s]), 0.9, False, False),
        ("04b_2saal_and_surveys", fade_edges(clips[4][c4_s:]), 0.9, False, False),
        ("05a_jobs_plfs", fade_edges(clips[5][:c5_s1]), 0.8, False, False),
        ("05b_ncrb_telemanas", fade_edges(clips[5][c5_s1:c5_s2]), 2.6, False, True),
        ("05c_india_2041_window", fade_edges(clips[5][c5_s2:]), 1.0, False, False),
        ("06a_influencer_lie", fade_edges(clips[6][:c6_s]), 0.8, False, False),
        ("06b_facecam_trust", fade_edges(clips[6][c6_s:]), 0.8, True, False),
        ("07_sebi_and_foundation", fade_edges(clips[7]), 1.0, False, False),
        ("08a_two_futures_2036", fade_edges(clips[8][:c8_s]), 0.7, False, False),
        ("08b_facecam_interrupt", fade_edges(clips[8][c8_s:]), 0.8, True, False),
        ("09a_country_365cr", fade_edges(clips[9][:c9_s1]), 1.0, False, False),
        ("09b_khara_ganit", fade_edges(clips[9][c9_s1:c9_s2]), 0.9, False, False),
        ("09c_steps_1_to_3", fade_edges(clips[9][c9_s2:]), 0.8, False, False),
        ("10a_steps_4_5", fade_edges(clips[10][:c10_s1]), 0.9, False, False),
        ("10b_facecam_close", fade_edges(clips[10][c10_s1:c10_s2]), 1.2, True, False),
        ("10c_final_callback", fade_edges(clips[10][c10_s2:]), 0.0, True, False),
    ]

    speech_sum = sum(len(a) / SR for _, a, _, _, _ in raw_parts)
    base_gaps = sum(g for _, _, g, _, _ in raw_parts)
    # Auto-scale gaps so speech + gaps + 0.35s intro lands right at 596.2s!
    target_gaps = max(6.0, 596.2 - 0.35 - speech_sum)
    gap_scale = target_gaps / base_gaps

    placements = []
    cursor = 0.35
    for seg_id, arr, g, fc, sz in raw_parts:
        dur = len(arr) / SR
        start = cursor
        end = start + dur
        place_mono(vo_l, vo_r, arr, start, 1.0, 1.0)
        placements.append({
            "id": seg_id,
            "start": round(start, 3),
            "end": round(end, 3),
            "duration": round(dur, 3),
            "face_cam": fc,
            "silence_zone": sz,
        })
        cursor = end + g * gap_scale

    print(f"Speech sum: {speech_sum:.2f}s | Final spoken word ends at: {placements[-1]['end']:.2f}s / {TOTAL_SEC}s")

    vo_gain = min(1.35, 0.84 / (float(np.max(np.abs(vo_l))) + 1e-6))
    vo_l *= vo_gain
    vo_r *= vo_gain

    bgm_l = np.zeros(N_SAMPLES, dtype=np.float32)
    bgm_r = np.zeros(N_SAMPLES, dtype=np.float32)

    def render_pulse_bed(t0: float, t1: float, bpm: float, root_hz: float, bright: float, amp: float, warm: bool = False):
        i0, i1 = int(t0 * SR), min(N_SAMPLES, int(t1 * SR))
        if i1 <= i0 + 100:
            return
        t = np.arange(i1 - i0, dtype=np.float32) / SR
        beat_pos = (t * (bpm / 60.0)) % 1.0
        pulse_env = np.exp(-beat_pos * 5.2).astype(np.float32)
        bar_idx = ((t * (bpm / 60.0)) // 4).astype(np.int32) % 4
        ratios = np.array([1.0, 1.0, 0.7937, 0.8909], dtype=np.float32) if not warm else np.array([1.0, 1.2599, 1.4983, 1.1225], dtype=np.float32)
        ph = (2 * np.pi * np.cumsum(root_hz * ratios[bar_idx]) / SR).astype(np.float32)
        bass = (np.sin(ph) * 0.72 + np.sin(ph * 2.0) * 0.28) * pulse_env

        pf2 = root_hz * (2.5198 if warm else 2.3784)
        pad_l = (np.sin(2 * np.pi * root_hz * 2.0 * t) + 0.6 * np.sin(2 * np.pi * pf2 * t + 0.4)) * 0.26
        pad_r = (np.sin(2 * np.pi * root_hz * 2.0 * t + 0.3) + 0.6 * np.sin(2 * np.pi * pf2 * t)) * 0.26
        arp = np.sin(2 * np.pi * (root_hz * 4.0) * t) * np.exp(-((t * (bpm / 30.0)) % 1.0) * 14.0) * 0.15

        b, a = butter(2, min(0.9, bright / (SR / 2)), btype="low")
        bgm_l[i0:i1] += fade_edges(lfilter(b, a, (bass + pad_l + arp * 0.8) * amp).astype(np.float32), 160.0)
        bgm_r[i0:i1] += fade_edges(lfilter(b, a, (bass + pad_r + arp * 1.1) * amp).astype(np.float32), 160.0)

    p_map = {p["id"]: p for p in placements}
    render_pulse_bed(0.35, p_map["03b_facecam_reset"]["start"] - 0.1, 100.0, 73.42, 900.0, 0.30, False)
    rst = p_map["03b_facecam_reset"]
    render_pulse_bed(rst["start"] + 4.5, rst["end"] + 0.6, 60.0, 55.0, 380.0, 0.22, False)
    render_pulse_bed(p_map["04a_math_build"]["start"], p_map["04a_math_build"]["end"] - 0.05, 68.0, 65.41, 620.0, 0.28, False)
    render_pulse_bed(p_map["04b_2saal_and_surveys"]["start"] + 2.0, p_map["05a_jobs_plfs"]["end"] - 0.2, 68.0, 65.41, 650.0, 0.26, False)
    for hb_s in np.arange(p_map["04a_math_build"]["start"], p_map["04a_math_build"]["end"] - 0.4, 60.0 / 68.0):
        place_mono(bgm_l, bgm_r, sfx_sub_impact(0.22, 85, 38, 0.22), float(hb_s))
        place_mono(bgm_l, bgm_r, sfx_sub_impact(0.18, 72, 34, 0.15), float(hb_s) + 0.23)

    render_pulse_bed(p_map["05c_india_2041_window"]["start"], p_map["05c_india_2041_window"]["end"], 96.0, 73.42, 850.0, 0.27, False)
    render_pulse_bed(p_map["06a_influencer_lie"]["start"], p_map["06a_influencer_lie"]["end"], 102.0, 61.74, 1050.0, 0.29, False)
    render_pulse_bed(p_map["06b_facecam_trust"]["start"], p_map["06b_facecam_trust"]["end"], 102.0, 61.74, 480.0, 0.14, False)
    render_pulse_bed(p_map["07_sebi_and_foundation"]["start"], p_map["07_sebi_and_foundation"]["end"], 100.0, 73.42, 920.0, 0.27, False)
    s8 = p_map["08a_two_futures_2036"]
    mid8 = s8["start"] + s8["duration"] * 0.46
    render_pulse_bed(s8["start"], mid8, 92.0, 65.41, 520.0, 0.24, False)
    render_pulse_bed(mid8, s8["end"] - 0.05, 98.0, 73.42, 1350.0, 0.30, True)
    render_pulse_bed(p_map["09a_country_365cr"]["start"], p_map["09a_country_365cr"]["end"] - 0.05, 100.0, 73.42, 1300.0, 0.30, True)
    render_pulse_bed(p_map["09c_steps_1_to_3"]["start"], p_map["10a_steps_4_5"]["end"], 106.0, 82.41, 1500.0, 0.31, True)

    s_close = p_map["10b_facecam_close"]
    i0, i1 = int(s_close["start"] * SR), int(s_close["end"] * SR)
    tc = np.arange(max(1, i1 - i0), dtype=np.float32) / SR
    wn = fade_edges(((np.sin(2 * np.pi * 146.83 * tc) + 0.5 * np.sin(2 * np.pi * 220.0 * tc)) * 0.09).astype(np.float32), 500.0)
    bgm_l[i0 : i0 + len(wn)] += wn
    bgm_r[i0 : i0 + len(wn)] += wn

    # Duck music -13.5 dB when voice speaks
    win = int(0.05 * SR)
    nw = N_SAMPLES // win
    speaking = (np.sqrt(np.mean(vo_l[: nw * win].reshape(nw, win) ** 2, axis=1)) > 0.015).astype(np.float32)
    duck_amount = np.convolve(speaking, np.ones(6, dtype=np.float32) / 6.0, mode="same")
    gain_sample = np.repeat(1.0 - 0.78 * np.clip(duck_amount * 1.3, 0.0, 1.0), win)
    if len(gain_sample) < N_SAMPLES:
        gain_sample = np.pad(gain_sample, (0, N_SAMPLES - len(gain_sample)), mode="edge")
    bgm_l *= gain_sample[:N_SAMPLES]
    bgm_r *= gain_sample[:N_SAMPLES]

    sfx_l = np.zeros(N_SAMPLES, dtype=np.float32)
    sfx_r = np.zeros(N_SAMPLES, dtype=np.float32)
    sfx_cues = []

    def add_sfx(ts: float, kind: str, sig: np.ndarray, pan: float = 0.0, note: str = ""):
        gl = float(np.sqrt(0.5 * (1.0 - pan)))
        gr = float(np.sqrt(0.5 * (1.0 + pan)))
        place_mono(sfx_l, sfx_r, sig, ts, gl, gr)
        sfx_cues.append({"time": round(ts, 2), "sfx": kind, "note": note})

    add_sfx(0.08, "sub_impact", sfx_sub_impact(0.9, 120, 35, 0.62), 0.0, "1-frame white flash + hook slam")
    for tk in [2.6, 3.1, 3.6, 4.1, 4.6, 5.1]:
        add_sfx(tk, "clock_tick", sfx_tick(0.22), 0.25 if int(tk * 2) % 2 == 0 else -0.25, "Hook clock ticks")
    add_sfx(5.9, "whoosh", sfx_whoosh(0.32, 1900, 0.28), -0.2, "Thumb 3x scroll cut")
    add_sfx(7.8, "sub_impact", sfx_sub_impact(1.0, 130, 32, 0.68), 0.0, "Smash zoom yellow 2 SAAL")
    add_sfx(13.8, "alarm_buzz", sfx_alarm(0.8, 0.26), -0.15, "Subah alarm")
    add_sfx(16.8, "phone_vibrate", sfx_phone_buzz(0.42, 0.25), 0.2, "Phone vibration")
    add_sfx(19.2, "notif_ping", sfx_notif_ping(0.28), -0.25, "Generic notification ping")
    add_sfx(21.4, "whoosh", sfx_whoosh(0.28, 2100, 0.24), 0.3, "Reels montage cut 1")
    add_sfx(23.5, "whoosh", sfx_whoosh(0.28, 2100, 0.24), -0.3, "Reels montage cut 2")
    add_sfx(34.5, "record_scratch", sfx_record_scratch(0.42, 0.32), 0.0, "Record scratch before Kal se pakka")
    add_sfx(p_map["02_problems_1_to_3"]["start"] - 1.4, "riser", sfx_riser(1.35, 0.28), 0.0, "Riser into 5 Problems")
    add_sfx(p_map["02_problems_1_to_3"]["start"] + 4.2, "sub_impact", sfx_sub_impact(0.75, 105, 38, 0.48), 0.0, "PROBLEM 1")
    add_sfx(p_map["02_problems_1_to_3"]["start"] + 28.5, "sub_impact", sfx_sub_impact(0.75, 105, 38, 0.48), 0.0, "PROBLEM 2")
    add_sfx(p_map["02_problems_1_to_3"]["start"] + 48.0, "sub_impact", sfx_sub_impact(0.75, 105, 38, 0.48), 0.0, "PROBLEM 3")
    add_sfx(p_map["03a_problems_4_5"]["start"] + 0.4, "sub_impact", sfx_sub_impact(0.75, 105, 38, 0.48), 0.0, "PROBLEM 4")
    add_sfx(p_map["03a_problems_4_5"]["start"] + 15.2, "sub_impact", sfx_sub_impact(0.75, 105, 38, 0.48), 0.0, "PROBLEM 5")
    add_sfx(p_map["03b_facecam_reset"]["start"] - 1.0, "riser", sfx_riser(0.95, 0.28), 0.0, "Riser into Face-Cam Reset")
    add_sfx(p_map["04a_math_build"]["start"] + 0.2, "sub_impact", sfx_sub_impact(0.85, 115, 36, 0.55), 0.0, "Math start")
    add_sfx(p_map["04b_2saal_and_surveys"]["start"] + 0.05, "sub_impact", sfx_sub_impact(1.15, 135, 30, 0.72), 0.0, "BIG REVEAL: DO SAAL!")
    add_sfx(p_map["05a_jobs_plfs"]["start"] + 6.0, "sub_impact", sfx_sub_impact(0.8, 110, 36, 0.50), 0.0, "PLFS 9.9% & 15%")
    add_sfx(p_map["06a_influencer_lie"]["start"] - 1.3, "riser", sfx_riser(1.25, 0.30), 0.0, "Riser into Influencer Lie")
    add_sfx(p_map["06a_influencer_lie"]["start"] + 5.0, "glitch_burst", sfx_glitch(0.20, 0.26), 0.2, "Fake thumbnail crack")
    add_sfx(p_map["06a_influencer_lie"]["start"] + 18.5, "brass_stab", sfx_brass_stab(0.80, 0.46), 0.0, "BRASS STAB: Tum Maal Ho")
    add_sfx(p_map["07_sebi_and_foundation"]["start"] + 2.8, "sub_impact", sfx_sub_impact(0.75, 110, 38, 0.48), 0.0, "SEBI Action")
    add_sfx(p_map["08a_two_futures_2036"]["start"] + 0.2, "sub_impact", sfx_sub_impact(0.85, 115, 36, 0.52), 0.0, "2036 Split")
    add_sfx(p_map["08b_facecam_interrupt"]["start"] - 0.35, "record_scratch", sfx_record_scratch(0.35, 0.34), 0.0, "6s Face-Cam Interrupt")
    add_sfx(p_map["09b_khara_ganit"]["start"] + 0.05, "sub_impact", sfx_sub_impact(0.95, 125, 33, 0.64), 0.0, "Ye khara ganit hai")
    s9c = p_map["09c_steps_1_to_3"]["start"]
    s10a = p_map["10a_steps_4_5"]["start"]
    for st_t, lbl in [(s9c + 4.2, "STEP 1"), (s9c + 14.0, "STEP 2"), (s9c + 22.5, "STEP 3"), (s10a + 0.5, "STEP 4"), (s10a + 13.0, "STEP 5")]:
        add_sfx(st_t, "lock_click", sfx_lock_click(0.38), 0.0, lbl)

    zero_windows = [
        (p_map["04a_math_build"]["end"] + 0.02, p_map["04b_2saal_and_surveys"]["start"] - 0.02),
        (p_map["05b_ncrb_telemanas"]["start"] - 0.2, p_map["05c_india_2041_window"]["start"] - 0.1),
        (p_map["09a_country_365cr"]["end"] + 0.02, p_map["09b_khara_ganit"]["start"] - 0.02),
        (p_map["10b_facecam_close"]["end"] + 0.02, TOTAL_SEC),
    ]
    for z0, z1 in zero_windows:
        ia, ib = max(0, int(z0 * SR)), min(N_SAMPLES, int(z1 * SR))
        bgm_l[ia:ib] = 0.0
        bgm_r[ia:ib] = 0.0
        sfx_l[ia:ib] = 0.0
        sfx_r[ia:ib] = 0.0

    bed_l = np.tanh((bgm_l + sfx_l) * 1.05) * 0.92
    bed_r = np.tanh((bgm_r + sfx_r) * 1.05) * 0.92
    mix_l = np.tanh((vo_l + bed_l) * 1.04) * 0.95
    mix_r = np.tanh((vo_r + bed_r) * 1.04) * 0.95

    write_aac("/tmp/master_mix_with_ai_vo.m4a", mix_l, mix_r, "144k")
    write_aac("videos/audio_stems/bgm_and_sfx_only_10min.m4a", bed_l, bed_r, "128k")
    write_aac("videos/audio_stems/ai_voiceover_timed_10min.m4a", vo_l, vo_r, "112k")

    with open("videos/timeline_manifest.json", "w", encoding="utf-8") as f:
        json.dump({
            "total_duration_sec": TOTAL_SEC,
            "placements": placements,
            "zero_silence_windows": [[round(a, 2), round(b, 2)] for a, b in zero_windows],
            "sfx_cue_sheet": sorted(sfx_cues, key=lambda x: x["time"]),
        }, f, indent=2)
    print("Audio master & stems ready!")


if __name__ == "__main__":
    main()
