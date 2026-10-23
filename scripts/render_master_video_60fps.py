#!/usr/bin/env python3
"""
60FPS Tycoon-MagnatesMedia-Vox-DhruvRathee Cinematic Documentary Renderer
1920x1080, 60fps, yuv420p, libx264, TRUE 60FPS with 2.5D parallax + environmental motion
"""
import os, sys, json, math, random, time, subprocess, multiprocessing
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter, ImageOps, ImageChops
import imageio_ffmpeg

W, H = 1920, 1080
FPS = 60
TOTAL_SEC = 600.0
TOTAL_FRAMES = int(TOTAL_SEC * FPS)
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
random.seed(42); np.random.seed(42)

C_BLACK=(6,6,10); C_PANEL=(15,16,24); C_WHITE=(248,249,252); C_MUTED=(165,170,185)
C_YELLOW=(255,214,0); C_MAGENTA=(255,30,138); C_CYAN=(0,229,255); C_GREEN=(0,230,118)
C_RED=(255,42,60); C_GOLD=(255,184,48)

# Fonts scaled for 1080p (1.5x from 720p)
try:
    F_ANTON_XL = ImageFont.truetype("assets/fonts/Anton-Regular.ttf", 177)
    F_ANTON_LG = ImageFont.truetype("assets/fonts/Anton-Regular.ttf", 123)
    F_ANTON_MD = ImageFont.truetype("assets/fonts/Anton-Regular.ttf", 81)
    F_ANTON_SM = ImageFont.truetype("assets/fonts/Anton-Regular.ttf", 54)
    F_POP_LG = ImageFont.truetype("assets/fonts/Poppins-Bold.ttf", 38)
    F_POP_MD = ImageFont.truetype("assets/fonts/Poppins-Bold.ttf", 32)
    F_POP_SM = ImageFont.truetype("assets/fonts/Poppins-Medium.ttf", 26)
    F_POP_XS = ImageFont.truetype("assets/fonts/Poppins-Medium.ttf", 22)
    F_POP_XXS = ImageFont.truetype("assets/fonts/Poppins-Medium.ttf", 18)
except:
    F_ANTON_XL=F_ANTON_LG=F_ANTON_MD=F_ANTON_SM=F_POP_LG=F_POP_MD=F_POP_SM=F_POP_XS=F_POP_XXS=ImageFont.load_default()

# --- Easing ---
def easeOutExpo(t): return 1.0 if t>=1 else 1 - pow(2, -10*t)
def easeOutCubic(t): return 1 - pow(1-t,3)
def easeInOutCubic(t): return 4*t*t*t if t<0.5 else 1 - pow(-2*t+2,3)/2
def bezier_161_1_03_1(t): # cubic-bezier(0.16,1,0.3,1) approx
    # use easeOutCubic as close approximation
    return easeOutCubic(t)
def spring_critical(t, w=14): # critically damped spring to 1
    if t>=1: return 1.0
    return 1 - (1 + w*t) * math.exp(-w*t)
def easeOutBack(t):
    c1=1.70158; c3=c1+1
    return 1 + c3*pow(t-1,3) + c1*pow(t-1,2)

# --- Plate library ---
ALL_PLATE_FILES = [
    # AI generated 10
    "assets/images/cinema_plate_01_midnight_study_desk.jpg",
    "assets/images/cinema_plate_02_rain_bus_window.jpg",
    "assets/images/cinema_plate_03_midnight_clock_glow.jpg",
    "assets/images/cinema_plate_04_lonely_metro_bokeh.jpg",
    "assets/images/cinema_plate_05_hourglass_neural.jpg",
    "assets/images/cinema_plate_06_library_vs_rooftop.jpg",
    "assets/images/cinema_plate_07_blueprint_city.jpg",
    "assets/images/cinema_plate_08_coding_flow.jpg",
    "assets/images/cinema_plate_09_editing_timeline.jpg",
    "assets/images/cinema_plate_10_fitness_flow.jpg",
    # synthetic 20
    "assets/images/cinema_plate_11_courtroom_gavel.jpg",
    "assets/images/cinema_plate_12_parallel_2036.jpg",
    "assets/images/cinema_plate_13_waking_morning_light.jpg",
    "assets/images/cinema_plate_14_phone_under_blanket.jpg",
    "assets/images/cinema_plate_15_dopamine_slot.jpg",
    "assets/images/cinema_plate_16_calendar_flip.jpg",
    "assets/images/cinema_plate_17_comparison_highlight.jpg",
    "assets/images/cinema_plate_18_india_nodes_night.jpg",
    "assets/images/cinema_plate_19_dark_street_bokeh.jpg",
    "assets/images/cinema_plate_20_foundation_blueprint.jpg",
    "assets/images/cinema_plate_21_influencer_trap_alt.jpg",
    "assets/images/cinema_plate_22_deep_work_timer.jpg",
    "assets/images/cinema_plate_23_skill_blueprint_ladder.jpg",
    "assets/images/cinema_plate_24_exam_anxiety_hope.jpg",
    "assets/images/cinema_plate_25_sunrise_mountains.jpg",
    "assets/images/cinema_plate_26_server_room.jpg",
    "assets/images/cinema_plate_27_vintage_hourglass_phone.jpg",
    "assets/images/cinema_plate_28_neuro_dopamine_trap.jpg",
    "assets/images/cinema_plate_29_midnight_rain_puddle.jpg",
    "assets/images/cinema_plate_30_blue_hour_coding.jpg",
    # original seg plates
    "assets/images/seg1_2am_phone_glow.jpg",
    "assets/images/seg2_tug_of_war_phone.jpg",
    "assets/images/seg2_comparison_split.jpg",
    "assets/images/seg3_hourglass_2_years.jpg",
    "assets/images/seg3_india_window_2041.jpg",
    "assets/images/seg4_influencer_trap.jpg",
    "assets/images/seg4_foundation_building.jpg",
    "assets/images/seg5_2036_two_futures.jpg",
]

# Face cam plate
FACE_PLATE = "assets/images/facecam_aryan_tight.jpg"

# Verify files exist, filter
ALL_PLATE_FILES = [p for p in ALL_PLATE_FILES if os.path.exists(p)]
print(f"Loaded {len(ALL_PLATE_FILES)} plates + face plate")

# Plate pools per segment (thematic)
POOL_MAP = {
    "01_hook_and_day": [p for p in ALL_PLATE_FILES if any(k in p for k in ["midnight_study","rain_bus","midnight_clock","phone_under","neuro","seg1_2am"])],
    "02_problems_1_to_3": [p for p in ALL_PLATE_FILES if any(k in p for k in ["tug_of_war","comparison_highlight","dopamine","slot","phone_under","neuro","lonely_metro"])],
    "03a_problems_4_5": [p for p in ALL_PLATE_FILES if any(k in p for k in ["courtroom","slot","neuro","calendar","street_bokeh"])],
    "03b_facecam_reset": [FACE_PLATE],
    "04a_math_build": [p for p in ALL_PLATE_FILES if any(k in p for k in ["hourglass","calendar","clock","blueprint","library"])],
    "04b_2saal_and_surveys": [p for p in ALL_PLATE_FILES if any(k in p for k in ["hourglass","calendar","library","server_room","coding"])],
    "05a_jobs_plfs": [p for p in ALL_PLATE_FILES if any(k in p for k in ["server_room","street_bokeh","metro","blueprint_city","india_window"])],
    "05b_ncrb_telemanas": [p for p in ALL_PLATE_FILES if any(k in p for k in ["waking_morning","exam_anxiety","sunrise","library"])],
    "05c_india_2041_window": [p for p in ALL_PLATE_FILES if any(k in p for k in ["india_nodes","blueprint_city","blueprint","india_window","sunrise"])],
    "06a_influencer_lie": [p for p in ALL_PLATE_FILES if any(k in p for k in ["influencer_trap","server_room","street_bokeh"])],
    "06b_facecam_trust": [FACE_PLATE],
    "07_sebi_and_foundation": [p for p in ALL_PLATE_FILES if any(k in p for k in ["courtroom","foundation","blueprint","india_nodes"])],
    "08a_two_futures_2036": [p for p in ALL_PLATE_FILES if any(k in p for k in ["parallel_2036","sunrise","skill_blueprint","foundation","library"])],
    "08b_facecam_interrupt": [FACE_PLATE],
    "09a_country_365cr": [p for p in ALL_PLATE_FILES if any(k in p for k in ["india_nodes","server_room","blueprint_city","street_bokeh"])],
    "09b_khara_ganit": [p for p in ALL_PLATE_FILES if any(k in p for k in ["calendar","hourglass","blueprint"])],
    "09c_steps_1_to_3": [p for p in ALL_PLATE_FILES if any(k in p for k in ["deep_work","phone_under","coding","editing_timeline","fitness_flow"])],
    "10a_steps_4_5": [p for p in ALL_PLATE_FILES if any(k in p for k in ["skill_blueprint","coding","editing_timeline","fitness_flow","library"])],
    "10b_facecam_close": [FACE_PLATE],
    "10c_final_callback": [FACE_PLATE],
}
# fallback for any missing
for k,v in list(POOL_MAP.items()):
    if not v:
        POOL_MAP[k]=ALL_PLATE_FILES[:6]

# Build shot schedule
def build_shot_schedule(manifest):
    random.seed(42)
    placements = manifest["placements"]
    shots=[]
    shot_id=0
    for p in placements:
        seg_id=p["id"]
        seg_start=p["start"]
        seg_end=p["end"]
        seg_dur=p["duration"]
        face=p.get("face_cam",False)
        pool=POOL_MAP.get(seg_id, ALL_PLATE_FILES[:6])
        if face:
            # face cam: single shot but still allow subtle motion
            shots.append({
                "id": shot_id,
                "seg_id": seg_id,
                "start": seg_start, "end": seg_end, "duration": seg_dur,
                "plate": FACE_PLATE,
                "trans_type": "fade" if seg_id=="05b_ncrb_telemanas" else "whip",
                "dir_x": random.uniform(-0.6,0.6),
                "dir_y": random.uniform(-0.4,0.4),
                "env": "dust",
                "grade": "warm_gold" if "close" in seg_id else "obsidian",
            })
            shot_id+=1
        else:
            t_cursor=seg_start
            remaining=seg_dur
            # subdivide into 3-5s shots (strict 3.0-5.0)
            # Compute ideal number of shots: round to keep avg ~4.1s
            n_shots = max(1, int(round(seg_dur / 4.1)))
            # Ensure each shot can be within 3.0-5.0
            if seg_dur / n_shots < 3.0:
                n_shots = max(1, int(seg_dur / 3.0))
            if seg_dur / n_shots > 5.0:
                n_shots = int(seg_dur / 5.0) + 1
            # Generate raw durations and normalize to exact seg_dur
            raw = [random.uniform(3.2,5.0) for _ in range(n_shots)]
            scale = seg_dur / sum(raw)
            durs = [r*scale for r in raw]
            # Clamp any outlier that scaled outside 3-5 due to rounding, redistribute
            for i in range(len(durs)):
                if durs[i] < 3.0:
                    durs[i]=3.0
                if durs[i] >5.0:
                    durs[i]=5.0
            # final normalize again
            sum2=sum(durs)
            durs=[d*seg_dur/sum2 for d in durs]
            t_cursor=seg_start
            for dur in durs:
                # pick plate avoiding repeat
                plate=random.choice(pool)
                if shots and shots[-1]["plate"]==plate and len(pool)>1:
                    alts=[x for x in pool if x!=plate]
                    plate=random.choice(alts)
                # trans type cycle
                trans_cycle=["whip","zoom","wipe","leak"]
                # choose based on emotional shift
                if seg_id in ["04b_2saal_and_surveys","05b_ncrb_telemanas","08a_two_futures_2036"] and len(shots)%3==0:
                    trans="zoom"
                elif seg_id in ["02_problems_1_to_3","06a_influencer_lie"]:
                    trans="whip"
                elif seg_id in ["05c_india_2041_window","09a_country_365cr"]:
                    trans="wipe"
                else:
                    trans=trans_cycle[shot_id % len(trans_cycle)]
                # safe zone gentle
                if seg_id=="05b_ncrb_telemanas":
                    trans="fade"
                # motion dir
                dir_x=random.choice([-1,1])*random.uniform(0.7,1.3)
                dir_y=random.choice([-1,1])*random.uniform(0.4,0.9)
                # env
                env_options=["dust","bokeh","rain","smoke","code","clock"]
                # thematic env
                if "rain" in plate or "bus" in plate:
                    env="rain"
                elif "bokeh" in plate or "street" in plate or "metro" in plate:
                    env="bokeh"
                elif "coding" in plate or "editing" in plate or "server" in plate:
                    env="code"
                elif "clock" in plate or "hourglass" in plate or "calendar" in plate:
                    env="clock"
                elif "blueprint" in plate:
                    env="smoke"
                else:
                    env=random.choice(env_options)
                if seg_id=="05b_ncrb_telemanas":
                    env="dust"  # calm
                # grade
                if seg_id in ["03a_problems_4_5","06a_influencer_lie"]:
                    grade="crimson"
                elif seg_id in ["05c_india_2041_window","07_sebi_and_foundation","08a_two_futures_2036","09a_country_365cr"]:
                    grade="cyan_gold"
                elif seg_id in ["08a_two_futures_2036","09a_country_365cr"] and shot_id%2==1:
                    grade="warm_gold"
                elif seg_id in ["10b_facecam_close","10c_final_callback"]:
                    grade="warm_gold"
                elif seg_id in ["09c_steps_1_to_3","10a_steps_4_5"]:
                    grade="green_gold"
                else:
                    grade="obsidian"
                shots.append({
                    "id": shot_id,
                    "seg_id": seg_id,
                    "start": t_cursor, "end": t_cursor+dur, "duration": dur,
                    "plate": plate,
                    "trans_type": trans,
                    "dir_x": dir_x, "dir_y": dir_y,
                    "env": env,
                    "grade": grade,
                })
                shot_id+=1
                t_cursor+=dur
                remaining-=dur
                if remaining<0.05: break
    if shots:
        shots[0]["plate"] = FACE_PLATE
        shots[0]["env"] = "dust"
    # sort by start
    shots.sort(key=lambda s: s["start"])
    return shots

# Vignette mask precomputed (1920x1080)
def make_vignette(w=W,h=H,strength=0.92):
    Y,X=np.ogrid[:h,:w]
    cx,cy=w/2,h/2
    dx=(X-cx)/cx; dy=(Y-cy)/cy
    d=np.sqrt(dx*dx+dy*dy)
    v=1 - strength * np.clip((d-0.55)/1.2,0,1)**1.6
    v=np.clip(v,0,1)
    return v

VIGNETTE = make_vignette()

# Fast vignette overlay (RGBA) - precomputed
def make_vignette_overlay():
    # alpha = (1 - vignette) * 95 at edges
    alpha = ((1 - VIGNETTE) * 92).astype(np.uint8)
    # add slight stronger at corners
    img = Image.new("RGBA", (W,H), (0,0,0,0))
    alpha_img = Image.fromarray(alpha, mode="L")
    vign = Image.new("RGBA", (W,H), (0,0,0,255))
    vign.putalpha(alpha_img)
    return vign
VIGNETTE_OVERLAY = make_vignette_overlay()

# Grain textures 4 frames - PIL RGBA overlays for fast composite
def make_grain(w=W,h=H):
    textures=[]
    overlays=[]
    for i in range(4):
        noise=np.random.randint(0,255,size=(h,w),dtype=np.uint8)
        textures.append(noise)
        # create RGBA grain overlay: white noise with low opacity scattered
        # Instead of full image, create sparse grain via drawing random dots? But use noise as alpha
        # For fast, create RGBA image where noise is translated to alpha jitter
        # We'll create overlay where grain is visible as semi-transparent speckles
        # Use noise threshold
        grain_arr = np.zeros((h,w,4), dtype=np.uint8)
        # random dust-like grain: where noise >200, add white pixel with low alpha
        mask = noise > 210
        grain_arr[mask, 0] = 255; grain_arr[mask, 1]=255; grain_arr[mask, 2]=255; grain_arr[mask, 3]=5
        # also dark grain
        mask2 = noise < 48
        grain_arr[mask2, 0]=0; grain_arr[mask2,1]=0; grain_arr[mask2,2]=0; grain_arr[mask2,3]=4
        overlay = Image.fromarray(grain_arr, mode="RGBA")
        overlays.append(overlay)
    return textures, overlays
GRAIN_TEX, GRAIN_OVERLAYS = make_grain()

# Bokeh sprite pre-render (for fast paste)
def make_bokeh_sprites():
    sprites=[]
    for r in [36,58,84,112]:
        sz=r*2+20
        spr=Image.new("RGBA",(sz,sz),(0,0,0,0))
        d=ImageDraw.Draw(spr)
        # soft circle with gradient
        for i in range(6,0,-1):
            rr=int(r * (i/6))
            alpha=int(22 * (i/6)**1.5)
            col=(255,210+random.randint(-20,20),120+random.randint(-20,40), alpha)
            d.ellipse([sz//2-rr,sz//2-rr,sz//2+rr,sz//2+rr], fill=col)
        spr=spr.filter(ImageFilter.GaussianBlur(3))
        sprites.append(spr)
    return sprites
BOKEH_SPRITES=make_bokeh_sprites()

def prep_plate_cached(path, scale_pad=1.15):
    # Load and resize to padded size for parallax
    im=Image.open(path).convert("RGB")
    tw,th=int(W*scale_pad), int(H*scale_pad)
    s=max(tw/im.width, th/im.height)
    nw,nh=int(im.width*s), int(im.height*s)
    im=im.resize((nw,nh), Image.Resampling.BICUBIC)
    # center crop to tw,th
    ox,oy=(nw-tw)//2, (nh-th)//2
    im=im.crop((ox,oy,ox+tw,oy+th))
    return im

# Cache for plates per worker
PLATE_CACHE={}
PLATE_CACHE_SIZE=8
def get_plate_image(path):
    if path in PLATE_CACHE:
        return PLATE_CACHE[path]
    # LRU evict if needed
    if len(PLATE_CACHE) >= PLATE_CACHE_SIZE:
        # remove oldest
        k=list(PLATE_CACHE.keys())[0]
        del PLATE_CACHE[k]
    im=prep_plate_cached(path)
    PLATE_CACHE[path]=im
    return im

def parallax_frame(plate_img, zoom, pan_x, pan_y):
    pw,ph=plate_img.size
    cw=int(W/zoom)
    ch=int(H/zoom)
    # ensure not exceed
    cw=min(pw,cw); ch=min(ph,ch)
    ox=int((pw-cw)* np.clip(pan_x,0,1))
    oy=int((ph-ch)* np.clip(pan_y,0,1))
    cropped=plate_img.crop((ox,oy,ox+cw,oy+ch))
    if cw!=W or ch!=H:
        return cropped.resize((W,H), Image.Resampling.BICUBIC)
    return cropped

def render_two_layer_parallax(plate_path, shot, t, shot_progress):
    plate_img=get_plate_image(plate_path)
    if shot["seg_id"] == "05b_ncrb_telemanas":
        return parallax_frame(plate_img, 1.02 + 0.01*easeInOutCubic(shot_progress), 0.5, 0.5)
    # parameters
    dir_x=shot["dir_x"]; dir_y=shot["dir_y"]
    # organic float multi-frequency
    # use t for global time for continuity across shots? Use shot local + global
    float_x = 0.008*math.sin(t*0.35*2*math.pi + shot["id"]*1.3) + 0.005*math.cos(t*0.82*2*math.pi)
    float_y = 0.008*math.cos(t*0.28*2*math.pi + shot["id"]*0.7) + 0.004*math.sin(t*0.61*2*math.pi)
    # base pan evolves with shot_progress
    # bg slower, fg faster
    base_pan_x=0.5 + dir_x*0.10*shot_progress
    base_pan_y=0.5 + dir_y*0.08*shot_progress
    # bg layer
    pan_bg_x = base_pan_x*0.65 + float_x*0.6
    pan_bg_y = base_pan_y*0.65 + float_y*0.6
    # fg layer faster
    pan_fg_x = base_pan_x*1.15 + float_x*1.4
    pan_fg_y = base_pan_y*1.15 + float_y*1.4
    # zooms
    # subtle zoom in over shot
    zoom_base = 1.02 + 0.06* easeOutCubic(shot_progress)
    zoom_bg = zoom_base * 0.96
    zoom_fg = zoom_base * 1.08
    bg = parallax_frame(plate_img, zoom_bg, pan_bg_x, pan_bg_y)
    fg = parallax_frame(plate_img, zoom_fg, pan_fg_x, pan_fg_y)
    # depth cue: bg darker/desat
    bg = ImageEnhance.Brightness(bg).enhance(0.88)
    bg = ImageEnhance.Color(bg).enhance(0.88)
    bg = ImageEnhance.Contrast(bg).enhance(0.96)
    fg = ImageEnhance.Brightness(fg).enhance(1.02)
    fg = ImageEnhance.Color(fg).enhance(1.04)
    # Clean camera plane: blending differently scaled copies of the same photo
    # creates double faces/clock hands. Foreground particles supply the second plane.
    return fg

def add_environmental(composed, shot, t, shot_progress, is_safe_zone):
    # is_safe_zone disables intense effects
    if is_safe_zone:
        return composed
    else:
        env=shot["env"]
    Wc,Hc=W,H
    overlay=Image.new("RGBA",(Wc,Hc),(0,0,0,0))
    d=ImageDraw.Draw(overlay, "RGBA")
    # common drifting
    # use shot id as seed offset
    sid=shot["id"]
    rng_offset=sid*137
    if env=="dust":
        # volumetric dust motes 34 particles
        for i in range(34):
            # deterministic position per shot with time drift
            seed=i*19+sid*31
            # initial pos
            ix=(seed*73)%W; iy=(seed*97)%H
            # velocity
            vx= 12 + (seed%7)*3  # px per sec
            vy= 8 + (seed%5)*2
            # drift with sin
            x = (ix + (t* vx) ) % (W+40) -20
            y = (iy + (t* vy) + 6*math.sin(t*0.6 + seed)) % (H+40) -20
            r=1 + (seed%3)
            alpha= 28 + int(14*math.sin(t*1.2+seed))
            alpha=np.clip(alpha,12,55)
            d.ellipse([x-r,y-r,x+r,y+r], fill=(255,255,240,alpha))
            # second layer faint larger
            if i%5==0:
                d.ellipse([x-2,y-2,x+2,y+2], fill=(255,255,240,int(alpha*0.45)))
    elif env=="bokeh":
        # pulsing bokeh orbs 14
        for i in range(14):
            seed=i*29+sid*17
            # base position with sine drift
            base_x = (seed*113)%W
            base_y = (seed*127)%H
            amp_x= 28 + (seed%18)
            amp_y= 18 + (seed%12)
            x = base_x + amp_x*math.sin(t*0.22 + seed*0.21)
            y = base_y + amp_y*math.cos(t*0.18 + seed*0.33)
            # pulse size
            scale= 0.85 + 0.18*math.sin(t*0.9 + seed)
            sprite=BOKEH_SPRITES[seed%len(BOKEH_SPRITES)]
            sw,sh=sprite.size
            # adjust alpha via scale? we paste with alpha blending
            # create resized sprite
            ns=int(sw*scale); ns=max(8,ns)
            if ns!=sw:
                spr=sprite.resize((ns,ns), Image.Resampling.BICUBIC)
            else:
                spr=sprite
            # color tint per grade? use warm gold vs cyan etc later
            # paste
            x=int(x - ns//2); y=int(y - ns//2)
            overlay.alpha_composite(spr, (x,y))
        # also add 20 small dust on top
        for i in range(18):
            seed=i*31+sid*11
            x=(seed*71 + int(t*9))%(W); y=(seed*83 + int(t*6))%(H)
            r=1
            alpha=18
            d.ellipse([x,y,x+1,y+1], fill=(255,255,255,alpha))
    elif env=="rain":
        # falling night rain streaks 70
        for i in range(70):
            seed=i*23+sid*7
            # speed
            speed= 420 + (seed%120) # px/sec
            base_x=(seed*89)%(W+200)-100
            base_y=(seed*101)%(H+600)-300
            y = (base_y + speed*t) % (H+600) -300
            x = base_x + 6*math.sin(t*0.4 + seed*0.05) # slight wind
            length= 18 + (seed%14)
            alpha= 55 + (seed%40)
            width=1 if i%2==0 else 2
            # line diagonal -6 x, length y
            d.line([(x,y),(x-6,y+length)], fill=(175,205,255,alpha), width=width)
        # puddle reflection hint: add subtle horizontal streaks at bottom
        for i in range(12):
            seed=i*37+sid*5
            x=(seed*67)%(W); y=H-120 + (seed%90)
            wob= 40 + (seed%60)
            alpha=18
            d.line([(x,y),(x+wob,y)], fill=(120,170,255,alpha), width=1)
    elif env=="smoke":
        # atmospheric smoke/fog layers drifting
        # 3 large soft ellipses moving slowly
        for i in range(3):
            seed=i*53+sid*13
            base_x=(seed*97)%W; base_y=(seed*103)%(H//2+120)+H//2-100
            x= base_x + 18*math.sin(t*0.07 + seed) + (t*6)%W*0.03
            y= base_y + 8*math.cos(t*0.05 + seed*0.5)
            rx= 220 + (seed%180); ry= 90 + (seed%70)
            # draw soft ellipse via drawing and blur? We'll use solid with low alpha and blur via image filter per frame heavy?
            # Instead draw ellipse with alpha and rely on final composite blur? Use translucent fill
            alpha= 14 + i*4
            col=(200,215,230,alpha) if i%2==0 else (180,200,240,alpha)
            d.ellipse([x-rx,y-ry,x+rx,y+ry], fill=col)
        # blur overlay via slight filter? Instead we keep soft due to large size and low alpha, no extra blur needed for perf
        # add dust on top
        for i in range(12):
            seed=i*41+sid*19
            x=(seed*73 + int(t*7))%W; y=(seed*79 + int(t*5))%H
            d.ellipse([x,y,x+2,y+2], fill=(255,255,255,16))
    elif env=="code":
        # scrolling code/UI feeds faint
        for i in range(18):
            seed=i*47+sid*23
            ybase=(seed*97)%H
            y=(ybase - int(t*34)) % H
            x=(seed*113)%(W-300)+40
            length= 120 + (seed%260)
            alpha= 14 + (seed%12)
            col=(0,230,180,alpha) if i%2==0 else (120,140,180,alpha)
            d.rectangle([x,y,x+length,y+3], fill=col)
        # also bokeh faint
        for i in range(8):
            seed=i*59+sid*7
            x=(seed*67)%W + int(10*math.sin(t*0.3+seed)); y=(seed*71)%H + int(6*math.cos(t*0.28+seed))
            d.ellipse([x-14,y-14,x+14,y+14], fill=(0,200,255,10))
    elif env=="clock":
        # clock hands moving: draw subtle rotating line overlay if plate is clockish
        # Add drifting light rays
        # center clock at approx center?
        cx,cy=W//2, H//2
        # hour hand
        angle_h = (t*0.5) % (2*math.pi) # fast for visual
        angle_m = (t*6) % (2*math.pi)
        # draw faint clock circle
        d.ellipse([cx-220,cy-220,cx+220,cy+220], outline=(255,210,100,14), width=2)
        # hour hand
        hx=int(cx+ 90*math.cos(angle_h - math.pi/2)); hy=int(cy+ 90*math.sin(angle_h - math.pi/2))
        d.line([(cx,cy),(hx,hy)], fill=(255,215,100,22), width=4)
        # minute hand
        mx=int(cx+ 150*math.cos(angle_m - math.pi/2)); my=int(cy+ 150*math.sin(angle_m - math.pi/2))
        d.line([(cx,cy),(mx,my)], fill=(255,255,240,18), width=3)
        # tick marks
        for k in range(12):
            ang=k*math.pi/6
            x1=int(cx+200*math.cos(ang)); y1=int(cy+200*math.sin(ang))
            x2=int(cx+214*math.cos(ang)); y2=int(cy+214*math.sin(ang))
            d.line([(x1,y1),(x2,y2)], fill=(255,210,100,16), width=2)
        # dust
        for i in range(16):
            seed=i*33+sid*11
            x=(seed*71 + int(t*8))%W; y=(seed*83 + int(t*5))%H
            d.ellipse([x,y,x+1,y+1], fill=(255,255,240,18))
    else:
        # fallback dust
        for i in range(20):
            seed=i*29+sid*17
            x=(seed*73 + int(t*10))%W; y=(seed*79 + int(t*7))%H
            d.ellipse([x,y,x+1,y+1], fill=(255,255,240,14))

    # composite overlay onto composed with alpha
    if overlay.getextrema()[3][1] !=0: # check if any alpha?
        composed=Image.alpha_composite(composed.convert("RGBA"), overlay).convert("RGB")
    return composed

def apply_film_look(img, grade, t, frame_idx, is_safe_zone):
    # Fast PIL-based film look (vignette + grade + grain + halation)
    # 1) Color grade via ImageEnhance (fast C)
    if grade=="obsidian":
        img = ImageEnhance.Color(img).enhance(0.90)
        img = ImageEnhance.Contrast(img).enhance(1.12)
        img = ImageEnhance.Brightness(img).enhance(0.96)
        # teal tint overlay 8% alpha
        tint = Image.new("RGBA", (W,H), (0, 28, 42, 18))
        img = Image.alpha_composite(img.convert("RGBA"), tint).convert("RGB")
    elif grade=="crimson":
        img = ImageEnhance.Color(img).enhance(0.86)
        img = ImageEnhance.Contrast(img).enhance(1.16)
        img = ImageEnhance.Brightness(img).enhance(0.92)
        tint = Image.new("RGBA", (W,H), (48, 8, 18, 28))
        img = Image.alpha_composite(img.convert("RGBA"), tint).convert("RGB")
    elif grade=="cyan_gold":
        img = ImageEnhance.Color(img).enhance(0.92)
        img = ImageEnhance.Contrast(img).enhance(1.10)
        tint = Image.new("RGBA", (W,H), (32, 24, 6, 16))
        img = Image.alpha_composite(img.convert("RGBA"), tint).convert("RGB")
    elif grade=="warm_gold":
        img = ImageEnhance.Color(img).enhance(0.96)
        img = ImageEnhance.Contrast(img).enhance(1.06)
        img = ImageEnhance.Brightness(img).enhance(1.03)
        tint = Image.new("RGBA", (W,H), (42, 32, 8, 20))
        # subtle warm lift
        img = Image.alpha_composite(img.convert("RGBA"), tint).convert("RGB")
    elif grade=="green_gold":
        img = ImageEnhance.Color(img).enhance(0.94)
        img = ImageEnhance.Contrast(img).enhance(1.08)
        tint = Image.new("RGBA", (W,H), (8, 28, 14, 18))
        img = Image.alpha_composite(img.convert("RGBA"), tint).convert("RGB")
    # 2) Vignette overlay (fast alpha composite)
    img_rgba = img.convert("RGBA")
    img_rgba = Image.alpha_composite(img_rgba, VIGNETTE_OVERLAY)
    img = img_rgba.convert("RGB")
    # 3) Grain overlay (fast)
    grain_alpha = 0.55 if is_safe_zone else 1.0
    if grain_alpha>0.01:
        grain_overlay = GRAIN_OVERLAYS[frame_idx % len(GRAIN_OVERLAYS)]
        # adjust alpha by global factor if safe zone
        if grain_alpha < 1.0:
            # reduce alpha channel
            # we can create copy with lower alpha
            arr = np.array(grain_overlay)
            arr[:,:,3] = (arr[:,:,3] * grain_alpha).astype(np.uint8)
            grain_overlay = Image.fromarray(arr, mode="RGBA")
        img = Image.alpha_composite(img.convert("RGBA"), grain_overlay).convert("RGB")
    # 4) Halation warm glow on bright highlights - cheap approximation: overlay warm gradient at center top if bright
    if not is_safe_zone:
        # Add subtle warm bloom as radial ellipse at center of bright areas? For perf, we just add faint warm overlay with low alpha that mimics halation
        # We can detect if image has bright pixels via quick histogram? Instead always add very subtle warm bloom 3% at center
        # Create bloom ellipse
        bloom = Image.new("RGBA", (W,H), (0,0,0,0))
        bd = ImageDraw.Draw(bloom)
        # two warm blobs
        for cx,cy,rx,ry,alpha in [(W*0.68,H*0.42, 280,180,10), (W*0.32,H*0.58, 220,140,8)]:
            bd.ellipse([cx-rx,cy-ry,cx+rx,cy+ry], fill=(255,120,32, alpha))
        img = Image.alpha_composite(img.convert("RGBA"), bloom).convert("RGB")
    return img

def draw_source_badge(draw, text, accent=C_YELLOW):
    label=f"SOURCE: {text}"
    bb=draw.textbbox((0,0), label, font=F_POP_XXS)
    bw=(bb[2]-bb[0])+44
    # scaled coordinates for 1080p
    draw.rounded_rectangle([54,42,54+bw,93], radius=12, fill=(10,11,18), outline=accent, width=3)
    draw.text((76,52), label, font=F_POP_XXS, fill=C_WHITE)

def draw_facecam_badge(draw, label, accent=C_CYAN):
    bb=draw.textbbox((0,0), label, font=F_POP_XXS)
    bw=(bb[2]-bb[0])+40
    draw.rounded_rectangle([W-54-bw,42,W-54,90], radius=12, fill=(12,14,22), outline=accent, width=3)
    draw.text((W-42-bw,50), label, font=F_POP_XXS, fill=accent)

def draw_centered(draw, y, text, font, fill, stroke_w=6, stroke_fill=(0,0,0)):
    bb=draw.textbbox((0,0), text, font=font)
    draw.text(((W-(bb[2]-bb[0]))//2, y), text, font=font, fill=fill, stroke_width=stroke_w, stroke_fill=stroke_fill)

# Segment lines with accent colors mapping
SEGMENT_LINES = {
    "01_hook_and_day": (C_MAGENTA, [
        ("HAAN. TUMSE HI","TUMSE"), ("BAAT KAR RAHA HOON.","BAAT"), ("JO PADHAI CHHOD KE","PADHAI"),
        ("'BAS EK MINUTE' KE LIYE AAYA HAI.","MINUTE'"), ("WAHI EK MINUTE TUMHARE","TUMHARE"),
        ("DO SAAL KHA JAATA HAI!","SAAL"), ("HISAAB DIKHATA HOON.","HISAAB"),
        ("AUR AAJ RAAT KA EK KAAM BHI.","RAAT"), ("SUBAH ALARM BAJTA HAI.","ALARM"),
        ("AANKH KHULNE SE PEHLE PHONE!","PHONE!"), ("PEHLA KAAM: NOTIFICATION CHECK.","NOTIFICATION"),
        ("NASHTE MEIN REELS.","REELS."), ("KAPDE PEHENTE HUE REELS.","REELS."),
        ("RASTE MEIN REELS.","REELS."), ("AUR RAAT KO? 'BAS 10 MINUTE.'","MINUTE.'"),
        ("GHADI MEIN 2 BAJ CHUKE HAIN!","2"), ("KAL TEST HAI...","TEST"),
        ("WAHI PURANA WADA: 'KAL SE PAKKA.'","PAKKA.'"), ("KITNI BAAR BOLA? 10 BAAR? 100 BAAR?","100"),
    ]),
    "02_problems_1_to_3": (C_MAGENTA, [
        ("AB WO 5 CHEEZEIN","5"), ("JO TUM KISI KO BATATE NAHI.","TUM"),
        ("#1: DISCIPLINE KA DHOKHA","DISCIPLINE"), ("PADHNE BAITHTE HO, 3 MIN MEIN PHONE.","PHONE."),
        ("TUMHE LAGTA HAI DISCIPLINE KAM HAI?","DISCIPLINE"), ("GALAT! DUNIYA KE SABSE MEHNGE DIMAAG","GALAT!"),
        ("TUMHARE KHILAF LAGE HAIN.","KHILAF"), ("UNKI KAMAAI TAB HOTI HAI","KAMAAI"),
        ("JAB TUM PHONE NAHI RAKHTE.","PHONE"), ("YE SEEDHI LADAI HAI.","LADAI"),
        ("#2: COMPARISON KA ZAAHAR","COMPARISON"), ("KISI KA SELECTION. KISI KI GOA STORY.","GOA"),
        ("AUR TUM? USI KAMRE, USI SYLLABUS MEIN:","TUM?"), ("'MAIN PEECHE REH GAYA.'","PEECHE"),
        ("UNKA HIGHLIGHT vs TUMHARA BEHIND-THE-SCENES!","HIGHLIGHT"), ("#3: SAVED FOLDER KA NASHA","SAVED"),
        ("300 REELS SAVED. 40 PDFs. 10 PLAYLISTS.","300"), ("DEKHNE MEIN PRODUCTIVE...","PRODUCTIVE..."),
        ("ASAL MEIN WAHI PURANA SCROLL.","SCROLL."),
    ]),
    "03a_problems_4_5": (C_RED, [
        ("#4: SHORTCUT KA JAAL","SHORTCUT"), ("'SIRF 500 KA DAAV. EK PREDICTION.'","500"),
        ("2025 MEIN ONLINE MONEY GAMES BAN HUE","BAN"), ("KYUNKI GHAR KE GHAR KARZ MEIN DOOB RAHE THE.","KARZ"),
        ("#5: DARD DABANA","DARD"), ("MOOD KHARAB? PHONE. AKELA? PHONE.","PHONE."),
        ("PHONE AB TUMHARA ANESTHESIA HAI.","ANESTHESIA"), ("DARD SUNN KARTA HAI, THEEK NAHI KARTA.","THEEK"),
    ]),
    "03b_facecam_reset": (C_YELLOW, [
        ("RUKO. EK SECOND.","RUKO."), ("YAHAN TAK HAR BAAT SACH LAGI NA?","SACH"),
        ("AB TAK MAINE SIRF AAINA DIKHAYA HAI.","AAINA"), ("AB ASLI HISAAB DIKHATA HOON. YE KADWA HAI.","HISAAB"),
    ]),
    "04a_math_build": (C_YELLOW, [
        ("AB SEEDHA HISAAB SUNO.","HISAAB"), ("ROZ ~3.2 GHANTE SOCIAL APPS PAR.","3.2"),
        ("HUM SIRF 3 GHANTE MAANTE HAIN.","3"), ("3 x 365 = SAAL KE 1,095 GHANTE!","1,095"),
        ("24 GHANTE SE POORE 45 DIN GAYAB.","45"), ("16 JAAGTE GHANTON SE: SAAL KE 68 DIN!","68"),
        ("AUR 10 SAAL MEIN? 684 JAAGTE DIN...","684"),
    ]),
    "04b_2saal_and_surveys": (C_YELLOW, [
        ("LAGBHAG DO SAAL! POORE 2 SAAL!","2"), ("ITNE MEIN EK POORI DEGREE YA TOP SKILL BANTI HAI.","SKILL"),
        ("SHAHRON KE 18-24 YUVA: ROZ 120+ MIN SOCIAL PAR.","120+"), ("74% STUDENTS: PADHAI KE BAHAR 2+ GHANTE SCREEN.","74%"),
        ("IIM ROHTAK STUDY: TOTAL SCREEN TIME ~7 GHANTE!","7"), ("ECONOMIC SURVEY MEIN DIGITAL ADDICTION DARJ HUA.","ADDICTION"),
    ]),
    "05a_jobs_plfs": (C_YELLOW, [
        ("AAGE EK LINE JO KOI INFLUENCER NAHI BOLEGA.","INFLUENCER"), ("PEHLE BAAZAR KA SACH DEKHO.","SACH"),
        ("PLFS 2025 ANNUAL: 9.9% YUVA BEROZGAARI.","9.9%"), ("TIMAHI BULLETIN MEIN 15% TAK GAYA.","15%"),
        ("HAR INTERVIEW MEIN EK SAWAAL: TUMHE KAAM KYA AATA HAI?","KAAM"),
    ]),
    "05b_ncrb_telemanas": (C_WHITE, [
        ("AUR EK INSAANI SACH...","INSAANI"), ("BOJH SIRF PHONE KA NAHI HOTA.","BOJH"),
        ("EXAM KA DAR, COMPARISON, AKELAPAN.","AKELAPAN."), ("NCRB 2024: 14,488 STUDENTS — 10 SAAL MEIN 80% ZYADA.","14,488"),
        ("AGAR TUM AISE ANDHERE MEIN HO, VIDEO YAHIN ROKO.","ROKO."), ("14416 PAR TELE-MANAS KO CALL KARO. TUM AKELE NAHI HO.","14416"),
    ]),
    "05c_india_2041_window": (C_CYAN, [
        ("AB DESH KI GHADI DEKHO.","DESH"), ("BHARAT KI MEDIAN UMR: 29.2 SAAL.","29.2"),
        ("KAAM KARNE WALI AABADI KA SHIKHAR: 2041 TAK.","2041"), ("TAB TUM 30 SE 40 KE BEECH HOGE.","TUM"),
        ("YE KHIDKI TUMHARI HAI, ABHI KHULI HAI.","KHIDKI"), ("AB WO HISSA JO KOI INFLUENCER NAHI BATAYEGA!","INFLUENCER"),
    ]),
    "06a_influencer_lie": (C_MAGENTA, [
        ("AB WO BAAT JO SEEDHI CHUBHEGI.","CHUBHEGI."), ("'30 DIN MEIN LAKHPATI!' 'COLLEGE CHHOD DO!'","LAKHPATI!'"),
        ("TUM SOCHTE HO: MAIN KITAAB GHIS RAHA HOON?","KITAAB"), ("EK KADWI LINE SUN LO:","KADWI"),
        ("WAHAN TUM CUSTOMER NAHI HO. TUM MAAL HO!","MAAL"), ("UNKI KAMAAI TUMHARE VIEW, CLICK AUR COURSE SE BANTI HAI.","COURSE"),
    ]),
    "06b_facecam_trust": (C_GOLD, [
        ("RUKO. MAIN BHI YAHAN VIDEO BANA RAHA HOON.","RUKO."), ("MERI BAAT BHI AANKH BAND KARKE MAT MAANO.","MAT"),
        ("HAR BOLNE WALE SE EK SAWAAL POOCHHO:","SAWAAL"), ("'TUMHARA PAISA KAHAN SE AATA HAI?'","PAISA"),
        ("AGAR JAWAB TUMHARA COURSE HAI — KHEL SAMAJH JAO.","COURSE"), ("JO TIKTE HAIN, UNHONE SAALON CHUPCHAAP KAAM GHISA HAI.","KAAM"),
    ]),
    "07_sebi_and_foundation": (C_CYAN, [
        ("YE HAWA MEIN KAHI BAAT MAT SAMAJHNA.","MAT"), ("SEBI KO KHUD NIYAM BANANA PADA!","SEBI"),
        ("UNREGISTERED FINFLUENCERS SE DOOR REHNE KA AADESH.","FINFLUENCERS"), ("KAI UNREGISTERED EDUCATORS PAR SEEDHI KAARVAAHI.","KAARVAAHI."),
        ("SABSE KHATARNAAK JHOOTH: 'PADHAI BEKAAR HAI.'","JHOOTH:"), ("AKELI DEGREE KAAFI NAHI, PAR BINA NEEV IMAARAT KAHAN?","NEEV"),
        ("PADHAI TUMHARI ZAMEEN HAI. SKILL US PAR BANI IMAARAT!","IMAARAT!"), ("BINA ZAMEEN KE MAHAL SIRF REELS MEIN TIKTA HAI.","REELS"),
    ]),
    "08a_two_futures_2036": (C_GOLD, [
        ("CHALO SEEDHA 2036 MEIN CHALTE HAIN.","2036"), ("WAHAN DO ALAG TUM KHADE HAIN.","DO"),
        ("PEHLA TUM: WAHI 3 GHANTE, WAHI 'KAL SE PAKKA'.","PEHLA"), ("30 KI UMR. DOST AAGE, TUM AB BHI STORIES DEKH RAHE HO.","STORIES"),
        ("DOOSRA TUM: ROZ SIRF 1 GHANTA WAPAS CHHEENA!","1"), ("1 GHANTA x 10 SAAL = 3,650 GHANTE!","3,650"),
        ("CODING, EDITING, DESIGN, SALES — GEHRAAI SE AA JAATA HAI.","CODING,"), ("WAHI KAMRA, WAHI SHEHER — BAS ROZ EK GHANTA.","GHANTA."),
    ]),
    "08b_facecam_interrupt": (C_RED, [
        ("EK SECOND! ABHI PHONE CHECK KIYA KYA?","PHONE"), ("WAPAS AAO. YAHAN DEKHO.","WAPAS"),
    ]),
    "09a_country_365cr": (C_CYAN, [
        ("AB IS HISAAB KO KAMRE SE BAHAR DEKHO.","BAHAR"), ("REUTERS: BHARAT SABSE BADA SOCIAL GROWTH MARKET HAI.","REUTERS:"),
        ("TECH COMPANIES KO TUMHARA DHYAAN AUR NEEND CHAHIYE.","DHYAAN"), ("TUMHARA WAQT UNKA SABSE BADA KAROBAAR HAI.","WAQT"),
        ("AGAR 1 KAROD LOG ROZ 1 GHANTA SKILL PAR WAPAS LAAYEIN...","1"), ("EK SAAL MEIN 365 KAROD GHANTE BANTE HAIN!","365"),
    ]),
    "09b_khara_ganit": (C_YELLOW, [("YE KHARA GANIT HAI.","GANIT"),]),
    "09c_steps_1_to_3": (C_GREEN, [
        ("AB AAJ RAAT KA KAAM: 5 SEEDHE KADAM!","5"), ("STEP 1: PHONE BISTAR SE DOOR, CHARGER DOOSRE KONE MEIN.","DOOR,"),
        ("SUBAH KA PEHLA GHANTA BINA PHONE KE.","BINA"), ("STEP 2: SABSE ZYADA TIME WALE 2 APPS PAR LIMIT LAGAO.","LIMIT"),
        ("FRICTION BADHAO, EXTRA LOCK LAGAO.","FRICTION"), ("STEP 3: ROZ 1 GHANTA DEEP WORK — 50 MIN KAAM, 10 MIN BREAK.","DEEP"),
    ]),
    "10a_steps_4_5": (C_GREEN, [
        ("STEP 4: PADHAI KE SAATH 90 DIN KE LIYE 1 SKILL CHUNO.","90"), ("HAR HAFTE 1 OUTPUT BANAO: CODE, EDIT, DESIGN, PROJECT.","OUTPUT"),
        ("DEKHNE SE NAHI, BANANE SE AATA HAI!","BANANE"), ("STEP 5: AISE 2 LOGON KE SAATH RAHO JO KAAM DIKHATE HAIN.","KAAM"),
        ("PHONE DUSHMAN NAHI HAI — WO SIRF EK AUZAAR HAI.","AUZAAR"), ("YA TUM USE CHALAOGE, YA WO TUMHE CHALAYEGA.","CHALAOGE,"),
    ]),
    "10b_facecam_close": (C_GOLD, [
        ("YE VIDEO 2 DIN KA JOSH DENE KE LIYE NAHI BANA.","JOSH"), ("JAB AGLI BAAR HAATH BINA SOCHE PHONE UTHAYE...","PHONE"),
        ("TUMHE YE AWAAZ YAAD AAYE.","AWAAZ"), ("IS VIDEO KO ABHI SAVE KAR LO.","SAVE"),
        ("JAB BHI 'BAS 10 MINUTE' BOLO, WAPAS DEKHNA.","WAPAS"), ("AB PHONE NEECHE RAKHO. 'KAL SE PAKKA' WALA KAAM AAJ SE!","AAJ"),
    ]),
    "10c_final_callback": (C_MAGENTA, [("HAAN... TUMSE HI BAAT KAR RAHA THA.","TUMSE"),]),
}

# Odometer helper
def draw_odometer(draw, x, y, value_str, progress, font, col):
    # value_str like "1,095" or "45"
    # we animate each digit rolling: for each char, if digit, draw with vertical offset based on frac
    # Simplified: we just draw with easing value interpolation showing smooth count
    # For rolling effect, we draw two layers offset
    # We'll compute numeric target and current with easing
    # Instead we just draw value_str with spring entrance scaling
    # Add rolling illusion: characters slide up slightly with progress
    # We'll implement per-char y offset with ease
    # Actually we will draw characters with staggered delay
    # Each char animates from y+22 to y with easeOutCubic and fade
    for i,ch in enumerate(value_str):
        if ch=="," or ch==" ":
            continue
        delay=i*0.06
        local_t=np.clip((progress - delay)/0.45,0,1)
        ease=easeOutExpo(local_t) if local_t>0 else 0
        yy=int(y - (1-ease)*22)
        alpha=int(180 + 75*ease)
        # draw char
        draw.text((x,yy), ch, font=font, fill=col)

def draw_kinetic_caption(draw, text, highlight_word, accent, t, seg_start, seg_end, line_idx, lines):
    words=text.split()
    # choose font size based on text length
    base_font=F_POP_LG if len(text)<=34 else F_POP_MD
    active_font=F_POP_LG if len(text)<=34 else F_POP_MD  # will scale via size
    # Determine active word progression within line display window
    line_cnt=len(lines)
    line_dur=(seg_end-seg_start)/line_cnt
    line_start=seg_start + line_idx*line_dur
    line_end=line_start+line_dur
    # within line, word progression
    word_cnt=len(words)
    if word_cnt==0:
        return
    # active word index based on t within line
    if t<line_start: active_idx=-1
    elif t>=line_end: active_idx=word_cnt-1
    else:
        prog=(t-line_start)/max(0.001, line_dur)
        active_idx=int(prog*word_cnt)
        active_idx=max(0,min(word_cnt-1, active_idx))
    # compute word widths with active scaling
    # we need to measure widths: for active word, width larger due to scale 1.14
    widths=[]
    for idx,w in enumerate(words):
        if idx==active_idx:
            # estimate scaled width: measure with slightly larger font approximation via scaling factor
            base_w=draw.textlength(w, font=base_font)
            widths.append(base_w*1.14)
        else:
            widths.append(draw.textlength(w, font=base_font))
    space_w=draw.textlength(" ", font=base_font)
    total_w=sum(widths)+space_w*max(0,len(words)-1)
    # bar bg
    y_bar=H-118
    x0=int((W-total_w)/2)
    # background bar with rounded rect
    draw.rounded_rectangle([x0-32, y_bar-16, x0+int(total_w)+32, y_bar+62], radius=16, fill=(8,9,16), outline=(42,46,68), width=2)
    # also subtle glow behind active word
    if 0<=active_idx<len(words):
        # glow bg
        # compute x before active
        cx=x0+sum(widths[:active_idx])+space_w*active_idx
        aw=widths[active_idx]
        draw.rounded_rectangle([int(cx-12), y_bar-12, int(cx+aw+12), y_bar+54], radius=10, fill=(accent[0],accent[1],accent[2],22))
    # draw words
    cx=x0
    for idx,(w,ww) in enumerate(zip(words,widths)):
        is_active=(idx==active_idx)
        if is_active:
            # scale 1.14 and glow
            # we simulate scale by using larger font size approx: create font with +14% size on fly? Instead we draw with offset to simulate scale
            # Use base_font but draw with stroke and glow
            # glow
            # draw with extra shadow
            # actual larger text: we can draw with font size scaled via creating temp font
            # For performance, we approximate by drawing with outline glow
            col=accent
            # add spring scale animation when word becomes active: quick pop
            # compute word activation progress within word window
            word_dur=line_dur/word_cnt
            word_start=line_start + idx*word_dur
            word_t=np.clip((t - word_start)/ (word_dur*0.6),0,1)
            s_scale=1.0 + 0.14* spring_critical(word_t, w=18) if is_active else 1.0
            # we will offset to center scaling
            # draw glow first
            # Use larger stroke for glow
            # draw text at position with scaling via offset adjustment (approx)
            # To keep simple, we draw at cx with active color and add glow text duplicate blurred
            # Glow via drawing with larger stroke in accent with alpha
            # First glow layer (blurred via double draw offset)
            for ox,oy in [(-1,0),(1,0),(0,-1),(0,1)]:
                draw.text((int(cx)+ox, y_bar+oy), w, font=base_font, fill=(accent[0],accent[1],accent[2],90))
            draw.text((int(cx), y_bar-3), w, font=ImageFont.truetype("assets/fonts/Poppins-Bold.ttf", round(base_font.size*s_scale)), fill=col, stroke_width=3, stroke_fill=(0,0,0))
            # add subtle scale via font size bump: we can also draw second copy slightly larger using F_ANTON? skip for perf
        else:
            col=C_WHITE if abs(idx-active_idx)>1 else (210,210,220)
            # distance fade
            if idx<active_idx:
                # spoken already, slightly dim
                col=(165,170,185)
            draw.text((int(cx), y_bar), w, font=base_font, fill=col, stroke_width=2, stroke_fill=(0,0,0))
        cx+=ww+space_w

def overlay_graphics(img, t, p_map, active_seg, shot, shots):
    # is safe zone?
    is_safe = p_map["05b_ncrb_telemanas"]["start"]-0.4 <= t < p_map["05c_india_2041_window"]["start"]
    is_close = t >= p_map["10b_facecam_close"]["start"]-0.3
    d=ImageDraw.Draw(img, "RGBA")
    # flash at 0.08
    # progress bar
    bar_col=C_GOLD if is_close else (C_GREEN if t>=p_map["09c_steps_1_to_3"]["start"] else C_YELLOW)
    prog_width=int(W*(t/TOTAL_SEC))
    d.rectangle([0,0,prog_width,7], fill=bar_col)
    # segment-specific graphics (scaled coords)
    # We reuse old logic but scaled 1.5x
    # For brevity, we will implement key moments with simplified UI but maintaining source badges and counters

    # Helper to map old 1280x720 coords to 1920x1080 (1.5x)
    s=1.5

    # Add facecam badges where needed
    if active_seg and active_seg.get("face_cam"):
        if t<12:
            draw_facecam_badge(d, "FACE CAM [TIGHT] — REPLACE WITH YOUR TAKE", C_MAGENTA)
        elif 139 <= t <154:
            draw_facecam_badge(d, "FACE CAM [MEDIUM-WIDE] — WARM LIGHT RESET", C_GOLD)
        elif 341 <= t <364:
            draw_facecam_badge(d, "FACE CAM [MEDIUM] — CREATOR TRUST BEAT", C_GOLD)
        elif 459 <= t <470:
            draw_facecam_badge(d, "FACE CAM [6s INTERRUPT] — ULTRA TIGHT", C_RED)
        elif t>=566:
            draw_facecam_badge(d, "FACE CAM [TIGHT] — QUIET CLOSE & LOOP", C_GOLD)

    # Source badges for data points
    if 154 <= t < 180:
        draw_source_badge(d, "Esya Centre (2023) via Reuters Factbox, Jan 2026", C_YELLOW)
    elif 190 <= t < 224:
        draw_source_badge(d, "IAMAI-VTION Report (June 2026) | NCCS via ORF | IIM Rohtak", C_YELLOW)
    elif 223 <= t < 250:
        # PLFS
        show_q = (t - p_map["05a_jobs_plfs"]["start"]) >= 11.5
        draw_source_badge(d, "PLFS Quarterly Bulletin (15%)" if show_q else "PLFS 2025 Annual (Govt Reply, 27 Jul 2026 — 9.9%)", C_YELLOW)
    elif 249 <= t < 284:
        draw_source_badge(d, "NCRB 2024 Report (14,488 Student Deaths; 8,068 in 2014)", C_GOLD)
    elif 284 <= t < 310:
        draw_source_badge(d, "India Demographics Projections (Median Age 29.2; Peak ~2041)", C_CYAN)
    elif 363 <= t < 387:
        draw_source_badge(d, "SEBI Finfluencer Regulations & Enforcement Orders", C_CYAN)
    elif 469 <= t < 500:
        draw_source_badge(d, "Reuters Factbox (Jan 2026) & Checked Math: 1 Cr x 1h x 365", C_CYAN)

    # Counter/Panel animations with easing
    # Example: 0:11 day montage
    if 11.2 <= t < 44.2:
        if t<18:
            # alarm panel with slide-in
            entrance=np.clip((t-11.2)/0.45,0,1); e=easeOutExpo(entrance)
            xoff=int((1-e)*280)
            d.rounded_rectangle([int(114- xoff), int(128), int(780- xoff), int(308)], radius=24, fill=(14,12,24), outline=C_RED, width=4)
            d.text((int(156 - xoff), 152), "06:30 AM — ALARM", font=F_ANTON_MD, fill=C_RED)
            d.text((int(156 - xoff), 242), "PEHLA KAAM: PHONE CHECK", font=F_POP_SM, fill=C_WHITE)
        elif t<27.5:
            tags=["NASHTE MEIN: REELS","KAPDE PEHENTE: REELS","RASTE MEIN: REELS"]
            for k in range(min(3, int((t-18)/3.1)+1)):
                yy=122 + k*123
                col=[C_YELLOW, C_MAGENTA, C_CYAN][k]
                # slide in
                ent=np.clip((t-(18+k*3.1))/0.5,0,1); ee=easeOutExpo(ent)
                xo=int((1-ee)*320)
                d.rounded_rectangle([int(111-xo), int(yy), int(870-xo), int(yy+99)], radius=18, fill=(12,13,22), outline=col, width=4)
                d.text((int(147-xo), int(yy+20)), tags[k], font=F_POP_MD, fill=col)
        elif t<34.4:
            e=np.clip((t-27.5)/0.5,0,1); ee=easeOutExpo(e)
            # clock panel zoom
            scale=0.92+0.08*ee
            # we can just draw with opacity
            alpha=int(255*ee)
            d.rounded_rectangle([1185,120,1800,412], radius=30, fill=(10,10,18), outline=C_MAGENTA, width=6)
            d.text((1248,144), "02:00 AM", font=F_ANTON_LG, fill=C_MAGENTA)
            d.text((1252,297), "KAL TEST HAI...", font=F_POP_MD, fill=C_RED)
        else:
            mult=int(min(1000, 10**(1.0+2.0* min(1.0,(t-34.4)/5.0))))
            # pulse scale
            pulse=1.0+0.04*math.sin(t*9)
            d.rounded_rectangle([int(435), int(195), int(W-435), int(592)], radius=36, fill=(10,10,16), outline=C_RED, width=7)
            # odometer style for mult
            # we approximate with scaling text
            draw_centered(d, 222, "KAL SE PAKKA", F_ANTON_LG, C_WHITE, 8)
            draw_centered(d, 382, f"x{mult}?", F_ANTON_XL, C_YELLOW, 8)

    # 5 Problems intro
    if 44.2 <= t < 48.4:
        e=np.clip((t-44.2)/0.55,0,1); ee=spring_critical(e, w=12)
        y_off=int((1-ee)*80)
        draw_centered(d, int(308+y_off), "5 CHEEZEIN", F_ANTON_XL, C_YELLOW, 12)
        draw_centered(d, int(540+y_off), "JO TUM KISI KO BATATE NAHI", F_ANTON_MD, C_MAGENTA, 6)

    # Problem 1 tug
    if 48.4 <= t < 72.7:
        d.rounded_rectangle([63,51,705,168], radius=18, fill=C_BLACK, outline=C_YELLOW, width=4)
        d.text((96,66), "PROBLEM 01  |  DISCIPLINE", font=F_ANTON_MD, fill=C_YELLOW)
        pull=0.62+0.14*math.sin(t*2.6)
        # animated bar with spring
        d.rounded_rectangle([480,780,1440,849], radius=18, fill=(15,15,22), outline=C_WHITE, width=3)
        split_x=int(480+960*(1.0-pull))
        d.rounded_rectangle([486,786,split_x,843], radius=12, fill=C_CYAN)
        d.rounded_rectangle([split_x,786,1434,843], radius=12, fill=C_MAGENTA)
        d.text((495,738), "TUMHARA FOCUS", font=F_POP_XS, fill=C_CYAN)
        d.text((1072,738), "BILLION-$ ALGORITHMS", font=F_POP_XS, fill=C_MAGENTA)

    if 72.7 <= t < 92.2:
        d.line([(W//2,0),(W//2,H-150)], fill=C_YELLOW, width=7)
        d.rounded_rectangle([63,51,742,168], radius=18, fill=C_BLACK, outline=C_YELLOW, width=4)
        d.text((96,66), "PROBLEM 02  |  COMPARISON", font=F_ANTON_MD, fill=C_YELLOW)
        d.rounded_rectangle([135,772,802,852], radius=15, fill=C_BLACK, outline=C_MAGENTA, width=3)
        d.text((172,789), "UNKA HIGHLIGHT REEL", font=F_POP_MD, fill=C_MAGENTA)
        d.rounded_rectangle([1072,772,1815,852], radius=15, fill=C_BLACK, outline=C_CYAN, width=3)
        d.text((1107,789), "TUMHARA BEHIND-THE-SCENES", font=F_POP_MD, fill=C_CYAN)

    if 92.2 <= t < 108.6:
        d.rounded_rectangle([63,51,682,168], radius=18, fill=C_PANEL, outline=C_YELLOW, width=4)
        d.text((96,66), "PROBLEM 03  |  SAVED", font=F_ANTON_MD, fill=C_YELLOW)
        p_prog=np.clip((t-(92.2+48.4-44.2))/7.5,0,1) # approximate
        # Actually use segment time
        # Use ease for counter
        e=easeOutExpo(p_prog)
        for title,val,col,cx in [("SAVED REELS", int(300*e), C_MAGENTA, 195), ("UNREAD PDFs", int(40*e), C_YELLOW, 750), ("PLAYLISTS", int(10*e), C_CYAN, 1305)]:
            # card reveal
            card_e=easeOutCubic(np.clip((p_prog*1.2 - (cx-195)/1305),0,1))
            y_off=int((1-card_e)*30)
            d.rounded_rectangle([cx, int(277+y_off), cx+465, int(682+y_off)], radius=30, fill=C_PANEL, outline=col, width=6)
            # odometer for numbers with rolling
            # draw number with spring
            num_text=f"{val}+"
            d.text((cx+62, int(315+y_off)), num_text, font=F_ANTON_XL, fill=col)
            d.text((cx+62, int(567+y_off)), title, font=F_POP_MD, fill=C_WHITE)
        draw_centered(d, 735, "FAKE PRODUCTIVITY  =  ZERO EXECUTION", F_ANTON_MD, C_RED, 4)

    if 108.6 <= t < 123.8:
        draw_source_badge(d, "Promotion & Regulation of Online Gaming Act, 2025 (PIB)", C_YELLOW)
        d.rounded_rectangle([63,120,742,234], radius=18, fill=C_PANEL, outline=C_YELLOW, width=4)
        d.text((96,135), "PROBLEM 04  |  SHORTCUT", font=F_ANTON_MD, fill=C_YELLOW)
        # card with scale
        e=np.clip((t-108.6)/0.6,0,1); ee=spring_critical(e,w=14)
        # scale via rectangle size
        pad=int((1-ee)*80)
        d.rounded_rectangle([330+pad,322+pad,W-330-pad,712-pad], radius=36, fill=(24,10,16), outline=C_RED, width=7)
        draw_centered(d, 357, "ONLINE REAL-MONEY GAMES", F_ANTON_LG, C_WHITE, 7)
        draw_centered(d, 532, "BANNED IN 2025 — ADDICTION & DEBT", F_ANTON_MD, C_RED, 5)

    if 123.8 <= t < 140:
        d.rounded_rectangle([63,51,780,168], radius=18, fill=C_PANEL, outline=C_YELLOW, width=4)
        d.text((96,66), "PROBLEM 05  |  ANESTHESIA", font=F_ANTON_MD, fill=C_YELLOW)
        local=t-(123.8)
        flat=np.clip((local-5.5)/5.0,0,1)
        # ECG line
        pts=[]
        for x in range(150, W-150, 9):
            ph=(x*0.045 - local*7.0) % (2*math.pi)
            spike=(math.exp(-((ph-3.0)**2)*18.0)*138 - math.exp(-((ph-3.35)**2)*28.0)*78)*(1.0-flat)
            pts.append((x, int(502 - spike)))
        if len(pts)>=2:
            d.line(pts, fill=C_RED if flat>0.6 else C_MAGENTA, width=7)
        draw_centered(d, 697, "DARD SUNN KARTA HAI  —  THEEK NAHI KARTA", F_ANTON_MD, C_WHITE, 4)

    # Face cam reset 139-154
    if 139.9 <= t < 154.2:
        draw_facecam_badge(d, "FACE CAM [MEDIUM-WIDE] — WARM LIGHT RESET", C_GOLD)
        # save badge with spring
        e=np.clip((t-142)/0.5,0,1); ee=easeOutExpo(e)
        xo=int((1-ee)*240)
        d.rounded_rectangle([63-xo,757,810-xo,852], radius=18, fill=C_YELLOW, outline=C_BLACK, width=4)
        d.text((99-xo,775), "YE WAALA HISSA SAVE KARNA", font=F_POP_MD, fill=C_BLACK)

    # Math build 154-179
    if 154.2 <= t < 179:
        lt=t-154.2
        if lt<9.5:
            # 3.2 HRS with odometer
            prog=np.clip(lt/1.2,0,1); ee=easeOutExpo(prog)
            d.rounded_rectangle([105,225,930,667], radius=33, fill=(10,10,16), outline=C_YELLOW, width=6)
            # odometer 3.2
            # scale entrance
            y_off=int((1-ee)*28)
            d.text((157, int(258+y_off)), "3.2 HRS / DAY", font=F_ANTON_XL, fill=C_YELLOW)
            d.text((162, int(513+y_off)), "SOCIAL NETWORKING APPS", font=F_POP_MD, fill=C_WHITE)
        elif lt<15.2:
            hrs=int(min(1095, 1095*((lt-9.5)/2.2))); prog=np.clip((lt-9.5)/2.2,0,1); ee=easeOutExpo(prog)
            d.rounded_rectangle([105,225,975,702], radius=33, fill=(10,10,16), outline=C_YELLOW, width=6)
            d.text((153,252), "3h x 365 DAYS =", font=F_ANTON_MD, fill=C_WHITE)
            # odometer hrs
            # rolling numbers: draw hrs with spring
            num=f"{hrs:,} HRS"
            d.text((153,360), num, font=F_ANTON_XL, fill=C_YELLOW)
            d.text((157,600), "HAR EK SAAL!", font=F_POP_MD, fill=C_RED)
        else:
            # 45 days with tiles
            d.rounded_rectangle([97,165,997,802], radius=33, fill=(10,10,16), outline=C_RED, width=6)
            lit=int(min(45, ((lt-15.2)/3.5)*45)); prog=lit/45; ee=easeOutExpo(prog)
            for idx in range(45):
                r,c=divmod(idx,9)
                tx,ty=142 + c*90, 207 + r*69
                col=C_RED if idx < lit else (35,36,48)
                # staggered tile entrance
                delay=idx*0.012; local=np.clip((lt-15.2 - delay)/0.4,0,1); le=easeOutExpo(local)
                yy=int((1-le)*12)
                d.rounded_rectangle([tx, ty+yy, tx+75, ty+54+yy], radius=9, fill=col)
            if lt<20:
                d.text((142,592), "45 FULL DAYS / YEAR (68 WAKING DAYS)", font=F_ANTON_SM, fill=C_YELLOW)
            else:
                d.text((142,577), "10 SAAL = 684 WAKING DAYS", font=F_ANTON_MD, fill=C_YELLOW)
                d.text((142,690), "1.9 YEARS OF WAKING LIFE", font=F_POP_MD, fill=C_RED)

    if 179 <= t < 180:
        draw_centered(d, 457, "684 JAAGTE DIN  =", F_ANTON_LG, C_MUTED, 0)

    if 179.4 <= t < 190:
        d.rounded_rectangle([435,217,W-435,667], radius=42, fill=(10,8,14), outline=C_YELLOW, width=8)
        prog=np.clip((t-179.4)/0.55,0,1); ee=spring_critical(prog,w=16)
        y_off=int((1-ee)*34)
        draw_centered(d, int(247+y_off), "DO SAAL!", F_ANTON_XL, C_YELLOW, 12)
        draw_centered(d, 495, "EK POORI DEGREE YA TOP SKILL KA WAQT", F_POP_MD, C_RED, 2)

    if 190 <= t < 224:
        lt=t-190
        active_idx=0 if lt<10.5 else (1 if lt<20 else 2)
        src=["IAMAI-VTION Report (June 2026)","NCCS Survey via ORF (April 2026)","IIM Rohtak Study & Economic Survey 2025-26"][active_idx]
        draw_source_badge(d, src, C_YELLOW)
        draw_centered(d, 138, "SCREEN TIME REALITY ACROSS INDIA", F_ANTON_LG, C_WHITE, 6)
        d.rounded_rectangle([210,352,W-210,435], radius=24, fill=C_PANEL, outline=C_MUTED, width=3)
        fill_w=int((W-432)* [0.38,0.68,1.0][active_idx] * easeOutExpo(np.clip((lt-active_idx*10.5)/1.0,0,1)))
        d.rounded_rectangle([216,358,216+fill_w,429], radius=18, fill=[C_MAGENTA,C_YELLOW,C_RED][active_idx])
        rows=[("120+ MIN / DAY","Urban Age 18-24 on Social Media (vs 97.9m avg) — IAMAI-VTION",C_MAGENTA),
              ("74% > 2 HRS  |  21% > 4 HRS","Students Non-Academic Screen Time — NCCS via ORF",C_YELLOW),
              ("6h 45m (M) / 7h 05m (F)","Total Daily Screen Time — IIM Rohtak + Economic Survey 2025-26",C_RED)]
        for i,(stat,desc,col) in enumerate(rows):
            yy=495+i*117
            hi=i<=active_idx
            # slide in
            delay=i*0.22; ent=np.clip((lt - delay)/0.55,0,1); ee=easeOutExpo(ent)
            xo=int((1-ee)*180)
            d.rounded_rectangle([210-xo,yy,W-210-xo,yy+96], radius=18, fill=C_PANEL if hi else (10,10,14), outline=col if hi else (35,35,45), width=4 if i==active_idx else 1)
            d.text((252-xo,yy+20), stat, font=F_POP_MD, fill=col if hi else C_MUTED)
            d.text((802-xo,yy+28), desc, font=F_POP_SM, fill=C_WHITE if hi else C_MUTED)

    if 223 <= t < 250:
        lt=t-223
        show_q=lt>=11.5
        # PLFS icons
        draw_centered(d, 129, "YOUTH UNEMPLOYMENT (AGE 15-29)", F_ANTON_LG, C_WHITE, 6)
        for k in range(10):
            cx,cy=172 + k*159,322
            col=C_RED if ((k==0) or (show_q and k==1)) else C_CYAN
            # pop animation
            delay=k*0.07; ent=np.clip((lt - delay)/0.45,0,1); ee=spring_critical(ent,w=10)
            yy_off=int((1-ee)*22)
            d.ellipse([cx+36, cy+yy_off, cx+102, cy+66+yy_off], fill=col)
            d.rounded_rectangle([cx+21, cy+78+yy_off, cx+117, cy+217+yy_off], radius=21, fill=col)
        # cards
        e=easeOutExpo(np.clip(lt/0.7,0,1))
        xo=int((1-e)*120)
        d.rounded_rectangle([210-xo,607,922-xo,783], radius=24, fill=C_PANEL, outline=C_YELLOW, width=4)
        d.text((252-xo,624), "9.9% ANNUAL", font=F_ANTON_MD, fill=C_YELLOW)
        d.text((252-xo,727), "PLFS 2025 Annual Report", font=F_POP_XS, fill=C_WHITE)
        # second card
        e2=easeOutExpo(np.clip((lt-0.25)/0.7,0,1)); xo2=int((1-e2)*120)
        d.rounded_rectangle([997-xo2,607,1710-xo2,783], radius=24, fill=C_PANEL, outline=C_RED if show_q else C_MUTED, width=4)
        d.text((1039-xo2,624), "15.0% QUARTERLY", font=F_ANTON_MD, fill=C_RED if show_q else C_MUTED)
        d.text((1039-xo2,727), "Recent PLFS Quarterly Bulletin", font=F_POP_XS, fill=C_WHITE if show_q else C_MUTED)

    if 250 <= t < 284:
        # Telemanas - calm, no animation shake
        d.ellipse([735,135,1185,585], fill=(26,20,14))
        draw_centered(d, 198, "TUM AKELE NAHI HO.", F_ANTON_LG, C_GOLD, 4)
        draw_centered(d, 367, "NCRB 2024: 14,488 Students  (Up ~80% Since 2014)", F_POP_MD, C_WHITE, 0)
        d.rounded_rectangle([180,477,W-180,771], radius=30, fill=(16,18,26), outline=C_GOLD, width=6)
        draw_centered(d, 504, "Tele-MANAS Helpline:  14416", F_ANTON_LG, C_WHITE, 2)
        draw_centered(d, 687, "Free, Confidential 24x7 Mental Health Support Across India", F_POP_SM, C_GOLD, 0)

    if 284 <= t < 310:
        lt=t-284
        d.rounded_rectangle([105,138,810,348], radius=27, fill=(8,12,20), outline=C_CYAN, width=4)
        d.text((147,159), "MEDIAN AGE: 29.2", font=F_ANTON_MD, fill=C_CYAN)
        d.text((147,267), "WORKING-AGE PEAK: ~2041", font=F_POP_SM, fill=C_YELLOW)
        close_pct=min(0.82, max(0.0, (lt-6.0)/16.0)); e=easeOutCubic(close_pct)
        d.rounded_rectangle([210,720,W-210,813], radius=21, fill=(10,12,18), outline=C_CYAN, width=4)
        open_w=int((W-438)*(1.0 - e*0.65))
        d.rounded_rectangle([216,726,216+open_w,807], radius=15, fill=C_CYAN)
        d.text((240,742), "2026 (TUM: 15-25)", font=F_POP_SM, fill=C_BLACK)
        d.text((1305,742), "2041 WINDOW CLOSING", font=F_POP_SM, fill=C_RED)

    if 309 <= t < 342:
        lt=t-309
        if lt<17:
            # influencer
            e=np.clip((lt)/0.6,0,1); ee=spring_critical(e,w=14)
            pad=int((1-ee)*60)
            d.rounded_rectangle([390+pad,142+pad,W-390-pad,402-pad], radius=27, fill=(20,10,24), outline=C_MAGENTA, width=6)
            draw_centered(d, 165, '"30 DIN MEIN LAKHPATI!"', F_ANTON_LG, C_YELLOW, 7)
            draw_centered(d, 318, '"COLLEGE CHHOD DO  •  SECRET PASSIVE INCOME"', F_POP_SM, C_MAGENTA, 0)
            if lt>5:
                d.line([(930,142),(982,270),(915,402)], fill=C_RED, width=9)
        else:
            e=np.clip((lt-17)/0.55,0,1); ee=easeOutExpo(e)
            pad=int((1-ee)*100)
            d.rounded_rectangle([405+pad,142+pad,W-405-pad,397-pad], radius=33, fill=(12,8,14), outline=C_RED, width=7)
            draw_centered(d, 168, "TUM MAAL HO.", F_ANTON_XL, C_RED, 12)
            for lbl,tx in [("VIEWS",345),("AFFILIATE CLICKS",750),("COURSE SALE",1282)]:
                # staggered
                delay=(tx-345)/800*0.3; ent=np.clip((lt-17-delay)/0.4,0,1); le=easeOutExpo(ent)
                yy=int((1-le)*22)
                d.rounded_rectangle([tx, 742+yy, tx+352, 832+yy], radius=18, fill=C_BLACK, outline=C_MAGENTA, width=4)
                d.text((tx+36, 765+yy), lbl, font=F_POP_SM, fill=C_MAGENTA)

    if 341 <= t < 364:
        # trust face cam overlay
        d.rounded_rectangle([81,747,1087,843], radius=18, fill=C_BLACK, outline=C_GOLD, width=4)
        d.text((114,768), "SAWAAL POOCHHO: 'PAISA KAHAN SE AATA HAI?'", font=F_POP_MD, fill=C_GOLD)

    if 363 <= t < 414:
        lt=t-363
        if lt<24:
            draw_source_badge(d, "SEBI Finfluencer Regulations & Enforcement Orders", C_CYAN)
            e=np.clip(lt/0.65,0,1); ee=spring_critical(e,w=12)
            pad=int((1-ee)*80)
            d.rounded_rectangle([270+pad,225+pad,W-270-pad,720-pad], radius=36, fill=C_PANEL, outline=C_CYAN, width=6)
            draw_centered(d, 267, "SEBI REGULATORY ACTION", F_ANTON_LG, C_CYAN, 7)
            draw_centered(d, 450, "• Regulated Entities Barred From Unregistered Finfluencers", F_POP_MD, C_WHITE, 0)
            draw_centered(d, 547, "• Orders Issued Against Unregistered Market Educators", F_POP_MD, C_YELLOW, 0)
        else:
            d.rounded_rectangle([142,738,840,840], radius=18, fill=C_BLACK, outline=C_CYAN, width=4)
            d.text((180,762), "PADHAI = ZAMEEN  |  SKILL = IMAARAT", font=F_POP_SM, fill=C_CYAN)
            d.rounded_rectangle([1065,738,1777,840], radius=18, fill=C_BLACK, outline=C_RED, width=4)
            d.text((1107,762), "NO FOUNDATION = SIRF REELS MEIN", font=F_POP_SM, fill=C_RED)

    if 413 <= t < 460:
        lt=t-413
        d.line([(W//2,0),(W//2,H-144)], fill=C_GOLD, width=6)
        d.rounded_rectangle([57,51,903,177], radius=21, fill=C_BLACK, outline=C_MAGENTA, width=4)
        d.text((93,69), "2036 (A): WAHI 3 GHANTE", font=F_ANTON_MD, fill=C_MAGENTA)
        d.rounded_rectangle([1017,51,1863,177], radius=21, fill=C_BLACK, outline=C_GOLD, width=4)
        d.text((1053,69), "2036 (B): ROZ +1 GHANTA", font=F_ANTON_MD, fill=C_GOLD)
        if lt>=23:
            hrs=int(min(3650, 3650*((lt-23)/4.5))); prog=np.clip((lt-23)/4.5,0,1); ee=easeOutExpo(prog)
            # card
            e2=easeOutExpo(np.clip((lt-23)/0.6,0,1)); pad=int((1-e2)*40)
            d.rounded_rectangle([1072+pad,618,1830+pad,858+pad], radius=27, fill=(12,12,18), outline=C_GOLD, width=6)
            # odometer
            num=f"{hrs:,} HRS"
            d.text((1128,630), num, font=F_ANTON_LG, fill=C_GOLD)
            d.text((1128,804), "1h x 365 x 10 YEARS  [CHECKED MATH]", font=F_POP_XXS, fill=C_WHITE)

    if 459 <= t < 470:
        d.rounded_rectangle([465,108,W-465,261], radius=24, fill=C_BLACK, outline=C_RED, width=6)
        draw_centered(d, 126, "PHONE CHECK KIYA?", F_ANTON_LG, C_RED, 7)

    if 469 <= t < 500:
        lt=t-469
        if lt<17.5:
            d.rounded_rectangle([111,157,1020,382], radius=27, fill=(8,12,20), outline=C_CYAN, width=4)
            d.text((153,183), "CRITICAL GROWTH MARKET", font=F_ANTON_MD, fill=C_CYAN)
            d.text((153,292), "TUMHARA DHYAAN = UNKA PRODUCT", font=F_POP_MD, fill=C_MAGENTA)
        else:
            cr=int(min(365, 365*((lt-17.5)/7.0))); prog=np.clip((lt-17.5)/7.0,0,1); ee=easeOutExpo(prog)
            e2=easeOutExpo(np.clip((lt-17.5)/0.6,0,1)); pad=int((1-e2)*80)
            d.rounded_rectangle([277+pad,217+pad,W-277-pad,678-pad], radius=36, fill=(10,12,18), outline=C_GOLD, width=7)
            draw_centered(d, 247, f"{cr} CRORE HRS", F_ANTON_XL, C_GOLD, 12)
            draw_centered(d, 513, "1 CRORE PEOPLE  x  1 HOUR  x  365 DAYS", F_POP_MD, C_CYAN, 0)

    if 500 <= t < 506:
        e=np.clip((t-500)/0.5,0,1); ee=spring_critical(e,w=14)
        y_off=int((1-ee)*30)
        draw_centered(d, int(427+y_off), "365,00,00,000 GHANTE.", F_ANTON_LG, C_GOLD, 6)
    if 506 <= t < 507:
        e=np.clip((t-500.4)/0.5,0,1); ee=spring_critical(e,w=14)
        draw_centered(d, 382, "YE KHARA GANIT HAI.", F_ANTON_XL, C_YELLOW, 12)

    # Steps
    if 506 <= t < 567:
        s9c=506.72; s10a=535.8
        if t < s9c+4.2:
            e=np.clip((t-s9c)/0.6,0,1); ee=spring_critical(e,w=14)
            y_off=int((1-ee)*34)
            draw_centered(d, int(307+y_off), "AAJ RAAT SE", F_ANTON_XL, C_GREEN, 12)
            draw_centered(d, int(540+y_off), "PAANCH SEEDHE KADAM", F_ANTON_LG, C_WHITE, 6)
        else:
            if t < s9c+14:
                idx,tag,sub,prog=1,"DOOR RAKHO","Charger Kamre Ke Doosre Kone Mein • Pehla 1 Ghanta No Phone", (t-(s9c+4.2))/9.5
            elif t < s9c+22.5:
                idx,tag,sub,prog=2,"LIMIT LAGAO","Top 2 Time-Sink Apps Par Friction & Extra Lock Lagao", (t-(s9c+14))/8.2
            elif t < s10a:
                idx,tag,sub,prog=3,"DEEP WORK","Roz 1 Ghanta: 50 Min Focus + 10 Min Break (Phone Bahar)", (t-(s9c+22.5))/8.0
            elif t < s10a+13:
                idx,tag,sub,prog=4,"90 DIN SKILL","Padhai Ke Saath 1 Skill • Har Hafte 1 Real Output Banao", (t-s10a)/12.5
            else:
                idx,tag,sub,prog=5,"SAHI LOG","2 Kaam Karne Wale Log Chuno • Phone Ek Auzaar Hai!", (t-(s10a+13))/14.0
            accent=C_GOLD if idx==5 else C_GREEN
            prog=float(np.clip(prog,0,1)); e_prog=easeOutExpo(prog)
            # step chips
            for k in range(1,6):
                bx=247 + (k-1)*293
                done=k<=idx
                # pop
                delay=(k-1)*0.07; ent=np.clip((prog*1.2 - delay)/0.4,0,1) if k==idx else (1 if done else 0)
                ee2=easeOutExpo(ent) if k==idx else (1 if done else 0)
                y_off=int((1-ee2)*14) if k==idx else 0
                d.rounded_rectangle([bx, 87+y_off, bx+255, 171+y_off], radius=18, fill=accent if k==idx else C_PANEL, outline=accent if done else (45,48,60), width=4)
                d.text((bx+63, 102+y_off), f"STEP 0{k}", font=F_POP_MD, fill=C_BLACK if k==idx else (accent if done else C_MUTED))
            d.rounded_rectangle([247,232,W-247,742], radius=39, fill=C_PANEL, outline=accent, width=6)
            # title with slide
            e_title=easeOutExpo(np.clip((prog)/0.35,0,1))
            xo=int((1-e_title)*36)
            d.text((322-xo,277), f"0{idx}  |  {tag}", font=F_ANTON_XL, fill=accent)
            d.text((327,513), sub, font=F_POP_MD, fill=C_WHITE)
            d.rounded_rectangle([322,622,W-322,678], radius=15, fill=(8,10,16), outline=accent, width=3)
            fw=int((W-657)*e_prog)
            if fw>8:
                d.rounded_rectangle([328,628,328+fw,672], radius=10, fill=accent)

    # End card after 596.2
    if t >= 596.28:
        # black end card overlay handled in main frame, but add text
        # we will in main render handle background, here just add text if needed
        pass
    if t >= p_map["10c_final_callback"]["end"]+0.08:
        # already handled in main, but ensure end card text
        # Draw end card content (over black)
        # Since main already draws black, we just add here for transition
        pass

    # Kinetic caption bar
    if active_seg and active_seg["id"] in SEGMENT_LINES:
        accent, lines = SEGMENT_LINES[active_seg["id"]]
        # find line index
        rel=(t - active_seg["start"])/max(0.05, active_seg["duration"])
        line_idx=min(len(lines)-1, max(0, int(rel*len(lines))))
        # guard if last line already passed? still show last
        txt, hl = lines[line_idx]
        draw_kinetic_caption(d, txt, hl, accent, t, active_seg["start"], active_seg["end"], line_idx, lines)

    return img

def apply_transition(prev_frame, curr_frame, trans_type, progress):
    # progress 0..1 where 0 = prev fully, 1 = curr fully
    # progress is ease curve
    e=easeInOutCubic(progress)
    if trans_type=="whip":
        # horizontal whip: prev slides left, curr slides right with motion blur mimic via alpha and offset
        # offset proportional to (1-e)
        # we simulate motion blur by blending with stretched alpha
        # compute offset
        off=int((1-e)*W*0.55)  # whip distance
        # prev displaced left
        # curr displaced right then to center
        # create new image
        out=Image.new("RGB",(W,H), (0,0,0))
        # prev at -off
        # We need to composite with cropping: paste prev shifted
        # For simplicity, we blend with alpha and offset overlay
        # Use alpha blend + horizontal shift approximation via crop
        # Create canvases
        # Instead of heavy shift, we do simple slide: prev slides out left, curr slides in right
        # We can create output by pasting both with x offset
        # prev
        prev_x = -int(e * W * 0.18) - int((1-e)* W*0.02) # subtle
        curr_x = int((1-e)* W * 0.18)
        # For true whip, we add motion blur via horizontal stretch: we can use PIL filter BoxBlur on a copy for middle progress
        # But to keep fast, we add extra alpha blend of 2 intermediate positions when progress ~0.5
        out.paste(prev_frame, (prev_x,0))
        # curr on top with alpha blend to smooth
        # create curr shifted
        # Use alpha composite via blending over out
        # We create temp image for curr
        temp=Image.new("RGB",(W,H),(0,0,0))
        temp.paste(curr_frame, (curr_x,0))
        # blend based on e
        # simple alpha
        # we can use blend function
        out=Image.blend(out, temp, e)
        # add directional blur hint when e ~0.5: darken slightly to mimic motion blur
        if 0.35 < e < 0.65:
            # add slight darken
            enh=ImageEnhance.Brightness(out).enhance(0.88)
            out=Image.blend(out, enh, 0.18)
        return out
    elif trans_type=="zoom":
        # zoom-through: prev scale 1.0 ->2.2, curr 0.85->1.0
        # progress maps to zoom
        prev_zoom=1.0 + 1.2*e
        curr_zoom=0.85 + 0.15*e
        # we need to zoom by resizing and cropping
        # For prev: enlarge
        pw=int(W*prev_zoom); ph=int(H*prev_zoom)
        prev_scaled=prev_frame.resize((pw,ph), Image.Resampling.BICUBIC)
        # crop center
        ox=(pw-W)//2; oy=(ph-H)//2
        prev_cropped=prev_scaled.crop((ox,oy,ox+W,oy+H))
        # darken prev as it zooms out
        prev_cropped=ImageEnhance.Brightness(prev_cropped).enhance(1.0 - 0.18*e)
        # curr scaled: if curr_zoom<1, we need to shrink and pad with black? Actually 0.85 means zoomed out, show black border then zoom in
        # Instead we can simulate by resizing curr to smaller and pasting centered on black, then scaling up
        # Simplify: curr zoom 0.85->1.0 via resize
        cw=int(W*curr_zoom); ch=int(H*curr_zoom)
        curr_scaled=curr_frame.resize((cw,ch), Image.Resampling.BICUBIC)
        # paste centered on black
        curr_board=Image.new("RGB",(W,H),(4,4,8))
        curr_board.paste(curr_scaled, ((W-cw)//2, (H-ch)//2))
        # also add radial blur hint: blend with slightly blurred version when mid
        if 0.25< e <0.75:
            # add radial glow
            glow=Image.new("RGB",(W,H),(255,200,80))
            # blend glow at low alpha
            curr_board=Image.blend(curr_board, glow, 0.06*(1-abs(e-0.5)*2))
        # now blend prev_cropped and curr_board by e with radial mask (circle expanding)
        # radial mask: circle radius grows with e
        # create mask: white circle radius = e*W*0.9, feather?
        # Use simple linear blend plus vignette for now
        out=Image.blend(prev_cropped, curr_board, e)
        # add radial blur hint: darken edges
        return out
    elif trans_type=="wipe":
        # diagonal split wipe
        # progress determines wipe line diagonal from top-left to bottom-right
        # create mask polygon
        mask=Image.new("L",(W,H),0)
        md=ImageDraw.Draw(mask)
        # diagonal line: x = -W + progress*2*W at top, and same at bottom but offset
        # Wipe from left-top to right-bottom diagonal
        p=e*2 -0.2 # allow over
        # define quad covering wiped area (revealing curr)
        # points: (0,0) -> (progress*W*1.6,0) -> (progress*W*1.6 - W*0.35, H) -> (0,H)
        # This creates diagonal edge
        x_top = int(-W*0.2 + e*W*1.8)
        x_bot = int(-W*0.65 + e*W*1.8)
        # clamp
        pts=[(0,0),(x_top,0),(x_bot,H),(0,H)]
        # ensure polygon covers area correctly, use larger
        md.polygon(pts, fill=255)
        # feather edge: blur mask slightly (per frame blur heavy, but we can do small blur radius 3)
        # To keep perf, we skip blur or do 1px blur every other frame
        # Composite
        out=Image.composite(curr_frame, prev_frame, mask)
        # add subtle edge highlight
        # draw line on edge
        # edge line between (x_top,0)-(x_bot,H)
        # we can draw gold line on output for tycoon style
        od=ImageDraw.Draw(out)
        od.line([(x_top,0),(x_bot,H)], fill=C_GOLD, width=4)
        return out
    elif trans_type=="leak":
        # warm film burn / light leak
        # blend with warm overlay and lens flare
        # progress: light leak peaks at 0.5
        leak_alpha= math.sin(e*math.pi) *0.42
        # warm gradient
        leak=Image.new("RGB",(W,H),(255,150,40))
        # radial gradient for leak: elliptical
        # create gradient via drawing ellipse with alpha
        leak_overlay=Image.new("RGBA",(W,H),(0,0,0,0))
        ld=ImageDraw.Draw(leak_overlay)
        # center leak at top-right or center based on progress
        cx=int(W*0.75 + 120*math.sin(e*math.pi))
        cy=int(H*0.35 + 80*math.cos(e*math.pi))
        for r in range(420,0,-42):
            alpha=int(28 * (1 - r/420)**1.4 * leak_alpha*1.6)
            ld.ellipse([cx-r,cy-r,cx+r,cy+r], fill=(255,230,140,alpha))
        # composite leak over blend
        base=Image.blend(prev_frame, curr_frame, e)
        base_rgba=base.convert("RGBA")
        # blend leak color over base with screen-like
        # simple alpha composite of leak_overlay + solid warm
        # first blend warm solid with low alpha
        warm_layer=Image.new("RGBA",(W,H),(255,120,32, int(90*leak_alpha)))
        base_rgba=Image.alpha_composite(base_rgba, warm_layer)
        base_rgba=Image.alpha_composite(base_rgba, leak_overlay)
        return base_rgba.convert("RGB")
    elif trans_type=="fade":
        return Image.blend(prev_frame, curr_frame, e)
    else:
        return Image.blend(prev_frame, curr_frame, e)

def render_frame_wrapper(args):
    # args: frame_idx, total_frames, p_map, placements, shots, shot_starts, transition_frames
    frame_idx=args
    t=frame_idx / FPS
    # shot lookup via binary search (shots sorted)
    # find shot where start <= t < end
    # linear search okay for ~150 shots, but binary better
    # we will have global SHOTS and SHOT_STARTS
    # use bisect
    import bisect
    # shot index
    idx=bisect.bisect_right(SHOT_STARTS, t) -1
    idx=max(0, min(len(SHOTS)-1, idx))
    shot=SHOTS[idx]
    # determine if in transition: first 8 frames of shot (except first shot and safe zone)
    is_transition=False
    prev_shot=None
    trans_progress=0
    TRANS_FRAMES=8
    if idx>0 and frame_idx >= int(shot["start"]*FPS) and frame_idx < int(shot["start"]*FPS)+TRANS_FRAMES:
        # check if not safe zone
        if shot["seg_id"]!="05b_ncrb_telemanas" and SHOTS[idx-1]["seg_id"]!="05b_ncrb_telemanas":
            is_transition=True
            prev_shot=SHOTS[idx-1]
            trans_progress=(frame_idx - int(shot["start"]*FPS))/TRANS_FRAMES
    # active segment lookup
    # placements list for active seg
    # find active seg where start <= t <= end
    active=None
    for p in PLACEMENTS:
        if p["start"] <= t <= p["end"]:
            active=p
            break
    # shot progress
    shot_progress=np.clip((t - shot["start"])/max(0.001, shot["duration"]),0,1)
    # white flash at 0.08
    if 0.08 <= t <0.13:
        return Image.new("RGB",(W,H),(255,255,255))
    # end card black after 596.2+0.08
    if t >= PLACEMENTS[-1]["end"]+0.08:
        frame=Image.new("RGB",(W,H), C_BLACK)
        d=ImageDraw.Draw(frame)
        draw_centered(d, int(315), "ARYAN CHAUDHARY EXTRA", F_ANTON_LG, C_GOLD, 6)
        draw_centered(d, int(487), "SAVE THIS VIDEO FOR THE NEXT TIME YOU SAY 'BAS 10 MINUTE'", F_POP_SM, C_WHITE, 0)
        d.rounded_rectangle([390,607,W-390,742], radius=21, fill=C_PANEL, outline=C_CYAN, width=3)
        draw_centered(d, 633, "24x7 Mental Health Support — Tele-MANAS: 14416", F_POP_MD, C_WHITE,0)
        draw_centered(d, 780, "All Official Sources (Reuters, IAMAI, NCCS, PLFS, NCRB, SEBI) Linked in Description", F_POP_XXS, C_MUTED,0)
        # progress bar
        d2=ImageDraw.Draw(frame,"RGBA")
        d2.rectangle([0,0,int(W*(t/TOTAL_SEC)),7], fill=C_GOLD)
        return frame
    # normal rendering
    # handle transition: need both prev and curr frames
    if is_transition:
        # render prev frame's content at its end time (shot end - epsilon) for prev
        # but we can render curr and prev separately and then blend
        # For prev, compute its shot progress at its end (just before transition)
        # prev_t = shot["start"] - 1/FPS (approx end of prev)
        prev_t=prev_shot["end"] - 0.008
        prev_shot_progress=1.0 - 1e-4
        # render prev base
        prev_bg=render_two_layer_parallax(prev_shot["plate"], prev_shot, prev_t, prev_shot_progress)
        prev_bg=add_environmental(prev_bg, prev_shot, prev_t, prev_shot_progress, False)
        # apply film look with prev grade
        prev_bg=apply_film_look(prev_bg, prev_shot["grade"], prev_t, frame_idx-TRANS_FRAMES, False)
        # overlay graphics for prev time? For transition we should not include kinetic captions of both? Simplify: include graphics of current t? But better include prev graphics at prev_t and curr at t and blend?
        # To keep simple, we render both with full graphics at respective times and then transition blend
        # But to avoid double captions, we will render base only and then after transition add current graphics
        # Let's render prev with its graphics
        # we need p_map and active for prev_t
        # find active for prev_t
        prev_active=None
        for p in PLACEMENTS:
            if p["start"] <= prev_t <= p["end"]:
                prev_active=p; break
        prev_bg=overlay_graphics(prev_bg, prev_t, P_MAP, prev_active, prev_shot, SHOTS)

        curr_bg=render_two_layer_parallax(shot["plate"], shot, t, shot_progress)
        curr_bg=add_environmental(curr_bg, shot, t, shot_progress, False)
        curr_bg=apply_film_look(curr_bg, shot["grade"], t, frame_idx, False)
        curr_bg=overlay_graphics(curr_bg, t, P_MAP, active, shot, SHOTS)
        # now transition blend
        blended=apply_transition(prev_bg, curr_bg, shot["trans_type"], trans_progress)
        return blended
    else:
        # single frame
        is_safe = P_MAP["05b_ncrb_telemanas"]["start"]-0.4 <= t < P_MAP["05c_india_2041_window"]["start"]
        base=render_two_layer_parallax(shot["plate"], shot, t, shot_progress)
        base=add_environmental(base, shot, t, shot_progress, is_safe)
        base=apply_film_look(base, shot["grade"], t, frame_idx, is_safe)
        base=overlay_graphics(base, t, P_MAP, active, shot, SHOTS)
        # glitch effect for non-safe close (0.0-0.09 per 8s)
        mod8=t%8.0
        in_close = t >= P_MAP["10b_facecam_close"]["start"]-0.3
        do_glitch = (not is_safe and not in_close and 0.0 <= mod8 <0.09 and int(t//8)%2==1 and t>4.0)
        if do_glitch:
            # RGB split
            r,g,b=base.split()
            r=ImageChops.offset(r,7,0)
            b=ImageChops.offset(b,-7,0)
            base=Image.merge("RGB",(r,g,b))
        # pi zoom pulse 0.22s per 8s
        # we already have parallax zoom, but add extra punch zoom for emphasis
        # if mod8<0.22 and t>1 and not is_safe and not in_close:
        # we could scale up 1.06
        # Instead we already handle via shot zoom, skip
        return base

# Globals for worker
SHOTS=[]
SHOT_STARTS=[]
P_MAP={}
PLACEMENTS=[]
VIGNETTE=make_vignette()

def init_worker(shots, shot_starts, p_map, placements):
    global SHOTS, SHOT_STARTS, P_MAP, PLACEMENTS, VIGNETTE
    SHOTS=shots; SHOT_STARTS=shot_starts; P_MAP=p_map; PLACEMENTS=placements
    # precompute vignette global already
    # also init plate cache clear
    global PLATE_CACHE
    PLATE_CACHE={}

def render_chunk(args):
    start_f, end_f, out_path, shots, shot_starts, p_map, placements = args
    init_worker(shots, shot_starts, p_map, placements)
    tmp_raw="/tmp/raw_{}_{}.rgb".format(start_f,end_f)
    # Use ffmpeg pipe
    cmd=[FFMPEG,"-y","-loglevel","error","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","-",
         "-c:v","libx264","-threads","1","-preset","veryfast","-crf","26","-pix_fmt","yuv420p","-r",str(FPS), out_path]
    proc=subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    for f_idx in range(start_f, end_f):
        #t=f_idx/FPS
        frame=render_frame_wrapper(f_idx)
        proc.stdin.write(frame.tobytes())
        if f_idx % 600 ==0:
            print(f"chunk {start_f}-{end_f} frame {f_idx} ({f_idx-start_f}/{end_f-start_f})", flush=True)
    proc.stdin.close()
    err=proc.stderr.read().decode(errors="ignore")
    ret=proc.wait()
    if ret!=0:
        print(err[-2000:])
        raise RuntimeError(f"ffmpeg chunk {start_f} failed")
    print(f"chunk {start_f}-{end_f} done {os.path.getsize(out_path)/1e6:.2f} MB")
    return out_path

def main():
    global SHOTS, SHOT_STARTS, P_MAP, PLACEMENTS
    os.makedirs("videos",exist_ok=True)
    manifest=json.load(open("videos/timeline_manifest.json","r",encoding="utf-8"))
    placements=manifest["placements"]
    p_map={p["id"]:p for p in placements}
    P_MAP=p_map; PLACEMENTS=placements
    # build shots
    shots=build_shot_schedule(manifest)
    SHOTS=shots
    SHOT_STARTS=[s["start"] for s in shots]
    print(f"Built {len(shots)} shots across {len(placements)} segments")
    for s in shots[:12]:
        print(f" shot {s['id']:02d} {s['seg_id'][:18]:18s} {s['start']:6.2f}-{s['end']:6.2f} {s['duration']:4.2f}s plate={os.path.basename(s['plate'])[:18]} trans={s['trans_type']:4s} env={s['env']}")
    print(f"Total duration check last shot end {shots[-1]['end']:.2f} vs {TOTAL_SEC:.2f}")
    # verify facecam slots: print those
    for s in shots:
        if s["plate"]==FACE_PLATE:
            print(f" FACE shot {s['id']} {s['seg_id']} {s['start']:.2f}-{s['end']:.2f}")

    # chunk rendering
    num_chunks=4  # use 4-8
    # split 36000 frames into num_chunks
    # Ensure chunk boundaries align to ~50 sec each
    chunk_size= TOTAL_FRAMES // num_chunks
    # adjust to not split inside transition? Not needed, transition across chunk boundary would be broken, so avoid splitting inside transition frames
    # We can ensure chunk boundaries are at shot boundaries to avoid transition across chunks
    # Instead of equal split, we split by shot count: distribute shots evenly
    # Simpler: equal frame split but transition handling across chunks will be incorrect for those boundary transitions (rare). Could accept small glitch? Better to split by shots.
    # Let's split by frames but ensure we handle transition by overlapping 8 frames: each chunk renders extra 8 frames before start except first
    # But easier: split by shot boundaries
    # Let's compute chunk boundaries as frame indices where shot starts
    # We'll create chunks based on frame ranges aligned to shot starts
    # Find shot start frames
    shot_start_frames=[int(s["start"]*FPS) for s in shots]
    # create chunks: target chunk_size frames, but snap to nearest shot start
    boundaries=[0]
    for i in range(1,num_chunks):
        target=i*chunk_size
        # find nearest shot start >= target
        cand=[f for f in shot_start_frames if f>=target]
        if cand:
            boundaries.append(min(cand, key=lambda x: abs(x-target)))
        else:
            boundaries.append(target)
    boundaries.append(TOTAL_FRAMES)
    boundaries=sorted(set(boundaries))
    print(f"Chunk boundaries frames: {boundaries}")
    # ensure num_chunks matches len(boundaries)-1
    tasks=[]
    tmp_segments=[]
    for i in range(len(boundaries)-1):
        start_f=boundaries[i]; end_f=boundaries[i+1]
        out_path=f"/tmp/chunk_{i:02d}_{start_f}_{end_f}.mp4"
        tmp_segments.append(out_path)
        tasks.append((start_f,end_f,out_path, shots, [s["start"] for s in shots], p_map, placements))
    print(f"Rendering {len(tasks)} chunks with {multiprocessing.cpu_count()} cores")
    # multiprocessing
    # Use pool
    # For stability, use spawn context
    import multiprocessing as mp
    # Try to render parallel, but if fails fallback to sequential
    t0=time.time()
    with mp.Pool(processes=min(2, len(tasks), mp.cpu_count())) as pool:
        results=pool.map(render_chunk, tasks)
    print(f"All chunks done in {time.time()-t0:.1f}s")
    # concat segments via ffmpeg concat demuxer
    concat_txt="/tmp/concat.txt"
    with open(concat_txt,"w") as f:
        for seg in tmp_segments:
            f.write(f"file '{seg}'\n")
    silent_video="/tmp/video_60fps_noaudio.mp4"
    cmd=[FFMPEG,"-y","-f","concat","-safe","0","-i",concat_txt,"-c","copy", silent_video]
    subprocess.run(cmd, check=True)
    print(f"Concatenated silent video {os.path.getsize(silent_video)/1e6:.2f} MB")
    # mux audio stems
    # Need to mux: silent video + bgm_and_sfx_only_10min.m4a + ai_voiceover_timed_10min.m4a? Actually final master should have both voice and bgm mixed? Original master MP4 audio is mixed voice + bgm. We have stems: bgm_and_sfx_only and ai_voiceover. The original build_audio_master.py mixes them with sidechain. But we have existing stems; we can mux by mixing them via ffmpeg amix
    # The simplest: mux with bgm_and_sfx + voiceover mixed as done in build_audio_master? But we haven't run build_audio_master, we have stems already. We can just mix them with ffmpeg amix and sidechain? Simpler: use same logic as replace_voice but with AI voiceover as input.
    # Let's do sidechain compression similar to replace_voice, but using the existing stems as inputs
    final_mp4="videos/Tum_Hi_Se_Baat_Kar_Raha_Hoon_10min_60FPS_REVIEW.mp4"
    # check durations
    # Use ffmpeg to mux: we have silent video (600s) and two audio stems (both 600s). We will apply sidechain: bgm+voice mix
    # Filter: [1:a][0:a] ??? No, we have video stream plus 2 audio
    # We'll create: voice is ai_voiceover, bed is bgm_sfx
    # Use sidechaincompress: bed ducked by voice, then mix
    cmd=[
        FFMPEG,"-y",
        "-i", silent_video,
        "-i", "videos/audio_stems/ai_voiceover_timed_10min.m4a",
        "-i", "videos/audio_stems/bgm_and_sfx_only_10min.m4a",
        "-filter_complex",
        "[1:a]highpass=f=80,acompressor=threshold=-18dB:ratio=3:attack=10:release=120,volume=1.35,asplit=2[vo][sc];"
        f"[2:a]volume=0:enable='between(t,{p_map['05b_ncrb_telemanas']['start']},{p_map['05b_ncrb_telemanas']['end']})'[safe_bed];"
        "[safe_bed][sc]sidechaincompress=threshold=0.02:ratio=6:attack=25:release=280[ducked_bed];"
        "[vo][ducked_bed]amix=inputs=2:duration=longest:dropout_transition=0,alimiter=limit=0.95[aout]",
        "-map","0:v:0","-map","[aout]",
        "-c:v","copy","-c:a","aac","-b:a","160k","-movflags","+faststart","-shortest","-r",str(FPS),
        final_mp4
    ]
    subprocess.run(cmd, check=True)
    print(f"Final MP4 ready: {final_mp4} {os.path.getsize(final_mp4)/1e6:.2f} MB in {time.time()-t0:.1f}s")
    # cleanup temp chunks
    for seg in tmp_segments:
        try: os.remove(seg)
        except: pass
    try: os.remove(silent_video); os.remove(concat_txt)
    except: pass
    # verify
    subprocess.run([FFMPEG,"-i", final_mp4], stderr=subprocess.STDOUT)
    # extract sample frames for verification
    os.makedirs("/tmp/verify", exist_ok=True)
    # extract at 5 points
    for ts in ["00:00:02","00:02:18","00:05:39","00:07:40","00:09:26"]:
        out=f"/tmp/verify/sample_{ts.replace(':','_')}.jpg"
        subprocess.run([FFMPEG,"-y","-ss",ts,"-i", final_mp4,"-vframes","1","-q:v","2", out], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if os.path.exists(out):
            print(f"sample {ts} -> {out} {os.path.getsize(out)//1024}KB")
    # cleanup
    # Check repo size
    # (will be done outside)

if __name__=="__main__":
    main()
