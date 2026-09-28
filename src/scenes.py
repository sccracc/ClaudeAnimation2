"""Scene choreography. All timings hang off the narration cue sheet (build/timeline.json)."""
import json, math, os, functools
import numpy as np
import skia
from engine import *
import chars, props
from props import cached_layer, draw_layer

lru = functools.lru_cache(None)
TL = json.load(open(os.path.join(ROOT, 'build', 'timeline.json')))
LN = TL['lines']

def ph(i, j=0, end=False):
    """phrase j of line i (1-based line numbers) start/end time"""
    p = LN[i - 1]['phrases'][j]
    return p[1] if end else p[0]

DURATION = 59.0

def render_image(fn, t, f, *a, **kw):
    s = new_surface(); c = s.getCanvas()
    fn(c, t, f, *a, **kw)
    return s.makeImageSnapshot()

def breath_of(t, period=3.4):
    return 0.5 + 0.5 * math.sin(2 * math.pi * t / period)

# ======================================================================= A: night exterior
WIN_EXT = (1108.0, 598.0, 128.0, 72.0)     # 16:9 lit window of the dreamer's house (world coords)

@lru
def _ext_hill(k):
    if k == 0:
        P = [(-900, 760), (-300, 690), (200, 720), (700, 660), (1200, 700), (1700, 650), (2300, 690), (2900, 700), (2900, 1500), (-900, 1500)]
    elif k == 1:
        P = [(-900, 880), (-200, 830), (500, 800), (900, 790), (1300, 792), (1700, 815), (2300, 850), (2900, 860), (2900, 1600), (-900, 1600)]
    else:
        P = [(-900, 1010), (-200, 960), (400, 990), (1000, 950), (1600, 985), (2300, 950), (2900, 990), (2900, 1700), (-900, 1700)]
    return rough_path(p_blob(P, 10), 80 + k, 1.4)

@lru
def _tree():
    return torn_path(p_union(p_circle(885, 600, 70), p_circle(840, 640, 55), p_circle(930, 645, 55), p_circle(885, 560, 50)), 121, 2.0)

@lru
def _winpath():
    x0, y0, ww, wh = WIN_EXT
    return rough_path(p_rect(x0, y0, ww, wh, 2), 131, 0.3)

@lru
def _winframe_ext():
    x0, y0, ww, wh = WIN_EXT
    return rough_path(p_diff(p_rect(x0 - 12, y0 - 12, ww + 24, wh + 24), p_rect(x0, y0, ww, wh)), 132, 0.5)

LIGHTS_OFF = [2.35, 2.62, 2.2, 2.85, 2.5, 2.95]

def exterior(c, t, f, cam, inside=None):
    b = boil_of(f)
    background(c, C['night'], 1)
    # --- sky layer (parallax 0.15)
    c.save(); cam.apply(c, 0.15)
    sh = skia.GradientShader.MakeLinear([skia.Point(0, 250), skia.Point(0, 900)], [with_alpha(C['night'], 0), with_alpha(C['night3'], 0.8)])
    c.drawRect(skia.Rect.MakeXYWH(-2000, -1000, 6000, 3000), skia.Paint(Shader=sh))
    stars = [(160, 140, 16), (420, 90, 11), (640, 230, 14), (860, 110, 10), (1080, 250, 12), (1250, 80, 15), (1760, 150, 13), (1880, 330, 10),
             (300, 380, 9), (980, 400, 8), (1640, 420, 9), (560, 470, 8), (60, 300, 10), (1400, 360, 8)]
    for i, (x, y, r) in enumerate(stars):
        props.star(c, x, y, r, t, 40 + i, C['gold'] if i % 3 else C['cream'], b)
    ss = prog(t, 0.45, 1.55, ease_io)
    if 0 < ss < 1:
        x0, y0 = 620 + ss * 760, 60 + ss * 210
        trail = [(x0 - k * 24 * (0.4 + ss), y0 - k * 6.6 * (0.4 + ss)) for k in range(10)]
        pencil(c, trail, 3.2, 60, b, C['cream'], 0.75 * math.sin(ss * math.pi), passes=1, taper=(0.9, 0.0))
        c.save(); c.translate(x0, y0); c.scale(math.sin(ss * math.pi), math.sin(ss * math.pi))
        props.star(c, 0, 0, 15, t * 4, 61, C['gold'], b, spark=False)
        c.restore()
    c.restore()
    c.save(); cam.apply(c, 0.25)
    props.moon(c, 1520, 220, 95, t, b)
    props.cloud(c, 300 + t * 16, 300, 360, 90, 70, hexc('#3d4b85'), 1.0, b, outline=False)
    props.cloud(c, 1240 - t * 11, 470, 420, 100, 71, hexc('#344178'), 1.0, b, outline=False)
    c.restore()
    # --- far hills + little town (0.45); their lights switch off one by one ("while you sleep")
    c.save(); cam.apply(c, 0.45)
    piece(c, _ext_hill(0), C['night3'], 80, 1.2)
    for i, (x, w, h, col) in enumerate([(120, 120, 110, 'blue2'), (300, 90, 150, 'lav'), (450, 140, 100, 'coral2'), (1500, 120, 130, 'blue2'),
                                         (1660, 110, 100, 'lav'), (1830, 150, 120, 'coral2')]):
        lit = 1.0 - prog(t, LIGHTS_OFF[i], LIGHTS_OFF[i] + 0.06)
        props.house(c, x, 745, w, h, 50, mix(C[col], C['night'], 0.35), mix(C['wood2'], C['night'], 0.3), 90 + i * 5, b,
                    windows=[(-w * 0.25, -h * 0.65, 30, 30)], lit=lit, chimney=(i % 2 == 0))
    c.restore()
    # --- mid hill with the dreamer's house (focal plane)
    c.save(); cam.apply(c, 1.0)
    piece(c, _ext_hill(1), C['teal'], 81, 1.6)
    ink(c, [(885, 800), (888, 640)], 18, 120, b, color=C['wood2'], alpha=1, taper=(0, 0.3))
    piece(c, _tree(), C['sage'], 121, 1.8)
    for k in range(4):
        pencil(c, arc(885 + (k - 1.5) * 30, 600 + (k % 2) * 30, 18, 12, 200, 340, 8), 1.6, 122 + k, b, alpha=0.35, passes=1)
    x0, y0, ww, wh = WIN_EXT
    props.house(c, 1172, 812, 300, 262, 120, C['brick'], C['wood2'], 130, b, windows=[], chimney=True)
    glow(c, x0 + ww / 2, y0 + wh / 2, 240, C['gold'], 0.5)
    if inside is not None:
        c.save(); c.clipPath(skia.Path.Rect(skia.Rect.MakeXYWH(x0, y0, ww, wh)), skia.ClipOp.kIntersect, True)
        c.translate(x0, y0); c.scale(ww / W, wh / H)
        c.drawImage(inside, 0, 0, SAMP, skia.Paint(AntiAlias=True))
        c.restore()
    else:
        piece(c, _winpath(), C['gold'], 131, 0.3, 0.2)
        ink(c, [(x0 + ww / 2, y0), (x0 + ww / 2, y0 + wh)], 3, 133, b, color=C['cream2'], alpha=0.95)
    piece(c, _winframe_ext(), C['cream2'], 132, 0.8)
    piece(c, rough_path(p_rect(1040, 722, 56, 90, 4), 134, 0.5), C['blue2'], 134, 0.8)
    c.drawCircle(1086, 770, 4, skia.Paint(AntiAlias=True, Color=C['gold']))
    c.restore()
    # --- foreground hill + grass (1.3)
    c.save(); cam.apply(c, 1.3)
    piece(c, _ext_hill(2), C['deepteal'], 82, 2.4)
    for k in range(16):
        gx = -100 + k * 150 + (k % 3) * 20; gy = 985 + (k % 4) * 16
        for m in range(3):
            ink(c, [(gx + m * 10, gy), (gx + m * 12 - 8 + 4 * math.sin(t * 2 + k + m), gy - 30 - m * 6)], 3.0, 140 + k * 3 + m, b, color=C['teal2'], alpha=0.9)
    c.restore()

def zoom_log(z0, z1, u):
    return math.exp(lerp(math.log(z0), math.log(z1), u))

A_PUSH_END = 3.25
A_ENTER = 4.15

def scene_A(c, t, f):
    x0, y0, ww, wh = WIN_EXT
    wc = (x0 + ww / 2, y0 + wh / 2)
    if t < A_PUSH_END:
        u = prog(t, 0.0, A_PUSH_END, ease_io)
        cam = Cam(lerp(W / 2, lerp(W / 2, wc[0], 0.45), u), lerp(H / 2, lerp(H / 2, wc[1], 0.4), u), lerp(1.0, 1.28, u))
        exterior(c, t, f, cam)
    else:
        u = prog(t, A_PUSH_END, A_ENTER, ease_io)
        z = zoom_log(1.28, W / ww, u)
        sx = lerp(lerp(W / 2, wc[0], 0.45), wc[0], ease_out(u)); sy = lerp(lerp(H / 2, wc[1], 0.4), wc[1], ease_out(u))
        inside = render_image(scene_B, t, f)
        exterior(c, t, f, Cam(sx, sy, z), inside=inside)

# ======================================================================= B: bedroom (shared by several beats)
def film_frames():
    def fr_fish(c, w, h):
        fill_paper(c, p_rect(0, 0, w, h), C['sea3'], 1)
        c.save(); c.translate(w / 2, h / 2); c.scale(0.5, 0.5); props.fish(c, 0, 0, 900, C['coral']); c.restore()
    def fr_star(c, w, h):
        fill_paper(c, p_rect(0, 0, w, h), C['night2'], 2)
        props.star(c, w / 2, h / 2, 30, 0, 5, C['gold'], 0, spark=False)
    def fr_cat(c, w, h):
        fill_paper(c, p_rect(0, 0, w, h), C['sage'], 3)
        c.save(); c.translate(w / 2, h * 0.98); c.scale(0.42, 0.42); props.cat(c, 0, 0, 0, eyes='open'); c.restore()
    def fr_boat(c, w, h):
        fill_paper(c, p_rect(0, 0, w, h), C['sky'], 4)
        c.save(); c.translate(w / 2, h * 0.8); c.scale(0.45, 0.45); props.toy_boat(c, 0, 0); c.restore()
    def fr_moon(c, w, h):
        fill_paper(c, p_rect(0, 0, w, h), C['lav'], 6)
        props.moon(c, w / 2, h / 2, 34, 0, 0, face=True)
    return [fr_fish, fr_star, fr_cat, fr_boat, fr_moon]

FRAMES = film_frames()
CLOUD = (1010, 330, 640, 400)   # thought cloud centre + size in the bedroom

def bedroom(c, t, f, cam=None, head_kw=None, cloud_grow=0.0, cloud_bubbles=0.0, cloud_content=None, dawn=0.0, sun=0.0,
            ring=0.0, toast=0.0, lamp=1.0, arm_limp=0.0, arm_twitch=0.0, strings=None, extra_front=None, cloud_col=None, night_tint=1.0,
            arm_raise=0.0, hand_item=None, cloud_pos=None):
    b = boil_of(f)
    cam = cam or Cam()
    c.save(); cam.apply(c)
    draw_layer(c, props.wall_layer())
    props.window_frame(c, b, lambda cc, tt, x, y, w, h: props.night_sky(cc, tt, x, y, w, h, dawn, sun), t)
    props.curtains(c, t, b)
    props.picture_frame(c, t, b)
    props.shelf(c, t, b)
    props.nightstand(c, t, b, ring, toast, lamp)
    props.toaster_front(c, t, b)
    c.save(); c.translate(props.BED_X, props.BED_Y); c.scale(props.BED_S, props.BED_S)
    chars.bed(c, t, b, breath_of(t), head_kw or {}, arm_limp, arm_twitch, strings, arm_raise=arm_raise, hand_item=hand_item)
    c.restore()
    # room light: night tint + lamp pool
    if night_tint > 0:
        c.drawRect(skia.Rect.MakeXYWH(-500, -500, W + 1000, H + 1000),
                   skia.Paint(Color=with_alpha(hexc('#1a1f45'), 0.28 * night_tint * (1 - dawn)), BlendMode=skia.BlendMode.kMultiply))
    if dawn > 0:
        # morning: warm the whole room, then a soft sunbeam from the window across the floor
        c.drawRect(skia.Rect.MakeXYWH(-500, -500, W + 1000, H + 1000),
                   skia.Paint(Color=with_alpha(hexc('#ffc890'), 0.30 * dawn), BlendMode=skia.BlendMode.kOverlay))
        sh = skia.GradientShader.MakeRadial(skia.Point(390, 320), 1500, [with_alpha(hexc('#ffd9a0'), 0.42 * dawn), with_alpha(hexc('#ffb080'), 0.0)])
        c.drawRect(skia.Rect.MakeXYWH(-500, -500, W + 1000, H + 1000), skia.Paint(Shader=sh, BlendMode=skia.BlendMode.kScreen))
        beam = p_poly([(175, 160), (605, 160), (1500, 1100), (560, 1100)])
        c.drawPath(beam, skia.Paint(AntiAlias=True, Color=with_alpha(hexc('#fff0c8'), 0.16 * dawn), BlendMode=skia.BlendMode.kScreen,
                                    MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 40)))
    hx, hy = props.HEAD_POS
    cx, cy, cw, chh = CLOUD
    props.thought(c, t, b, cx, cy, cw, chh, cloud_grow, (hx + 60, hy - 80), cloud_content, cloud_bubbles, cloud_col)
    if extra_front: extra_front(c, t, b)
    c.restore()

def scene_B(c, t, f):
    """Bedroom intro: the thought cloud opens, a film rolls, a clapper claps, 'starring you'."""
    b = boil_of(f)
    t_b = ph(1, 2) + 0.12            # "your brain will make a movie"
    grow = spring(t - (t_b + 0.45), 1.3, 5.0) if t > t_b + 0.45 else 0.0
    bub = prog(t, t_b, t_b + 0.5)
    push = prog(t, 7.05, 7.95, ease_in)
    zoom = lerp(1.0 + 0.04 * prog(t, 3.5, 7.0), 7.5, push ** 1.4) if push > 0 else 1.0 + 0.04 * prog(t, 3.5, 7.0)
    cx, cy = CLOUD[0], CLOUD[1]
    cam = Cam(lerp(W / 2, cx, ease_io(prog(t, 6.9, 7.8))), lerp(H / 2, cy, ease_io(prog(t, 6.9, 7.8))), zoom)
    t_star = ph(1, 3)
    film_out = prog(t, 6.85, 7.4, ease_in)

    def content(cc):
        # film strip scrolling through the dream cloud
        off = (t - t_b) * 150
        cc.save(); cc.translate(0, film_out * 420)
        props.filmstrip(cc, t, b, 0, 10, 900, off, FRAMES, 118)
        cc.restore()
        # star badge: "starring you"
        s = spring(t - t_star, 1.5, 5.0) if t > t_star else 0.0
        if s > 0:
            cc.save(); cc.translate(140, -40); cc.translate(0, film_out * 420)
            props.star_badge(cc, t, b, s * 0.9)
            cc.restore()
            props.sparkle(cc, 140, -40 + film_out * 420, 150, t_star + 0.1, t, b, 5)

    def front(cc, tt, bb):
        # clapperboard pops up beside the cloud and claps on "movie"
        t_c = t_b + 0.9
        s = spring(t - t_c, 1.6, 5.5) if t > t_c else 0.0
        out = prog(t, 6.0, 6.4, ease_in)
        if s > 0 and out < 1:
            cc.save(); cc.translate(640, 420 + out * 700); cc.rotate(-10 + 6 * wig(t, 1, 3)); cc.scale(s * 0.9, s * 0.9)
            clap_t = t_c + 0.55
            op = 1.0 if t < clap_t else max(0.0, 1 - (t - clap_t) * 14)
            if t < t_c + 0.2: op = prog(t, t_c, t_c + 0.2)
            props.clapper(cc, t, bb, op)
            cc.restore()
    breath = breath_of(t)
    bedroom(c, t, f, cam, head_kw=dict(eyes='closed', mouth_kind='o', breath=breath, sway=0.2 * math.sin(t * 0.9)),
            cloud_grow=grow, cloud_bubbles=bub, cloud_content=content, extra_front=front)

# ======================================================================= C: sleep-cycle chart (hypnogram)
LV = dict(awake=250, rem=360, light=560, deep=770)
HYP_PTS = [(205, 256), (245, 266), (292, 560), (340, 765), (420, 772), (470, 560), (508, 372), (535, 361), (579, 361), (604, 372), (640, 575), (690, 750), (760, 755),
           (810, 560), (848, 372), (878, 361), (926, 361), (956, 372), (992, 560), (1040, 672), (1100, 676), (1150, 560), (1188, 372), (1225, 361),
           (1289, 361), (1326, 372), (1362, 560), (1420, 598), (1480, 580), (1518, 372), (1565, 361), (1649, 361), (1696, 370), (1738, 318), (1790, 256)]
REM_X = [(512, 600), (852, 952), (1192, 1322), (1522, 1692)]
REM_C = [557, 902, 1257, 1607]

@lru
def _hyp_curve():
    P = catmull(HYP_PTS, 10)
    Q, s = resample(P, 3.0, False)
    return Q, s

def _chart_paper(c):
    fill_paper(c, p_rect(-40, -40, W + 80, H + 80), C['cream'], 1201)
    for i in range(0, W + 60, 60):
        pencil(c, [(i, -20), (i + 2, H + 20)], 1.3, 1202 + i, 0, hexc('#8fa6c8'), 0.28, passes=1, taper=(0, 0))
    for j in range(0, H + 60, 60):
        pencil(c, [(-20, j), (W + 20, j + 1)], 1.3, 1300 + j, 0, hexc('#8fa6c8'), 0.28, passes=1, taper=(0, 0))
    pencil(c, [(118, -20), (120, H + 20)], 2.2, 1400, 0, hexc('#d9786a'), 0.55, passes=1, taper=(0, 0))

def chart_layer():
    return cached_layer('chart', _chart_paper, scale=1.25)

DREAM_ICONS = ['fish', 'star', 'cat', 'boat']

def dream_icon(c, kind, t, b, s=1.0):
    c.save(); c.scale(s, s)
    if kind == 'fish':
        c.rotate(-15); props.fish(c, t, b, 900, C['coral'], wiggle=0.5)
    elif kind == 'star':
        props.star(c, 0, 0, 44, t, 1210, C['gold'], b, spark=False)
    elif kind == 'cat':
        c.scale(0.7, 0.7); c.translate(0, 130); props.cat(c, t, b, 0, eyes='open')
    elif kind == 'boat':
        c.scale(0.8, 0.8); c.translate(0, 60); props.toy_boat(c, t, b)
    elif kind == 'moon':
        props.moon(c, 0, 0, 40, t, b)
    c.restore()

C_T0 = 7.8
C_DRAW = (7.95, 10.05)

def scene_C(c, t, f):
    b = boil_of(f)
    cam = Cam(W / 2 + 6 * math.sin(t * 0.3), H / 2, 1.0 + 0.012 * prog(t, C_T0, 14.5))
    c.save(); cam.apply(c)
    draw_layer(c, chart_layer())
    # fade from the plain cream cloud interior
    a_in = prog(t, C_T0, C_T0 + 0.45)
    if a_in < 1:
        c.drawRect(skia.Rect.MakeXYWH(-100, -100, W + 200, H + 200), skia.Paint(Color=with_alpha(C['cream'], 1 - a_in)))
    # level guides + labels
    for k, (name, y) in enumerate([('awake', LV['awake']), ('light sleep', LV['light']), ('deep sleep', LV['deep'])]):
        a = prog(t, 8.0 + k * 0.12, 8.4 + k * 0.12)
        if a > 0:
            hand_text(c, name, 40, y - 24, 38, hexc('#4a4658'), HAND, 1500 + k, b, align='left', reveal=min(1.0, a * 2.2), alpha=0.85)
            Q = np.array([(128, y), (128 + 1650 * a, y)])
            pencil(c, Q, 1.4, 1510 + k, b, hexc('#6c6a80'), 0.25, passes=1, taper=(0, 0))
    # doodled moon (night) and sun (morning) at either end of the night
    a = prog(t, 8.2, 8.6)
    if a > 0:
        c.save(); c.translate(185, 150); c.scale(a, a); props.moon(c, 0, 0, 34, t, b); c.restore()
        c.save(); c.translate(1790, 150); c.scale(a, a)
        for k in range(8):
            ang = math.radians(k * 45 + t * 20)
            ink(c, [(math.cos(ang) * 44, math.sin(ang) * 44), (math.cos(ang) * 62, math.sin(ang) * 62)], 3.4, 1520 + k, b, color=C['mustard'])
        piece(c, _sun_small(), C['sun'], 1530, 1.0)
        c.restore()
    # the curve, drawn by a pencil
    Q, s = _hyp_curve()
    r = prog(t, *C_DRAW, ease_io)
    n = max(2, int(len(Q) * r))
    if r > 0:
        ink(c, Q[:n], 6.0, 1540, b, color=hexc('#35323f'), taper=(0.02, 0.02), spacing=3.0)
        for k, (x0, x1) in enumerate(REM_X):
            m = (Q[:n, 0] >= x0 - 4) & (Q[:n, 0] <= x1 + 4)
            if m.sum() > 2:
                pts = Q[:n][m]
                crayon_line = ink_path(pts, 16, 1550 + k, b, taper=(0.1, 0.1))
                c.drawPath(crayon_line, grain_paint(C['coral'], 'crayon', 1560 + k, 0.8, 0.85))
    if 0 < r < 1 or (C_DRAW[1] <= t < C_DRAW[1] + 0.5):
        if r < 1:
            tip = Q[n - 1]
        else:
            tip = Q[-1] + np.array([1, -0.6]) * 900 * ease_in(prog(t, C_DRAW[1], C_DRAW[1] + 0.5))
        props.pencil_sprite(c, tip[0], tip[1], -38 + 6 * math.sin(t * 9), b)
    # "~90 min" bracket between the first two REM periods
    br = prog(t, 8.8, 9.3, ease_out)
    fade = 1 - prog(t, 11.9, 12.3)
    if br > 0 and fade > 0:
        y = 190
        xa, xb = REM_C[0], REM_C[1]
        P = np.array([(xa, y + 26), (xa, y)] + [(lerp(xa, xb, u), y) for u in np.linspace(0, 1, 20)] + [(xb, y), (xb, y + 26)])
        m = max(2, int(len(P) * br))
        pencil(c, P[:m], 3.0, 1570, b, hexc('#3b3a4a'), 0.85 * fade, passes=2, taper=(0.05, 0.05))
        hand_text(c, '~90 minutes', (xa + xb) / 2, y - 22, 44, hexc('#35323f'), HAND2, 1571, b, reveal=prog(t, 9.0, 9.6), alpha=fade)
    # REM stamps
    t_st = [10.35 + k * 0.36 for k in range(4)]
    for k in range(4):
        props.stamp_mark(c, REM_C[k], 292, 'REM', t_st[k], t, b, rot=[-6, 4, -3, 5][k])
    if t_st[0] - 0.3 < t < t_st[-1] + 0.6:
        # one stamp hopping from plateau to plateau
        k = 0
        for i in range(4):
            if t >= t_st[i] - 0.2: k = i
        tk = t_st[k]
        if t < tk:
            lift = 380 * ease_in(1 - prog(t, tk - 0.2, tk)) if k == 0 else 380 * (1 - prog(t, tk - 0.2, tk, ease_in))
            x = REM_C[k] if k == 0 else lerp(REM_C[k - 1], REM_C[k], prog(t, tk - 0.3, tk - 0.1, ease_io))
        else:
            dt = t - tk
            lift = 0 if dt < 0.05 else 380 * ease_out(prog(dt, 0.05, 0.25))
            x = REM_C[k] if k == 3 or dt < 0.12 else lerp(REM_C[k], REM_C[k + 1], prog(t, tk + 0.12, tk + 0.26, ease_io))
            if k == 3: lift = 0 if dt < 0.05 else 900 * ease_in(prog(dt, 0.05, 0.5))
        sq = 1 - clamp(abs(t - tk - 0.02) / 0.05)
        props.rubber_stamp(c, x, 330 - 4, lift, b, sq)
    # vivid dreams bubble up out of each REM period
    for k in range(4):
        t_p = 12.45 + k * 0.26
        if t > t_p:
            u = t - t_p
            s = spring(u, 1.4, 4.5)
            y = 340 - 190 * ease_out(clamp(u / 0.9)) - 12 * u + 8 * math.sin(t * 2.2 + k)
            c.save(); c.translate(REM_C[k] + 10 * math.sin(t * 1.6 + k), y); c.rotate(8 * math.sin(t * 1.3 + k * 2))
            dream_icon(c, DREAM_ICONS[k], t, b, 0.62 * s)
            c.restore()
            props.sparkle(c, REM_C[k], 300, 90, t_p, t, b, 1580 + k)
    c.restore()

@lru
def _sun_small():
    return rough_path(p_circle(0, 0, 34), 1531, 0.6)

# ======================================================================= transitions
@lru
def _tear_line(seed, x_top, x_bot):
    r = rnd(seed)
    ys = np.linspace(-60, H + 60, 70)
    xs = np.linspace(x_top, x_bot, 70) + np.cumsum(r.normal(0, 7, 70)) * 0.6
    P = np.stack([xs, ys], 1)
    Q, s = resample(P, 3.0, False)
    Nn = normals(Q, False)
    d = 5 * noise1(s / 9, seed) + 2.5 * noise1(s / 2.5, seed + 3)
    return Q + Nn * d[:, None]

def tear_transition(c, t, f, drawA, drawB, t0, t1, seed=5):
    """Paper A rips top-down and the halves are pulled away, revealing B underneath."""
    u = prog(t, t0, t1)
    drawB(c, t, f)
    if u >= 1: return
    imgA = render_image(drawA, t, f)
    L = _tear_line(seed, 1010, 930)
    e = ease_in(u)
    for side in (-1, 1):
        if side < 0:
            poly = np.vstack([[(-400, -400)], L, [(-400, H + 400)]])
            piv = (-100, H + 100); ang = -14 * e - 2 * u; dx, dy = -1500 * e, 150 * e
        else:
            poly = np.vstack([[(W + 400, -400)], L, [(W + 400, H + 400)]])
            piv = (W + 100, H + 100); ang = 16 * e + 2 * u; dx, dy = 1500 * e, 260 * e
        path = to_path(poly, True)
        c.save()
        c.translate(dx, dy); c.translate(*piv); c.rotate(ang); c.translate(-piv[0], -piv[1])
        shadow(c, path, 3.0 + 6 * u, 0.4)
        # white torn core peeking out along the edge
        rim = to_path(np.vstack([poly[:1], L + np.array([side * -7.0, 0]) + np.stack([noise1(np.arange(len(L)) / 3.0, seed + side) * 3, np.zeros(len(L))], 1), poly[-1:]]), True)
        c.drawPath(rim, skia.Paint(AntiAlias=True, Color=C['white']))
        c.save(); c.clipPath(path, skia.ClipOp.kIntersect, True)
        c.drawImage(imgA, 0, 0)
        c.restore()
        c.restore()

# ======================================================================= D: the brain studio
def keyframes(t, keys):
    """keys: list of (time, x, y, zoom); eased interpolation (zoom in log space)."""
    if t <= keys[0][0]: k = keys[0]; return Cam(k[1], k[2], k[3])
    for a, bk in zip(keys[:-1], keys[1:]):
        if t <= bk[0]:
            u = ease_io(prog(t, a[0], bk[0]))
            return Cam(lerp(a[1], bk[1], u), lerp(a[2], bk[2], u), zoom_log(a[3], bk[3], u))
    k = keys[-1]; return Cam(k[1], k[2], k[3])

P_STEM = (-190, 830, 205)
P_HIPPO = (-380, 150, 330)
P_AMYG = (270, 310, 235)
P_PFC = (650, -330, 300)

T_LEVER = ph(3, 0) + 1.72        # "...flips on"
T_TODAY = ph(4, 1) - 0.05
T_LONG = ph(4, 2) - 0.05
T_GLOW = ph(5, 0) + 1.05
T_PFC = ph(5, 1)
T_DOZE = ph(5, 3)

D_KEYS = [(14.0, -80, 230, 0.315), (15.05, -80, 220, 0.33), (16.35, -250, 810, 1.72), (T_LEVER + 0.3, -245, 800, 1.78),
          (18.15, -220, 420, 0.8), (19.0, -370, 205, 1.3), (24.15, -360, 210, 1.36), (25.0, 270, 330, 1.62), (26.9, 275, 335, 1.68),
          (27.95, 650, -300, 1.62), (31.3, 650, -300, 1.74), (33.0, 650, -300, 1.78)]

@lru
def _head_profile():
    P = [(-760, 1950), (-740, 1300), (-900, 1000), (-1180, 600), (-1300, 100), (-1200, -450), (-900, -850), (-400, -1060), (200, -1060),
         (700, -900), (1100, -560), (1300, -100), (1330, 150), (1300, 260), (1360, 380), (1520, 560), (1480, 640), (1370, 660), (1390, 740),
         (1420, 790), (1360, 840), (1400, 900), (1330, 960), (1320, 1060), (1200, 1150), (900, 1180), (650, 1300), (620, 1950)]
    return rough_path(p_blob(P, 10), 2001, 2.0)

@lru
def _brain():
    P = [(-1100, 0), (-1000, -450), (-650, -720), (-100, -800), (500, -730), (950, -480), (1120, -50), (1000, 350), (700, 600), (300, 700),
         (-60, 620), (-500, 700), (-900, 520)]
    return rough_path(p_blob(P, 10), 2002, 2.0)

@lru
def _cerebellum():
    return rough_path(p_ellipse(-640, 740, 330, 210), 2003, 1.4)

@lru
def _stem():
    return rough_path(p_blob([(-430, 540), (70, 540), (20, 1050), (-80, 1950), (-340, 1950), (-400, 1050)], 8), 2004, 1.4)

@lru
def _cap_big():
    P = [(1080, -700), (900, -1050), (500, -1330), (-100, -1440), (-700, -1420), (-1250, -1200), (-1650, -800), (-1850, -300), (-1800, 150),
         (-1700, -250), (-1520, -700), (-1180, -540), (-900, -850), (-400, -1060), (200, -1060), (700, -900)]
    return rough_path(p_blob(P, 10), 2005, 2.4)

@lru
def _cap_band_big():
    top = [(-1260, -560), (-960, -930), (-420, -1150), (200, -1150), (740, -990), (1150, -760)]
    bot = [(1060, -620), (680, -860), (200, -1010), (-380, -1010), (-860, -800), (-1130, -470)]
    return rough_path(p_blob(top + bot, 8), 2006, 1.6)

@lru
def _pocket(i):
    x, y, r = [P_STEM, P_HIPPO, P_AMYG, P_PFC][i]
    r0 = rnd(2010 + i)
    pts = [(x + math.cos(a) * r * r0.uniform(0.94, 1.06), y + math.sin(a) * r * r0.uniform(0.94, 1.06)) for a in np.linspace(0, 2 * math.pi, 10, endpoint=False)]
    return rough_path(p_blob(pts, 10), 2010 + i, 1.2)

@lru
def _gyri():
    r = rnd(2020)
    strokes = []
    brain = _brain()
    for k in range(70):
        x, y = r.uniform(-1050, 1050), r.uniform(-760, 680)
        if not brain.contains(x, y): continue
        pts = [(x, y)]; ang = r.uniform(0, 2 * math.pi)
        for m in range(r.integers(4, 9)):
            ang += r.uniform(-1.6, 1.6)
            x += math.cos(ang) * 60; y += math.sin(ang) * 60
            pts.append((x, y))
        strokes.append(catmull(pts, 6))
    return strokes

def pocket_open(c, i, inner):
    """Hole cut into the pink paper: plum room, contents, then the paper edge's shadow falling inside."""
    pp = _pocket(i)
    x, y, r = [P_STEM, P_HIPPO, P_AMYG, P_PFC][i]
    c.save(); c.clipPath(pp, skia.ClipOp.kIntersect, True)
    fill_paper(c, p_rect(x - r - 60, y - r - 60, 2 * r + 120, 2 * r + 120), hexc('#4a2c50'), 2030 + i)
    sh = skia.GradientShader.MakeRadial(skia.Point(x, y + r * 0.35), r * 1.2, [with_alpha(hexc('#f6b77a'), 0.35), with_alpha(hexc('#f6b77a'), 0)])
    c.drawCircle(x, y, r * 1.3, skia.Paint(Shader=sh, BlendMode=skia.BlendMode.kScreen))
    # floor line
    fill_paper(c, p_rect(x - r - 40, y + r * 0.62, 2 * r + 80, r), hexc('#3a2140'), 2040 + i)
    inner(c)
    # inner shadow cast by the surrounding paper
    M = c.getTotalMatrix(); s = math.sqrt(abs(M.getScaleX() * M.getScaleY()))
    outer = p_diff(p_rect(x - r * 3, y - r * 3, r * 6, r * 6), pp)
    c.save(); c.setMatrix(skia.Matrix.Concat(skia.Matrix.Translate(9 * s, 15 * s), M))
    c.drawPath(outer, skia.Paint(AntiAlias=True, Color=with_alpha(SHADOW, 0.6), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, max(0.5, 12 * s), False)))
    c.restore()
    c.restore()
    ink(c, path_points(pp, 6)[0], 3.0, 2050 + i, boil_of(0), closed=True, alpha=0.45, jitter=1.5)

HIPPO_SCRAPS = ['friend', 'cup', 'ticket', 'school', 'cat', 'boat']

def _line_pos(k):
    x0, y0 = P_HIPPO[0] - 225, P_HIPPO[1] - 250
    u = (k + 0.5) / 6
    x = x0 + u * 450
    sag = 26 * math.sin(u * math.pi)
    return x, y0 + sag

def hippo_room(c, t, f):
    b = boil_of(f)
    tq = tw(t)
    x, y, r = P_HIPPO
    # clothesline
    pts = [_line_pos(k) for k in range(6)]
    line = [(x - 330, y - 262)] + pts + [(x + 330, y - 268)]
    pencil(c, catmull(line, 6), 2.0, 2100, b, C['cream'], 0.6, passes=1)
    # cabinet
    o_today = prog(t, T_TODAY, T_TODAY + 0.3, ease_out)
    o_long = prog(t, T_LONG, T_LONG + 0.3, ease_out)
    c.save(); c.translate(x + 150, y + 205); c.scale(0.8, 0.8)
    chars.cabinet(c, t, b, (o_today, 0.0, o_long))
    c.restore()
    # dust puff from the old drawer
    dp = prog(t, T_LONG + 0.1, T_LONG + 1.1)
    if 0 < dp < 1:
        for k in range(6):
            ang = math.radians(150 + k * 25)
            rr = 30 + 110 * ease_out(dp)
            px, py = x + 150 - 90 * 0.8 + math.cos(ang) * rr * 0.8, y + 205 - 60 + math.sin(ang) * rr * 0.6
            c.save(); c.translate(px, py); sc = 0.4 + dp
            c.scale(sc, sc)
            fill_paper(c, _dust(k), hexc('#c9c0b8'), 2110 + k, alpha=0.7 * (1 - dp))
            c.restore()
    # seahorse
    look = 0.0
    turn = prog(t, T_TODAY - 0.3, T_TODAY)
    bob = 12 * math.sin(tq * 2.2)
    c.save(); c.translate(x - 165, y + 112 + bob); c.scale(0.76, 0.76); c.rotate(4 * math.sin(tq * 1.1) + 8 * turn)
    fin = 1.0 if (ph(4, 0) + 1.2 < t < ph(4, 0) + 2.2) else 0.0
    chars.seahorse(c, tq, b, look=0.8 * turn, fin=fin, blink=1.0 if (tq % 3.1) < 0.12 else 0.0)
    c.restore()
    # scraps fly from the drawers up to the line
    for k, kind in enumerate(HIPPO_SCRAPS):
        t0 = (T_TODAY + 0.25 + k * 0.3) if k < 3 else (T_LONG + 0.25 + (k - 3) * 0.28)
        if t < t0: continue
        u = prog(t, t0, t0 + 0.6, ease_io)
        sx, sy = x + 150 - 80, y + 205 - (250 if k < 3 else 60) * 0.8
        ex, ey = _line_pos(k)
        px = lerp(sx, ex, u); py = lerp(sy, ey + 44, u) - 150 * math.sin(u * math.pi)
        rot = (1 - u) * (220 if k % 2 else -200) + 5 * math.sin(t * 2.3 + k) * u
        sc = lerp(0.3, 0.58, ease_out(u))
        c.save(); c.translate(px, py)
        if u >= 1:
            c.translate(0, -44); c.rotate(4 * math.sin(t * 2.1 + k * 1.7)); c.translate(0, 44)
        c.rotate(rot); c.scale(sc, sc)
        chars.scrap(c, kind, t, b)
        c.restore()
        if u >= 1:
            c.save(); c.translate(ex, ey + 4); c.rotate(4 * math.sin(t * 2.1 + k * 1.7)); chars.clothespin(c, b); c.restore()

@lru
def _dust(k):
    return torn_path(p_circle(0, 0, 26 + k * 3), 2120 + k, 3.0)

def stem_room(c, t, f):
    b = boil_of(f)
    x, y, r = P_STEM
    tq = tw(t)
    lev = 0.0
    if t > T_LEVER: lev = clamp(spring(t - T_LEVER, 2.2, 7.0), 0, 1.15)
    on = prog(t, T_LEVER + 0.08, T_LEVER + 0.16)
    c.save(); c.translate(x + 70, y + 130); c.scale(0.95, 0.95)
    chars.lever_panel(c, t, b, lev, on)
    c.restore()
    # worker: idle -> anticipation -> pull -> cheer
    ant = prog(t, T_LEVER - 0.35, T_LEVER - 0.05, ease_out) * (1 - prog(t, T_LEVER, T_LEVER + 0.1))
    cheer = prog(t, T_LEVER + 0.2, T_LEVER + 0.45, ease_out) * (1 - prog(t, T_LEVER + 1.2, T_LEVER + 1.6))
    reach = prog(t, T_LEVER - 0.6, T_LEVER - 0.3, ease_io) * (1 - cheer)
    hop = 30 * math.sin(clamp((t - T_LEVER - 0.2) / 0.5) * math.pi) if T_LEVER + 0.2 < t < T_LEVER + 0.7 else 0
    pose = dict(arm_r=lerp(-15, 150, reach) + 20 * ant - 40 * (1 - ant) * (t > T_LEVER) * reach, arm_l=lerp(15, 30, reach) + 150 * cheer,
                lean=-10 * ant + 6 * reach, eyes='open', mouth='grin' if cheer > 0.3 else 'smile', look=(1, -0.5) if reach > 0.5 else (0.4, 0))
    if cheer > 0: pose['arm_r'] = lerp(pose['arm_r'], 150, cheer)
    c.save(); c.translate(x - 80, y + 70 - hop + 3 * math.sin(tq * 3)); c.scale(0.78, 0.78)
    chars.person(c, tq, b, dict(shirt=C['coral'], torso='overalls', pants=C['blue2'], hat='hardhat'), pose, seed=2200)
    c.restore()
    if t > T_LEVER:
        props.sparkle(c, x + 70, y + 20, 120, T_LEVER + 0.1, t, b, 2210, C['gold'])

def amyg_room(c, t, f):
    b = boil_of(f)
    x, y, r = P_AMYG
    tq = tw(t)
    g = clamp(spring(t - T_GLOW, 1.2, 3.5), 0, 1.2) if t > T_GLOW else 0.0
    # rays of coloured light (cut paper gels)
    if g > 0:
        c.save(); c.translate(x + 70, y - 10); c.rotate(t * 6)
        for k in range(10):
            col = [C['gold'], C['pink'], hexc('#ffc58f'), C['rose']][k % 4]
            c.save(); c.rotate(k * 36); c.scale(g, g)
            fill_paper(c, _ray(k), col, 2300 + k, soft=True, alpha=0.35)
            c.restore()
        c.restore()
    arm_up = prog(t, T_GLOW - 0.4, T_GLOW - 0.1, ease_out)
    by = 6 * math.sin(tq * 2.6)
    lx, ly = x - 30 + 118 * 0.9, y + 60 + by + (-40 - 34 * arm_up) * 0.9
    chars.lantern_glow(c, lx, ly, g)
    c.save(); c.translate(x - 30, y + 60 + by); c.scale(0.9, 0.9)
    chars.almond(c, tq, b, g, blink=1.0 if (tq % 2.7) < 0.1 else 0.0, arm_up=arm_up, mood='grin' if g > 0.5 else 'smile')
    c.translate(118, -40 - 34 * arm_up); c.rotate(6 * math.sin(tq * 2))
    chars.lantern(c, t, b, g, halo=False)
    c.restore()

@lru
def _ray(k):
    return rough_path(p_poly([(0, 0), (-40, -560), (40, -560)]), 2310 + k, 1.0)

def pfc_room(c, t, f):
    b = boil_of(f)
    x, y, r = P_PFC
    tq = tw(t)
    yawn = prog(t, T_DOZE - 0.75, T_DOZE - 0.35) * (1 - prog(t, T_DOZE - 0.2, T_DOZE + 0.1))
    doze = prog(t, T_DOZE - 0.05, T_DOZE + 0.5, ease_io)
    write = 1.0 if (T_PFC - 0.3 < t < T_DOZE - 0.9) else 0.0
    ticks = int(clamp((t - T_PFC) / 0.65, 0, 3)) if t > T_PFC else 0
    lamp = 1 - 0.6 * prog(t, T_DOZE + 0.3, T_DOZE + 0.9)
    # director seated behind the desk
    head_t = -4 + 26 * doze + 3 * math.sin(tq * 1.2) * doze
    pose = dict(seated=True, arm_r=lerp(40 + 14 * math.sin(tq * 16) * write, 10, doze), arm_l=lerp(60, 150, yawn) * (1 - doze) + 20 * doze,
                eyes='closed' if doze > 0.5 else ('half' if yawn > 0.4 or doze > 0.05 else 'open'),
                mouth='yawn' if yawn > 0.05 else ('o' if doze > 0.5 else 'flat'), mouth_open=yawn, head=head_t, lean=10 * doze, look=(-0.6, 0.6))
    c.save(); c.translate(x - 30, y + 100 + 6 * doze); c.scale(1.0, 1.0)
    chars.person(c, tq, b, dict(shirt=hexc('#e8d9b0'), hat='beret', glasses=True, pants=C['wood2'], hair='bob', hair_col=C['ink']), pose, seed=2400)
    c.restore()
    c.save(); c.translate(x, y + 150); c.scale(0.95, 0.95)
    chars.desk(c, t, b, ticks, lamp)
    c.restore()
    # Zzz
    if doze > 0.5:
        for k in range(3):
            u = ((t - T_DOZE - 0.2) * 0.55 + k / 3) % 1.0
            if t - T_DOZE - 0.2 < k * 0.6: continue
            zx = x + 20 + 90 * u + 20 * math.sin(u * 7 + k); zy = y - 40 - 230 * u
            hand_text(c, 'Z' if k % 2 == 0 else 'z', zx, zy, 60 - 12 * k, C['cream'], TITLE, 2450 + k, b, alpha=math.sin(u * math.pi))

@lru
def _signal_paths():
    sx, sy = P_STEM[0], P_STEM[1] - P_STEM[2] - 10
    targets = [(P_HIPPO[0] + 60, P_HIPPO[1] + P_HIPPO[2] - 20), (P_AMYG[0] - 40, P_AMYG[1] + P_AMYG[2] - 10), (P_PFC[0] - 180, P_PFC[1] + 240),
               (-850, -250), (-150, -620), (350, -560), (-760, 300)]
    out = []
    for i, (tx, ty) in enumerate(targets):
        mx = (sx + tx) / 2 + (80 if i % 2 else -80); my = (sy + ty) / 2
        out.append(catmull([(sx + (i - 3) * 12, sy), (mx, my), (tx, ty)], 20))
    return out

def signals(c, t, f):
    b = boil_of(f)
    t0 = T_LEVER + 0.15
    if t < t0 or t > t0 + 3.2: return
    for i, P in enumerate(_signal_paths()):
        Q, s = resample(P, 4.0, False)
        u = prog(t, t0 + i * 0.07, t0 + 0.9 + i * 0.07, ease_out)
        fade = 1 - prog(t, t0 + 2.2, t0 + 3.2)
        n = max(2, int(len(Q) * u))
        pencil(c, Q[:n], 3.0, 2500 + i, b, C['gold'], 0.55 * fade, passes=1, taper=(0.05, 0.4))
        for k in range(3):
            v = ((t - t0) * 0.9 - k * 0.18 - i * 0.05)
            if 0 < v < 1:
                p = Q[min(len(Q) - 1, int(v * len(Q)))]
                glow(c, p[0], p[1], 46, C['gold'], 0.9 * fade)
                c.drawCircle(p[0], p[1], 9, skia.Paint(AntiAlias=True, Color=with_alpha(C['white'], fade)))
        if u >= 1:
            tip = Q[-1]
            glow(c, tip[0], tip[1], 150 * (0.6 + 0.4 * math.sin(t * 6 + i)), C['gold'], 0.5 * fade)

def brain_world(c, t, f, cam):
    b = boil_of(f)
    background(c, C['night'], 7)
    c.save(); cam.apply(c)
    # a few stars far behind
    for i, (sx, sy) in enumerate([(-2300, -900), (1900, -1100), (2100, 300), (-2400, 900), (1700, -300), (-1900, -1500)]):
        props.star(c, sx, sy, 40, t, 2600 + i, C['gold'] if i % 2 else C['cream'], b)
    piece(c, _cap_big(), C['coral'], 2601, 3.0, 0.35)
    c.save(); c.clipPath(_cap_big(), skia.ClipOp.kIntersect, True)
    for k in range(-14, 14):
        fill_paper(c, p_poly([(-2000 + k * 160, -1600), (-1920 + k * 160, -1600), (-1400 + k * 160, 400), (-1480 + k * 160, 400)]), C['cream'], 2602 + k, soft=True, alpha=0.9)
    c.restore()
    c.save(); c.translate(-1800, 150); c.rotate(wig(t, 0.6, 3) * 8)
    piece(c, _pom_big(), C['mustard'], 2640, 2.2)
    c.restore()
    piece(c, _head_profile(), C['skin'], 2641, 3.0, 0.35)
    piece(c, _cap_band_big(), C['cream'], 2642, 2.0)
    # face
    ink(c, arc(1150, 250, 70, 40, 20, 160, 16), 12, 2643, b, taper=(0.3, 0.3))
    ink(c, arc(1140, 150, 80, 30, 200, 330, 14), 10, 2644, b, alpha=0.8)
    chars.cheek(c, 1230, 470, 70, 2645, 0.7)
    ink(c, [(1370, 790), (1420, 792)], 8, 2646, b, alpha=0.7)
    # brain parts
    piece(c, _stem(), hexc('#c98fa2'), 2650, 2.0)
    c.save(); c.clipPath(_stem(), skia.ClipOp.kIntersect, True)
    for k in range(5):
        pencil(c, [(-380 + k * 80, 600), (-300 + k * 50, 1900)], 4, 2651 + k, b, hexc('#8a4a66'), 0.35, passes=1)
    c.restore()
    piece(c, _cerebellum(), hexc('#d98b98'), 2656, 2.0)
    c.save(); c.clipPath(_cerebellum(), skia.ClipOp.kIntersect, True)
    for k in range(6):
        pencil(c, arc(-640, 700, 330 - k * 40, 190 - k * 25, 0, 180, 30), 4, 2657 + k, b, hexc('#8a4a66'), 0.4, passes=1)
    c.restore()
    bp = _brain()
    piece(c, bp, C['pink'], 2663, 3.0, 0.4)
    c.save(); c.clipPath(bp, skia.ClipOp.kIntersect, True)
    for i, P in enumerate(_gyri()):
        ink(c, P, 7, 2700 + i, b, color=hexc('#b9606f'), alpha=0.55, taper=(0.3, 0.3))
    ink(c, catmull([(-250, 330), (100, 240), (500, 180), (820, 60)], 12), 11, 2690, b, color=hexc('#a4505f'), alpha=0.7)
    # brain lights up when the signals arrive
    lit = prog(t, T_LEVER + 0.6, T_LEVER + 1.2) * (1 - 0.6 * prog(t, T_LEVER + 1.8, T_LEVER + 3.0))
    if lit > 0:
        c.drawPath(bp, skia.Paint(AntiAlias=True, Color=with_alpha(hexc('#ffd28a'), 0.28 * lit), BlendMode=skia.BlendMode.kScreen))
    c.restore()
    # the four rooms
    pocket_open(c, 0, lambda cc: stem_room(cc, t, f))
    pocket_open(c, 1, lambda cc: hippo_room(cc, t, f))
    pocket_open(c, 2, lambda cc: amyg_room(cc, t, f))
    pocket_open(c, 3, lambda cc: pfc_room(cc, t, f))
    signals(c, t, f)
    # labels
    for (txt, x, y, t0, rot, sz, sd) in [('brainstem', P_STEM[0] - P_STEM[2] - 90, P_STEM[1] - 40, ph(3, 0) + 0.35, -5, 38, 2801),
                                         ('hippocampus', P_HIPPO[0] - 140, P_HIPPO[1] + P_HIPPO[2] + 24, ph(4, 0) + 0.15, 3, 44, 2802),
                                         ('amygdala', P_AMYG[0] + 40, P_AMYG[1] + P_AMYG[2] + 34, ph(5, 0) + 0.2, -4, 40, 2803),
                                         ('prefrontal cortex', P_PFC[0] + 10, P_PFC[1] + P_PFC[2] + 10, ph(5, 2) + 0.05, 2, 38, 2804)]:
        if t > t0:
            sc = ease_out_back(prog(t, t0, t0 + 0.35))
            label(c, txt, x, y, sz, rot, sd, b, reveal=prog(t, t0 + 0.08, t0 + 0.5), scale=sc)
    c.restore()

@lru
def _pom_big():
    return torn_path(p_circle(0, 0, 110), 2640, 6.0)

def scene_D(c, t, f):
    brain_world(c, t, f, keyframes(t, D_KEYS))
