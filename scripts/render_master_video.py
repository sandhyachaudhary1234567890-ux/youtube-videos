#!/usr/bin/env python3
"""
Fable 5.1 / After-Effects Style Motion-Graphics + Cinematic B-Roll Renderer
Outputs: videos/Tum_Hi_Se_Baat_Kar_Raha_Hoon_10min_MASTER.mp4 (1920x1080, 24fps, 10:00)
"""
import os
import sys
import json
import math
import time
import subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageChops
import imageio_ffmpeg

W, H = 1280, 720
FPS = 24
TOTAL_SEC = 600.0
TOTAL_FRAMES = int(TOTAL_SEC * FPS)
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

C_BLACK = (6, 6, 10)
C_PANEL = (15, 16, 24)
C_WHITE = (248, 249, 252)
C_MUTED = (165, 170, 185)
C_YELLOW = (255, 214, 0)
C_MAGENTA = (255, 30, 138)
C_CYAN = (0, 229, 255)
C_GREEN = (0, 230, 118)
C_RED = (255, 42, 60)
C_GOLD = (255, 184, 48)

F_ANTON_XL = ImageFont.truetype("assets/fonts/Anton-Regular.ttf", 118)
F_ANTON_LG = ImageFont.truetype("assets/fonts/Anton-Regular.ttf", 82)
F_ANTON_MD = ImageFont.truetype("assets/fonts/Anton-Regular.ttf", 54)
F_ANTON_SM = ImageFont.truetype("assets/fonts/Anton-Regular.ttf", 36)

F_POP_MD = ImageFont.truetype("assets/fonts/Poppins-Bold.ttf", 26)
F_POP_SM = ImageFont.truetype("assets/fonts/Poppins-Medium.ttf", 20)
F_POP_XS = ImageFont.truetype("assets/fonts/Poppins-Medium.ttf", 16)


def prep_plate(path: str, scale_pad=1.18, sat=1.0, bright=1.0, contrast=1.08) -> Image.Image:
    im = Image.open(path).convert("RGB")
    tw, th = int(W * scale_pad), int(H * scale_pad)
    s = max(tw / im.width, th / im.height)
    im = im.resize((int(im.width * s), int(im.height * s)), Image.Resampling.BILINEAR)
    ox, oy = (im.width - tw) // 2, (im.height - th) // 2
    im = im.crop((ox, oy, ox + tw, oy + th))
    if sat != 1.0:
        im = ImageEnhance.Color(im).enhance(sat)
    if bright != 1.0:
        im = ImageEnhance.Brightness(im).enhance(bright)
    if contrast != 1.0:
        im = ImageEnhance.Contrast(im).enhance(contrast)
    return im


PLATES = {
    "face_tight": prep_plate("assets/images/facecam_aryan_tight.jpg", 1.26, 1.06, 0.98, 1.12),
    "face_warm": prep_plate("assets/images/facecam_aryan_tight.jpg", 1.14, 1.12, 1.04, 1.08),
    "day_2am": prep_plate("assets/images/seg1_2am_phone_glow.jpg", 1.18, 1.10, 0.82, 1.14),
    "tug_phone": prep_plate("assets/images/seg2_tug_of_war_phone.jpg", 1.18, 1.12, 0.78, 1.14),
    "comp_split": prep_plate("assets/images/seg2_comparison_split.jpg", 1.14, 1.05, 0.84, 1.12),
    "hourglass": prep_plate("assets/images/seg3_hourglass_2_years.jpg", 1.18, 0.88, 0.72, 1.16),
    "india_map": prep_plate("assets/images/seg3_india_window_2041.jpg", 1.18, 1.08, 0.76, 1.14),
    "inf_trap": prep_plate("assets/images/seg4_influencer_trap.jpg", 1.18, 1.10, 0.74, 1.15),
    "foundation": prep_plate("assets/images/seg4_foundation_building.jpg", 1.16, 1.12, 0.80, 1.14),
    "futures_2036": prep_plate("assets/images/seg5_2036_two_futures.jpg", 1.12, 1.08, 0.88, 1.12),
}


def camera_crop(plate: Image.Image, zoom: float = 1.0, pan_x: float = 0.5, pan_y: float = 0.5) -> Image.Image:
    pw, ph = plate.size
    cw = min(pw, max(640, int(W / max(1.0, zoom))))
    ch = min(ph, max(360, int(H / max(1.0, zoom))))
    ox = int((pw - cw) * np.clip(pan_x, 0.0, 1.0))
    oy = int((ph - ch) * np.clip(pan_y, 0.0, 1.0))
    cropped = plate.crop((ox, oy, ox + cw, oy + ch))
    if cw != W or ch != H:
        return cropped.resize((W, H), Image.Resampling.NEAREST if zoom > 1.04 else Image.Resampling.BILINEAR)
    return cropped


def draw_centered(d: ImageDraw.ImageDraw, y: int, text: str, font, fill, stroke_w=4, stroke_fill=(0, 0, 0)):
    bb = d.textbbox((0, 0), text, font=font)
    d.text(((W - (bb[2] - bb[0])) // 2, y), text, font=font, fill=fill, stroke_width=stroke_w, stroke_fill=stroke_fill)


def draw_source_badge(d: ImageDraw.ImageDraw, text: str, accent=C_YELLOW):
    label = f"SOURCE: {text}"
    bb = d.textbbox((0, 0), label, font=F_POP_XS)
    bw = (bb[2] - bb[0]) + 28
    d.rounded_rectangle([36, 28, 36 + bw, 62], radius=8, fill=(10, 11, 18), outline=accent, width=2)
    d.text((50, 35), label, font=F_POP_XS, fill=C_WHITE)


def draw_facecam_badge(d: ImageDraw.ImageDraw, label: str, accent=C_CYAN):
    bb = d.textbbox((0, 0), label, font=F_POP_XS)
    bw = (bb[2] - bb[0]) + 26
    d.rounded_rectangle([W - 36 - bw, 28, W - 36, 60], radius=8, fill=(12, 14, 22), outline=accent, width=2)
    d.text((W - 23 - bw, 34), label, font=F_POP_XS, fill=accent)


SEGMENT_LINES = {
    "01_hook_and_day": (C_MAGENTA, [
        ("HAAN. TUMSE HI", "TUMSE"),
        ("BAAT KAR RAHA HOON.", "BAAT"),
        ("JO PADHAI CHHOD KE", "PADHAI"),
        ("'BAS EK MINUTE' KE LIYE AAYA HAI.", "MINUTE'"),
        ("WAHI EK MINUTE TUMHARE", "TUMHARE"),
        ("DO SAAL KHA JAATA HAI!", "SAAL"),
        ("HISAAB DIKHATA HOON.", "HISAAB"),
        ("AUR AAJ RAAT KA EK KAAM BHI.", "RAAT"),
        ("SUBAH ALARM BAJTA HAI.", "ALARM"),
        ("AANKH KHULNE SE PEHLE PHONE!", "PHONE!"),
        ("PEHLA KAAM: NOTIFICATION CHECK.", "NOTIFICATION"),
        ("NASHTE MEIN REELS.", "REELS."),
        ("KAPDE PEHENTE HUE REELS.", "REELS."),
        ("RASTE MEIN REELS.", "REELS."),
        ("AUR RAAT KO? 'BAS 10 MINUTE.'", "MINUTE.'"),
        ("GHADI MEIN 2 BAJ CHUKE HAIN!", "2"),
        ("KAL TEST HAI...", "TEST"),
        ("WAHI PURANA WADA: 'KAL SE PAKKA.'", "PAKKA.'"),
        ("KITNI BAAR BOLA? 10 BAAR? 100 BAAR?", "100"),
    ]),
    "02_problems_1_to_3": (C_MAGENTA, [
        ("AB WO 5 CHEEZEIN", "5"),
        ("JO TUM KISI KO BATATE NAHI.", "TUM"),
        ("#1: DISCIPLINE KA DHOKHA", "DISCIPLINE"),
        ("PADHNE BAITHTE HO, 3 MIN MEIN PHONE.", "PHONE."),
        ("TUMHE LAGTA HAI DISCIPLINE KAM HAI?", "DISCIPLINE"),
        ("GALAT! DUNIYA KE SABSE MEHNGE DIMAAG", "GALAT!"),
        ("TUMHARE KHILAF LAGE HAIN.", "KHILAF"),
        ("UNKI KAMAAI TAB HOTI HAI", "KAMAAI"),
        ("JAB TUM PHONE NAHI RAKHTE.", "PHONE"),
        ("YE SEEDHI LADAI HAI.", "LADAI"),
        ("#2: COMPARISON KA ZAAHAR", "COMPARISON"),
        ("KISI KA SELECTION. KISI KI GOA STORY.", "GOA"),
        ("AUR TUM? USI KAMRE, USI SYLLABUS MEIN:", "TUM?"),
        ("'MAIN PEECHE REH GAYA.'", "PEECHE"),
        ("UNKA HIGHLIGHT vs TUMHARA BEHIND-THE-SCENES!", "HIGHLIGHT"),
        ("#3: SAVED FOLDER KA NASHA", "SAVED"),
        ("300 REELS SAVED. 40 PDFs. 10 PLAYLISTS.", "300"),
        ("DEKHNE MEIN PRODUCTIVE...", "PRODUCTIVE..."),
        ("ASAL MEIN WAHI PURANA SCROLL.", "SCROLL."),
    ]),
    "03a_problems_4_5": (C_RED, [
        ("#4: SHORTCUT KA JAAL", "SHORTCUT"),
        ("'SIRF 500 KA DAAV. EK PREDICTION.'", "500"),
        ("2025 MEIN ONLINE MONEY GAMES BAN HUE", "BAN"),
        ("KYUNKI GHAR KE GHAR KARZ MEIN DOOB RAHE THE.", "KARZ"),
        ("#5: DARD DABANA", "DARD"),
        ("MOOD KHARAB? PHONE. AKELA? PHONE.", "PHONE."),
        ("PHONE AB TUMHARA ANESTHESIA HAI.", "ANESTHESIA"),
        ("DARD SUNN KARTA HAI, THEEK NAHI KARTA.", "THEEK"),
    ]),
    "03b_facecam_reset": (C_YELLOW, [
        ("RUKO. EK SECOND.", "RUKO."),
        ("YAHAN TAK HAR BAAT SACH LAGI NA?", "SACH"),
        ("AB TAK MAINE SIRF AAINA DIKHAYA HAI.", "AAINA"),
        ("AB ASLI HISAAB DIKHATA HOON. YE KADWA HAI.", "HISAAB"),
    ]),
    "04a_math_build": (C_YELLOW, [
        ("AB SEEDHA HISAAB SUNO.", "HISAAB"),
        ("ROZ ~3.2 GHANTE SOCIAL APPS PAR.", "3.2"),
        ("HUM SIRF 3 GHANTE MAANTE HAIN.", "3"),
        ("3 x 365 = SAAL KE 1,095 GHANTE!", "1,095"),
        ("24 GHANTE SE POORE 45 DIN GAYAB.", "45"),
        ("16 JAAGTE GHANTON SE: SAAL KE 68 DIN!", "68"),
        ("AUR 10 SAAL MEIN? 684 JAAGTE DIN...", "684"),
    ]),
    "04b_2saal_and_surveys": (C_YELLOW, [
        ("LAGBHAG DO SAAL! POORE 2 SAAL!", "2"),
        ("ITNE MEIN EK POORI DEGREE YA TOP SKILL BANTI HAI.", "SKILL"),
        ("SHAHRON KE 18-24 YUVA: ROZ 120+ MIN SOCIAL PAR.", "120+"),
        ("74% STUDENTS: PADHAI KE BAHAR 2+ GHANTE SCREEN.", "74%"),
        ("IIM ROHTAK STUDY: TOTAL SCREEN TIME ~7 GHANTE!", "7"),
        ("ECONOMIC SURVEY MEIN DIGITAL ADDICTION DARJ HUA.", "ADDICTION"),
    ]),
    "05a_jobs_plfs": (C_YELLOW, [
        ("AAGE EK LINE JO KOI INFLUENCER NAHI BOLEGA.", "INFLUENCER"),
        ("PEHLE BAAZAR KA SACH DEKHO.", "SACH"),
        ("PLFS 2025 ANNUAL: 9.9% YUVA BEROZGAARI.", "9.9%"),
        ("TIMAHI BULLETIN MEIN 15% TAK GAYA.", "15%"),
        ("HAR INTERVIEW MEIN EK SAWAAL: TUMHE KAAM KYA AATA HAI?", "KAAM"),
    ]),
    "05b_ncrb_telemanas": (C_WHITE, [
        ("AUR EK INSAANI SACH...", "INSAANI"),
        ("BOJH SIRF PHONE KA NAHI HOTA.", "BOJH"),
        ("EXAM KA DAR, COMPARISON, AKELAPAN.", "AKELAPAN."),
        ("NCRB 2024: 14,488 STUDENTS — 10 SAAL MEIN 80% ZYADA.", "14,488"),
        ("AGAR TUM AISE ANDHERE MEIN HO, VIDEO YAHIN ROKO.", "ROKO."),
        ("14416 PAR TELE-MANAS KO CALL KARO. TUM AKELE NAHI HO.", "14416"),
    ]),
    "05c_india_2041_window": (C_CYAN, [
        ("AB DESH KI GHADI DEKHO.", "DESH"),
        ("BHARAT KI MEDIAN UMR: 29.2 SAAL.", "29.2"),
        ("KAAM KARNE WALI AABADI KA SHIKHAR: 2041 TAK.", "2041"),
        ("TAB TUM 30 SE 40 KE BEECH HOGE.", "TUM"),
        ("YE KHIDKI TUMHARI HAI, ABHI KHULI HAI.", "KHIDKI"),
        ("AB WO HISSA JO KOI INFLUENCER NAHI BATAYEGA!", "INFLUENCER"),
    ]),
    "06a_influencer_lie": (C_MAGENTA, [
        ("AB WO BAAT JO SEEDHI CHUBHEGI.", "CHUBHEGI."),
        ("'30 DIN MEIN LAKHPATI!' 'COLLEGE CHHOD DO!'", "LAKHPATI!'"),
        ("TUM SOCHTE HO: MAIN KITAAB GHIS RAHA HOON?", "KITAAB"),
        ("EK KADWI LINE SUN LO:", "KADWI"),
        ("WAHAN TUM CUSTOMER NAHI HO. TUM MAAL HO!", "MAAL"),
        ("UNKI KAMAAI TUMHARE VIEW, CLICK AUR COURSE SE BANTI HAI.", "COURSE"),
    ]),
    "06b_facecam_trust": (C_GOLD, [
        ("RUKO. MAIN BHI YAHAN VIDEO BANA RAHA HOON.", "RUKO."),
        ("MERI BAAT BHI AANKH BAND KARKE MAT MAANO.", "MAT"),
        ("HAR BOLNE WALE SE EK SAWAAL POOCHHO:", "SAWAAL"),
        ("'TUMHARA PAISA KAHAN SE AATA HAI?'", "PAISA"),
        ("AGAR JAWAB TUMHARA COURSE HAI — KHEL SAMAJH JAO.", "COURSE"),
        ("JO TIKTE HAIN, UNHONE SAALON CHUPCHAAP KAAM GHISA HAI.", "KAAM"),
    ]),
    "07_sebi_and_foundation": (C_CYAN, [
        ("YE HAWA MEIN KAHI BAAT MAT SAMAJHNA.", "MAT"),
        ("SEBI KO KHUD NIYAM BANANA PADA!", "SEBI"),
        ("UNREGISTERED FINFLUENCERS SE DOOR REHNE KA AADESH.", "FINFLUENCERS"),
        ("KAI UNREGISTERED EDUCATORS PAR SEEDHI KAARVAAHI.", "KAARVAAHI."),
        ("SABSE KHATARNAAK JHOOTH: 'PADHAI BEKAAR HAI.'", "JHOOTH:"),
        ("AKELI DEGREE KAAFI NAHI, PAR BINA NEEV IMAARAT KAHAN?", "NEEV"),
        ("PADHAI TUMHARI ZAMEEN HAI. SKILL US PAR BANI IMAARAT!", "IMAARAT!"),
        ("BINA ZAMEEN KE MAHAL SIRF REELS MEIN TIKTA HAI.", "REELS"),
    ]),
    "08a_two_futures_2036": (C_GOLD, [
        ("CHALO SEEDHA 2036 MEIN CHALTE HAIN.", "2036"),
        ("WAHAN DO ALAG TUM KHADE HAIN.", "DO"),
        ("PEHLA TUM: WAHI 3 GHANTE, WAHI 'KAL SE PAKKA'.", "PEHLA"),
        ("30 KI UMR. DOST AAGE, TUM AB BHI STORIES DEKH RAHE HO.", "STORIES"),
        ("DOOSRA TUM: ROZ SIRF 1 GHANTA WAPAS CHHEENA!", "1"),
        ("1 GHANTA x 10 SAAL = 3,650 GHANTE!", "3,650"),
        ("CODING, EDITING, DESIGN, SALES — GEHRAAI SE AA JAATA HAI.", "CODING,"),
        ("WAHI KAMRA, WAHI SHEHER — BAS ROZ EK GHANTA.", "GHANTA."),
    ]),
    "08b_facecam_interrupt": (C_RED, [
        ("EK SECOND! ABHI PHONE CHECK KIYA KYA?", "PHONE"),
        ("WAPAS AAO. YAHAN DEKHO.", "WAPAS"),
    ]),
    "09a_country_365cr": (C_CYAN, [
        ("AB IS HISAAB KO KAMRE SE BAHAR DEKHO.", "BAHAR"),
        ("REUTERS: BHARAT SABSE BADA SOCIAL GROWTH MARKET HAI.", "REUTERS:"),
        ("TECH COMPANIES KO TUMHARA DHYAAN AUR NEEND CHAHIYE.", "DHYAAN"),
        ("TUMHARA WAQT UNKA SABSE BADA KAROBAAR HAI.", "WAQT"),
        ("AGAR 1 KAROD LOG ROZ 1 GHANTA SKILL PAR WAPAS LAAYEIN...", "1"),
        ("EK SAAL MEIN 365 KAROD GHANTE BANTE HAIN!", "365"),
    ]),
    "09b_khara_ganit": (C_YELLOW, [
        ("YE KHARA GANIT HAI.", "GANIT"),
    ]),
    "09c_steps_1_to_3": (C_GREEN, [
        ("AB AAJ RAAT KA KAAM: 5 SEEDHE KADAM!", "5"),
        ("STEP 1: PHONE BISTAR SE DOOR, CHARGER DOOSRE KONE MEIN.", "DOOR,"),
        ("SUBAH KA PEHLA GHANTA BINA PHONE KE.", "BINA"),
        ("STEP 2: SABSE ZYADA TIME WALE 2 APPS PAR LIMIT LAGAO.", "LIMIT"),
        ("FRICTION BADHAO, EXTRA LOCK LAGAO.", "FRICTION"),
        ("STEP 3: ROZ 1 GHANTA DEEP WORK — 50 MIN KAAM, 10 MIN BREAK.", "DEEP"),
    ]),
    "10a_steps_4_5": (C_GREEN, [
        ("STEP 4: PADHAI KE SAATH 90 DIN KE LIYE 1 SKILL CHUNO.", "90"),
        ("HAR HAFTE 1 OUTPUT BANAO: CODE, EDIT, DESIGN, PROJECT.", "OUTPUT"),
        ("DEKHNE SE NAHI, BANANE SE AATA HAI!", "BANANE"),
        ("STEP 5: AISE 2 LOGON KE SAATH RAHO JO KAAM DIKHATE HAIN.", "KAAM"),
        ("PHONE DUSHMAN NAHI HAI — WO SIRF EK AUZAAR HAI.", "AUZAAR"),
        ("YA TUM USE CHALAOGE, YA WO TUMHE CHALAYEGA.", "CHALAOGE,"),
    ]),
    "10b_facecam_close": (C_GOLD, [
        ("YE VIDEO 2 DIN KA JOSH DENE KE LIYE NAHI BANA.", "JOSH"),
        ("JAB AGLI BAAR HAATH BINA SOCHE PHONE UTHAYE...", "PHONE"),
        ("TUMHE YE AWAAZ YAAD AAYE.", "AWAAZ"),
        ("IS VIDEO KO ABHI SAVE KAR LO.", "SAVE"),
        ("JAB BHI 'BAS 10 MINUTE' BOLO, WAPAS DEKHNA.", "WAPAS"),
        ("AB PHONE NEECHE RAKHO. 'KAL SE PAKKA' WALA KAAM AAJ SE!", "AAJ"),
    ]),
    "10c_final_callback": (C_MAGENTA, [
        ("HAAN... TUMSE HI BAAT KAR RAHA THA.", "TUMSE"),
    ]),
}


def draw_caption_bar(d: ImageDraw.ImageDraw, text: str, highlight_word: str, accent_color):
    words = text.split()
    font = F_POP_MD if len(text) <= 44 else F_POP_SM
    space_w = d.textlength(" ", font=font)
    word_widths = [d.textlength(w, font=font) for w in words]
    total_w = sum(word_widths) + space_w * max(0, len(words) - 1)
    y_bar = H - 84
    x0 = int((W - total_w) / 2)
    d.rounded_rectangle([x0 - 24, y_bar - 11, x0 + int(total_w) + 24, y_bar + 45], radius=12, fill=(6, 7, 12), outline=(40, 44, 62), width=2)
    cx = x0
    for w, ww in zip(words, word_widths):
        col = accent_color if (highlight_word and highlight_word in w) else C_WHITE
        d.text((int(cx), y_bar), w, font=font, fill=col, stroke_width=2, stroke_fill=(0, 0, 0))
        cx += ww + space_w


def apply_glitch_rgb(frame: Image.Image, shift_px: int = 7) -> Image.Image:
    r, g, b = frame.split()
    return Image.merge("RGB", (ImageChops.offset(r, shift_px, 0), g, ImageChops.offset(b, -shift_px, 0)))


def render_frame(t: float, p_map: dict, active_seg: dict | None) -> Image.Image:
    if 0.08 <= t < 0.13:
        return Image.new("RGB", (W, H), (255, 255, 255))

    in_telemanas = p_map["05b_ncrb_telemanas"]["start"] - 0.4 <= t < p_map["05c_india_2041_window"]["start"]
    in_close = t >= p_map["10b_facecam_close"]["start"] - 0.3
    mod8 = t % 8.0
    pi_zoom = 1.06 if (not in_telemanas and not in_close and mod8 < 0.22 and t > 1.0) else 1.0
    do_glitch = (not in_telemanas and not in_close and 0.0 <= mod8 < 0.09 and int(t // 8) % 2 == 1 and t > 4.0)

    if t >= p_map["10c_final_callback"]["end"] + 0.08:
        frame = Image.new("RGB", (W, H), C_BLACK)
        d = ImageDraw.Draw(frame)
        draw_centered(d, 210, "ARYAN CHAUDHARY EXTRA", F_ANTON_LG, C_GOLD, 4)
        draw_centered(d, 325, "SAVE THIS VIDEO FOR THE NEXT TIME YOU SAY 'BAS 10 MINUTE'", F_POP_SM, C_WHITE, 0)
        d.rounded_rectangle([260, 405, W - 260, 495], radius=14, fill=C_PANEL, outline=C_CYAN, width=2)
        draw_centered(d, 422, "24x7 Mental Health Support — Tele-MANAS: 14416", F_POP_MD, C_WHITE, 0)
        draw_centered(d, 520, "All Official Sources (Reuters, IAMAI, NCCS, PLFS, NCRB, SEBI) Linked in Description", F_POP_XS, C_MUTED, 0)
        return frame

    if t < 11.2:
        if t < 5.6:
            frame = camera_crop(PLATES["face_tight"], zoom=1.16 * pi_zoom + 0.03 * (t / 5.6), pan_x=0.5, pan_y=0.38)
            d = ImageDraw.Draw(frame)
            draw_facecam_badge(d, "FACE CAM [TIGHT] — REPLACE WITH YOUR TAKE", C_MAGENTA)
            if 0.8 <= t < 3.4:
                draw_centered(d, 78, "TUMSE HI", F_ANTON_XL, C_MAGENTA, 8)
        elif t < 7.7:
            frame = Image.new("RGB", (W, H), C_BLACK)
            d = ImageDraw.Draw(frame)
            px0, py0, px1, py1 = 485, 55, 795, 615
            d.rounded_rectangle([px0, py0, px1, py1], radius=32, fill=(16, 17, 26), outline=C_MAGENTA, width=4)
            scroll_y = int((t * 620) % 220)
            for k in range(-1, 4):
                cy = py0 + 28 + k * 220 - scroll_y
                if py0 + 15 < cy < py1 - 60:
                    col = C_MAGENTA if k % 2 == 0 else C_CYAN
                    d.rounded_rectangle([px0 + 20, cy, px1 - 20, cy + 190], radius=16, fill=(28, 26, 42), outline=col, width=2)
                    d.text((px0 + 42, cy + 72), "REEL #0" + str((int(t * 5) + k) % 9 + 1), font=F_ANTON_MD, fill=col)
            d.text((90, 240), "BAS 1 MINUTE?", font=F_ANTON_LG, fill=C_WHITE, stroke_width=5, stroke_fill=(0, 0, 0))
            d.text((845, 245), "3x SCROLL", font=F_ANTON_LG, fill=C_MAGENTA, stroke_width=5, stroke_fill=(0, 0, 0))
        else:
            frame = camera_crop(PLATES["face_tight"], zoom=1.24 + 0.04 * math.sin(t * 8), pan_x=0.5, pan_y=0.36)
            d = ImageDraw.Draw(frame)
            d.rounded_rectangle([350, 72, W - 350, 245], radius=20, fill=(8, 8, 14), outline=C_YELLOW, width=5)
            draw_centered(d, 85, "2 SAAL!", F_ANTON_XL, C_YELLOW, 8)
        d = ImageDraw.Draw(frame)
        rem = max(0.0, 10.5 - t)
        d.rounded_rectangle([36, 28, 176, 76], radius=10, fill=(12, 12, 18), outline=C_YELLOW, width=2)
        d.text((54, 34), f"00:{int(rem):02d}.{int((rem%1)*10)}", font=F_ANTON_SM, fill=C_YELLOW)

    elif t < p_map["02_problems_1_to_3"]["start"]:
        beat = int((t - 11.2) // 2.8)
        z = (1.03 + 0.06 * (((t - 11.2) % 2.8) / 2.8)) * pi_zoom
        frame = camera_crop(PLATES["day_2am"], zoom=z, pan_x=(0.25 if beat % 2 == 0 else 0.75), pan_y=0.45)
        d = ImageDraw.Draw(frame)
        if t < 18.0:
            d.rounded_rectangle([76, 85, 520, 205], radius=16, fill=(14, 12, 24), outline=C_RED, width=3)
            d.text((104, 102), "06:30 AM — ALARM", font=F_ANTON_MD, fill=C_RED)
            d.text((104, 162), "PEHLA KAAM: PHONE CHECK", font=F_POP_SM, fill=C_WHITE)
        elif t < 27.5:
            tags = ["NASHTE MEIN: REELS", "KAPDE PEHENTE: REELS", "RASTE MEIN: REELS"]
            for k in range(min(3, int((t - 18.0) / 3.1) + 1)):
                yy = 82 + k * 82
                col = [C_YELLOW, C_MAGENTA, C_CYAN][k]
                d.rounded_rectangle([74, yy, 580, yy + 66], radius=12, fill=(12, 13, 22), outline=col, width=3)
                d.text((98, yy + 14), tags[k], font=F_POP_MD, fill=col)
        elif t < 34.4:
            d.rounded_rectangle([790, 80, 1200, 275], radius=20, fill=(10, 10, 18), outline=C_MAGENTA, width=4)
            d.text((832, 96), "02:00 AM", font=F_ANTON_LG, fill=C_MAGENTA)
            d.text((835, 198), "KAL TEST HAI...", font=F_POP_MD, fill=C_RED)
        else:
            mult = int(min(1000, 10 ** (1.0 + 2.0 * min(1.0, (t - 34.4) / 5.0))))
            d.rounded_rectangle([290, 130, W - 290, 395], radius=24, fill=(10, 10, 16), outline=C_RED, width=5)
            draw_centered(d, 148, "KAL SE PAKKA", F_ANTON_LG, C_WHITE, 6)
            draw_centered(d, 255, f"x{mult}?", F_ANTON_XL, C_YELLOW, 6)

    elif t < p_map["03b_facecam_reset"]["start"] - 0.3:
        s2_t = t - p_map["02_problems_1_to_3"]["start"]
        s3a_start = p_map["03a_problems_4_5"]["start"]
        if t < p_map["02_problems_1_to_3"]["start"] + 4.2:
            frame = Image.new("RGB", (W, H), C_BLACK)
            d = ImageDraw.Draw(frame)
            draw_centered(d, 205, "5 CHEEZEIN", F_ANTON_XL, C_YELLOW, 8)
            draw_centered(d, 360, "JO TUM KISI KO BATATE NAHI", F_ANTON_MD, C_MAGENTA, 4)
        elif s2_t < 28.6:
            frame = camera_crop(PLATES["tug_phone"], zoom=(1.04 + 0.05 * (int(s2_t // 3.4) % 2)) * pi_zoom, pan_x=0.5, pan_y=0.45)
            d = ImageDraw.Draw(frame)
            d.rounded_rectangle([42, 34, 470, 112], radius=12, fill=C_BLACK, outline=C_YELLOW, width=3)
            d.text((64, 44), "PROBLEM 01  |  DISCIPLINE", font=F_ANTON_MD, fill=C_YELLOW)
            pull = 0.62 + 0.14 * math.sin(t * 2.6)
            d.rounded_rectangle([320, 520, 960, 566], radius=12, fill=(15, 15, 22), outline=C_WHITE, width=2)
            split_x = int(320 + 640 * (1.0 - pull))
            d.rounded_rectangle([324, 524, split_x, 562], radius=8, fill=C_CYAN)
            d.rounded_rectangle([split_x, 524, 956, 562], radius=8, fill=C_MAGENTA)
            d.text((330, 492), "TUMHARA FOCUS", font=F_POP_XS, fill=C_CYAN)
            d.text((715, 492), "BILLION-$ ALGORITHMS", font=F_POP_XS, fill=C_MAGENTA)
        elif s2_t < 48.4:
            frame = camera_crop(PLATES["comp_split"], zoom=(1.02 + 0.06 * (int(s2_t // 3.2) % 2)) * pi_zoom, pan_x=0.5, pan_y=0.5)
            d = ImageDraw.Draw(frame)
            d.line([(W // 2, 0), (W // 2, H - 100)], fill=C_YELLOW, width=5)
            d.rounded_rectangle([42, 34, 495, 112], radius=12, fill=C_BLACK, outline=C_YELLOW, width=3)
            d.text((64, 44), "PROBLEM 02  |  COMPARISON", font=F_ANTON_MD, fill=C_YELLOW)
            d.rounded_rectangle([90, 515, 535, 568], radius=10, fill=C_BLACK, outline=C_MAGENTA, width=2)
            d.text((115, 526), "UNKA HIGHLIGHT REEL", font=F_POP_MD, fill=C_MAGENTA)
            d.rounded_rectangle([715, 515, 1210, 568], radius=10, fill=C_BLACK, outline=C_CYAN, width=2)
            d.text((738, 526), "TUMHARA BEHIND-THE-SCENES", font=F_POP_MD, fill=C_CYAN)
        elif t < s3a_start:
            frame = Image.new("RGB", (W, H), C_BLACK)
            d = ImageDraw.Draw(frame)
            d.rounded_rectangle([42, 34, 455, 112], radius=12, fill=C_PANEL, outline=C_YELLOW, width=3)
            d.text((64, 44), "PROBLEM 03  |  SAVED", font=F_ANTON_MD, fill=C_YELLOW)
            p_prog = min(1.0, max(0.0, (t - (p_map["02_problems_1_to_3"]["start"] + 48.4)) / 7.5))
            for title, val, col, cx in [("SAVED REELS", int(300 * p_prog), C_MAGENTA, 130), ("UNREAD PDFs", int(40 * p_prog), C_YELLOW, 500), ("PLAYLISTS", int(10 * p_prog), C_CYAN, 870)]:
                d.rounded_rectangle([cx, 185, cx + 310, 455], radius=20, fill=C_PANEL, outline=col, width=4)
                d.text((cx + 42, 210), f"{val}+", font=F_ANTON_XL, fill=col)
                d.text((cx + 42, 378), title, font=F_POP_MD, fill=C_WHITE)
            draw_centered(d, 490, "FAKE PRODUCTIVITY  =  ZERO EXECUTION", F_ANTON_MD, C_RED, 3)
        elif t < s3a_start + 15.5:
            frame = Image.new("RGB", (W, H), C_BLACK)
            d = ImageDraw.Draw(frame)
            draw_source_badge(d, "Promotion & Regulation of Online Gaming Act, 2025 (PIB)", C_YELLOW)
            d.rounded_rectangle([42, 80, 495, 156], radius=12, fill=C_PANEL, outline=C_YELLOW, width=3)
            d.text((64, 90), "PROBLEM 04  |  SHORTCUT", font=F_ANTON_MD, fill=C_YELLOW)
            d.rounded_rectangle([220, 215, W - 220, 475], radius=24, fill=(24, 10, 16), outline=C_RED, width=5)
            draw_centered(d, 238, "ONLINE REAL-MONEY GAMES", F_ANTON_LG, C_WHITE, 5)
            draw_centered(d, 355, "BANNED IN 2025 — ADDICTION & DEBT", F_ANTON_MD, C_RED, 4)
        else:
            frame = Image.new("RGB", (W, H), C_BLACK)
            d = ImageDraw.Draw(frame)
            d.rounded_rectangle([42, 34, 520, 112], radius=12, fill=C_PANEL, outline=C_YELLOW, width=3)
            d.text((64, 44), "PROBLEM 05  |  ANESTHESIA", font=F_ANTON_MD, fill=C_YELLOW)
            local = t - (s3a_start + 15.5)
            flat = min(1.0, max(0.0, (local - 5.5) / 5.0))
            pts = []
            for x in range(100, W - 100, 6):
                ph = (x * 0.045 - local * 7.0) % (2 * math.pi)
                spike = (math.exp(-((ph - 3.0) ** 2) * 18.0) * 115 - math.exp(-((ph - 3.35) ** 2) * 28.0) * 65) * (1.0 - flat)
                pts.append((x, int(335 - spike)))
            d.line(pts, fill=C_RED if flat > 0.6 else C_MAGENTA, width=5)
            draw_centered(d, 465, "DARD SUNN KARTA HAI  —  THEEK NAHI KARTA", F_ANTON_MD, C_WHITE, 3)

    elif t < p_map["04a_math_build"]["start"] - 0.2:
        frame = camera_crop(PLATES["face_warm"], zoom=1.03, pan_x=0.5, pan_y=0.45)
        d = ImageDraw.Draw(frame)
        draw_facecam_badge(d, "FACE CAM [MEDIUM-WIDE] — WARM LIGHT RESET", C_GOLD)
        d.rounded_rectangle([42, 505, 540, 568], radius=12, fill=C_YELLOW, outline=C_BLACK, width=3)
        d.text((66, 517), "YE WAALA HISSA SAVE KARNA", font=F_POP_MD, fill=C_BLACK)

    elif t < p_map["05a_jobs_plfs"]["start"] - 0.2:
        s4a = p_map["04a_math_build"]
        s4b = p_map["04b_2saal_and_surveys"]
        if t < s4a["end"]:
            lt = t - s4a["start"]
            frame = camera_crop(PLATES["hourglass"], zoom=(1.04 + 0.03 * math.sin(lt)) * pi_zoom, pan_x=0.5, pan_y=0.5)
            d = ImageDraw.Draw(frame)
            draw_source_badge(d, "Esya Centre (2023) via Reuters Factbox, Jan 2026", C_YELLOW)
            if lt < 9.5:
                d.rounded_rectangle([70, 150, 620, 445], radius=22, fill=(10, 10, 16), outline=C_YELLOW, width=4)
                d.text((105, 172), "3.2 HRS / DAY", font=F_ANTON_XL, fill=C_YELLOW)
                d.text((108, 342), "SOCIAL NETWORKING APPS", font=F_POP_MD, fill=C_WHITE)
            elif lt < 15.2:
                hrs = int(min(1095, 1095 * ((lt - 9.5) / 2.2)))
                d.rounded_rectangle([70, 150, 650, 468], radius=22, fill=(10, 10, 16), outline=C_YELLOW, width=4)
                d.text((102, 168), "3h x 365 DAYS =", font=F_ANTON_MD, fill=C_WHITE)
                d.text((102, 240), f"{hrs:,} HRS", font=F_ANTON_XL, fill=C_YELLOW)
                d.text((105, 400), "HAR EK SAAL!", font=F_POP_MD, fill=C_RED)
            else:
                d.rounded_rectangle([65, 110, 665, 535], radius=22, fill=(10, 10, 16), outline=C_RED, width=4)
                lit_tiles = int(min(45, ((lt - 15.2) / 3.5) * 45))
                for idx in range(45):
                    r, c = divmod(idx, 9)
                    tx, ty = 95 + c * 60, 138 + r * 46
                    d.rounded_rectangle([tx, ty, tx + 50, ty + 36], radius=6, fill=C_RED if idx < lit_tiles else (35, 36, 48))
                if lt < 20.0:
                    d.text((95, 395), "45 FULL DAYS / YEAR (68 WAKING DAYS)", font=F_ANTON_SM, fill=C_YELLOW)
                else:
                    d.text((95, 385), "10 SAAL = 684 WAKING DAYS", font=F_ANTON_MD, fill=C_YELLOW)
                    d.text((95, 460), "1.9 YEARS OF WAKING LIFE", font=F_POP_MD, fill=C_RED)
        elif t < s4b["start"]:
            frame = Image.new("RGB", (W, H), C_BLACK)
            d = ImageDraw.Draw(frame)
            draw_centered(d, 305, "684 JAAGTE DIN  =", F_ANTON_LG, C_MUTED, 0)
        elif t < s4b["start"] + 10.5:
            frame = camera_crop(PLATES["hourglass"], zoom=1.16 * pi_zoom, pan_x=0.5, pan_y=0.45)
            d = ImageDraw.Draw(frame)
            draw_source_badge(d, "Checked Math: 3h x 365 x 10 = 10,950h (~684 Waking Days / 1.9 Yrs)", C_YELLOW)
            d.rounded_rectangle([290, 145, W - 290, 445], radius=28, fill=(10, 8, 14), outline=C_YELLOW, width=6)
            draw_centered(d, 165, "DO SAAL!", F_ANTON_XL, C_YELLOW, 8)
            draw_centered(d, 330, "EK POORI DEGREE YA TOP SKILL KA WAQT", F_POP_MD, C_RED, 2)
        else:
            lt = t - (s4b["start"] + 10.5)
            frame = Image.new("RGB", (W, H), C_BLACK)
            d = ImageDraw.Draw(frame)
            active_idx = 0 if lt < 10.5 else (1 if lt < 20.0 else 2)
            src = ["IAMAI-VTION Report (June 2026)", "NCCS Survey via ORF (April 2026)", "IIM Rohtak Study & Economic Survey 2025-26"][active_idx]
            draw_source_badge(d, src, C_YELLOW)
            draw_centered(d, 92, "SCREEN TIME REALITY ACROSS INDIA", F_ANTON_LG, C_WHITE, 4)
            d.rounded_rectangle([140, 235, W - 140, 290], radius=16, fill=C_PANEL, outline=C_MUTED, width=2)
            fill_w = int((W - 288) * [0.38, 0.68, 1.0][active_idx])
            d.rounded_rectangle([144, 239, 144 + fill_w, 286], radius=12, fill=[C_MAGENTA, C_YELLOW, C_RED][active_idx])
            rows = [
                ("120+ MIN / DAY", "Urban Age 18-24 on Social Media (vs 97.9m avg) — IAMAI-VTION", C_MAGENTA),
                ("74% > 2 HRS  |  21% > 4 HRS", "Students Non-Academic Screen Time — NCCS via ORF", C_YELLOW),
                ("6h 45m (M) / 7h 05m (F)", "Total Daily Screen Time — IIM Rohtak + Economic Survey 2025-26", C_RED),
            ]
            for i, (stat, desc, col) in enumerate(rows):
                yy = 330 + i * 78
                hi = i <= active_idx
                d.rounded_rectangle([140, yy, W - 140, yy + 64], radius=12, fill=C_PANEL if hi else (10, 10, 14), outline=col if hi else (35, 35, 45), width=3 if i == active_idx else 1)
                d.text((168, yy + 14), stat, font=F_POP_MD, fill=col if hi else C_MUTED)
                d.text((535, yy + 19), desc, font=F_POP_SM, fill=C_WHITE if hi else C_MUTED)

    elif t < p_map["05b_ncrb_telemanas"]["start"] - 0.2:
        lt = t - p_map["05a_jobs_plfs"]["start"]
        frame = Image.new("RGB", (W, H), C_BLACK)
        d = ImageDraw.Draw(frame)
        show_q = lt >= 11.5
        draw_source_badge(d, "PLFS Quarterly Bulletin (15%)" if show_q else "PLFS 2025 Annual (Govt Reply, 27 Jul 2026 — 9.9%)", C_YELLOW)
        draw_centered(d, 86, "YOUTH UNEMPLOYMENT (AGE 15-29)", F_ANTON_LG, C_WHITE, 4)
        for k in range(10):
            cx, cy = 115 + k * 106, 215
            col = C_RED if ((k == 0) or (show_q and k == 1)) else C_CYAN
            d.ellipse([cx + 24, cy, cx + 68, cy + 44], fill=col)
            d.rounded_rectangle([cx + 14, cy + 52, cx + 78, cy + 145], radius=14, fill=col)
        d.rounded_rectangle([140, 405, 615, 522], radius=16, fill=C_PANEL, outline=C_YELLOW, width=3)
        d.text((168, 416), "9.9% ANNUAL", font=F_ANTON_MD, fill=C_YELLOW)
        d.text((168, 485), "PLFS 2025 Annual Report", font=F_POP_XS, fill=C_WHITE)
        d.rounded_rectangle([665, 405, 1140, 522], radius=16, fill=C_PANEL, outline=C_RED if show_q else C_MUTED, width=3)
        d.text((693, 416), "15.0% QUARTERLY", font=F_ANTON_MD, fill=C_RED if show_q else C_MUTED)
        d.text((693, 485), "Recent PLFS Quarterly Bulletin", font=F_POP_XS, fill=C_WHITE if show_q else C_MUTED)

    elif t < p_map["05c_india_2041_window"]["start"]:
        frame = Image.new("RGB", (W, H), (8, 8, 12))
        d = ImageDraw.Draw(frame)
        d.ellipse([490, 90, 790, 390], fill=(26, 20, 14))
        draw_source_badge(d, "NCRB 2024 Report (14,488 Student Deaths; 8,068 in 2014)", C_GOLD)
        draw_centered(d, 132, "TUM AKELE NAHI HO.", F_ANTON_LG, C_GOLD, 3)
        draw_centered(d, 245, "NCRB 2024: 14,488 Students  (Up ~80% Since 2014)", F_POP_MD, C_WHITE, 0)
        d.rounded_rectangle([120, 318, W - 120, 514], radius=20, fill=(16, 18, 26), outline=C_GOLD, width=4)
        draw_centered(d, 336, "Tele-MANAS Helpline:  14416", F_ANTON_LG, C_WHITE, 2)
        draw_centered(d, 458, "Free, Confidential 24x7 Mental Health Support Across India", F_POP_SM, C_GOLD, 0)

    elif t < p_map["06a_influencer_lie"]["start"] - 0.2:
        lt = t - p_map["05c_india_2041_window"]["start"]
        frame = camera_crop(PLATES["india_map"], zoom=(1.03 + 0.05 * min(1.0, lt / 24.0)) * pi_zoom, pan_x=0.5, pan_y=0.5)
        d = ImageDraw.Draw(frame)
        draw_source_badge(d, "India Demographics Projections (Median Age 29.2; Peak ~2041)", C_CYAN)
        d.rounded_rectangle([70, 92, 540, 232], radius=18, fill=(8, 12, 20), outline=C_CYAN, width=3)
        d.text((98, 106), "MEDIAN AGE: 29.2", font=F_ANTON_MD, fill=C_CYAN)
        d.text((98, 178), "WORKING-AGE PEAK: ~2041", font=F_POP_SM, fill=C_YELLOW)
        close_pct = min(0.82, max(0.0, (lt - 6.0) / 16.0))
        d.rounded_rectangle([140, 480, W - 140, 542], radius=14, fill=(10, 12, 18), outline=C_CYAN, width=3)
        open_w = int((W - 288) * (1.0 - close_pct * 0.65))
        d.rounded_rectangle([144, 484, 144 + open_w, 538], radius=10, fill=C_CYAN)
        d.text((160, 495), "2026 (TUM: 15-25)", font=F_POP_SM, fill=C_BLACK)
        d.text((870, 495), "2041 WINDOW CLOSING", font=F_POP_SM, fill=C_RED)

    elif t < p_map["06b_facecam_trust"]["start"] - 0.2:
        lt = t - p_map["06a_influencer_lie"]["start"]
        frame = camera_crop(PLATES["inf_trap"], zoom=(1.04 + 0.05 * ((int(lt // 3.5)) % 2)) * pi_zoom, pan_x=0.5, pan_y=0.5)
        d = ImageDraw.Draw(frame)
        if lt < 17.0:
            d.rounded_rectangle([260, 95, W - 260, 268], radius=18, fill=(20, 10, 24), outline=C_MAGENTA, width=4)
            draw_centered(d, 110, "\"30 DIN MEIN LAKHPATI!\"", F_ANTON_LG, C_YELLOW, 5)
            draw_centered(d, 212, "\"COLLEGE CHHOD DO  •  SECRET PASSIVE INCOME\"", F_POP_SM, C_MAGENTA, 0)
            if lt > 5.0:
                d.line([(620, 95), (655, 180), (610, 268)], fill=C_RED, width=6)
        else:
            d.rounded_rectangle([270, 95, W - 270, 265], radius=22, fill=(12, 8, 14), outline=C_RED, width=5)
            draw_centered(d, 112, "TUM MAAL HO.", F_ANTON_XL, C_RED, 8)
            for lbl, tx in [("VIEWS", 230), ("AFFILIATE CLICKS", 500), ("COURSE SALE", 855)]:
                d.rounded_rectangle([tx, 495, tx + 235, 555], radius=12, fill=C_BLACK, outline=C_MAGENTA, width=3)
                d.text((tx + 24, 510), lbl, font=F_POP_SM, fill=C_MAGENTA)

    elif t < p_map["07_sebi_and_foundation"]["start"] - 0.2:
        frame = camera_crop(PLATES["face_warm"], zoom=1.10 * pi_zoom, pan_x=0.5, pan_y=0.40)
        d = ImageDraw.Draw(frame)
        draw_facecam_badge(d, "FACE CAM [MEDIUM] — CREATOR TRUST BEAT", C_GOLD)
        d.rounded_rectangle([54, 498, 725, 562], radius=12, fill=C_BLACK, outline=C_GOLD, width=3)
        d.text((76, 512), "SAWAAL POOCHHO: 'PAISA KAHAN SE AATA HAI?'", font=F_POP_MD, fill=C_GOLD)

    elif t < p_map["08a_two_futures_2036"]["start"] - 0.2:
        lt = t - p_map["07_sebi_and_foundation"]["start"]
        if lt < 24.0:
            frame = Image.new("RGB", (W, H), C_BLACK)
            d = ImageDraw.Draw(frame)
            draw_source_badge(d, "SEBI Finfluencer Regulations & Enforcement Orders", C_CYAN)
            d.rounded_rectangle([180, 150, W - 180, 480], radius=24, fill=C_PANEL, outline=C_CYAN, width=4)
            draw_centered(d, 178, "SEBI REGULATORY ACTION", F_ANTON_LG, C_CYAN, 5)
            draw_centered(d, 300, "• Regulated Entities Barred From Unregistered Finfluencers", F_POP_MD, C_WHITE, 0)
            draw_centered(d, 365, "• Orders Issued Against Unregistered Market Educators", F_POP_MD, C_YELLOW, 0)
        else:
            frame = camera_crop(PLATES["foundation"], zoom=(1.02 + 0.05 * ((int(lt // 3.5)) % 2)) * pi_zoom, pan_x=0.5, pan_y=0.5)
            d = ImageDraw.Draw(frame)
            d.rounded_rectangle([95, 492, 560, 560], radius=12, fill=C_BLACK, outline=C_CYAN, width=3)
            d.text((120, 508), "PADHAI = ZAMEEN  |  SKILL = IMAARAT", font=F_POP_SM, fill=C_CYAN)
            d.rounded_rectangle([710, 492, 1185, 560], radius=12, fill=C_BLACK, outline=C_RED, width=3)
            d.text((738, 508), "NO FOUNDATION = SIRF REELS MEIN", font=F_POP_SM, fill=C_RED)

    elif t < p_map["08b_facecam_interrupt"]["start"] - 0.15:
        lt = t - p_map["08a_two_futures_2036"]["start"]
        frame = camera_crop(PLATES["futures_2036"], zoom=(1.02 + 0.04 * math.sin(lt * 0.4)) * pi_zoom, pan_x=0.5, pan_y=0.5)
        d = ImageDraw.Draw(frame)
        d.line([(W // 2, 0), (W // 2, H - 96)], fill=C_GOLD, width=4)
        d.rounded_rectangle([38, 34, 602, 118], radius=14, fill=C_BLACK, outline=C_MAGENTA, width=3)
        d.text((62, 46), "2036 (A): WAHI 3 GHANTE", font=F_ANTON_MD, fill=C_MAGENTA)
        d.rounded_rectangle([678, 34, 1242, 118], radius=14, fill=C_BLACK, outline=C_GOLD, width=3)
        d.text((702, 46), "2036 (B): ROZ +1 GHANTA", font=F_ANTON_MD, fill=C_GOLD)
        if lt >= 23.0:
            hrs = int(min(3650, 3650 * ((lt - 23.0) / 4.5)))
            d.rounded_rectangle([715, 412, 1220, 572], radius=18, fill=(12, 12, 18), outline=C_GOLD, width=4)
            d.text((752, 420), f"{hrs:,} HRS", font=F_ANTON_LG, fill=C_GOLD)
            d.text((752, 536), "1h x 365 x 10 YEARS  [CHECKED MATH]", font=F_POP_XS, fill=C_WHITE)

    elif t < p_map["09a_country_365cr"]["start"] - 0.15:
        frame = camera_crop(PLATES["face_tight"], zoom=1.24, pan_x=0.5, pan_y=0.35)
        d = ImageDraw.Draw(frame)
        draw_facecam_badge(d, "FACE CAM [6s INTERRUPT] — ULTRA TIGHT", C_RED)
        d.rounded_rectangle([310, 72, W - 310, 174], radius=16, fill=C_BLACK, outline=C_RED, width=4)
        draw_centered(d, 84, "PHONE CHECK KIYA?", F_ANTON_LG, C_RED, 5)

    elif t < p_map["09c_steps_1_to_3"]["start"] - 0.2:
        s9a = p_map["09a_country_365cr"]
        s9b = p_map["09b_khara_ganit"]
        if t < s9a["end"]:
            lt = t - s9a["start"]
            frame = camera_crop(PLATES["india_map"], zoom=(1.05 + 0.06 * (lt / 31.0)) * pi_zoom, pan_x=0.5, pan_y=0.48)
            d = ImageDraw.Draw(frame)
            draw_source_badge(d, "Reuters Factbox (Jan 2026) & Checked Math: 1 Cr x 1h x 365", C_CYAN)
            if lt < 17.5:
                d.rounded_rectangle([74, 105, 680, 255], radius=18, fill=(8, 12, 20), outline=C_CYAN, width=3)
                d.text((102, 122), "CRITICAL GROWTH MARKET", font=F_ANTON_MD, fill=C_CYAN)
                d.text((102, 195), "TUMHARA DHYAAN = UNKA PRODUCT", font=F_POP_MD, fill=C_MAGENTA)
            else:
                cr = int(min(365, 365 * ((lt - 17.5) / 7.0)))
                d.rounded_rectangle([185, 145, W - 185, 452], radius=24, fill=(10, 12, 18), outline=C_GOLD, width=5)
                draw_centered(d, 165, f"{cr} CRORE HRS", F_ANTON_XL, C_GOLD, 8)
                draw_centered(d, 342, "1 CRORE PEOPLE  x  1 HOUR  x  365 DAYS", F_POP_MD, C_CYAN, 0)
        elif t < s9b["start"]:
            frame = Image.new("RGB", (W, H), C_BLACK)
            d = ImageDraw.Draw(frame)
            draw_centered(d, 285, "365,00,00,000 GHANTE.", F_ANTON_LG, C_GOLD, 4)
        else:
            frame = Image.new("RGB", (W, H), C_BLACK)
            d = ImageDraw.Draw(frame)
            draw_centered(d, 255, "YE KHARA GANIT HAI.", F_ANTON_XL, C_YELLOW, 8)

    elif t < p_map["10b_facecam_close"]["start"] - 0.2:
        s9c = p_map["09c_steps_1_to_3"]["start"]
        s10a = p_map["10a_steps_4_5"]["start"]
        frame = Image.new("RGB", (W, H), C_BLACK)
        d = ImageDraw.Draw(frame)
        if t < s9c + 4.2:
            draw_centered(d, 205, "AAJ RAAT SE", F_ANTON_XL, C_GREEN, 8)
            draw_centered(d, 360, "PAANCH SEEDHE KADAM", F_ANTON_LG, C_WHITE, 4)
        else:
            if t < s9c + 14.0:
                idx, tag, sub, prog = 1, "DOOR RAKHO", "Charger Kamre Ke Doosre Kone Mein • Pehla 1 Ghanta No Phone", (t - (s9c + 4.2)) / 9.5
            elif t < s9c + 22.5:
                idx, tag, sub, prog = 2, "LIMIT LAGAO", "Top 2 Time-Sink Apps Par Friction & Extra Lock Lagao", (t - (s9c + 14.0)) / 8.2
            elif t < s10a:
                idx, tag, sub, prog = 3, "DEEP WORK", "Roz 1 Ghanta: 50 Min Focus + 10 Min Break (Phone Bahar)", (t - (s9c + 22.5)) / 8.0
            elif t < s10a + 13.0:
                idx, tag, sub, prog = 4, "90 DIN SKILL", "Padhai Ke Saath 1 Skill • Har Hafte 1 Real Output Banao", (t - s10a) / 12.5
            else:
                idx, tag, sub, prog = 5, "SAHI LOG", "2 Kaam Karne Wale Log Chuno • Phone Ek Auzaar Hai!", (t - (s10a + 13.0)) / 14.0
            accent = C_GOLD if idx == 5 else C_GREEN
            prog = float(np.clip(prog, 0.0, 1.0))
            for k in range(1, 6):
                bx = 165 + (k - 1) * 195
                done = k <= idx
                d.rounded_rectangle([bx, 58, bx + 170, 114], radius=12, fill=accent if k == idx else C_PANEL, outline=accent if done else (45, 48, 60), width=3)
                d.text((bx + 42, 68), f"STEP 0{k}", font=F_POP_MD, fill=C_BLACK if k == idx else (accent if done else C_MUTED))
            d.rounded_rectangle([165, 155, W - 165, 495], radius=26, fill=C_PANEL, outline=accent, width=4)
            d.text((215, 185), f"0{idx}  |  {tag}", font=F_ANTON_XL, fill=accent)
            d.text((218, 342), sub, font=F_POP_MD, fill=C_WHITE)
            d.rounded_rectangle([215, 415, W - 215, 452], radius=10, fill=(8, 10, 16), outline=accent, width=2)
            fw = int((W - 438) * prog)
            if fw > 8:
                d.rounded_rectangle([219, 419, 219 + fw, 448], radius=7, fill=accent)

    else:
        s_close = p_map["10b_facecam_close"]
        s_cb = p_map["10c_final_callback"]
        if s_close["end"] < t < s_cb["start"]:
            frame = camera_crop(PLATES["face_warm"], zoom=1.22, pan_x=0.5, pan_y=0.36)
        else:
            z = 1.18 + 0.04 * min(1.0, max(0.0, (t - s_close["start"]) / 28.0))
            frame = camera_crop(PLATES["face_warm"], zoom=z, pan_x=0.5, pan_y=0.37)
            d = ImageDraw.Draw(frame)
            draw_facecam_badge(d, "FACE CAM [TIGHT] — QUIET CLOSE & LOOP", C_GOLD)
            if t >= s_cb["start"]:
                draw_centered(d, 82, "TUMSE HI.", F_ANTON_XL, C_MAGENTA, 8)

    d = ImageDraw.Draw(frame)
    bar_col = C_GOLD if in_close else (C_GREEN if t >= p_map["09c_steps_1_to_3"]["start"] else C_YELLOW)
    d.rectangle([0, 0, int(W * (t / TOTAL_SEC)), 5], fill=bar_col)

    if active_seg is not None and active_seg["id"] in SEGMENT_LINES:
        accent, lines = SEGMENT_LINES[active_seg["id"]]
        rel = (t - active_seg["start"]) / max(0.05, active_seg["duration"])
        txt, hl = lines[min(len(lines) - 1, max(0, int(rel * len(lines))))]
        draw_caption_bar(d, txt, hl, accent)

    return apply_glitch_rgb(frame, 7) if do_glitch else frame


def main():
    os.makedirs("videos", exist_ok=True)
    manifest = json.load(open("videos/timeline_manifest.json", "r", encoding="utf-8"))
    placements = manifest["placements"]
    p_map = {p["id"]: p for p in placements}

    start_f = int(sys.argv[1]) if len(sys.argv) >= 4 else 0
    end_f = int(sys.argv[2]) if len(sys.argv) >= 4 else TOTAL_FRAMES
    out_mp4 = sys.argv[3] if len(sys.argv) >= 4 else "videos/Tum_Hi_Se_Baat_Kar_Raha_Hoon_10min_MASTER.mp4"

    cmd = [
        FFMPEG, "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-vf", "scale=1920:1080:flags=bicubic",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "25", "-pix_fmt", "yuv420p",
        out_mp4,
    ]

    t0 = time.time()
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    seg_idx, n_segs = 0, len(placements)

    for f_idx in range(start_f, end_f):
        t = f_idx / FPS
        while seg_idx < n_segs and placements[seg_idx]["end"] < t:
            seg_idx += 1
        active = placements[seg_idx] if (seg_idx < n_segs and placements[seg_idx]["start"] <= t <= placements[seg_idx]["end"]) else None
        proc.stdin.write(render_frame(t, p_map, active).tobytes())

    proc.stdin.close()
    err = proc.stderr.read().decode("utf-8", errors="ignore")
    if proc.wait() != 0:
        raise RuntimeError(err[-1200:])
    print(f"Rendered {out_mp4} ({os.path.getsize(out_mp4)/1e6:.1f} MB) in {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()
