"""
Logo dizayn dvigateli (100% bepul, internet va pullik API kerak emas).
Pillow yordamida premium geometrik belgi + toza wordmark chizadi.
"""
import colorsys
import math
import random
import re
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT_DIR = Path(__file__).parent / "fonts"
S = 2048  # ichki o'lcham (supersampling), chiqish 1024x1024

# ----------------------------------------------------------------------------
# Ranglar palitralari: bg (chet), bg2 (markaz yorug'ligi), primary, accent, text
# ----------------------------------------------------------------------------
PALETTES = {
    "emerald_gold":   dict(bg="#0B2E22", bg2="#16603F", primary="#D9B96A", accent="#5BB08A", text="#F3E9C8"),
    "black_gold":     dict(bg="#0A0A0A", bg2="#222222", primary="#D4AF37", accent="#8F7424", text="#F5E6B3"),
    "navy_ice":       dict(bg="#08162C", bg2="#14407A", primary="#8AD0FF", accent="#3E86D6", text="#F2F8FF"),
    "royal_purple":   dict(bg="#190B33", bg2="#3F1F78", primary="#C3A0FF", accent="#E7B84C", text="#F6F0FF"),
    "burgundy_cream": dict(bg="#35090F", bg2="#6E1626", primary="#E8D3A8", accent="#C9A66B", text="#FFF4DE"),
    "charcoal_copper": dict(bg="#18181C", bg2="#32323A", primary="#E09A6C", accent="#F2C197", text="#F4EDE6"),
    "white_blue":     dict(bg="#F4F7FB", bg2="#FFFFFF", primary="#1646C8", accent="#0B1F5C", text="#0B1F5C"),
    "white_black":    dict(bg="#EDEDED", bg2="#FFFFFF", primary="#111111", accent="#8A8A8A", text="#111111"),
    "coffee":         dict(bg="#241610", bg2="#4F3122", primary="#CFA573", accent="#EAD3B2", text="#F7E9D5"),
    "crimson_black":  dict(bg="#0C0C0E", bg2="#2C1015", primary="#E63946", accent="#F1F1F1", text="#FFFFFF"),
    "teal_mint":      dict(bg="#052A2E", bg2="#0C6169", primary="#5EEAD4", accent="#F5D76E", text="#E8FFFB"),
}

SYMBOLS = ["monogram", "hex_rings", "diamond", "orbit", "peaks", "burst",
           "shield", "crown", "cube", "leaf", "rise"]
LAYOUTS = ["stacked", "wordmark"]

# font oilalari: (display shrift, caps?, tracking nisbati, kichik shrift)
FONTS = {
    "modern":  dict(file="Poppins-Bold.ttf",        upper=True,  track=0.14, max_size=0.085, small="Poppins-Medium.ttf"),
    "tech":    dict(file="Michroma-Regular.ttf",    upper=True,  track=0.10, max_size=0.062, small="Poppins-Medium.ttf"),
    "luxury":  dict(file="DMSerifDisplay-Regular.ttf", upper=False, track=0.02, max_size=0.105, small="Poppins-Medium.ttf"),
    "bold":    dict(file="Anton-Regular.ttf",       upper=True,  track=0.10, max_size=0.125, small="Poppins-Medium.ttf"),
    "sport":   dict(file="BebasNeue-Regular.ttf",   upper=True,  track=0.12, max_size=0.15,  small="Poppins-Medium.ttf"),
    "elegant": dict(file="Poppins-SemiBold.ttf",    upper=True,  track=0.30, max_size=0.072, small="Poppins-Medium.ttf"),
}


# ----------------------------------------------------------------------------
# Rang yordamchilari
# ----------------------------------------------------------------------------
HEX_RE = re.compile(r"^#?([0-9a-fA-F]{6})$")


def hex_to_rgb(h: str):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def mix(c1, c2, t):
    a, b = hex_to_rgb(c1), hex_to_rgb(c2)
    return "#%02X%02X%02X" % tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def luma(h):
    r, g, b = hex_to_rgb(h)
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255


def valid_hex(v):
    if isinstance(v, str) and HEX_RE.match(v.strip()):
        return "#" + HEX_RE.match(v.strip()).group(1).upper()
    return None


def build_palette(spec: dict) -> dict:
    custom = spec.get("custom_colors") or {}
    bg = valid_hex(custom.get("bg"))
    primary = valid_hex(custom.get("primary"))
    if bg and primary:
        accent = valid_hex(custom.get("accent")) or mix(primary, bg, 0.35)
        text = valid_hex(custom.get("text")) or ("#FFFFFF" if luma(bg) < 0.5 else "#111111")
        return dict(bg=bg, bg2=mix(bg, primary, 0.22 if luma(bg) < 0.5 else 0.0) if luma(bg) < 0.5 else "#FFFFFF",
                    primary=primary, accent=accent, text=text)
    return dict(PALETTES.get(spec.get("palette"), PALETTES["black_gold"]))


# ----------------------------------------------------------------------------
# Chizish yordamchilari
# ----------------------------------------------------------------------------
def poly_pts(cx, cy, r, n, rot=-90):
    return [(cx + r * math.cos(math.radians(rot + 360 / n * i)),
             cy + r * math.sin(math.radians(rot + 360 / n * i))) for i in range(n)]


def closed_line(d, pts, w, fill):
    d.line(list(pts) + [pts[0], pts[1]], fill=fill, width=int(w), joint="curve")


def dot(d, x, y, r, fill):
    d.ellipse([x - r, y - r, x + r, y + r], fill=fill)


def round_line(d, p0, p1, w, fill):
    d.line([p0, p1], fill=fill, width=int(w))
    dot(d, p0[0], p0[1], w / 2, fill)
    dot(d, p1[0], p1[1], w / 2, fill)


def ellipse_pts(cx, cy, a, b, rot_deg, n=120):
    rot = math.radians(rot_deg)
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        x, y = a * math.cos(t), b * math.sin(t)
        pts.append((cx + x * math.cos(rot) - y * math.sin(rot),
                    cy + x * math.sin(rot) + y * math.cos(rot)))
    return pts


def lens_pts(p0, p1, bulge, n=40):
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    ln = math.hypot(dx, dy) or 1
    nx, ny = -dy / ln, dx / ln
    top, bot = [], []
    for i in range(n + 1):
        t = i / n
        k = math.sin(math.pi * t) * bulge
        x, y = p0[0] + dx * t, p0[1] + dy * t
        top.append((x + nx * k, y + ny * k))
        bot.append((x - nx * k, y - ny * k))
    return top + bot[::-1]


def bezier(p0, p1, p2, n=24):
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1])
            for t in [i / n for i in range(n + 1)]]


def load_font(name, size):
    """Use project fonts when present; otherwise use fonts installed on the OS."""
    size = max(9, int(size))
    bundled = FONT_DIR / name
    if bundled.exists():
        return ImageFont.truetype(str(bundled), size)

    # Standard fonts included in Windows 11, with cross-platform alternatives.
    win = Path(r"C:\Windows\Fonts")
    low = name.lower()
    if 'serif' in low:
        choices = ['georgiab.ttf', 'georgia.ttf', 'timesbd.ttf', 'DejaVuSerif.ttf']
    elif 'anton' in low or 'bebas' in low:
        choices = ['impact.ttf', 'arialbd.ttf', 'DejaVuSansCondensed-Bold.ttf']
    elif 'michroma' in low:
        choices = ['bahnschrift.ttf', 'seguisb.ttf', 'DejaVuSans.ttf']
    else:
        choices = ['segoeuib.ttf', 'arialbd.ttf', 'DejaVuSans-Bold.ttf']
    locations = [win, Path('/usr/share/fonts/truetype/dejavu'), Path('/usr/share/fonts/truetype/liberation2')]
    for base in locations:
        for candidate in choices:
            file = base / candidate
            if file.is_file():
                return ImageFont.truetype(str(file), size)
    for candidate in choices:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            pass
    return ImageFont.load_default(size=size)


def text_width(text, font, tracking):
    if tracking <= 0:
        return font.getlength(text)
    return sum(font.getlength(ch) for ch in text) + tracking * (len(text) - 1)


def draw_text(d, cx, baseline, text, font, fill, tracking=0.0):
    w = text_width(text, font, tracking)
    x = cx - w / 2
    if tracking <= 0:
        d.text((x, baseline), text, font=font, fill=fill, anchor="ls")
        return
    for ch in text:
        d.text((x, baseline), ch, font=font, fill=fill, anchor="ls")
        x += font.getlength(ch) + tracking


def cap_height(font):
    bb = font.getbbox("H", anchor="ls")
    return -bb[1]


# ----------------------------------------------------------------------------
# Belgilar (symbols)
# ----------------------------------------------------------------------------
def sym_monogram(d, cx, cy, R, c, brand, fam):
    lw = R * 0.075
    d.ellipse([cx - R, cy - R, cx + R, cy + R], outline=c["primary"], width=int(lw))
    r2 = R * 0.84
    d.ellipse([cx - r2, cy - r2, cx + r2, cy + r2], outline=c["accent"], width=max(3, int(lw * 0.35)))
    words = [w for w in re.split(r"\s+", brand.strip()) if w]
    initials = "".join(w[0] for w in words[:2]).upper() or brand[:1].upper()
    size = R * (1.05 if len(initials) == 1 else 0.82)
    font = load_font(FONTS[fam]["file"], size)
    while text_width(initials, font, 0) > R * 1.25 and size > 20:
        size *= 0.94
        font = load_font(FONTS[fam]["file"], size)
    draw_text(d, cx, cy + cap_height(font) / 2, initials, font, c["primary"])


def sym_hex_rings(d, cx, cy, R, c, **_):
    lw = R * 0.08
    closed_line(d, poly_pts(cx, cy, R, 6), lw, c["primary"])
    closed_line(d, poly_pts(cx, cy, R * 0.68, 6), lw * 0.55, c["accent"])
    d.polygon(poly_pts(cx, cy, R * 0.30, 6), fill=c["primary"])
    for p in poly_pts(cx, cy, R, 6):
        dot(d, p[0], p[1], lw * 0.9, c["accent"])


def sym_diamond(d, cx, cy, R, c, **_):
    lw = R * 0.07
    d.ellipse([cx - R, cy - R, cx + R, cy + R], outline=c["primary"], width=int(lw * 0.9))
    r2 = R * 0.88
    d.ellipse([cx - r2, cy - r2, cx + r2, cy + r2], outline=c["accent"], width=max(3, int(lw * 0.3)))
    def dia(k):
        return [(cx, cy - 0.78 * R * k), (cx + 0.5 * R * k, cy), (cx, cy + 0.78 * R * k), (cx - 0.5 * R * k, cy)]
    closed_line(d, dia(1), lw, c["primary"])
    closed_line(d, dia(0.52), lw * 0.6, c["accent"])
    dot(d, cx, cy, R * 0.09, c["primary"])


def sym_orbit(d, cx, cy, R, c, **_):
    lw = R * 0.07
    for rot, col in ((35, c["primary"]), (-35, c["accent"]), (90, c["primary"])):
        pts = ellipse_pts(cx, cy, R, R * 0.36, rot)
        d.line(pts + [pts[0], pts[1]], fill=col, width=int(lw), joint="curve")
    dot(d, cx, cy, R * 0.26, c["primary"])
    dot(d, cx, cy, R * 0.12, c["bg"])
    for ang, col in ((35, c["accent"]), (215, c["primary"])):
        a = math.radians(ang)
        dot(d, cx + R * math.cos(a), cy + R * math.sin(a), R * 0.1, col)


def sym_peaks(d, cx, cy, R, c, **_):
    base = cy + 0.62 * R
    t2 = [(cx - 0.02 * R, base), (cx + 0.52 * R, cy - 0.28 * R), (cx + 1.05 * R, base)]
    t1 = [(cx - 1.05 * R, base), (cx - 0.2 * R, cy - 0.78 * R), (cx + 0.62 * R, base)]
    d.polygon(t2, fill=c["accent"])
    d.polygon(t1, fill=c["primary"])
    closed_line(d, t1, R * 0.05, c["bg"])
    snow = [(cx - 0.2 * R, cy - 0.78 * R), (cx - 0.02 * R, cy - 0.5 * R), (cx - 0.2 * R, cy - 0.58 * R),
            (cx - 0.38 * R, cy - 0.5 * R)]
    d.polygon(snow, fill=c["bg"])
    dot(d, cx + 0.62 * R, cy - 0.62 * R, R * 0.12, c["primary"])
    d.line([(cx - 1.05 * R, base + R * 0.2), (cx + 1.05 * R, base + R * 0.2)], fill=c["accent"], width=int(R * 0.05))


def sym_burst(d, cx, cy, R, c, **_):
    dot(d, cx, cy, R * 0.34, c["primary"])
    dot(d, cx, cy, R * 0.2, c["bg"])
    dot(d, cx, cy, R * 0.1, c["accent"])
    n = 16
    for i in range(n):
        a = math.radians(360 / n * i - 90)
        r0 = R * 0.56
        r1 = R * (1.0 if i % 2 == 0 else 0.78)
        round_line(d, (cx + r0 * math.cos(a), cy + r0 * math.sin(a)),
                   (cx + r1 * math.cos(a), cy + r1 * math.sin(a)), R * 0.07,
                   c["primary"] if i % 2 == 0 else c["accent"])


def shield_pts(cx, cy, R, k=1.0):
    w, top, bot = 0.82 * R * k, cy - 0.95 * R * k, cy + 1.05 * R * k
    side = cy + 0.1 * R * k
    pts = [(cx - w, top), (cx + w, top), (cx + w, side)]
    pts += bezier((cx + w, side), (cx + w, cy + 0.75 * R * k), (cx, bot))
    pts += bezier((cx, bot), (cx - w, cy + 0.75 * R * k), (cx - w, side))
    return pts


def sym_shield(d, cx, cy, R, c, brand="", fam="modern", **_):
    d.polygon(shield_pts(cx, cy, R), fill=c["primary"])
    d.polygon(shield_pts(cx, cy, R, 0.86), fill=c["bg"])
    closed_line(d, shield_pts(cx, cy, R, 0.76), R * 0.04, c["accent"])
    letter = (brand.strip()[:1] or "A").upper()
    size = R * 1.05
    font = load_font(FONTS[fam]["file"], size)
    draw_text(d, cx, cy + cap_height(font) / 2 - R * 0.02, letter, font, c["primary"])


def sym_crown(d, cx, cy, R, c, **_):
    k = [(-0.92, 0.42), (-1.0, -0.52), (-0.42, 0.04), (0, -0.78), (0.42, 0.04), (1.0, -0.52), (0.92, 0.42)]
    pts = [(cx + x * R, cy + y * R) for x, y in k]
    d.polygon(pts, fill=c["primary"])
    d.rounded_rectangle([cx - 0.92 * R, cy + 0.52 * R, cx + 0.92 * R, cy + 0.78 * R], radius=R * 0.08, fill=c["accent"])
    for x, y in ((-1.0, -0.52), (0, -0.78), (1.0, -0.52)):
        dot(d, cx + x * R, cy + y * R, R * 0.1, c["accent"])
    for x in (-0.4, 0, 0.4):
        dot(d, cx + x * R, cy + 0.2 * R, R * 0.06, c["bg"])


def sym_cube(d, cx, cy, R, c, **_):
    v = lambda a: (cx + R * math.cos(math.radians(a)), cy + R * math.sin(math.radians(a)))
    top = [v(-90), v(-30), (cx, cy), v(210)]
    right = [v(-30), v(30), v(90), (cx, cy)]
    left = [v(210), (cx, cy), v(90), v(150)]
    d.polygon(top, fill=c["primary"])
    d.polygon(right, fill=c["accent"])
    d.polygon(left, fill=mix(c["primary"], c["bg"], 0.5))
    for poly in (top, right, left):
        closed_line(d, poly, R * 0.035, c["bg"])


def sym_leaf(d, cx, cy, R, c, **_):
    base = (cx, cy + 0.95 * R)
    d.polygon(lens_pts(base, (cx, cy - 0.95 * R), R * 0.34), fill=c["primary"])
    d.polygon(lens_pts((cx, cy + 0.35 * R), (cx - 0.95 * R, cy - 0.45 * R), R * 0.24), fill=c["accent"])
    d.polygon(lens_pts((cx, cy + 0.35 * R), (cx + 0.95 * R, cy - 0.45 * R), R * 0.24), fill=c["accent"])
    d.line([base, (cx, cy - 0.5 * R)], fill=c["bg"], width=max(3, int(R * 0.03)))


def sym_rise(d, cx, cy, R, c, **_):
    w = R * 0.15
    for i, col in enumerate((c["accent"], c["primary"], c["primary"])):
        off = (1 - i) * R * 0.52
        pts = [(cx - 0.85 * R, cy + 0.35 * R + off), (cx, cy - 0.5 * R + off), (cx + 0.85 * R, cy + 0.35 * R + off)]
        d.line(pts, fill=col, width=int(w), joint="curve")
        for p in (pts[0], pts[2]):
            dot(d, p[0], p[1], w / 2, col)


SYMBOL_FUNCS = dict(monogram=sym_monogram, hex_rings=sym_hex_rings, diamond=sym_diamond, orbit=sym_orbit,
                    peaks=sym_peaks, burst=sym_burst, shield=sym_shield, crown=sym_crown, cube=sym_cube,
                    leaf=sym_leaf, rise=sym_rise)


# ----------------------------------------------------------------------------
# Sahna: fon, ramka, matn
# ----------------------------------------------------------------------------
def make_background(c):
    base = Image.new("RGB", (S, S), c["bg"])
    glow = Image.new("RGB", (S, S), c["bg2"])
    mask = Image.radial_gradient("L").resize((S, S), Image.BICUBIC)
    return Image.composite(base, glow, mask)


def draw_border(d, c):
    col = c["primary"]
    for i, (m, w) in enumerate(((0.035, 5), (0.046, 3), (0.057, 2))):
        mm = int(S * m)
        d.rounded_rectangle([mm, mm, S - mm, S - mm], radius=int(S * (0.075 - i * 0.008)),
                            outline=mix(col, c["bg"], 0.25 + i * 0.2), width=w + 1)


def divider(d, cx, y, width, c):
    half = width / 2
    d.line([(cx - half, y), (cx - 28, y)], fill=c["accent"], width=5)
    d.line([(cx + 28, y), (cx + half, y)], fill=c["accent"], width=5)
    d.polygon([(cx, y - 15), (cx + 15, y), (cx, y + 15), (cx - 15, y)], fill=c["primary"])


def fit_brand(brand, fam, max_w, size_scale=1.0):
    spec = FONTS[fam]
    text = brand.upper() if spec["upper"] else brand
    size = S * spec["max_size"] * size_scale
    min_size = S * 0.05
    words = text.split()

    def width_at(t, sz):
        f = load_font(spec["file"], sz)
        return text_width(t, f, sz * spec["track"])

    # bir qatorga sig'adimi?
    sz = size
    while width_at(text, sz) > max_w and sz > min_size:
        sz *= 0.96
    if width_at(text, sz) <= max_w:
        return [text], sz
    # ikki qator
    if len(words) >= 2:
        best = None
        for i in range(1, len(words)):
            l1, l2 = " ".join(words[:i]), " ".join(words[i:])
            diff = abs(len(l1) - len(l2))
            if best is None or diff < best[0]:
                best = (diff, l1, l2)
        lines = [best[1], best[2]]
        sz = size
        while max(width_at(l, sz) for l in lines) > max_w and sz > S * 0.03:
            sz *= 0.96
        return lines, sz
    while width_at(text, sz) > max_w and sz > S * 0.03:
        sz *= 0.96
    return [text], sz


def render(spec: dict, seed: int = 0) -> bytes:
    """spec -> PNG bytes (1024x1024)."""
    c = build_palette(spec)
    fam = spec.get("font") if spec.get("font") in FONTS else "modern"
    brand = (spec.get("brand") or "BRAND").strip()
    symbol = spec.get("symbol")
    rng = random.Random(seed or brand)
    if symbol not in SYMBOL_FUNCS:
        symbol = rng.choice(SYMBOLS)
    layout = spec.get("layout") if spec.get("layout") in LAYOUTS else "stacked"
    tagline = (spec.get("tagline") or "").strip().upper()[:30]

    img = make_background(c)
    d = ImageDraw.Draw(img)
    if spec.get("border", True):
        draw_border(d, c)

    fs = FONTS[fam]
    lines, size = fit_brand(brand, fam, S * 0.80, 1.0 if layout == "stacked" else 1.15)
    font = load_font(fs["file"], size)
    track = size * fs["track"]
    caph = cap_height(font)
    line_gap = size * 0.34
    text_h = caph * len(lines) + line_gap * (len(lines) - 1)

    small = load_font(fs["small"], S * 0.024)
    tag_h = cap_height(small) if tagline else 0
    div_gap = S * 0.045
    tag_gap = S * 0.04

    if layout == "stacked":
        R = S * 0.17
        sym_h = R * 2.3
        gap = S * 0.075
        total = sym_h + gap + text_h + div_gap + (tag_gap + tag_h if tagline else 0)
        top = (S - total) / 2
        cy = top + sym_h / 2
        SYMBOL_FUNCS[symbol](d, S / 2, cy, R, c, brand=brand, fam=fam)
        y = top + sym_h + gap + caph
    else:
        total = text_h + div_gap * 2 + (tag_gap + tag_h if tagline else 0)
        top = (S - total) / 2
        divider(d, S / 2, top - S * 0.05, S * 0.34, c)
        y = top + caph

    for i, ln in enumerate(lines):
        draw_text(d, S / 2, y + i * (caph + line_gap), ln, font, c["text"], track)
    y_end = y + (len(lines) - 1) * (caph + line_gap)

    divider(d, S / 2, y_end + div_gap, S * 0.34 if layout == "stacked" else S * 0.2, c)
    if tagline:
        draw_text(d, S / 2, y_end + div_gap + tag_gap + tag_h, tagline, small, mix(c["text"], c["bg"], 0.2),
                  S * 0.0065)

    out = img.resize((1024, 1024), Image.LANCZOS)
    buf = BytesIO()
    out.save(buf, "PNG", optimize=True)
    return buf.getvalue()


# ----------------------------------------------------------------------------
# Variantlar / tezkor o'zgartirishlar
# ----------------------------------------------------------------------------
def vary(spec: dict, rng: random.Random | None = None) -> dict:
    """Xuddi shu brend va ranglar, lekin yangi konsepsiya."""
    rng = rng or random.Random()
    new = dict(spec)
    new["symbol"] = rng.choice([s for s in SYMBOLS if s != spec.get("symbol")])
    new["font"] = rng.choice([f for f in FONTS if f != spec.get("font")])
    new["layout"] = "stacked" if rng.random() < 0.8 else "wordmark"
    return new


def tweak(spec: dict, key: str) -> dict:
    new = dict(spec)
    if key == "minimal":
        new.update(font="elegant", border=False, layout="stacked",
                   symbol=random.choice(["diamond", "hex_rings", "monogram", "orbit"]))
        if "custom_colors" not in new or not new.get("custom_colors"):
            new["palette"] = random.choice(["white_black", "white_blue", "black_gold"])
    elif key == "luxury":
        new.update(font="luxury", border=True,
                   symbol=random.choice(["crown", "shield", "monogram", "diamond"]),
                   custom_colors=None,
                   palette=random.choice(["black_gold", "emerald_gold", "burgundy_cream"]))
    return new
