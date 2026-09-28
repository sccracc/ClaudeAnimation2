"""Props & set pieces (bedroom, night exterior, dream objects)."""
import math, functools
import numpy as np
import skia
from engine import *
import chars

lru = functools.lru_cache(None)

# ======================================================================= layer cache (static artwork -> image)
_LAYERS = {}

def cached_layer(key, draw_fn, w=W, h=H, scale=1.5, ox=0, oy=0):
    """Render static artwork once (per key) into a hi-res image; returns (image, scale, ox, oy)."""
    if key not in _LAYERS:
        s = new_surface(int(w * scale), int(h * scale)); c = s.getCanvas()
        c.clear(skia.ColorTRANSPARENT)
        c.scale(scale, scale); c.translate(-ox, -oy)
        draw_fn(c)
        _LAYERS[key] = (s.makeImageSnapshot().withDefaultMipmaps(), scale, ox, oy)
    return _LAYERS[key]

def draw_layer(c, layer, alpha=1.0):
    img, scale, ox, oy = layer
    c.save(); c.translate(ox, oy); c.scale(1 / scale, 1 / scale)
    p = skia.Paint(AntiAlias=True)
    if alpha < 1: p.setAlphaf(alpha)
    c.drawImage(img, 0, 0, SAMP, p)
    c.restore()

# ======================================================================= sky bits
@lru
def _star(r, seed):
    return rough_path(p_star(0, 0, r, r * 0.46), seed, 0.35)

def star(c, x, y, r, t, seed, col=None, b=0, spark=True):
    tw_ = 1 + 0.12 * math.sin(t * 2.3 + seed) if spark else 1
    c.save(); c.translate(x, y); c.rotate(wig(t, 0.5, seed) * 12); c.scale(tw_, tw_)
    piece(c, _star(int(r), seed), col if col is not None else C['gold'], seed, 0.8, 0.25)
    c.restore()
    if spark and (math.sin(t * 1.7 + seed * 1.3) > 0.55):
        for a in range(4):
            ang = math.radians(a * 90 + 45)
            ink(c, [(x + math.cos(ang) * r * 1.3, y + math.sin(ang) * r * 1.3), (x + math.cos(ang) * r * 1.9, y + math.sin(ang) * r * 1.9)],
                2.2, seed + a, b, color=C['cream'], alpha=0.7)

@lru
def _moon(r):
    return rough_path(p_diff(p_circle(0, 0, r), p_circle(r * 0.45, -r * 0.32, r * 0.9)), 31, 0.7)

def moon(c, x, y, r, t, b, face=True):
    glow(c, x - r * 0.2, y + r * 0.1, r * 2.8, C['gold'], 0.22)
    c.save(); c.translate(x, y); c.rotate(-8 + wig(t, 0.3, 5) * 4)
    mp = _moon(int(r))
    piece(c, mp, C['cream'], 32, 1.6, 0.25)
    c.save(); c.clipPath(mp, skia.ClipOp.kIntersect, True)
    crayon(c, p_circle(-r * 0.45, r * 0.35, r * 0.18), C['cream2'], 33, 0.8)
    crayon(c, p_circle(-r * 0.62, -r * 0.2, r * 0.1), C['cream2'], 34, 0.8)
    c.restore()
    if face:
        chars.eye_closed(c, -r * 0.55, -r * 0.05, r * 0.2, 35, b, lw=max(2.0, r * 0.035))
        chars.cheek(c, -r * 0.62, r * 0.22, r * 0.1, 36, 0.6)
    c.restore()

@lru
def _cloud(w, h, seed):
    return rough_path(p_cloud(0, 0, w, h, 5, seed), seed, 1.0)

def cloud(c, x, y, w, h, seed, col=None, elev=1.2, b=0, outline=True):
    c.save(); c.translate(x, y)
    cp = _cloud(int(w), int(h), seed)
    piece(c, cp, col if col is not None else C['cream'], seed, elev, 0.25)
    if outline:
        pencil(c, path_points(cp, 5)[0][: len(path_points(cp, 5)[0]) // 2], 1.8, seed, b, alpha=0.35, passes=1)
    c.restore()

# ======================================================================= houses / exterior
@lru
def _house(w, h, roof, seed):
    body = rough_path(p_rect(-w / 2, -h, w, h), seed, 0.9)
    rf = rough_path(p_poly([(-w / 2 - 22, -h + 8), (0, -h - roof), (w / 2 + 22, -h + 8)]), seed + 1, 0.9)
    return body, rf

def house(c, x, y, w, h, roof, col, roof_col, seed, b, windows=(), lit=1.0, chimney=True):
    c.save(); c.translate(x, y)
    body, rf = _house(int(w), int(h), int(roof), seed)
    if chimney:
        piece(c, rough_path(p_rect(w * 0.18, -h - roof * 0.75, 26, roof * 0.6), seed + 9, 0.6), C['wood2'], seed + 9, 1.0)
    piece(c, body, col, seed, 1.4)
    piece(c, rf, roof_col, seed + 1, 1.6)
    for i, (wx, wy, ww, wh) in enumerate(windows):
        glow(c, wx + ww / 2, wy + wh / 2, ww * 1.6, C['gold'], 0.35 * lit)
        wp = rough_path(p_rect(wx, wy, ww, wh, 3), seed + 20 + i, 0.4)
        piece(c, wp, mix(C['night3'], C['gold'], lit), seed + 20 + i, 0.3, 0.2)
        ink(c, [(wx + ww / 2, wy + 2), (wx + ww / 2, wy + wh - 2)], 2.2, seed + 30 + i, b, alpha=0.8)
        ink(c, [(wx + 2, wy + wh / 2), (wx + ww - 2, wy + wh / 2)], 2.2, seed + 40 + i, b, alpha=0.8)
    c.restore()

# ======================================================================= bedroom
BED_X, BED_Y, BED_S = 960, 975, 1.22
HEAD_POS = (BED_X + (-238) * BED_S, BED_Y + (-232) * BED_S)
WIN = (170, 150, 440, 330)   # window rect in the bedroom (x, y, w, h)

def _wall(c):
    fill_paper(c, p_rect(-320, -320, W + 640, 1200), C['wall'], 501)
    # hand-drawn wallpaper: little stars & dots in pencil
    r = rnd(502)
    for j in range(-3, 9):
        for i in range(-3, 19):
            x = 60 + i * 124 + (j % 2) * 62 + r.uniform(-6, 6); y = 50 + j * 96 + r.uniform(-6, 6)
            if (i + j) % 3 == 0:
                c.save(); c.translate(x, y); c.rotate(r.uniform(-20, 20))
                piece(c, _star(9, 503 + (i * 7 + j) % 11), hexc('#56609a'), 504 + i + j, 0.0, edge=False)
                c.restore()
            else:
                c.drawCircle(x, y, 3.2, grain_paint(hexc('#5a64a0'), 'crayon', 505 + i, 1.0, 0.9))
    # skirting board + floor
    fill_paper(c, p_rect(-320, 860, W + 640, 560), C['floor'], 506)
    for k in range(12):
        pencil(c, [(-320, 900 + k * 30 + (k % 2) * 3), (W + 320, 898 + k * 30)], 1.6, 507 + k, 0, alpha=0.35, passes=1)
    for k in range(12):
        x = 80 + k * 160 + (k % 3) * 17
        y0 = 870 + (k % 7) * 30
        pencil(c, [(x, y0), (x + 1, y0 + 30)], 1.4, 520 + k, 0, alpha=0.35, passes=1)
    piece(c, rough_path(p_rect(-320, 846, W + 640, 26), 530, 0.8), C['wood2'], 530, 1.4)
    # rug
    rug = rough_path(p_ellipse(1000, 1030, 560, 60), 531, 1.2)
    piece(c, rug, C['coral2'], 531, 0.6)
    stitches(c, arc(1000, 1030, 520, 44, 180, 360, 60), 532, 0, 10, 8, 2.0, C['cream'], 0.6)

def wall_layer():
    return cached_layer('wall', _wall, w=W + 600, h=H + 600, scale=1.3, ox=-300, oy=-300)

def window_frame(c, b, sky_fn, t, open_=0.0):
    x, y, w, h = WIN
    glass = p_rect(x, y, w, h)
    c.save(); c.clipPath(glass, skia.ClipOp.kIntersect, True)
    sky_fn(c, t, x, y, w, h)
    c.restore()
    frame = p_diff(p_rect(x - 22, y - 22, w + 44, h + 44), p_rect(x, y, w, h))
    piece(c, _winframe(), C['cream2'], 540, 1.4)
    for d in (0,):
        piece(c, rough_path(p_rect(x + w / 2 - 7, y, 14, h), 541, 0.4), C['cream2'], 541, 0.8)
        piece(c, rough_path(p_rect(x, y + h / 2 - 7, w, 14), 542, 0.4), C['cream2'], 542, 0.8)
    # sill
    piece(c, rough_path(p_rect(x - 40, y + h + 14, w + 80, 22, 4), 543, 0.6), C['cream'], 543, 1.6)

@lru
def _winframe():
    x, y, w, h = WIN
    return rough_path(p_diff(p_rect(x - 22, y - 22, w + 44, h + 44), p_rect(x, y, w, h)), 540, 0.7)

@lru
def _curtain(side):
    x, y, w, h = WIN
    if side < 0:
        P = [(x - 70, y - 50), (x + 70, y - 50), (x + 40, y + 120), (x + 10, y + h * 0.55), (x + 30, y + h + 60), (x - 80, y + h + 70)]
    else:
        P = [(x + w - 70, y - 50), (x + w + 70, y - 50), (x + w + 80, y + h + 70), (x + w - 30, y + h + 60), (x + w - 10, y + h * 0.55), (x + w - 40, y + 120)]
    return rough_path(p_blob(P, 8), 550 + side, 1.0)

def curtains(c, t, b):
    x, y, w, h = WIN
    for side in (-1, 1):
        cp = _curtain(side)
        c.save()
        sway = wig(t, 0.4, 551 + side) * 1.2
        c.translate(x + w / 2 + side * (w / 2), y - 50); c.rotate(sway); c.translate(-(x + w / 2 + side * (w / 2)), -(y - 50))
        piece(c, cp, C['sage'], 552 + side, 2.0)
        c.save(); c.clipPath(cp, skia.ClipOp.kIntersect, True)
        for k in range(5):
            xx = x + side * (w / 2) + w / 2 + side * (-50 + k * 26)
            pencil(c, [(xx - side * 30, y - 40), (xx + side * 10, y + h + 60)], 1.8, 553 + k + side, b, alpha=0.4, passes=1)
        c.restore()
        c.restore()
    # rod
    piece(c, rough_path(p_rect(x - 110, y - 62, w + 220, 14, 7), 556, 0.5), C['wood2'], 556, 1.6)
    for sx in (x - 116, x + w + 104):
        piece(c, rough_path(p_circle(sx + 6, y - 55, 14), 557, 0.4), C['mustard'], 557, 1.6)

def night_sky(c, t, x, y, w, h, dawn=0.0, sun=0.0):
    col = mix(C['night2'], hexc('#f4b08a'), dawn)
    fill_paper(c, p_rect(x - 5, y - 5, w + 10, h + 10), col, 560)
    if dawn > 0:
        sh = skia.GradientShader.MakeLinear([skia.Point(x, y), skia.Point(x, y + h)],
                                            [with_alpha(hexc('#f7d7a0'), 0), with_alpha(hexc('#fbe3b0'), 0.9 * dawn)])
        c.drawRect(skia.Rect.MakeXYWH(x, y, w, h), skia.Paint(Shader=sh))
    if dawn < 1:
        a = 1 - dawn
        for i, (sx, sy, r) in enumerate([(x + 60, y + 60, 12), (x + 170, y + 110, 8), (x + 330, y + 50, 10), (x + 250, y + 200, 7), (x + 90, y + 220, 7)]):
            c.save(); c.translate(0, -dawn * 80)
            star(c, sx, sy, r, t, 570 + i, C['gold'] if i % 2 else C['cream'])
            c.restore()
        c.save(); c.translate(0, dawn * 260)
        moon(c, x + w * 0.72, y + h * 0.32, 52, t, 0)
        c.restore()
    if sun > 0:
        sy = y + h + 80 - sun * (h * 0.62)
        glow(c, x + w * 0.5, sy, 260, C['sun'], 0.6)
        piece(c, _sun_path(x + w * 0.5, sy), C['sun'], 575, 1.2)
    # far rooftops
    fill_paper(c, _roofs(), mix(C['deepteal'], hexc('#c98a6a'), dawn), 576)

def _sun_path(x, y):
    p = skia.Path(_sun()); p.offset(x, y); return p

@lru
def _sun():
    return rough_path(p_circle(0, 0, 58), 575, 0.8)

@lru
def _roofs():
    x, y, w, h = WIN
    P = [(x - 10, y + h + 10), (x - 10, y + h - 40), (x + 50, y + h - 40), (x + 50, y + h - 80), (x + 90, y + h - 110), (x + 130, y + h - 80),
         (x + 130, y + h - 50), (x + 210, y + h - 50), (x + 210, y + h - 95), (x + 260, y + h - 95), (x + 260, y + h - 60), (x + 330, y + h - 60),
         (x + 360, y + h - 100), (x + 390, y + h - 60), (x + w + 10, y + h - 60), (x + w + 10, y + h + 10)]
    return rough_path(p_poly(P), 577, 0.8)

@lru
def _nightstand():
    return rough_path(p_rect(1560, 700, 230, 170, 6), 580, 0.9), rough_path(p_rect(1545, 686, 260, 24, 5), 581, 0.8)

def nightstand(c, t, b, ring=0.0, toast=0.0, lamp=1.0):
    body, top = _nightstand()
    piece(c, body, C['wood'], 582, 1.8)
    piece(c, top, C['wood2'], 583, 1.8)
    piece(c, rough_path(p_rect(1580, 745, 190, 60, 4), 584, 0.6), mix(C['wood'], C['cream'], 0.15), 584, 0.5)
    ink_dots(c, [(1675, 775)], 6, 585, b, C['mustard'])
    # legs
    for lx in (1570, 1760):
        piece(c, rough_path(p_rect(lx, 866, 20, 30, 3), 586 + lx, 0.4), C['wood2'], 586, 1.0)
    # lamp
    lx, ly = 1610, 686
    piece(c, rough_path(p_rect(lx - 6, ly - 90, 12, 90), 590, 0.4), C['cream2'], 590, 1.0)
    piece(c, rough_path(p_ellipse(lx, ly - 4, 36, 10), 591, 0.4), C['wood2'], 591, 1.0)
    shade = rough_path(p_poly([(lx - 55, ly - 90), (lx - 30, ly - 170), (lx + 30, ly - 170), (lx + 55, ly - 90)]), 592, 0.8)
    if lamp > 0:
        glow(c, lx, ly - 110, 280, C['gold'], 0.45 * lamp)
    piece(c, shade, mix(C['coral2'], C['gold'], 0.55 * lamp), 593, 1.6)
    stitches(c, [(lx - 50, ly - 100), (lx + 50, ly - 100)], 594, b, 7, 6, 1.6, alpha=0.5)
    # alarm clock (rings: shakes)
    cx, cy = 1700, 640
    sh = math.sin(t * 60) * 6 * ring
    c.save(); c.translate(cx + sh * 0.5, cy); c.rotate(sh)
    for s in (-1, 1):
        piece(c, rough_path(p_circle(s * 26, -40, 13), 595 + s, 0.4), C['mustard'], 595, 1.0)
    piece(c, rough_path(p_circle(0, 0, 44), 597, 0.6), C['red'], 597, 1.4)
    piece(c, rough_path(p_circle(0, 0, 34), 598, 0.4), C['cream'], 598, 0.4)
    ink(c, [(0, 0), (0, -24)], 3.2, 599, b); ink(c, [(0, 0), (16, 6)], 3.2, 600, b)
    for k in range(12):
        a = math.radians(k * 30)
        c.drawCircle(math.cos(a) * 27, math.sin(a) * 27, 1.8, skia.Paint(AntiAlias=True, Color=C['ink']))
    c.restore()
    if ring > 0.05:
        for k in range(3):
            a = -60 + k * 30
            r0 = 60 + 10 * math.sin(t * 30 + k)
            ink(c, [(cx + math.cos(math.radians(a - 90)) * r0 * 0.9, cy - 20 + math.sin(math.radians(a - 90)) * r0 * 0.9),
                    (cx + math.cos(math.radians(a - 90)) * r0 * 1.25, cy - 20 + math.sin(math.radians(a - 90)) * r0 * 1.25)], 3.0, 601 + k, b, alpha=ring)
    # toaster
    tx, ty = 1560, 686
    if toast > 0:
        up = spring(toast, 1.6, 4.5) * 70
        for k, dx in enumerate((-18, 14)):
            c.save(); c.translate(tx + 190 + dx, ty - 60 - up * (1 - 0.15 * k)); c.rotate(-6 + k * 10)
            piece(c, _toast(), hexc('#e0a45c'), 610 + k, 1.2)
            piece(c, _toast_in(), hexc('#f2d49a'), 612 + k, 0.2, edge=False)
            c.restore()

@lru
def _toast():
    return rough_path(p_blob([(-26, 30), (-28, -10), (-34, -30), (-18, -44), (0, -38), (18, -44), (34, -30), (28, -10), (26, 30)], 6), 614, 0.6)

@lru
def _toast_in():
    return rough_path(p_blob([(-18, 24), (-20, -8), (-24, -26), (-12, -34), (0, -29), (12, -34), (24, -26), (20, -8), (18, 24)], 6), 615, 0.5)

def toaster_front(c, t, b):
    tx, ty = 1560 + 190, 686
    tp = rough_path(p_rect(tx - 60, ty - 80, 120, 80, 18), 620, 0.6)
    piece(c, tp, hexc('#9fb7c4'), 620, 1.4)
    ink(c, [(tx - 40, ty - 60), (tx - 40, ty - 20)], 2.0, 621, b, alpha=0.5)
    ink(c, [(tx + 40, ty - 50), (tx + 50, ty - 50)], 3.0, 622, b)
    c.drawCircle(tx - 30, ty - 70, 3, skia.Paint(AntiAlias=True, Color=C['white']))

def picture_frame(c, t, b):
    # framed cat portrait on the wall (the cat appears in the dream later)
    x, y = 1360, 180
    piece(c, rough_path(p_rect(x, y, 170, 200, 4), 630, 0.7), C['mustard'], 630, 1.8)
    piece(c, rough_path(p_rect(x + 18, y + 18, 134, 164), 631, 0.5), C['cream'], 631, 0.3)
    c.save(); c.translate(x + 85, y + 150); c.scale(0.55, 0.55)
    cat(c, t, b, 0)
    c.restore()
    ink(c, [(x + 85, y - 50), (x + 20, y + 2)], 2.0, 632, b, alpha=0.7)
    ink(c, [(x + 85, y - 50), (x + 150, y + 2)], 2.0, 633, b, alpha=0.7)
    c.drawCircle(x + 85, y - 50, 5, skia.Paint(AntiAlias=True, Color=C['ink']))

def shelf(c, t, b):
    x, y = 1240, 520
    piece(c, rough_path(p_rect(x, y, 300, 18, 3), 640, 0.6), C['wood2'], 640, 1.6)
    c.save(); c.translate(x + 90, y); c.scale(0.5, 0.5)
    toy_boat(c, t, b)
    c.restore()
    # little stack of books
    for k, (col, hh) in enumerate([(C['blue'], 70), (C['coral'], 60), (C['sage'], 76)]):
        piece(c, rough_path(p_rect(x + 190 + k * 26, y - hh, 24, hh, 3), 641 + k, 0.4), col, 641 + k, 1.0)

# ======================================================================= cat
@lru
def _cat_parts():
    body = rough_path(p_blob([(-50, 0), (-58, -50), (-40, -100), (0, -118), (40, -100), (56, -50), (50, 0)], 8), 650, 0.9)
    head = rough_path(p_union(p_ellipse(0, -140, 52, 44), p_poly([(-48, -150), (-40, -205), (-12, -176)]), p_poly([(48, -150), (40, -205), (12, -176)])), 651, 0.8)
    tail = ink_path(catmull([(40, -10), (90, -20), (110, -70), (90, -110)]), 18, 652, 0, taper=(0.0, 0.5), jitter=0)
    return body, head, tail

def cat(c, t, b, seed=0, eyes='closed', col=None, talk=0.0, tail_wave=0.0):
    col = col if col is not None else hexc('#e59a52')
    body, head, tail = _cat_parts()
    c.save(); c.rotate(math.sin(t * 2.0) * 6 * tail_wave)
    piece(c, tail, col, 653, 1.0)
    c.restore()
    piece(c, body, col, 654, 1.3)
    for k in range(3):
        ink(c, [(-40 + k * 8, -90 + k * 22), (-18 + k * 6, -84 + k * 22)], 3.0, 655 + k, b, alpha=0.6)
    piece(c, head, col, 658, 1.3)
    for sx in (-1, 1):
        crayon(c, p_poly([(sx * 40, -160), (sx * 36, -192), (sx * 18, -172)]), C['pink'], 659 + sx, 0.8)
    if eyes == 'closed':
        chars.eye_closed(c, -20, -140, 16, 660, b, lw=3.2)
        chars.eye_closed(c, 20, -140, 16, 661, b, lw=3.2)
    else:
        chars.eye_open(c, -20, -142, 6, 660, b, white=False)
        chars.eye_open(c, 20, -142, 6, 661, b, white=False)
    c.drawCircle(0, -126, 5, skia.Paint(AntiAlias=True, Color=C['pink2']))
    if talk > 0:
        chars.mouth(c, 0, -112, 16, 'o', 662, b, talk)
    else:
        ink(c, [(-8, -116), (0, -120), (8, -116)], 2.4, 662, b)
    for sx in (-1, 1):
        for k in range(2):
            ink(c, [(sx * 26, -124 + k * 8), (sx * 62, -130 + k * 12)], 1.6, 663 + k + sx, b, alpha=0.7)

# ======================================================================= boats / school / fish
@lru
def _toy_boat():
    hull = rough_path(p_poly([(-80, -40), (80, -40), (60, 0), (-60, 0)]), 670, 0.6)
    sail = rough_path(p_poly([(0, -170), (0, -50), (70, -50)]), 671, 0.6)
    sail2 = rough_path(p_poly([(-6, -150), (-6, -50), (-60, -50)]), 672, 0.6)
    return hull, sail, sail2

def toy_boat(c, t, b):
    hull, sail, sail2 = _toy_boat()
    ink(c, [(0, -175), (0, -40)], 4, 673, b)
    piece(c, sail2, C['cream'], 674, 1.0)
    piece(c, sail, C['white'], 675, 1.2)
    piece(c, hull, C['red'], 676, 1.4)
    stitches(c, [(-66, -22), (66, -22)], 677, b, 8, 6, 2.0, C['cream'], 0.8)

@lru
def _school():
    d = {}
    d['body'] = rough_path(p_rect(-230, -260, 460, 260), 700, 1.0)
    d['roof'] = rough_path(p_poly([(-260, -250), (0, -370), (260, -250)]), 701, 1.0)
    d['tower'] = rough_path(p_rect(-50, -470, 100, 150), 702, 0.8)
    d['troof'] = rough_path(p_poly([(-70, -462), (0, -540), (70, -462)]), 703, 0.8)
    d['clock'] = rough_path(p_circle(0, -300, 34), 704, 0.5)
    d['door'] = rough_path(p_union(p_rect(-36, -110, 72, 110), p_circle(0, -110, 36)), 705, 0.6)
    d['hull'] = rough_path(p_blob([(-330, -10), (330, -10), (300, 60), (240, 120), (-240, 120), (-300, 60)], 6), 706, 1.2)
    d['bell'] = rough_path(p_blob([(-18, 0), (-14, -26), (0, -34), (14, -26), (18, 0)], 5), 707, 0.4)
    d['flag'] = rough_path(p_poly([(0, 0), (80, 18), (0, 40)]), 708, 0.5)
    return d

def school_boat(c, t, b, bell=0.0):
    d = _school()
    # mast + flag
    ink(c, [(170, -250), (170, -470)], 6, 709, b)
    c.save(); c.translate(172, -470); c.scale(1 + 0.08 * math.sin(t * 5), 1); c.skew(0, 0.08 * math.sin(t * 4.3))
    piece(c, d['flag'], C['mustard'], 710, 1.0)
    c.restore()
    piece(c, d['tower'], C['brick'], 711, 1.4)
    c.save(); c.translate(0, -360); c.rotate(math.sin(t * 3.4) * 16 * bell)
    piece(c, d['bell'], C['gold'], 712, 0.8)
    c.restore()
    piece(c, d['troof'], C['wood2'], 713, 1.6)
    piece(c, d['body'], C['brick'], 714, 1.8)
    # brick pencil marks
    for j in range(7):
        for i in range(8):
            x = -210 + i * 58 + (j % 2) * 29; y = -240 + j * 34
            if (i * 3 + j) % 4 == 0:
                pencil(c, [(x, y), (x + 30, y)], 1.6, 715 + i + j * 8, b, alpha=0.35, passes=1)
    piece(c, d['roof'], C['wood2'], 780, 2.0)
    piece(c, d['clock'], C['cream'], 781, 0.8)
    ink(c, [(0, -300), (0, -322)], 3, 782, b); ink(c, [(0, -300), (14, -294)], 3, 783, b)
    # windows
    for i, x in enumerate((-170, -100, 70, 140)):
        for j, y in enumerate((-220, -140)):
            wp = rough_path(p_rect(x, y, 44, 54, 3), 784 + i * 2 + j, 0.4)
            piece(c, wp, C['gold'], 784 + i * 2 + j, 0.4, 0.2)
            ink(c, [(x + 22, y + 2), (x + 22, y + 52)], 2, 800 + i * 2 + j, b, alpha=0.8)
    piece(c, d['door'], C['blue2'], 810, 0.8)
    c.drawCircle(18, -50, 4, skia.Paint(AntiAlias=True, Color=C['gold']))
    piece(c, rough_path(p_rect(-62, -232, 124, 40, 4), 811, 0.4), C['cream'], 811, 0.8)
    hand_text(c, 'SCHOOL', 0, -202, 28, C['ink'], HAND, 812, b, jitter=0.5)
    # hull
    piece(c, d['hull'], C['wood'], 812, 2.2)
    for k in range(3):
        ink(c, [(-300 + k * 10, 20 + k * 30), (300 - k * 20, 20 + k * 30)], 2.2, 813 + k, b, alpha=0.45)
    for k, x in enumerate((-200, -80, 40, 160)):
        piece(c, rough_path(p_circle(x, 45, 16), 820 + k, 0.4), C['cream'], 820 + k, 0.4)
        ink(c, arc(x, 45, 16, 16, 0, 360, 24), 2.4, 824 + k, b, closed=True, alpha=0.8)

@lru
def _fish(seed):
    body = rough_path(p_blob([(-60, 0), (-20, -30), (30, -26), (60, 0), (30, 26), (-20, 30)], 8), seed, 0.6)
    tail = rough_path(p_poly([(-50, 0), (-90, -32), (-80, 0), (-90, 32)]), seed + 1, 0.6)
    return body, tail

def fish(c, t, b, seed=900, col=None, eye=True, wiggle=0.0):
    col = col if col is not None else C['coral']
    body, tail = _fish(seed)
    c.save(); c.translate(-50, 0); c.rotate(math.sin(t * 12) * 18 * wiggle); c.translate(50, 0)
    piece(c, tail, mix(col, C['ink'], 0.12), seed + 2, 1.0)
    c.restore()
    piece(c, body, col, seed + 3, 1.2)
    c.save(); c.clipPath(body, skia.ClipOp.kIntersect, True)
    for k in range(3):
        ink(c, arc(-10 + k * 16, 0, 14, 22, 120, 240, 10), 2.0, seed + 4 + k, b, alpha=0.45)
    c.restore()
    ink(c, arc(22, 0, 12, 20, -70, 70, 10), 2.4, seed + 8, b, alpha=0.7)
    if eye:
        chars.eye_open(c, 36, -6, 6, seed + 9, b, white=False)

# ======================================================================= thought cloud / film / clapper / star badge
@lru
def _thought_cloud(w, h):
    return rough_path(p_cloud(0, 0, w, h, 6, 950), 950, 1.2)

def thought(c, t, b, x, y, w, h, grow, head, content=None, bubbles=1.0, col=None):
    """Thought cloud centred at (x,y); `grow` 0..1 (spring it); little bubbles lead from `head`."""
    hx, hy = head
    for i in range(3):
        u = (i + 1) / 4
        g = clamp(bubbles * 3 - i)
        if g <= 0: continue
        bx = lerp(hx, x - w * 0.25, u); by = lerp(hy, y + h * 0.42, u)
        r = (10 + i * 7) * ease_out_back(g)
        c.save(); c.translate(bx, by); c.scale(r / 20, r / 20)
        piece(c, _bub(i), col if col is not None else C['cream'], 951 + i, 1.0)
        c.restore()
    if grow <= 0.001: return None
    c.save(); c.translate(x, y); c.scale(grow, grow)
    cp = _thought_cloud(int(w), int(h))
    piece(c, cp, col if col is not None else C['cream'], 955, 2.2, 0.35)
    if content is not None:
        c.save(); c.clipPath(cp, skia.ClipOp.kIntersect, True)
        content(c)
        c.restore()
    pts = path_points(cp, 5)[0]
    ink(c, pts, 2.6, 956, b, closed=True, alpha=0.5, jitter=1.3)
    c.restore()
    return cp

@lru
def _bub(i):
    return rough_path(p_circle(0, 0, 20), 951 + i, 0.4)

def filmstrip(c, t, b, x, y, length, offset, frames, fh=120):
    """Horizontal film strip centred at (x,y), scrolling by `offset`; frames = list of draw fns (c, w, h)."""
    fw = fh * 1.25
    c.save(); c.translate(x, y); c.rotate(-4)
    strip = rough_path(p_rect(-length / 2, -fh / 2 - 26, length, fh + 52, 4), 960, 0.6)
    piece(c, strip, hexc('#3a3340'), 961, 1.6)
    c.save(); c.clipPath(strip, skia.ClipOp.kIntersect, True)
    n = int(length / (fw + 20)) + 3
    off = offset % (fw + 20)
    for i in range(-1, n):
        fx = -length / 2 + i * (fw + 20) - off + 10
        fp = rough_path(p_rect(0, 0, fw, fh, 3), 962 + (i % 3), 0.4)
        c.save(); c.translate(fx, -fh / 2)
        piece(c, fp, C['cream'], 963 + i % 5, 0.2, 0.2, edge=False)
        k = int((i + math.floor(offset / (fw + 20)))) % len(frames)
        c.save(); c.clipPath(fp, skia.ClipOp.kIntersect, True); frames[k](c, fw, fh); c.restore()
        c.restore()
        for j in range(4):
            hx = fx + j * (fw + 20) / 4
            for hy in (-fh / 2 - 15, fh / 2 + 15):
                c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(hx, hy - 6, 14, 12), 3, 3), skia.Paint(AntiAlias=True, Color=C['cream2']))
    c.restore()
    c.restore()

def clapper(c, t, b, open_=0.0):
    """Clapperboard; origin bottom-centre; open_ 0..1 lifts the top stick."""
    board = rough_path(p_rect(-120, -150, 240, 150, 6), 970, 0.7)
    piece(c, board, hexc('#2f2a36'), 971, 1.6)
    hand_text(c, 'DREAM', 0, -92, 40, C['cream'], HAND, 972, b)
    hand_text(c, 'scene 1', -58, -34, 26, C['cream'], HAND2, 973, b)
    hand_text(c, 'take 1', 62, -34, 26, C['cream'], HAND2, 974, b)
    ink(c, [(-110, -66), (110, -66)], 2.0, 975, b, color=C['cream'], alpha=0.7)
    ink(c, [(0, -64), (0, -12)], 2.0, 976, b, color=C['cream'], alpha=0.7)
    c.save(); c.translate(-120, -152); c.rotate(-28 * open_)
    stick = rough_path(p_rect(0, -34, 240, 34, 4), 977, 0.6)
    piece(c, stick, C['cream'], 978, 1.4)
    c.save(); c.clipPath(stick, skia.ClipOp.kIntersect, True)
    for k in range(6):
        fill_paper(c, p_poly([(k * 44, 0), (k * 44 + 22, 0), (k * 44 + 44, -34), (k * 44 + 22, -34)]), hexc('#2f2a36'), 979 + k)
    c.restore()
    c.restore()

@lru
def _badge():
    return rough_path(p_star(0, 0, 120, 62), 990, 0.8)

def star_badge(c, t, b, scale):
    if scale <= 0.01: return
    c.save(); c.scale(scale, scale); c.rotate(-8 + wig(t, 0.8, 991) * 5)
    piece(c, _badge(), C['gold'], 992, 2.0, 0.35)
    ink(c, path_points(_badge(), 5)[0], 2.4, 993, b, closed=True, alpha=0.5)
    c.save(); c.translate(0, 8); c.scale(0.62, 0.62)
    chars.sleeper_head(c, t, b, eyes='happy', mouth_kind='smile', sway=0.4)
    c.restore()
    c.restore()

def sparkle(c, x, y, r, t0, t, b, seed=0, col=None):
    p = prog(t, t0, t0 + 0.6)
    if p <= 0 or p >= 1: return
    for k in range(8):
        a = math.radians(k * 45 + seed * 7)
        r0 = r * (0.4 + 0.9 * ease_out(p)); r1 = r0 + r * 0.35 * (1 - p)
        ink(c, [(x + math.cos(a) * r0, y + math.sin(a) * r0), (x + math.cos(a) * r1, y + math.sin(a) * r1)], 3.2 * (1 - p) + 0.8, seed + k, b,
            color=col if col is not None else C['gold'], alpha=1 - p * 0.5)

# ======================================================================= pencil sprite, stamp
@lru
def _pencil_parts():
    body = rough_path(p_rect(0, -14, 260, 28, 2), 1001, 0.4)
    wood = rough_path(p_poly([(0, -14), (-46, 0), (0, 14)]), 1002, 0.4)
    lead = rough_path(p_poly([(-30, -5), (-48, 0), (-30, 5)]), 1003, 0.2)
    ferrule = rough_path(p_rect(260, -15, 26, 30, 2), 1004, 0.3)
    eraser = rough_path(p_rect(286, -14, 34, 28, 8), 1005, 0.3)
    return body, wood, lead, ferrule, eraser

def pencil_sprite(c, x, y, ang, b):
    """Pencil with its graphite tip at (x,y), angled `ang` degrees."""
    body, wood, lead, ferrule, eraser = _pencil_parts()
    c.save(); c.translate(x, y); c.rotate(ang); c.translate(48, 0)
    piece(c, body, C['mustard'], 1006, 3.0, 0.3)
    ink(c, [(4, -4), (256, -4)], 1.6, 1007, b, alpha=0.35)
    piece(c, wood, hexc('#e8c79a'), 1008, 3.0, 0.3)
    piece(c, lead, C['ink'], 1009, 0.2, 0.1)
    piece(c, ferrule, C['grey'], 1010, 3.0, 0.3)
    for k in range(3):
        ink(c, [(266 + k * 7, -14), (266 + k * 7, 14)], 1.4, 1011 + k, b, alpha=0.5)
    piece(c, eraser, C['pink'], 1014, 3.0, 0.3)
    c.restore()

@lru
def _stamp_parts():
    handle = rough_path(p_union(p_circle(0, -150, 34), p_rect(-16, -130, 32, 90, 6)), 1020, 0.5)
    block = rough_path(p_rect(-80, -44, 160, 36, 5), 1021, 0.5)
    rubber = rough_path(p_rect(-74, -10, 148, 12, 2), 1022, 0.3)
    return handle, block, rubber

def rubber_stamp(c, x, y, lift, b, squash=0.0):
    """Stamp whose rubber face sits at (x,y) when lift=0."""
    handle, block, rubber = _stamp_parts()
    c.save(); c.translate(x, y - lift); c.scale(1 + 0.06 * squash, 1 - 0.1 * squash)
    piece(c, handle, C['wood'], 1023, 2.4 + lift / 60, 0.3)
    piece(c, block, C['wood2'], 1024, 2.4 + lift / 60, 0.3)
    piece(c, rubber, C['red'], 1025, 0.4, 0.2)
    c.restore()

def stamp_mark(c, x, y, text, t0, t, b, rot=-6, size=58, col=None):
    """Red rubber-stamp imprint (appears at t0)."""
    if t < t0: return
    col = col if col is not None else hexc('#c8433a')
    c.save(); c.translate(x, y); c.rotate(rot)
    w = text_width(text, size, HAND) + 40; h = size * 1.15
    br = ink_path(np.array([(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)], float), 5, 1030 + int(x), 0, closed=True, jitter=0.6)
    c.drawPath(br, grain_paint(col, 'crayon', 1031 + int(x), 0.7, 0.9))
    f = skia.Font(typeface(HAND), size)
    blob = skia.TextBlob.MakeFromString(text, f)
    tw_ = f.measureText(text)
    c.drawTextBlob(blob, -tw_ / 2, size * 0.34, grain_paint(col, 'crayon', 1032 + int(x), 0.7, 0.95))
    c.restore()
