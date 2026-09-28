"""Characters and props, all built from the collage engine primitives.

Every function draws around a local origin; callers position with canvas transforms.
`b` is the line-boil index (0..2); `t` is time in seconds (already quantised to twos by callers when wanted).
"""
import math, functools
import numpy as np
import skia
from engine import *

lru = functools.lru_cache(None)

# ======================================================================= face kit
def eye_closed(c, x, y, w, seed, b, happy=False, lw=4.0):
    # sleeping eye: a soft downward arc with a tiny lash flick
    if happy:
        P = arc(x, y + w * 0.25, w / 2, w * 0.45, 200, 340, 16)
    else:
        P = arc(x, y - w * 0.15, w / 2, w * 0.40, 20, 160, 16)
    ink(c, P, lw, seed, b, taper=(0.3, 0.3))

def eye_open(c, x, y, r, seed, b, look=(0, 0), blink=0.0, white=True):
    if blink > 0.85:
        ink(c, [(x - r * 1.1, y), (x + r * 1.1, y)], r * 0.45, seed, b); return
    sy = 1 - blink
    if white:
        c.save(); c.translate(x, y); c.scale(1, sy)
        piece(c, _eye_white(round(r)), C['white'], seed, 0.2, 0.2, edge=False)
        c.restore()
        px, py = x + look[0] * r * 0.35, y + look[1] * r * 0.35
        c.save(); c.translate(px, py); c.scale(1, sy)
        c.drawCircle(0, 0, r * 0.55, skia.Paint(AntiAlias=True, Color=C['ink']))
        c.drawCircle(-r * 0.18, -r * 0.2, r * 0.17, skia.Paint(AntiAlias=True, Color=C['white']))
        c.restore()
    else:
        c.save(); c.translate(x + look[0] * r * 0.3, y + look[1] * r * 0.3); c.scale(1, sy)
        c.drawCircle(0, 0, r, skia.Paint(AntiAlias=True, Color=C['ink']))
        c.drawCircle(-r * 0.3, -r * 0.35, r * 0.3, skia.Paint(AntiAlias=True, Color=C['white']))
        c.restore()

@lru
def _eye_white(r):
    return rough_path(p_ellipse(0, 0, r, r * 1.08), r, 0.3)

def cheek(c, x, y, r, seed, alpha=0.75):
    crayon(c, p_circle(x, y, r), C['cheek'], seed, alpha, 0.8)

def mouth(c, x, y, w, kind, seed, b, open_=0.0):
    if kind == 'smile':
        ink(c, arc(x, y - w * 0.25, w / 2, w * 0.4, 20, 160, 14), 3.6, seed, b)
    elif kind == 'o':
        rr = w * (0.18 + 0.12 * open_)
        c.save(); c.translate(x, y); c.scale(1, 1.25)
        piece(c, _mouth_o(), hexc('#7a3445'), seed, 0.15, 0.15, edge=False)
        c.restore()
    elif kind == 'yawn':
        c.save(); c.translate(x, y); c.scale(1 + 0.2 * open_, 0.6 + 1.2 * open_)
        piece(c, _mouth_o(), hexc('#7a3445'), seed, 0.15, 0.15, edge=False)
        c.restore()
    elif kind == 'flat':
        ink(c, [(x - w / 2, y), (x + w / 2, y + 1)], 3.4, seed, b)
    elif kind == 'grin':
        c.save(); c.translate(x, y)
        piece(c, _grin(round(w)), hexc('#7a3445'), seed, 0.15, 0.15, edge=False)
        c.restore()

@lru
def _mouth_o():
    return rough_path(p_ellipse(0, 0, 8, 8), 5, 0.3)

@lru
def _grin(w):
    P = arc(0, 0, w / 2, w * 0.45, 0, 180, 18)
    return rough_path(p_poly(P), 9, 0.4)

# ======================================================================= sleeper head
@lru
def _head(r):
    return rough_path(p_circle(0, 0, r), 101, 0.7)

@lru
def _hair_front():
    P = [(-66, 6), (-62, -30), (-40, -58), (0, -70), (40, -58), (62, -30), (66, 6), (54, -12), (40, -26), (22, -20), (6, -32), (-12, -22), (-30, -30), (-48, -18)]
    return rough_path(p_blob(P, 8), 102, 0.8)

@lru
def _cap(sway_i):
    s = sway_i / 10.0
    tipx, tipy = -150 + s * 30, -40 - s * 10
    P = [(-70, -22), (-60, -62), (-20, -92), (30, -86), (58, -52), (70, -24), (40, -44), (-10, -66), (-60, -62 + 20),
         ]
    # floppy cone that droops toward the left over the pillow
    P = [(-66, -20), (-52, -66), (-10, -98), (40, -92), (68, -48), (70, -22),
         (40, -40), (0, -52), (-40 + s * 6, -44), (-90 + s * 18, -24 - s * 6), (tipx + 12, tipy + 8), (tipx, tipy),
         (tipx - 4, tipy - 14), (-100 + s * 16, -64 - s * 6), (-70, -58)]
    body = p_blob(P, 8)
    return rough_path(body, 103 + sway_i, 0.8), (tipx, tipy)

@lru
def _cap_band():
    P = [(-72, -16), (-60, -40), (0, -52), (60, -40), (74, -16), (60, -6), (0, -20), (-60, -6)]
    return rough_path(p_blob(P, 6), 104, 0.8)

@lru
def _pompom():
    return torn_path(p_circle(0, 0, 20), 105, 2.4)

def sleeper_head(c, t, b, eyes='closed', mouth_kind='o', sway=0.0, breath=0.0, look=(0, 0), blink=0.0, cap=True, seed=0):
    """Head of the dreamer, facing camera, radius ~62. Origin = head centre."""
    s10 = int(round(clamp(sway, -1, 1) * 10))
    if cap:
        cp, tip = _cap(s10)
        # stripes clipped into the cap
        piece(c, cp, C['coral'], 110, 1.2)
        c.save(); c.clipPath(cp, skia.ClipOp.kIntersect, True)
        for k in range(-6, 7):
            q = p_poly([(-200 + k * 38, -160), (-180 + k * 38, -160), (-60 + k * 38, 40), (-80 + k * 38, 40)])
            fill_paper(c, q, C['cream'], 111 + k, soft=True, alpha=0.9)
        c.restore()
        ink(c, path_points(cp, 4)[0], 2.4, 112, b, closed=True, alpha=0.55, jitter=1.4)
    piece(c, _head(62), C['skin'], 120, 1.2)
    piece(c, _hair_front(), C['hair'], 121, 0.6)
    if cap:
        piece(c, _cap_band(), C['cream'], 122, 0.9)
        stitches(c, arc(0, 40, 72, 78, 205, 335, 30), 123, b, 7, 6, 1.6, alpha=0.5)
        c.save(); c.translate(tip[0], tip[1]); c.rotate(wig(t, 0.7, 3) * 8)
        piece(c, _pompom(), C['mustard'], 124, 1.4)
        crayon(c, p_circle(4, 6, 14), C['coral2'], 125, 0.25)
        c.restore()
    # face
    if eyes == 'closed':
        eye_closed(c, -22, 12, 20, 130, b)
        eye_closed(c, 22, 12, 20, 131, b)
    elif eyes == 'happy':
        eye_closed(c, -22, 10, 20, 130, b, happy=True)
        eye_closed(c, 22, 10, 20, 131, b, happy=True)
    else:
        eye_open(c, -22, 8, 9, 130, b, look, blink, white=False)
        eye_open(c, 22, 8, 9, 131, b, look, blink, white=False)
    cheek(c, -38, 28, 13, 132)
    cheek(c, 38, 28, 13, 133)
    ink(c, arc(0, 22, 5, 4, 20, 160, 8), 2.6, 134, b)
    mouth(c, 0, 42, 22, mouth_kind, 135, b, breath)

# ======================================================================= bed
@lru
def _bed_parts():
    d = {}
    d['headboard'] = rough_path(p_union(p_rect(-420, -330, 70, 330, 8), p_circle(-385, -330, 35)), 201, 1.0)
    d['footboard'] = rough_path(p_union(p_rect(350, -230, 60, 230, 8), p_circle(380, -230, 30)), 202, 1.0)
    d['rail'] = rough_path(p_rect(-360, -120, 720, 70, 6), 203, 1.0)
    d['legL'] = rough_path(p_rect(-350, -60, 30, 60, 4), 204, 0.6)
    d['legR'] = rough_path(p_rect(310, -60, 30, 60, 4), 205, 0.6)
    d['mattress'] = rough_path(p_rect(-355, -170, 710, 60, 18), 206, 1.0)
    d['pillow'] = rough_path(p_blob([(-340, -170), (-345, -215), (-300, -250), (-200, -255), (-150, -230), (-140, -185), (-180, -165), (-280, -160)], 8), 207, 1.2)
    return d

@lru
def _quilt(breath_i):
    k = breath_i / 10.0
    top = [(-175, -188), (-120, -222 - 10 * k), (-40, -240 - 14 * k), (60, -228 - 6 * k), (170, -214), (260, -212), (320, -222), (365, -205)]
    P = top + [(378, -150), (384, -70), (330, -60), (-150, -60), (-176, -120)]
    return rough_path(p_blob(P, 8), 210, 1.1), top

QUILT_COLS = ['coral', 'mustard', 'sage', 'cream', 'pink', 'blue', 'lav', 'teal2']

def bed(c, t, b, breath=0.0, head_kw=None, arm_limp=0.0, arm_twitch=0.0, strings=None, draw_head=True, night=1.0, arm_raise=0.0, hand_item=None):
    """Side-view bed, floor at y=0, spanning x -420..410. Sleeper lies with head on the pillow at (-235,-238)."""
    d = _bed_parts()
    piece(c, d['legL'], C['wood2'], 220, 1.0)
    piece(c, d['legR'], C['wood2'], 221, 1.0)
    piece(c, d['headboard'], C['wood'], 222, 2.0)
    for i, x in enumerate([-400, -385, -370]):
        pencil(c, [(x, -300 + i * 10), (x + 3, -30)], 1.6, 223 + i, b, alpha=0.35, passes=1)
    piece(c, d['rail'], C['wood'], 226, 1.6)
    ink(c, [(-340, -86), (340, -84)], 2.0, 227, b, alpha=0.4)
    piece(c, d['mattress'], C['cream2'], 228, 1.2)
    piece(c, d['pillow'], C['white'], 229, 1.4)
    pencil(c, catmull([(-300, -200), (-250, -212), (-200, -205)]), 1.8, 230, b, alpha=0.35, passes=1)
    # head on the pillow
    if draw_head:
        c.save(); c.translate(-238, -232); c.rotate(-8)
        sleeper_head(c, t, b, **(head_kw or {}))
        c.restore()
    # quilt (patchwork) with breathing
    bi = int(round(clamp(breath, 0, 1) * 10))
    qp, top = _quilt(bi)
    shadow(c, qp, 2.0, 0.35)
    c.save(); c.clipPath(qp, skia.ClipOp.kIntersect, True)
    for i in range(-2, 7):
        for j in range(0, 3):
            x0 = -200 + i * 92 + (j % 2) * 30; y0 = -260 + j * 72
            col = C[QUILT_COLS[(i * 3 + j * 5) % len(QUILT_COLS)]]
            fill_paper(c, _patch(i, j), col, 240 + i * 7 + j, soft=True)
            c.save(); c.translate(x0, y0)
            c.restore()
    for i in range(-2, 7):
        x0 = -200 + i * 92
        stitches(c, [(x0 + 60, -270), (x0 + 60, -50)], 250 + i, b, 8, 7, 1.6, alpha=0.5)
    for j in range(0, 3):
        stitches(c, [(-200, -198 + j * 72), (400, -198 + j * 72)], 260 + j, b, 8, 7, 1.6, alpha=0.5)
    c.restore()
    ink(c, path_points(qp, 4)[0], 2.6, 263, b, closed=True, alpha=0.55, jitter=1.2)
    # hem ruffle line
    pencil(c, [(-150, -75), (380, -80)], 1.6, 264, b, alpha=0.35, passes=1)
    # the arm resting on the quilt, emerging from under the turned-down sheet
    arm_on_quilt(c, t, b, arm_limp, arm_twitch, arm_raise, hand_item)
    fp = _fold(bi)
    piece(c, fp, C['white'], 265, 1.2)
    stitches(c, catmull(_fold_line(bi)), 266, b, 7, 6, 1.6, alpha=0.45)
    # footboard in front
    piece(c, d['footboard'], C['wood'], 270, 1.8)
    if strings is not None:
        strings(c)

@lru
def _patch(i, j):
    x0 = -200 + i * 92 + (j % 2) * 30 - 30; y0 = -300 + j * 72 + 30
    return rough_path(p_rect(x0, y0, 96, 76), 300 + i * 11 + j, 0.8)

@lru
def _sleeve():
    return rough_path(p_blob([(0, -16), (60, -20), (120, -16), (128, 0), (120, 16), (60, 18), (0, 16), (-6, 0)], 6), 280, 0.8)

@lru
def _hand(r):
    return rough_path(p_blob([(-r, -r * 0.7), (r * 0.4, -r * 0.95), (r * 1.1, -r * 0.3), (r * 1.1, r * 0.4), (r * 0.3, r * 0.95), (-r, r * 0.7)], 6), 281 + r, 0.6)

ARM_SHOULDER = (-128, -214)

@lru
def _fold_line(bi):
    k = bi / 10.0
    return [(-176, -150), (-150, -206 - 6 * k), (-110, -226 - 10 * k), (-76, -236 - 13 * k)]

@lru
def _fold(bi):
    k = bi / 10.0
    top = [(-182, -186), (-150, -216 - 8 * k), (-100, -236 - 12 * k), (-60, -244 - 14 * k)]
    bot = [(-40, -208 - 10 * k), (-96, -196 - 8 * k), (-140, -170), (-168, -110)]
    return rough_path(p_blob(top + bot, 6), 267 + bi, 0.8)

def arm_on_quilt(c, t, b, limp=0.0, twitch=0.0, raise_=0.0, hand_item=None):
    # arm lies along the quilt; `twitch` lifts the hand a little (dream movement), `limp` drops it flat,
    # `raise_` is the big morning stretch, `hand_item` draws something resting in the hand
    lift = twitch * (1 - limp)
    ang = -6 - 18 * lift + 6 * limp - 62 * raise_
    c.save(); c.translate(*ARM_SHOULDER); c.rotate(ang)
    piece(c, _sleeve(), C['blue'], 282, 1.2)
    c.save(); c.clipPath(_sleeve(), skia.ClipOp.kIntersect, True)
    for k in range(5):
        fill_paper(c, p_rect(8 + k * 26, -30, 10, 60), C['cream'], 283 + k, soft=True, alpha=0.85)
    c.restore()
    c.save(); c.translate(136, 0); c.rotate(-10 * lift + 14 * limp)
    if hand_item is not None:
        hand_item(c)
    piece(c, _hand(17), C['skin'], 284, 1.0)
    ink(c, [(4, -4), (14, -2)], 1.8, 285, b, alpha=0.6)
    c.restore()
    c.restore()

# ======================================================================= standing / seated person rig
@lru
def _torso(kind):
    if kind == 'coat':
        P = [(-44, -10), (-38, -70), (0, -82), (38, -70), (46, -10), (50, 60), (0, 66), (-50, 60)]
    elif kind == 'overalls':
        P = [(-42, -10), (-36, -72), (0, -80), (36, -72), (42, -10), (44, 50), (0, 54), (-44, 50)]
    else:
        P = [(-40, -10), (-36, -72), (0, -80), (36, -72), (40, -10), (42, 40), (0, 46), (-42, 40)]
    return rough_path(p_blob(P, 6), 400 + len(kind), 0.9)

@lru
def _limb(L, w):
    return rough_path(p_rect(-w / 2, 0, w, L, w / 2), 410 + int(L) + int(w), 0.6)

@lru
def _foot():
    return rough_path(p_ellipse(8, 0, 20, 10), 420, 0.5)

@lru
def _beret():
    return rough_path(p_blob([(-58, -40), (-40, -70), (10, -80), (56, -64), (66, -44), (40, -36), (-40, -34)], 6), 430, 0.8)

@lru
def _hardhat():
    return rough_path(p_union(p_blob([(-48, -40), (-44, -76), (0, -96), (44, -76), (48, -40)], 6), p_rect(-66, -46, 132, 14, 6)), 431, 0.8)

@lru
def _hair(style):
    if style == 'tuft':
        P = [(-56, -10), (-54, -44), (-20, -64), (20, -64), (54, -40), (56, -8), (40, -30), (0, -40), (-40, -30)]
    elif style == 'bob':
        P = [(-62, 20), (-60, -40), (-24, -66), (24, -66), (60, -40), (62, 20), (46, 10), (40, -30), (0, -40), (-40, -30), (-46, 10)]
    elif style == 'curly':
        return torn_path(p_union(*[p_circle(math.cos(a) * 44, -18 + math.sin(a) * 34, 22) for a in np.linspace(math.pi, 2 * math.pi, 7)]), 432, 2.0)
    else:
        P = [(-56, -10), (-50, -46), (0, -64), (50, -46), (56, -10), (30, -34), (-30, -34)]
    return rough_path(p_blob(P, 6), 433 + len(style), 0.8)

def person(c, t, b, style, pose=None, seed=0):
    """Generic little paper person, origin at the hips; head centre at about (0,-150). Height ~ 260."""
    pose = pose or {}
    st = dict(skin=C['skin'], shirt=C['blue'], stripes=None, pants=C['blue2'], hat=None, glasses=False, hair='tuft',
              hair_col=C['hair'], torso='shirt', collar=None)
    st.update(style)
    la, ra = pose.get('arm_l', 15), pose.get('arm_r', -15)       # degrees from hanging down (positive = outward)
    ll, rl = pose.get('leg_l', 4), pose.get('leg_r', -4)
    lean = pose.get('lean', 0.0); head_tilt = pose.get('head', 0.0)
    seated = pose.get('seated', False)
    c.save(); c.rotate(lean)
    # legs
    if not seated:
        for side, ang in ((-1, ll), (1, rl)):
            c.save(); c.translate(side * 18, 30); c.rotate(ang)
            piece(c, _limb(78, 26), st['pants'], seed + 10 + side, 1.0)
            c.translate(0, 80); piece(c, _foot(), C['ink'], seed + 12 + side, 0.6)
            c.restore()
    # back arm
    def arm(side, ang, sd):
        c.save(); c.translate(side * 34, -62); c.rotate(-side * ang)
        piece(c, _limb(70, 22), st['shirt'], seed + sd, 1.0)
        if st['stripes'] is not None:
            c.save(); c.clipPath(_limb(70, 22), skia.ClipOp.kIntersect, True)
            for k in range(4):
                fill_paper(c, p_rect(-20, 8 + k * 17, 40, 7), st['stripes'], seed + sd + k, soft=True)
            c.restore()
        c.translate(0, 74); piece(c, _hand(12), st['skin'], seed + sd + 5, 0.8)
        c.restore()
    arm(-1, la, 20)
    # torso
    tp = _torso(st['torso'])
    piece(c, tp, st['shirt'], seed + 30, 1.4)
    if st['stripes'] is not None:
        c.save(); c.clipPath(tp, skia.ClipOp.kIntersect, True)
        for k in range(8):
            fill_paper(c, p_rect(-60, -76 + k * 19, 120, 8), st['stripes'], seed + 31 + k, soft=True)
        c.restore()
    if st['torso'] == 'coat':
        ink(c, [(0, -74), (2, 60)], 2.2, seed + 40, b, alpha=0.6)
        ink(c, [(-14, -76), (0, -40), (14, -76)], 2.2, seed + 41, b, alpha=0.6)
        ink_dots(c, [(8, -20), (8, 10), (8, 40)], 3, seed + 42, b)
    if st['torso'] == 'overalls':
        piece(c, rough_path(p_rect(-28, -40, 56, 50, 6), 450, 0.6), st['pants'], seed + 43, 0.4)
        ink(c, [(-26, -40), (-30, -78)], 5, seed + 44, b, color=st['pants'], alpha=1)
        ink(c, [(26, -40), (30, -78)], 5, seed + 45, b, color=st['pants'], alpha=1)
        ink_dots(c, [(-24, -36), (24, -36)], 4, seed + 46, b, C['mustard'])
    # head
    c.save(); c.translate(0, -140); c.rotate(head_tilt)
    piece(c, _head(52), st['skin'], seed + 50, 1.2)
    piece(c, _hair(st['hair']), st['hair_col'], seed + 51, 0.6)
    eyes = pose.get('eyes', 'open')
    if eyes == 'open':
        lk = pose.get('look', (0, 0)); bl = pose.get('blink', 0.0)
        eye_open(c, -18, 4, 6.5, seed + 52, b, lk, bl, white=False)
        eye_open(c, 18, 4, 6.5, seed + 53, b, lk, bl, white=False)
    elif eyes == 'half':
        for x in (-18, 18):
            c.drawCircle(x, 7, 5.5, skia.Paint(AntiAlias=True, Color=C['ink']))
            fill_paper(c, p_rect(x - 12, -8, 24, 13), st['skin'], seed + 54)
            ink(c, [(x - 10, 5), (x + 10, 5)], 2.6, seed + 55 + x, b)
    else:
        eye_closed(c, -18, 6, 16, seed + 52, b, lw=3.4)
        eye_closed(c, 18, 6, 16, seed + 53, b, lw=3.4)
    if st['glasses']:
        for x in (-18, 18):
            ink(c, arc(x, 5, 14, 13, 0, 360, 30), 2.4, seed + 56 + x, b, closed=True)
        ink(c, [(-5, 3), (5, 3)], 2.2, seed + 58, b)
    cheek(c, -30, 22, 10, seed + 59, 0.6)
    cheek(c, 30, 22, 10, seed + 60, 0.6)
    mouth(c, 0, 30, 18, pose.get('mouth', 'smile'), seed + 61, b, pose.get('mouth_open', 0.0))
    hat = st['hat']
    if hat == 'beret':
        piece(c, _beret(), C['red'], seed + 62, 1.0)
        ink(c, [(10, -80), (14, -92)], 3, seed + 63, b)
    elif hat == 'hardhat':
        piece(c, _hardhat(), C['mustard'], seed + 64, 1.0)
        ink(c, [(0, -94), (0, -46)], 2.0, seed + 65, b, alpha=0.5)
    elif hat == 'nightcap':
        c.save(); c.scale(0.8, 0.8); c.translate(0, 8)
        cp, tip = _cap(int(round(clamp(pose.get('sway', 0), -1, 1) * 10)))
        piece(c, cp, C['coral'], seed + 66, 1.0)
        c.save(); c.clipPath(cp, skia.ClipOp.kIntersect, True)
        for k in range(-6, 7):
            fill_paper(c, p_poly([(-200 + k * 38, -160), (-180 + k * 38, -160), (-60 + k * 38, 40), (-80 + k * 38, 40)]), C['cream'], seed + 67 + k, soft=True, alpha=0.9)
        c.restore()
        piece(c, _cap_band(), C['cream'], seed + 80, 0.8)
        c.save(); c.translate(*tip); piece(c, _pompom(), C['mustard'], seed + 81, 1.2); c.restore()
        c.restore()
    c.restore()
    # front arm
    arm(1, ra, 90)
    c.restore()

# ======================================================================= brain crew
@lru
def _seahorse_body():
    P = [(150, -196), (104, -206), (64, -234), (34, -266), (-18, -252), (-52, -206), (-72, -126), (-78, -40), (-58, 40), (-24, 92),
         (40, 84), (66, 22), (62, -58), (46, -126), (72, -160), (150, -180)]
    body = p_blob(P, 8)
    tail_pts = catmull([(8, 70), (26, 128), (12, 182), (-30, 204), (-66, 184), (-68, 146), (-42, 130), (-26, 150)], 10)
    tail = ink_path(tail_pts, 64, 1601, 0, taper=(0.0, 0.9), jitter=0, press=0.0)
    return rough_path(p_union(body, tail), 1602, 0.9)

@lru
def _seahorse_fin():
    return rough_path(p_blob([(0, 0), (-40, -20), (-70, 10), (-60, 50), (-10, 40)], 6), 1603, 0.6)

@lru
def _crown():
    return rough_path(p_poly([(-14, -250), (-6, -290), (6, -262), (18, -296), (26, -258), (40, -284), (40, -248)]), 1604, 0.5)

def seahorse(c, t, b, look=0.0, fin=0.0, blink=0.0, smile=True, hold=None):
    col = hexc('#ef8f5a')
    # dorsal fin (flutters)
    c.save(); c.translate(-66, -40); c.rotate(10 * math.sin(t * 14) * (0.3 + fin))
    piece(c, _seahorse_fin(), C['gold'], 1605, 0.8)
    for k in range(4):
        ink(c, [(-5, 5), (-30 - k * 8, -10 + k * 16)], 1.8, 1606 + k, b, alpha=0.5)
    c.restore()
    piece(c, _crown(), C['mustard'], 1610, 1.0)
    sp = _seahorse_body()
    piece(c, sp, col, 1611, 1.6)
    c.save(); c.clipPath(sp, skia.ClipOp.kIntersect, True)
    # belly plates
    for k in range(7):
        y = -110 + k * 26
        ink(c, arc(40, y, 40, 10, 150, 210, 10), 2.4, 1612 + k, b, alpha=0.45)
        fill_paper(c, p_rect(-10, y - 5, 90, 12), C['cream'], 1620 + k, soft=True, alpha=0.45)
    # tail rings
    for k in range(6):
        a = math.radians(40 + k * 45)
        cx, cy = -28, 168
        ink(c, [(cx + math.cos(a) * 20, cy + math.sin(a) * 20), (cx + math.cos(a) * 56, cy + math.sin(a) * 56)], 2.2, 1630 + k, b, alpha=0.4)
    c.restore()
    ink(c, path_points(sp, 5)[0], 2.2, 1640, b, closed=True, alpha=0.45, jitter=1.1)
    # face: eye with round glasses
    ex, ey = 58 + look * 4, -200
    eye_open(c, ex, ey, 11, 1641, b, (look, 0), blink, white=True)
    ink(c, arc(58, -200, 24, 24, 0, 360, 30), 3.0, 1642, b, closed=True)
    ink(c, [(34, -204), (-10, -212)], 2.2, 1643, b, alpha=0.8)
    cheek(c, 80, -170, 11, 1644, 0.7)
    if smile:
        ink(c, arc(118, -186, 16, 8, 20, 150, 10), 2.6, 1645, b)

@lru
def _almond():
    return rough_path(p_blob([(0, -120), (40, -84), (64, -20), (60, 40), (34, 78), (0, 88), (-34, 78), (-60, 40), (-64, -20), (-40, -84)], 8), 1700, 0.8)

def almond(c, t, b, glow_amt=0.0, blink=0.0, arm_up=0.0, mood='smile', squash=0.0):
    col = hexc('#d9926a')
    ap = _almond()
    # legs
    for s in (-1, 1):
        ink(c, [(s * 20, 70), (s * 26, 128)], 7, 1701 + s, b)
        piece(c, _foot_at(s), C['ink'], 1703 + s, 0.5)
    # arm (back) holds lantern
    ink(c, [(58, 0), (104, -30 - 30 * arm_up)], 7, 1705, b)
    ink(c, [(-58, 0), (-96, 30 - 50 * arm_up)], 7, 1706, b)
    c.drawCircle(-98, 32 - 50 * arm_up, 12, skia.Paint(AntiAlias=True, Color=C['ink']))
    c.save(); c.scale(1 + 0.05 * squash, 1 - 0.05 * squash)
    piece(c, ap, col, 1707, 1.6)
    c.save(); c.clipPath(ap, skia.ClipOp.kIntersect, True)
    for k in range(5):
        pencil(c, catmull([(-40 + k * 20, -90 + abs(k - 2) * 10), (-46 + k * 22, 0), (-36 + k * 18, 80)]), 1.8, 1708 + k, b, hexc('#8a4a36'), 0.35, passes=1)
    crayon(c, p_circle(26, -60, 30), C['cream'], 1713, 0.25)
    c.restore()
    eye_open(c, -22, -18, 13, 1714, b, (0.3, -0.2), blink, white=True)
    eye_open(c, 22, -18, 13, 1715, b, (0.3, -0.2), blink, white=True)
    cheek(c, -38, 12, 12, 1716, 0.6 + 0.4 * glow_amt)
    cheek(c, 38, 12, 12, 1717, 0.6 + 0.4 * glow_amt)
    mouth(c, 0, 20, 22, 'grin' if mood == 'grin' else 'smile', 1718, b)
    c.restore()

@lru
def _foot_at(s):
    return rough_path(p_ellipse(s * 26 + 4, 132, 18, 9), 1719 + s, 0.4)

@lru
def _lantern():
    body = rough_path(p_blob([(-34, -40), (0, -52), (34, -40), (40, 0), (34, 40), (0, 52), (-34, 40), (-40, 0)], 6), 1720, 0.6)
    cap = rough_path(p_rect(-22, -64, 44, 14, 3), 1721, 0.4)
    base = rough_path(p_rect(-22, 50, 44, 12, 3), 1722, 0.4)
    return body, cap, base

def lantern_glow(c, x, y, amt):
    glow(c, x, y, 120 + 380 * amt, C['gold'], 0.55 + 0.35 * amt)
    glow(c, x, y, 60 + 180 * amt, hexc('#ffb3a0'), 0.5 * amt + 0.2)

def lantern(c, t, b, amt, halo=True):
    body, cap, base = _lantern()
    if halo: lantern_glow(c, 0, 0, amt)
    ink(c, arc(0, -64, 24, 28, 180, 360, 16), 3, 1723, b)
    piece(c, body, mix(C['coral'], C['gold'], 0.4 + 0.5 * amt), 1724, 1.0)
    c.save(); c.clipPath(body, skia.ClipOp.kIntersect, True)
    for k in range(-2, 3):
        ink(c, arc(k * 14, 0, 12, 52, -90, 90, 12), 1.6, 1725 + k, b, alpha=0.4)
    glow(c, 0, 4, 40, C['white'], 0.4 + 0.5 * amt)
    c.restore()
    piece(c, cap, C['ink'], 1730, 0.6)
    piece(c, base, C['ink'], 1731, 0.6)

# ---------------------------------------------------------------- filing cabinet + memory scraps
@lru
def _cabinet():
    body = rough_path(p_rect(-120, -300, 240, 300, 6), 1800, 0.8)
    drawers = [rough_path(p_rect(-104, -284 + k * 94, 208, 80, 4), 1801 + k, 0.6) for k in range(3)]
    return body, drawers

DRAWER_LABELS = ['today', 'last week', 'long ago']

def cabinet(c, t, b, open_=(0, 0, 0)):
    body, drawers = _cabinet()
    piece(c, body, C['wood'], 1805, 2.0)
    for k in range(3):
        o = open_[k]
        c.save(); c.translate(-90 * o, 0)
        if o > 0.01:
            # drawer box sides visible when pulled out
            fill_paper(c, p_rect(-104, -284 + k * 94 - 10, 208, 12), C['wood2'], 1806 + k)
        piece(c, drawers[k], mix(C['wood'], C['cream'], 0.18), 1810 + k, 1.0 + 1.5 * o)
        y = -284 + k * 94
        piece(c, _card(k), C['cream'], 1813 + k, 0.4)
        hand_text(c, DRAWER_LABELS[k], 0, y + 34, 26, C['ink'], HAND2, 1816 + k, b)
        ink(c, [(-26, y + 60), (26, y + 60)], 7, 1820 + k, b, color=C['mustard'], alpha=1)
        c.restore()
    if True:
        # cobweb on the old drawer corner
        ink(c, [(96, -96), (120, -120)], 1.4, 1830, b, color=C['cream'], alpha=0.5)
        ink(c, arc(120, -96, 16, 16, 180, 270, 8), 1.2, 1831, b, color=C['cream'], alpha=0.5)
        ink(c, arc(120, -96, 8, 8, 180, 270, 6), 1.2, 1832, b, color=C['cream'], alpha=0.5)

@lru
def _card(k):
    return rough_path(p_rect(-60, -284 + k * 94 + 10, 120, 32, 2), 1840 + k, 0.4)

@lru
def _scrap_card(kind):
    if kind in ('school', 'cat', 'boat'):
        return torn_path(p_rect(-62, -76, 124, 146), 1850 + len(kind), 2.2)
    if kind == 'ticket':
        return rough_path(p_rect(-80, -34, 160, 68, 3), 1851, 0.5)
    return rough_path(p_rect(-62, -76, 124, 146, 2), 1852 + len(kind), 0.5)

def scrap(c, kind, t, b):
    """A memory scrap (photo / ticket / drawing). Origin = card centre."""
    cp = _scrap_card(kind)
    old = kind in ('school', 'cat', 'boat')
    if kind == 'ticket':
        piece(c, cp, C['mustard'], 1860, 1.4)
        hand_text(c, 'BUS', -20, 14, 38, C['ink'], HAND, 1861, b)
        hand_text(c, 'No. 42', 42, 10, 22, C['ink'], HAND2, 1862, b)
        for k in range(5):
            c.drawCircle(-66, -24 + k * 12, 3, skia.Paint(AntiAlias=True, Color=hexc('#b88a2c')))
        return
    piece(c, cp, hexc('#e8d3a8') if old else C['white'], 1863 + len(kind), 1.4)
    ph_ = rough_path(p_rect(-50, -64, 100, 100), 1870 + len(kind), 0.3)
    bgc = {'friend': C['sea3'], 'cup': C['rose'], 'school': hexc('#c9a878'), 'cat': hexc('#c3a27a'), 'boat': hexc('#cdb08a')}[kind]
    fill_paper(c, ph_, bgc, 1880 + len(kind))
    c.save(); c.clipPath(ph_, skia.ClipOp.kIntersect, True)
    if kind == 'friend':
        c.save(); c.translate(0, 64); c.scale(0.55, 0.55)
        person(c, t, b, dict(shirt=C['mustard'], hair='curly', hair_col=C['hair']), dict(eyes='open', mouth='grin'), seed=1890)
        c.restore()
    elif kind == 'cup':
        piece(c, rough_path(p_rect(-26, -30, 52, 56, 8), 1891, 0.4), C['blue'], 1892, 0.8)
        ink(c, arc(30, -2, 14, 16, -80, 80, 10), 5, 1893, b, color=C['blue'], alpha=1)
        for k in range(3):
            ink(c, catmull([(-12 + k * 12, -38), (-6 + k * 12, -48), (-12 + k * 12, -58)]), 2, 1894 + k, b, alpha=0.6)
    elif kind == 'school':
        c.save(); c.translate(0, 34); c.scale(0.17, 0.17); props_school_icon(c, t, b); c.restore()
    elif kind == 'cat':
        c.save(); c.translate(0, 38); c.scale(0.45, 0.45)
        import props as _p; _p.cat(c, t, b, 0, eyes='open', col=hexc('#b77c45'))
        c.restore()
    elif kind == 'boat':
        c.save(); c.translate(0, 16); c.scale(0.48, 0.48)
        import props as _p; _p.toy_boat(c, t, b)
        c.restore()
    if old:
        c.drawRect(skia.Rect.MakeXYWH(-60, -70, 120, 110), skia.Paint(Color=with_alpha(hexc('#b08850'), 0.35), BlendMode=skia.BlendMode.kMultiply))
    c.restore()

def props_school_icon(c, t, b):
    import props as _p
    d = _p._school()
    piece(c, d['tower'], C['brick'], 1900, 1.0)
    piece(c, d['troof'], C['wood2'], 1901, 1.0)
    piece(c, d['body'], C['brick'], 1902, 1.0)
    piece(c, d['roof'], C['wood2'], 1903, 1.0)
    piece(c, d['clock'], C['cream'], 1904, 0.5)
    piece(c, d['door'], C['blue2'], 1905, 0.5)

def clothespin(c, b):
    piece(c, _pin(), hexc('#d9b07a'), 1910, 0.8)
    ink(c, [(0, -14), (0, 14)], 1.4, 1911, b, alpha=0.6)

@lru
def _pin():
    return rough_path(p_rect(-7, -18, 14, 36, 3), 1912, 0.3)

# ---------------------------------------------------------------- control panel with the REM lever
@lru
def _panel():
    return rough_path(p_rect(-80, -150, 160, 150, 8), 1950, 0.7), rough_path(p_rect(-40, -60, 80, 26, 5), 1951, 0.4)

def lever_panel(c, t, b, lever=0.0, on=0.0):
    body, slot = _panel()
    piece(c, body, hexc('#8aa3b5'), 1952, 1.8)
    ink_dots(c, [(-66, -136), (66, -136), (-66, -14), (66, -14)], 4, 1953, b, C['grey'])
    # two bulbs
    for k, (x, col_on) in enumerate(((-36, hexc('#9ad17a')), (36, C['gold']))):
        lit = on
        if lit > 0: glow(c, x, -110, 70, col_on, 0.7 * lit)
        piece(c, rough_path(p_circle(x, -110, 16), 1954 + k, 0.3), mix(hexc('#5b5f6e'), col_on, lit), 1954 + k, 0.4)
    hand_text(c, 'REM', 0, -70, 30, C['ink'], HAND, 1956, b)
    piece(c, slot, C['ink'], 1957, 0.2, edge=False)
    ang = lerp(-50, 50, lever)
    c.save(); c.translate(0, -46); c.rotate(ang)
    ink(c, [(0, 0), (0, -96)], 10, 1958, b, color=C['grey'], alpha=1)
    piece(c, rough_path(p_circle(0, -104, 20), 1959, 0.4), C['red'], 1959, 1.2)
    c.restore()

# ---------------------------------------------------------------- desk for the director (prefrontal cortex)
@lru
def _desk():
    top = rough_path(p_rect(-200, -10, 400, 24, 4), 1970, 0.6)
    front = rough_path(p_rect(-180, 14, 360, 150, 4), 1971, 0.7)
    clip = rough_path(p_rect(-40, -120, 120, 112, 4), 1972, 0.5)
    paper_ = rough_path(p_rect(-30, -104, 100, 94, 2), 1973, 0.4)
    return top, front, clip, paper_

def desk(c, t, b, ticks=0, lamp=1.0):
    top, front, clip, paper_ = _desk()
    # lamp
    lx = 150
    if lamp > 0:
        glow(c, lx - 20, -40, 200, C['gold'], 0.45 * lamp)
    ink(c, [(lx, -10), (lx - 10, -90), (lx - 40, -120)], 6, 1974, b, color=C['grey'], alpha=1)
    piece(c, rough_path(p_poly([(lx - 80, -110), (lx - 30, -150), (lx - 10, -118), (lx - 50, -90)]), 1975, 0.4), mix(C['sage'], C['gold'], 0.3 * lamp), 1975, 1.0)
    piece(c, front, C['wood'], 1976, 1.4)
    piece(c, top, C['wood2'], 1977, 1.6)
    c.save(); c.translate(-60, 0); c.rotate(-6)
    piece(c, clip, C['kraft'], 1978, 1.0)
    piece(c, paper_, C['white'], 1979, 0.4)
    for k in range(3):
        y = -84 + k * 26
        ink(c, [(4, y), (58, y)], 2.0, 1980 + k, b, alpha=0.5)
        c.save(); c.translate(-14, y)
        ink(c, arc(0, 0, 7, 7, 0, 360, 12), 1.8, 1983 + k, b, closed=True, alpha=0.8)
        if ticks > k:
            ink(c, [(-6, -2), (-1, 6), (10, -10)], 3.0, 1986 + k, b, color=C['red'], alpha=1)
        c.restore()
    piece(c, rough_path(p_rect(0, -128, 40, 12, 3), 1990, 0.3), C['grey'], 1990, 0.6)
    c.restore()
