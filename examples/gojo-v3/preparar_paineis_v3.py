#!/usr/bin/env python3
"""Cria 24 painéis Gojo em três linguagens visuais, sem baixar arte de terceiros."""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parent
SOURCE_DIR = ROOT / "assets_v2" / "paineis"
OUT_DIR = ROOT / "assets_v3" / "paineis"
CONTACT = ROOT / "analise_v3" / "paineis_v3_contato.jpg"
W, H = 1080, 1920
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_CJK = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size)


def grade(img: Image.Image, tint: tuple[int, int, int], color: float, contrast: float) -> Image.Image:
    base = ImageEnhance.Contrast(img.convert("RGB")).enhance(contrast)
    gray = ImageOps.grayscale(base)
    toned = ImageOps.colorize(gray, black=(3, 5, 10), white=tint)
    return Image.blend(toned, ImageEnhance.Color(base).enhance(color), 0.28)


def cover_crop(img: Image.Image, width: int, height: int, zoom: float = 1.0) -> Image.Image:
    scale = max(width / img.width, height / img.height) * zoom
    resized = img.resize((round(img.width * scale), round(img.height * scale)), Image.Resampling.LANCZOS)
    x = max(0, (resized.width - width) // 2)
    y = max(0, round((resized.height - height) * 0.42))
    return resized.crop((x, y, x + width, y + height))


def common_finish(img: Image.Image, seed: int, accent: tuple[int, int, int]) -> Image.Image:
    rng = np.random.default_rng(seed)
    a = np.asarray(img.convert("RGB"), dtype=np.float32)
    yy, xx = np.mgrid[0:H, 0:W]
    radius = np.sqrt(((xx - W / 2) / (W * 0.64)) ** 2 + ((yy - H * 0.46) / (H * 0.68)) ** 2)
    a *= np.clip(1.08 - 0.32 * radius**1.8, 0.52, 1.0)[..., None]
    a += rng.normal(0, 3.1, a.shape)
    # Scanlines finas e textura de impressão preservando o rosto.
    a[::4] *= 0.965
    a[:, ::11] *= 0.985
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")

    shade = np.zeros((H, W, 4), dtype=np.uint8)
    alpha = np.clip((np.arange(H) - H * 0.69) / (H * 0.18), 0, 1) * 246
    shade[..., :3] = (4, 4, 12)
    shade[..., 3] = alpha[:, None].astype(np.uint8)
    img = Image.alpha_composite(img, Image.fromarray(shade, "RGBA"))
    d = ImageDraw.Draw(img, "RGBA")
    d.line((30, 145, 238, 145), fill=(*accent, 180), width=5)
    d.line((W - 238, H - 150, W - 30, H - 150), fill=(*accent, 180), width=5)
    d.text((50, 82), f"5160 / {seed:02d}", font=font(FONT_BOLD, 22), fill=(245, 247, 255, 145))
    return img.convert("RGB")


def mahoraga_language(base: Image.Image, index: int) -> Image.Image:
    """Peso preto/verde-petróleo, geometria circular e impactos vermelhos."""
    rng = np.random.default_rng(1100 + index)
    img = grade(base, (126, 206, 196), 0.72, 1.35).convert("RGBA")
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow, "RGBA")
    cx, cy = W * (0.46 + 0.025 * (index % 3)), H * 0.37
    for r, alpha, width in ((390, 50, 5), (320, 74, 3), (250, 100, 3)):
        gd.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(113, 242, 226, alpha), width=width)
    for spoke in range(8):
        ang = spoke * math.pi / 4 + index * 0.07
        x1, y1 = cx + math.cos(ang) * 260, cy + math.sin(ang) * 260
        x2, y2 = cx + math.cos(ang) * 420, cy + math.sin(ang) * 420
        gd.line((x1, y1, x2, y2), fill=(151, 255, 240, 62), width=5)
    glow = glow.filter(ImageFilter.GaussianBlur(3))
    img = Image.alpha_composite(img, glow)
    d = ImageDraw.Draw(img, "RGBA")
    # Diagonais assimétricas: leitura de golpe sem copiar quadro do modelo.
    for n in range(3):
        y = 1250 + n * 88 + int(rng.integers(-25, 26))
        d.polygon(((-80, y), (W + 80, y - 360), (W + 80, y - 335), (-80, y + 25)), fill=(232, 43, 61, 125 - n * 24))
    d.text((55, 1540), "ADAPTAÇÃO", font=font(FONT_BOLD, 52), fill=(239, 246, 244, 185))
    d.text((58, 1602), "INFINITO // SEIS OLHOS", font=font(FONT_BOLD, 23), fill=(236, 63, 73, 205))
    return common_finish(img, index, (62, 223, 203))


def toji_language(base: Image.Image, index: int) -> Image.Image:
    """Composição em quadros de mangá, sépia e vermelho seco."""
    warm = grade(base, (234, 214, 174), 0.38, 1.48)
    canvas = Image.new("RGB", (W, H), (8, 7, 8))
    bg = cover_crop(warm.filter(ImageFilter.GaussianBlur(13)), W, H, 1.12)
    canvas = Image.blend(canvas, bg, 0.36)
    d = ImageDraw.Draw(canvas, "RGBA")
    # Três recortes com escala diferente criam um painel editorial forte.
    pieces = [
        ((36, 110, 1044, 1080), cover_crop(warm, 1008, 970, 1.03)),
        ((36, 1110, 650, 1645), cover_crop(warm, 614, 535, 1.48)),
        ((680, 1110, 1044, 1645), cover_crop(ImageOps.mirror(warm), 364, 535, 1.72)),
    ]
    for box, piece in pieces:
        canvas.paste(piece, box[:2])
        d.rectangle(box, outline=(248, 242, 225, 220), width=8)
        d.rectangle((box[0] + 10, box[1] + 10, box[2] - 10, box[3] - 10), outline=(108, 22, 29, 170), width=3)
    d.polygon(((0, 995), (W, 905), (W, 1028), (0, 1118)), fill=(148, 23, 32, 205))
    d.text((55, 925), "O MAIS FORTE", font=font(FONT_BOLD, 68), fill=(255, 248, 232, 235), stroke_width=3, stroke_fill=(10, 8, 8, 220))
    d.text((58, 1690), "SEM LIMITE  /  SEM ALCANCE", font=font(FONT_BOLD, 28), fill=(239, 222, 189, 200))
    # Retícula quadrada discreta, semelhante à impressão de mangá.
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay, "RGBA")
    for y in range(120, 1660, 14):
        for x in range(40 + (y // 14 % 2) * 7, 1040, 14):
            od.ellipse((x, y, x + 2, y + 2), fill=(0, 0, 0, 45))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay)
    return common_finish(canvas, 20 + index, (205, 48, 58))


def lightning(draw: ImageDraw.ImageDraw, rng: np.random.Generator, start: tuple[float, float], end: tuple[float, float], alpha: int) -> None:
    pts = [start]
    for n in range(1, 9):
        t = n / 9
        pts.append((start[0] + (end[0] - start[0]) * t + rng.normal(0, 42), start[1] + (end[1] - start[1]) * t))
    pts.append(end)
    draw.line(pts, fill=(205, 252, 255, alpha), width=9, joint="curve")
    draw.line(pts, fill=(70, 226, 255, min(255, alpha + 35)), width=3, joint="curve")


def kashimo_language(base: Image.Image, index: int) -> Image.Image:
    """Ciano elétrico, preto profundo, glitch e grande área negativa."""
    rng = np.random.default_rng(3100 + index)
    img = grade(base, (170, 244, 255), 0.58, 1.62)
    # Glitch real por fatias horizontais, sem depender de filtro externo.
    glitched = img.copy()
    for _ in range(17):
        y = int(rng.integers(120, 1600))
        h = int(rng.integers(3, 24))
        strip = img.crop((0, y, W, min(H, y + h)))
        shift = int(rng.integers(-46, 47))
        glitched.paste(ImageChops.offset(strip, shift, 0), (0, y))
    img = glitched.convert("RGBA")
    energy = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ed = ImageDraw.Draw(energy, "RGBA")
    for n in range(5):
        lightning(ed, rng, (rng.uniform(-120, W + 120), -40), (rng.uniform(60, W - 60), H * rng.uniform(0.72, 1.04)), 105 + n * 18)
    energy = energy.filter(ImageFilter.GaussianBlur(2.2))
    img = Image.alpha_composite(img, energy)
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle((0, 1295, W, 1675), fill=(2, 7, 13, 218))
    d.rectangle((0, 1295, 22, 1675), fill=(45, 229, 255, 235))
    d.text((60, 1352), "∞", font=font(FONT_BOLD, 170), fill=(215, 251, 255, 235))
    d.text((260, 1400), "ACIMA", font=font(FONT_BOLD, 74), fill=(241, 253, 255, 240))
    d.text((263, 1490), "DO INFINITO", font=font(FONT_BOLD, 42), fill=(71, 228, 255, 220))
    d.text((62, 1730), "五条 悟", font=font(FONT_CJK, 42), fill=(209, 250, 255, 165))
    return common_finish(img, 40 + index, (46, 228, 255))


def make_contact(paths: list[Path]) -> None:
    tw, th = 180, 320
    sheet = Image.new("RGB", (tw * 6, th * 4), (8, 8, 12))
    for i, path in enumerate(paths):
        thumb = Image.open(path).convert("RGB").resize((tw, th), Image.Resampling.LANCZOS)
        sheet.paste(thumb, ((i % 6) * tw, (i // 6) * th))
    CONTACT.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(CONTACT, quality=92)


def main() -> None:
    sources = sorted(SOURCE_DIR.glob("painel_*.png"))
    if len(sources) < 12:
        raise SystemExit(f"Esperados 12 painéis-base em {SOURCE_DIR}; encontrados {len(sources)}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    # Ordem narrativa: ameaça/peso -> precisão física -> liberação elétrica.
    source_order = [10, 0, 3, 1, 4, 5, 6, 2, 7, 5, 8, 3, 9, 1, 6, 10, 11, 7, 4, 8, 2, 9, 10, 11]
    for i, source_index in enumerate(source_order):
        base = Image.open(sources[source_index]).convert("RGB")
        if i < 8:
            panel = mahoraga_language(base, i)
        elif i < 16:
            panel = toji_language(base, i - 8)
        else:
            panel = kashimo_language(base, i - 16)
        out = OUT_DIR / f"painel_{i + 1:02d}.png"
        tmp = out.with_suffix(".tmp.png")
        panel.save(tmp, compress_level=3)
        tmp.replace(out)
        outputs.append(out)
        print(f"ok {out.name}")
    make_contact(outputs)
    print(f"contato: {CONTACT}")


if __name__ == "__main__":
    main()
