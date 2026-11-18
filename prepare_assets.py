"""Rasterizes the cburnett SVG piece set in assets/pieces to 208px transparent PNGs.
Dependency-free (PIL only): parses SVG paths, flattens curves/arcs, even-odd fill, round strokes.
Run once after cloning: python prepare_assets.py
"""
import os
import re
import math
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw, ImageChops

BASE = os.path.dirname(os.path.abspath(__file__))
PIECES = os.path.join(BASE, "assets", "pieces")
OUT_SIZE = 208
SS = 2  # supersample factor


def tokenize(d):
    return re.findall(r"[MmLlHhVvCcSsQqTtAaZz]|[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?", d)


def arc_to_beziers(x1, y1, rx, ry, phi, fa, fs, x2, y2):
    if rx == 0 or ry == 0:
        return [(x1, y1, x2, y2, x2, y2)]
    rx, ry = abs(rx), abs(ry)
    cos_p, sin_p = math.cos(phi), math.sin(phi)
    dx2, dy2 = (x1 - x2) / 2, (y1 - y2) / 2
    x1p = cos_p * dx2 + sin_p * dy2
    y1p = -sin_p * dx2 + cos_p * dy2
    lam = x1p * x1p / (rx * rx) + y1p * y1p / (ry * ry)
    if lam > 1:
        s = math.sqrt(lam)
        rx, ry = rx * s, ry * s
    num = rx * rx * ry * ry - rx * rx * y1p * y1p - ry * ry * x1p * x1p
    den = rx * rx * y1p * y1p + ry * ry * x1p * x1p
    co = math.sqrt(max(0, num / den)) if den else 0
    if fa == fs:
        co = -co
    cxp = co * rx * y1p / ry
    cyp = -co * ry * x1p / rx
    cx = cos_p * cxp - sin_p * cyp + (x1 + x2) / 2
    cy = sin_p * cxp + cos_p * cyp + (y1 + y2) / 2

    def angle(ux, uy, vx, vy):
        dot = ux * vx + uy * vy
        ln = math.sqrt((ux * ux + uy * uy) * (vx * vx + vy * vy))
        a = math.acos(max(-1, min(1, dot / ln))) if ln else 0
        if ux * vy - uy * vx < 0:
            a = -a
        return a

    th1 = angle(1, 0, (x1p - cxp) / rx, (y1p - cyp) / ry)
    dth = angle((x1p - cxp) / rx, (y1p - cyp) / ry, (-x1p - cxp) / rx, (-y1p - cyp) / ry)
    if not fs and dth > 0:
        dth -= 2 * math.pi
    if fs and dth < 0:
        dth += 2 * math.pi
    segs = max(1, int(math.ceil(abs(dth) / (math.pi / 4))))
    out = []
    for i in range(segs):
        t1 = th1 + dth * i / segs
        t2 = th1 + dth * (i + 1) / segs
        alpha = math.sin(t2 - t1) * (math.sqrt(4 + 3 * math.tan((t2 - t1) / 2) ** 2) - 1) / 3

        def pt(t):
            return (cx + rx * math.cos(t) * cos_p - ry * math.sin(t) * sin_p,
                    cy + rx * math.cos(t) * sin_p + ry * math.sin(t) * cos_p)

        def deriv(t):
            return (-rx * math.sin(t) * cos_p - ry * math.cos(t) * sin_p,
                    -rx * math.sin(t) * sin_p + ry * math.cos(t) * cos_p)

        p1, p2 = pt(t1), pt(t2)
        d1, d2 = deriv(t1), deriv(t2)
        out.append((p1[0] + alpha * d1[0], p1[1] + alpha * d1[1],
                    p2[0] - alpha * d2[0], p2[1] - alpha * d2[1], p2[0], p2[1]))
    return out


def flatten_path(d):
    """Returns list of subpaths, each a list of (x, y) points."""
    toks = tokenize(d)
    i = 0
    x = y = sx = sy = 0.0
    prev_cmd = None
    prev_ctrl = None
    subpaths, cur = [], []

    def num():
        nonlocal i
        v = float(toks[i]); i += 1
        return v

    def flush(close):
        nonlocal cur
        if cur:
            if close:
                cur.append(cur[0])
            subpaths.append(cur)
            cur = []

    while i < len(toks):
        t = toks[i]
        if re.match(r"[A-Za-z]", t):
            cmd = t; i += 1
        else:
            cmd = prev_cmd or "L"
            if cmd == "M":
                cmd = "L"
            if cmd == "m":
                cmd = "l"
        rel = cmd.islower()
        c = cmd.upper()
        if c == "Z":
            flush(True)
            x, y = sx, sy
            prev_ctrl = None
        elif c == "M":
            flush(False)
            nx, ny = num(), num()
            x, y = (x + nx, y + ny) if rel else (nx, ny)
            sx, sy = x, y
            cur = [(x, y)]
            prev_ctrl = None
        elif c == "L":
            nx, ny = num(), num()
            x, y = (x + nx, y + ny) if rel else (nx, ny)
            cur.append((x, y)); prev_ctrl = None
        elif c == "H":
            nx = num()
            x = x + nx if rel else nx
            cur.append((x, y)); prev_ctrl = None
        elif c == "V":
            ny = num()
            y = y + ny if rel else ny
            cur.append((x, y)); prev_ctrl = None
        elif c in ("C", "S"):
            if c == "C":
                x1, y1 = num(), num()
                if rel:
                    x1 += x; y1 += y
            else:
                if prev_ctrl:
                    x1, y1 = 2 * x - prev_ctrl[0], 2 * y - prev_ctrl[1]
                else:
                    x1, y1 = x, y
            x2, y2 = num(), num()
            nx, ny = num(), num()
            if rel:
                x2 += x; y2 += y; nx += x; ny += y
            steps = 24
            for s in range(1, steps + 1):
                t = s / steps
                mt = 1 - t
                px = mt**3 * x + 3 * mt**2 * t * x1 + 3 * mt * t**2 * x2 + t**3 * nx
                py = mt**3 * y + 3 * mt**2 * t * y1 + 3 * mt * t**2 * y2 + t**3 * ny
                cur.append((px, py))
            prev_ctrl = (x2, y2)
            x, y = nx, ny
        elif c in ("Q", "T"):
            if c == "Q":
                x1, y1 = num(), num()
                if rel:
                    x1 += x; y1 += y
            else:
                if prev_ctrl:
                    x1, y1 = 2 * x - prev_ctrl[0], 2 * y - prev_ctrl[1]
                else:
                    x1, y1 = x, y
            nx, ny = num(), num()
            if rel:
                nx += x; ny += y
            steps = 24
            for s in range(1, steps + 1):
                t = s / steps
                mt = 1 - t
                px = mt**2 * x + 2 * mt * t * x1 + t**2 * nx
                py = mt**2 * y + 2 * mt * t * y1 + t**2 * ny
                cur.append((px, py))
            prev_ctrl = (x1, y1)
            x, y = nx, ny
        elif c == "A":
            rx, ry = num(), num()
            rot = num() * math.pi / 180
            fa, fs = int(num()), int(num())
            nx, ny = num(), num()
            if rel:
                nx += x; ny += y
            for b in arc_to_beziers(x, y, rx, ry, rot, fa, fs, nx, ny):
                x1, y1, x2, y2, ex, ey = b
                steps = 12
                for s in range(1, steps + 1):
                    t = s / steps
                    mt = 1 - t
                    px = mt**3 * x + 3 * mt**2 * t * x1 + 3 * mt * t**2 * x2 + t**3 * ex
                    py = mt**3 * y + 3 * mt**2 * t * y1 + 3 * mt * t**2 * y2 + t**3 * ey
                    cur.append((px, py))
            x, y = nx, ny
            prev_ctrl = None
        else:
            raise ValueError(f"unsupported command {cmd}")
        prev_cmd = cmd
    flush(False)
    return subpaths


def parse_color(s, default=None):
    if not s or s == "none":
        return None
    s = s.strip()
    if s.startswith("#"):
        h = s[1:]
        if len(h) == 3:
            h = "".join(ch * 2 for ch in h)
        return tuple(int(h[j:j + 2], 16) for j in (0, 2, 4)) + (255,)
    return {"white": (255, 255, 255, 255), "black": (0, 0, 0, 255)}.get(s, default)


def render_svg(svg_path, out_path):
    with open(svg_path, "r", encoding="utf-8") as f:
        raw = f.read()
    if "<!DOCTYPE" in raw or "<!ENTITY" in raw:
        raise ValueError(f"refusing SVG with DTD/entities: {svg_path}")
    root = ET.fromstring(raw)
    ns = "{http://www.w3.org/2000/svg}"
    vb = root.get("viewBox", "0 0 45 45").split()
    vw, vh = float(vb[2]), float(vb[3])
    scale = OUT_SIZE * SS / vw
    size = OUT_SIZE * SS
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))

    def walk(el, fill, stroke, sw):
        fill = parse_color(el.get("fill"), fill) if el.get("fill") is not None else fill
        stroke = parse_color(el.get("stroke"), stroke) if el.get("stroke") is not None else stroke
        if el.get("stroke-width"):
            sw = float(el.get("stroke-width"))
        if el.tag == ns + "circle":
            cx, cy, r = float(el.get("cx")), float(el.get("cy")), float(el.get("r"))
            d = ImageDraw.Draw(img)
            box = [(cx - r) * scale, (cy - r) * scale, (cx + r) * scale, (cy + r) * scale]
            if fill:
                d.ellipse(box, fill=fill)
            if stroke and sw > 0:
                d.ellipse(box, outline=stroke, width=max(1, int(round(sw * scale))))
        if el.tag == ns + "path" and el.get("d"):
            subpaths = flatten_path(el.get("d"))
            if fill:
                mask = Image.new("1", (size, size), 0)
                for sp in subpaths:
                    if len(sp) < 3:
                        continue
                    poly = Image.new("1", (size, size), 0)
                    pd = ImageDraw.Draw(poly)
                    pd.polygon([(px * scale, py * scale) for px, py in sp], fill=1)
                    mask = ImageChops.logical_xor(mask, poly)
                solid = Image.new("RGBA", (size, size), fill)
                img.paste(solid, (0, 0), mask.convert("L"))
            if stroke and sw > 0:
                d = ImageDraw.Draw(img)
                w = max(1, int(round(sw * scale)))
                r = w / 2
                for sp in subpaths:
                    pts = [(px * scale, py * scale) for px, py in sp]
                    if len(pts) >= 2:
                        d.line(pts, fill=stroke, width=w, joint="curve")
                    for px, py in pts:
                        d.ellipse([px - r, py - r, px + r, py + r], fill=stroke)
        for child in el:
            walk(child, fill, stroke, sw)

    walk(root, (0, 0, 0, 255), (0, 0, 0, 255), 1.5)
    img = img.resize((OUT_SIZE, OUT_SIZE), Image.LANCZOS)
    img.save(out_path)


if __name__ == "__main__":
    for name in ["wK", "wQ", "wR", "wB", "wN", "wP", "bK", "bQ", "bR", "bB", "bN", "bP"]:
        render_svg(os.path.join(PIECES, name + ".svg"), os.path.join(PIECES, name + ".png"))
        print("rendered", name)