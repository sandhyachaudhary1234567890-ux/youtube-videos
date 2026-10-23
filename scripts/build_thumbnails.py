#!/usr/bin/env python3
import os
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter

os.makedirs("thumbnails", exist_ok=True)
W, H = 1920, 1080
FONT_ANTON = "assets/fonts/Anton-Regular.ttf"
FONT_POPPINS = "assets/fonts/Poppins-Bold.ttf"


def fit_cover(im: Image.Image, tw: int, th: int, align_x=0.5, align_y=0.5) -> Image.Image:
    iw, ih = im.size
    scale = max(tw / iw, th / ih)
    nw, nh = int(iw * scale), int(ih * scale)
    resized = im.resize((nw, nh), Image.Resampling.LANCZOS)
    ox = int((nw - tw) * align_x)
    oy = int((nh - th) * align_y)
    return resized.crop((ox, oy, ox + tw, oy + th))


def draw_glow_text(
    canvas: Image.Image,
    pos: tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: tuple[int, int, int],
    stroke_width: int = 14,
    stroke_fill: tuple[int, int, int] = (0, 0, 0),
    glow_color: tuple[int, int, int] | None = None,
    glow_radius: int = 24,
    shadow_offset: tuple[int, int] = (10, 14),
):
    x, y = pos
    if glow_color is not None:
        gl = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        gd = ImageDraw.Draw(gl)
        gd.text((x, y), text, font=font, fill=(*glow_color, 155), stroke_width=stroke_width + 6, stroke_fill=(*glow_color, 90))
        canvas.alpha_composite(gl.filter(ImageFilter.GaussianBlur(glow_radius)))

    sh = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)
    sd.text((x + shadow_offset[0], y + shadow_offset[1]), text, font=font, fill=(0, 0, 0, 230), stroke_width=stroke_width + 4, stroke_fill=(0, 0, 0, 230))
    canvas.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6)))

    tl = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    td = ImageDraw.Draw(tl)
    td.text((x, y), text, font=font, fill=(*fill, 255), stroke_width=stroke_width, stroke_fill=(*stroke_fill, 255))
    canvas.alpha_composite(tl)


def draw_tilted_badge(
    canvas: Image.Image,
    center: tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
    bg_color: tuple[int, int, int],
    text_color: tuple[int, int, int],
    angle: float = -3.5,
    pad_x: int = 40,
    pad_y: int = 12,
    border_color: tuple[int, int, int] = (255, 255, 255),
    stroke_width: int = 4,
):
    dummy = ImageDraw.Draw(canvas)
    bbox = dummy.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    bw, bh = tw + pad_x * 2, th + pad_y * 2 + 12

    badge = Image.new("RGBA", (bw + 80, bh + 80), (0, 0, 0, 0))
    bd = ImageDraw.Draw(badge)
    bd.rounded_rectangle([48, 52, 40 + bw + 8, 40 + bh + 12], radius=20, fill=(0, 0, 0, 210))
    badge = badge.filter(ImageFilter.GaussianBlur(5))
    bd = ImageDraw.Draw(badge)
    bd.rounded_rectangle([40, 40, 40 + bw, 40 + bh], radius=18, fill=(*bg_color, 255), outline=(*border_color, 255), width=5)
    bd.text((40 + pad_x - bbox[0], 40 + pad_y - bbox[1] + 2), text, font=font, fill=(*text_color, 255), stroke_width=stroke_width, stroke_fill=(0, 0, 0, 220))
    rot = badge.rotate(angle, resample=Image.Resampling.BICUBIC, expand=True)
    canvas.alpha_composite(rot, (center[0] - rot.width // 2, center[1] - rot.height // 2))


def polish(im: Image.Image) -> Image.Image:
    rgb = im.convert("RGB")
    rgb = ImageEnhance.Contrast(rgb).enhance(1.14)
    rgb = ImageEnhance.Color(rgb).enhance(1.12)
    return ImageEnhance.Sharpness(rgb).enhance(1.28)


def main():
    # Option 1 (Recommended Winner): MrBeast / Dhruv Rathee '2 SAAL BARBAAD!'
    b1 = fit_cover(Image.open("assets/images/thumb_base_mrbeast.jpg"), W, H).convert("RGBA")
    ov1 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od1 = ImageDraw.Draw(ov1)
    od1.rounded_rectangle([980, 20, 1890, 520], radius=40, fill=(5, 5, 10, 165))
    b1.alpha_composite(ov1.filter(ImageFilter.GaussianBlur(45)))

    f_huge = ImageFont.truetype(FONT_ANTON, 242)
    f_badge = ImageFont.truetype(FONT_ANTON, 90)
    f_tag = ImageFont.truetype(FONT_POPPINS, 38)

    pill = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pd = ImageDraw.Draw(pill)
    lbl = "3 HRS / DAY ="
    tb = pd.textbbox((0, 0), lbl, font=f_tag)
    pw = (tb[2] - tb[0]) + 56
    pd.rounded_rectangle([1055, 48, 1055 + pw, 118], radius=14, fill=(18, 18, 26, 235), outline=(255, 30, 138, 255), width=4)
    pd.text((1083, 56), lbl, font=f_tag, fill=(255, 255, 255, 255))
    b1.alpha_composite(pill)

    draw_glow_text(b1, (1045, 106), "2 SAAL", f_huge, fill=(255, 218, 0), stroke_width=16, glow_color=(255, 170, 0))
    draw_tilted_badge(b1, (1365, 438), "BARBAAD!", f_badge, bg_color=(225, 18, 42), text_color=(255, 255, 255), angle=-3.5, border_color=(255, 218, 0))
    p1 = polish(b1)
    p1.save("thumbnails/01_MRBEAST_2_SAAL_MAIN.jpg", quality=95)
    p1.resize((1280, 720), Image.Resampling.LANCZOS).save("thumbnails/01_MRBEAST_2_SAAL_1280x720.jpg", quality=95)

    # Option 2: Direct Call-Out 'TUMSE HI — RUKO 1 MIN!'
    left = fit_cover(Image.open("assets/images/facecam_aryan_tight.jpg"), int(W * 0.58), H, 0.5, 0.35)
    right = fit_cover(Image.open("assets/images/seg3_hourglass_2_years.jpg"), int(W * 0.56), H, 0.5, 0.45)
    c2 = Image.new("RGBA", (W, H), (5, 5, 10, 255))
    c2.paste(right.convert("RGBA"), (int(W * 0.44), 0))
    mask = Image.new("L", left.size, 255)
    md = ImageDraw.Draw(mask)
    for x in range(left.width - 340, left.width):
        a = int(255 * (1.0 - (x - (left.width - 340)) / 340.0) ** 1.4)
        md.line([(x, 0), (x, H)], fill=a)
    c2.paste(left.convert("RGBA"), (0, 0), mask)
    draw_glow_text(c2, (930, 62), "TUMSE HI", ImageFont.truetype(FONT_ANTON, 205), fill=(255, 30, 138), stroke_width=15, glow_color=(255, 30, 138))
    draw_tilted_badge(c2, (1375, 355), "RUKO 1 MIN!", ImageFont.truetype(FONT_ANTON, 84), bg_color=(255, 214, 0), text_color=(12, 12, 16), angle=2.0, border_color=(0, 0, 0), stroke_width=0)
    polish(c2).save("thumbnails/02_DIRECT_CALLOUT_TUMSE_HI.jpg", quality=95)

    # Option 3: Influencer Expose 'TUM MAAL HO — KADWA SACH'
    bg3 = ImageEnhance.Brightness(fit_cover(Image.open("assets/images/seg4_influencer_trap.jpg"), W, H)).enhance(0.78).convert("RGBA")
    port = fit_cover(Image.open("assets/images/thumb_base_mrbeast.jpg"), W, H).crop((0, 0, 1020, H)).convert("RGBA")
    m3 = Image.new("L", (1020, H), 255)
    md3 = ImageDraw.Draw(m3)
    for x in range(835, 1020):
        md3.line([(x, 0), (x, H)], fill=int(255 * (1.0 - (x - 835) / 185.0)))
    bg3.paste(port, (0, 0), m3)
    draw_glow_text(bg3, (935, 70), "TUM MAAL HO", ImageFont.truetype(FONT_ANTON, 178), fill=(255, 218, 0), stroke_width=14, glow_color=(255, 150, 0))
    draw_tilted_badge(bg3, (1400, 355), "KADWA SACH", ImageFont.truetype(FONT_ANTON, 82), bg_color=(225, 20, 45), text_color=(255, 255, 255), angle=-2.5, border_color=(255, 255, 255))
    polish(bg3).save("thumbnails/03_TYCOON_EXPOSED_TUM_MAAL_HO.jpg", quality=95)
    print("Built all 3 high-CTR thumbnails!")


if __name__ == "__main__":
    main()
