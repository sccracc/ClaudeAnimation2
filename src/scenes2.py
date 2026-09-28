"""Second half of the film: curtains, the dream at sea, muscles go limp, why we dream, morning, ending."""
import math, functools
import numpy as np
import skia
from engine import *
import chars, props
from scenes import ph, keyframes, zoom_log, render_image, breath_of, bedroom, CLOUD, P_HIPPO

lru = functools.lru_cache(None)

# ======================================================================= curtains (theatre transition into the dream)
@lru
def _curtain_big(side):
    P = [(0, -60), (1060, -60), (1040, 300), (1070, 700), (1030, 1140), (0, 1140)]
    if side > 0: P = [(W - x, y) for x, y in P]
    return rough_path(p_blob(P, 8), 3000 + side, 1.6)

@lru
def _valance():
    P = [(-40, -40), (W + 40, -40), (W + 40, 150)]
    for k in range(12, -1, -1):
        x = k * 160
        P.append((x + 80, 186)); P.append((x, 150))
    P.append((-40, 150))
    return rough_path(p_poly(P), 3065, 1.2)

T_CURTAIN_CLOSE = 31.85
T_CURTAIN_OPEN = 32.45

def curtains_big(c, t, f, t_close=T_CURTAIN_CLOSE, t_open=T_CURTAIN_OPEN):
    b = boil_of(f)
    cl = prog(t, t_close, t_close + 0.45, ease_io)
    op = prog(t, t_open, t_open + 0.7, ease_io)
    amt = cl * (1 - op)
    val = prog(t, t_close - 0.15, t_close + 0.25, ease_out) * (1 - prog(t, t_open + 0.45, t_open + 0.95, ease_in))
    if amt <= 0.001 and val <= 0.001: return
    for side in (-1, 1):
        dx = -(1 - amt) * 1100 if side < 0 else (1 - amt) * 1100
        cp = _curtain_big(side)
        c.save(); c.translate(dx, 0)
        piece(c, cp, hexc('#a8323a'), 3010 + side, 4.0, 0.45)
        c.save(); c.clipPath(cp, skia.ClipOp.kIntersect, True)
        for k in range(9):
            x0 = (80 + k * 110) if side < 0 else (W - 80 - k * 110)
            pencil(c, catmull([(x0, -40), (x0 + 12 * math.sin(k + t * 2), 500), (x0 - 10, 1120)]), 6, 3020 + k + side, b, hexc('#6e1f28'), 0.45, passes=1)
            crayon(c, p_rect(x0 + 18, -60, 30, 1200), hexc('#d95a5a'), 3030 + k + side, 0.18)
        c.restore()
        edge_x = 1052 if side < 0 else W - 1052
        for k in range(22):
            y = -20 + k * 52
            ink(c, [(edge_x, y), (edge_x, y + 34)], 6, 3040 + k + side, b, color=C['gold'], alpha=0.9)
        c.restore()
    if val > 0:
        c.save(); c.translate(0, -220 * (1 - val))
        piece(c, _valance(), hexc('#8e2a33'), 3060, 4.5, 0.45)
        for k in range(12):
            ink(c, arc(80 + k * 160, 150, 80, 36, 10, 170, 14), 5, 3061 + k, b, color=C['gold'], alpha=0.9)
        c.restore()

# ======================================================================= E: the dream at sea
@lru
def _wave_strip(lam, amp, base, seed):
    xs = np.arange(-1400, 3600, 6.0)
    ys = base - amp * np.abs(np.sin(np.pi * xs / lam)) ** 0.7
    P = np.vstack([np.stack([xs, ys], 1), [(3600, 2600), (-1400, 2600)]])
    return rough_path(to_path(P, True), seed, 1.0)

def wave_layer(c, t, k, col, lam, amp, base, speed, seed, bob=6.0, foam=None, b=0):
    ph_ = (t * abs(speed)) % lam
    dx = -ph_ if speed > 0 else ph_ - lam
    c.save(); c.translate(dx, bob * math.sin(t * 1.3 + k))
    piece(c, _wave_strip(lam, amp, base, seed), col, seed, 2.0 + k * 0.4, 0.35)
    if foam is not None:
        for i in range(-6, int(3600 / lam) + 2):
            cx = i * lam
            ink(c, arc(cx + lam * 0.2, base - amp * 0.7, lam * 0.12, amp * 0.3, 190, 330, 10), 3.2, seed + 7 + (i % 5), b, color=foam, alpha=0.8)
    c.restore()

DREAM_SKY = (hexc('#9d8fd0'), hexc('#e9a3b4'), hexc('#f8cf9e'))
DREAM_FISH = [(33.45, 300, 'coral'), (34.3, 1400, 'mustard'), (35.2, 560, 'pink'), (36.2, 1560, 'coral'), (37.2, 180, 'mustard')]

def dream_world(c, t, f, run=0.0):
    """The dream: a school floating out at sea (world ~ -1400..3600 x, -900..2100 y)."""
    b = boil_of(f)
    tq = tw(t)
    sh = skia.GradientShader.MakeLinear([skia.Point(0, -300), skia.Point(0, 760)], list(DREAM_SKY), [0.0, 0.6, 1.0])
    c.drawRect(skia.Rect.MakeXYWH(-1400, -900, 5000, 3000), skia.Paint(Shader=sh))
    c.drawRect(skia.Rect.MakeXYWH(-1400, -900, 5000, 3000), paper_tex_paint(3100))
    for i, (x, y, r) in enumerate([(120, 80, 16), (380, 200, 11), (640, 40, 14), (1180, 150, 12), (1480, 60, 10), (1880, 220, 13), (-300, 200, 12),
                                   (2300, 120, 14), (-700, 60, 12), (2700, 260, 11)]):
        props.star(c, x, y, r, t, 3110 + i, C['cream'] if i % 2 else C['gold'], b)
    props.moon(c, 1560, 210, 120, t, b)
    props.cloud(c, 300 + (t * 12) % 400, 330, 380, 100, 3120, C['rose'], 1.4, b)
    props.cloud(c, 1900 - (t * 9) % 300, 420, 460, 110, 3121, hexc('#f9dcc4'), 1.4, b)
    # the dozing director on his own little cloud: nobody is checking the logic
    c.save(); c.translate(250, 140 + 8 * math.sin(tq * 1.5))
    props.cloud(c, 0, 70, 320, 90, 3122, C['cream'], 1.4, b)
    c.save(); c.translate(-10, 30); c.scale(0.5, 0.5)
    chars.person(c, tq, b, dict(shirt=hexc('#e8d9b0'), hat='beret', glasses=True, pants=C['wood2'], hair='bob', hair_col=C['ink']),
                 dict(seated=True, eyes='closed', mouth='o', head=24 + 3 * math.sin(tq * 1.2), lean=10, arm_l=10, arm_r=-10), seed=2400)
    c.restore()
    for k in range(3):
        u = ((t * 0.5) + k / 3) % 1.0
        hand_text(c, 'z', 60 + 70 * u, -50 - 110 * u, 50 - 8 * k, C['ink'], TITLE, 3123 + k, b, alpha=math.sin(u * math.pi) * 0.8)
    c.restore()
    wave_layer(c, t, 0, C['sea3'], 260, 34, 700, 26, 3130, 4, None, b)
    for k in range(3):
        gx = (t * 60 + k * 420) % 2600 - 400; gy = 300 + k * 50 + 20 * math.sin(t + k)
        flap = math.sin(t * 7 + k)
        ink(c, [(gx - 34, gy - 10 * flap), (gx, gy + 6), (gx + 34, gy - 10 * flap)], 5, 3140 + k, b, color=C['white'], alpha=0.95, taper=(0.4, 0.4))
    wave_layer(c, t, 1, C['sea'], 330, 40, 790, -34, 3150, 6, C['foam'], b)
    # the school, floating out at sea
    bob = 14 * math.sin(tq * 1.6); roll = 3.0 * math.sin(tq * 1.1 + 0.6)
    c.save(); c.translate(980, 845 + bob); c.rotate(roll); c.scale(0.95, 0.95)
    bell = prog(t, 33.6, 34.0) * (1 - prog(t, 36.0, 37.0))
    c.save(); c.translate(-285, -12); c.scale(0.62, 0.62)
    if run > 0:
        ph2 = tq * 11
        pose = dict(leg_l=34 * math.sin(ph2), leg_r=-34 * math.sin(ph2), arm_l=45 * math.sin(ph2 + 1.5) + 25, arm_r=-45 * math.sin(ph2 + 1.5) - 25,
                    lean=8, eyes='open', mouth='grin', sway=math.sin(ph2))
    else:
        pose = dict(arm_r=20, arm_l=150 + 25 * math.sin(tq * 9), eyes='open', mouth='grin', sway=0.5 * math.sin(tq * 3), look=(-0.4, -0.3))
    c.restore()
    props.school_boat(c, tq, b, bell)
    c.save(); c.translate(-282, -12); c.scale(0.62, 0.62)
    chars.person(c, tq, b, dict(shirt=C['blue'], stripes=C['cream'], pants=C['blue'], hat='nightcap'), pose, seed=3200)
    c.restore()
    c.save(); c.translate(285, -10); c.scale(0.42, 0.42)
    props.cat(c, tq, b, 0, eyes='open', tail_wave=1.0)
    c.restore()
    c.restore()
    for k, (t0, x0, col) in enumerate(DREAM_FISH):
        for rep in range(4):
            tt = t0 + rep * 5.2
            u = prog(t, tt, tt + 1.15)
            if 0 < u < 1:
                x = x0 + 330 * u; y = 900 - 330 * math.sin(u * math.pi)
                dy = -330 * math.pi * math.cos(u * math.pi); ang = math.degrees(math.atan2(dy, 330))
                c.save(); c.translate(x, y); c.rotate(ang); c.scale(0.7, 0.7)
                props.fish(c, t, b, 3300 + k * 20, C[col], wiggle=1.0)
                c.restore()
            sp = prog(t, tt + 1.05, tt + 1.6)
            if 0 < sp < 1:
                for m in range(5):
                    a = math.radians(-150 + m * 30)
                    rr = 20 + 70 * ease_out(sp)
                    c.drawCircle(x0 + 330 + math.cos(a) * rr, 880 + math.sin(a) * rr + 60 * sp * sp, 9 * (1 - sp), skia.Paint(AntiAlias=True, Color=C['foam']))
    wave_layer(c, t, 2, C['sea2'], 420, 46, 900, 44, 3160, 8, C['foam'], b)
    wave_layer(c, t, 3, hexc('#244a74'), 520, 50, 1010, -56, 3170, 9, None, b)

DREAM_CAM = [(32.3, 900, 560, 1.0), (37.6, 1040, 540, 1.07)]

def scene_E(c, t, f):
    background(c, DREAM_SKY[0], 3099)
    cam = keyframes(t, DREAM_CAM)
    c.save(); cam.apply(c)
    dream_world(c, t, f)
    c.restore()

# ======================================================================= F: back in bed; muscles go limp
T_F = 37.25                  # pull back out of the dream into the thought cloud
T_LIMP = ph(7, 1) + 0.55     # "your muscles go limp"
F_ZOOM0 = 5.2

def dream_in_cloud(c, t, f, run):
    """Draw the dream world inside the thought cloud so the pull-back is seamless."""
    cam = keyframes(t, DREAM_CAM)
    s_c = cam.zoom / F_ZOOM0
    c.save(); c.scale(s_c, s_c); c.translate(-cam.x, -cam.y)
    dream_world(c, t, f, run)
    c.restore()

def _string_pts(a, bpt, sag):
    mx, my = (a[0] + bpt[0]) / 2, (a[1] + bpt[1]) / 2 + sag
    return catmull([a, (mx, my), bpt], 12)

def scene_F(c, t, f):
    b = boil_of(f)
    u = prog(t, T_F, T_F + 1.15, ease_io)
    z = zoom_log(F_ZOOM0, 1.0, u)
    cx, cy = CLOUD[0], CLOUD[1]
    cam = Cam(lerp(cx, W / 2, u), lerp(cy, H / 2, u), z)
    limp = prog(t, T_LIMP, T_LIMP + 0.35, ease_out)
    run = 1.0
    twitch = (0.5 + 0.5 * math.sin(tw(t) * 11)) * (1 - limp)
    badge = 0.0   # (pause badge removed: the slack strings + flopping arm carry the idea)

    def strings(cc):
        # marionette strings from the dream down to the body; they go slack
        hand = (7 + 60 * limp, -226 + 14 * limp - 30 * twitch)
        toe = (340, -226)
        knee = (150, -236)
        tops = [(-60, -560), (150, -560), (330, -560)]
        ends = [hand, knee, toe]
        for i in range(3):
            sag = 10 + 150 * limp
            P = _string_pts(tops[i], ends[i], sag)
            ink(cc, P, 3.4, 3500 + i, b, color=C['cream'], alpha=0.95, taper=(0, 0), jitter=0.5)
            cc.drawCircle(ends[i][0], ends[i][1], 7, skia.Paint(AntiAlias=True, Color=C['mustard']))
        if badge > 0:
            cc.save(); cc.translate(230, -150); cc.rotate(-8); cc.scale(badge, badge)
            piece(cc, _pause_badge(), C['coral'], 3510, 1.6)
            for dx in (-15, 15):
                piece(cc, _pause_bar(dx), C['cream'], 3511 + dx, 0.4, edge=False)
            tape(cc, 0, -46, 60, 22, -12, 3514)
            cc.restore()

    bedroom(c, t, f, cam, head_kw=dict(eyes='closed', mouth_kind='o', breath=breath_of(t), sway=0.2 * math.sin(t * 0.9)),
            cloud_grow=1.0, cloud_bubbles=1.0, cloud_content=lambda cc: dream_in_cloud(cc, t, f, run),
            arm_limp=limp, arm_twitch=twitch, strings=strings)

@lru
def _pause_badge():
    return rough_path(p_rect(-48, -46, 96, 92, 18), 3513, 0.6)

@lru
def _pause_bar(dx):
    return rough_path(p_rect(dx - 9, -26, 18, 52, 4), 3515 + dx, 0.3)
