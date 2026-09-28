"""Why we dream (theories board), morning, and the ending."""
import math, functools
import numpy as np
import skia
from engine import *
import chars, props
from scenes import ph, keyframes, zoom_log, render_image, breath_of, bedroom, CLOUD
from scenes2 import dream_world

lru = functools.lru_cache(None)

# ======================================================================= G: why do we dream? (a kraft-paper theory board)
T_G = 41.75
X2, X3 = 2620, 4170     # centres of the 'sort memories' and 'soothe feelings' sections
G_KEYS = [(T_G, 960, 540, 1.0), (ph(8, 1) - 0.55, 990, 540, 1.03), (ph(8, 1) + 0.1, X2, 540, 1.0), (ph(8, 2) - 0.45, X2 + 20, 540, 1.02),
          (ph(8, 2) + 0.15, X3, 540, 1.0), (49.5, X3 + 25, 540, 1.05)]

@lru
def _qmark():
    hook = ink_path(catmull([(-110, -120), (-90, -210), (0, -250), (95, -205), (100, -110), (30, -50), (0, 20), (0, 70)], 12), 70, 3600, 0,
                    taper=(0.0, 0.0), jitter=0, press=0.0)
    return rough_path(hook, 3601, 1.0), rough_path(p_circle(0, 160, 44), 3602, 0.6)

@lru
def _note(w, h, seed):
    return rough_path(p_rect(-w / 2, -h / 2, w, h, 2), seed, 0.6)

@lru
def _bubble(w, h, seed, tail_dx):
    body = p_ellipse(0, 0, w / 2, h / 2)
    tail = p_poly([(-20, h / 2 - 16), (20, h / 2 - 16), (tail_dx, h / 2 + 70)])
    return rough_path(p_union(body, tail), seed, 1.0)

@lru
def _heart_half(side):
    P = [(0, -40), (-30 * side, -92), (-86 * side, -96), (-120 * side, -50), (-110 * side, 10), (-60 * side, 70), (0, 120)]
    # jagged tear down the middle
    r = rnd(3700)
    tear = [(side * (4 + r.uniform(-10, 10)), y) for y in np.linspace(120, -40, 9)]
    pts = P + tear[1:-1]
    return rough_path(to_path(np.array(catmull(P, 8).tolist() + tear[1:-1]), True), 3701 + side, 0.8)

@lru
def _folder(k):
    back = rough_path(p_union(p_rect(-80, -100, 160, 110, 6), p_rect(-80, -118, 64, 24, 6)), 3710 + k, 0.6)
    front = rough_path(p_rect(-84, -70, 168, 84, 6), 3720 + k, 0.6)
    return back, front

FOLDER_COLS = ['coral', 'sage', 'blue']
SORT_SCRAPS = [('friend', 0), ('school', 1), ('cup', 0), ('cat', 2), ('ticket', 0), ('boat', 1)]

def theory_board(c, t, f):
    b = boil_of(f)
    tq = tw(t)
    fill_paper(c, p_rect(-400, -200, 6200, 1500), C['kraft'], 3800)
    # collage clutter pinned to the board
    for i, (x, y, w, h, rot, col) in enumerate([(180, 180, 200, 140, -6, 'cream'), (1700, 140, 180, 120, 5, 'rose'), (3150, 200, 200, 130, -4, 'cream'),
                                                 (4600, 160, 190, 150, 7, 'sage'), (1700, 900, 170, 120, 4, 'cream'), (3200, 930, 180, 110, -5, 'rose'),
                                                 (4650, 930, 170, 120, 3, 'cream'), (150, 920, 160, 130, 5, 'sage'), (3500, 560, 150, 110, -8, 'sage')]):
        c.save(); c.translate(x, y); c.rotate(rot)
        piece(c, _note(w, h, 3810 + i), C[col], 3810 + i, 1.2)
        for k in range(3):
            pencil(c, [(-w / 2 + 20, -h / 2 + 30 + k * 28), (w / 2 - 30 - 20 * (k % 2), -h / 2 + 30 + k * 28)], 2.0, 3820 + i * 3 + k, b, alpha=0.45, passes=1)
        c.drawCircle(0, -h / 2 + 12, 9, skia.Paint(AntiAlias=True, Color=C['red']))
        c.restore()
    # --- 1. scientists debate around a big question mark
    hook, dot = _qmark()
    qs = spring(t - (T_G + 0.35), 1.4, 4.5) if t > T_G + 0.35 else 0.0
    c.save(); c.translate(960, 470); c.rotate(4 * math.sin(tq * 1.4)); c.scale(1.35 * qs, 1.35 * qs)
    piece(c, hook, C['coral'], 3830, 2.4)
    piece(c, dot, C['coral'], 3831, 2.4)
    c.restore()
    for side, (x, st, sd) in enumerate([(560, dict(shirt=C['white'], torso='coat', glasses=True, hair='curly', hair_col=C['coral2'], pants=C['grey']), 3840),
                                          (1360, dict(shirt=C['white'], torso='coat', glasses=False, hair='bob', hair_col=C['hair'], pants=C['blue2']), 3860)]):
        talk = (int((t - T_G) / 0.7) % 2) == side
        gest = 0.5 + 0.5 * math.sin(tq * 6 + side * 2) if talk else 0.0
        pose = dict(arm_r=(60 + 60 * gest) if side == 0 else -20, arm_l=(20 if side == 0 else 60 + 60 * gest), eyes='open',
                    mouth='o' if talk and (int(tq * 8) % 2) else 'smile', look=(1, -0.3) if side == 0 else (-1, -0.3), head=6 * math.sin(tq * 2 + side),
                    lean=(4 if side == 0 else -4))
        c.save(); c.translate(x, 800); c.scale(1.25, 1.25)
        chars.person(c, tq, b, st, pose, seed=sd)
        c.restore()
    # thought bubbles: two ideas
    for k, (x, y, t0, dx) in enumerate([(430, 250, T_G + 0.9, 60), (1500, 250, T_G + 1.5, -60)]):
        s = spring(t - t0, 1.5, 5.0) if t > t0 else 0.0
        if s <= 0: continue
        c.save(); c.translate(x, y); c.scale(s, s)
        piece(c, _bubble(300, 200, 3880 + k, dx), C['white'], 3880 + k, 2.0)
        if k == 0:
            c.save(); c.translate(-50, -10); c.rotate(-8); c.scale(0.55, 0.55); chars.scrap(c, 'friend', t, b); c.restore()
            c.save(); c.translate(50, 0); c.rotate(10); c.scale(0.55, 0.55); chars.scrap(c, 'cat', t, b); c.restore()
        else:
            c.save(); c.scale(0.42, 0.42)
            for sd_ in (-1, 1):
                piece(c, _heart_half(sd_), C['red'], 3890 + sd_, 1.2)
            c.restore()
        hand_text(c, '?', 118 if k == 0 else -118, -40, 64, C['ink'], TITLE, 3895 + k, b)
        c.restore()
    # --- 2. sorting memories into folders
    x0 = X2
    c.save(); c.translate(x0 - 330, 620 + 12 * math.sin(tq * 2.2)); c.scale(1.05, 1.05); c.rotate(4 * math.sin(tq * 1.1))
    chars.seahorse(c, tq, b, look=1.0, fin=1.0 if t > ph(8, 1) else 0.0, blink=1.0 if (tq % 2.9) < 0.1 else 0.0)
    c.restore()
    folders = [(x0 + 60 + k * 200, 900) for k in range(3)]
    for k, (fx, fy) in enumerate(folders):
        back, front = _folder(k)
        c.save(); c.translate(fx, fy); piece(c, back, mix(C[FOLDER_COLS[k]], C['ink'], 0.12), 3900 + k, 1.6); c.restore()
    t_sort = ph(8, 1) + 0.15
    for i, (kind, fk) in enumerate(SORT_SCRAPS):
        t0 = t_sort + i * 0.24
        u = prog(t, t0, t0 + 0.55, ease_io)
        sx, sy = x0 - 40 + (i % 3) * 36 - 36, 520 + (i // 3) * 30
        fx, fy = folders[fk]
        ex, ey = fx + (i % 2) * 14 - 7, fy - 70
        px = lerp(sx, ex, u); py = lerp(sy, ey, u) - 200 * math.sin(u * math.pi)
        rot = lerp([-14, 10, -6, 12, -10, 6][i], [-4, 3, -2, 4, -3, 2][i], u) + 360 * u * (1 if i % 2 else -1) * (u < 1)
        c.save(); c.translate(px, py); c.rotate(rot); c.scale(lerp(0.62, 0.5, u), lerp(0.62, 0.5, u))
        chars.scrap(c, kind, t, b)
        c.restore()
    for k, (fx, fy) in enumerate(folders):
        back, front = _folder(k)
        c.save(); c.translate(fx, fy)
        piece(c, front, C[FOLDER_COLS[k]], 3910 + k, 1.2)
        ink(c, [(-50, -30), (50, -30)], 2.0, 3915 + k, b, alpha=0.4)
        c.restore()
    # --- 3. soothing feelings: the almond mends a torn heart with tape
    x1 = X3
    t_heal = ph(8, 2)
    join = prog(t, t_heal - 0.1, t_heal + 0.35, ease_io)
    warm = prog(t, t_heal + 0.9, t_heal + 1.4)
    c.save(); c.translate(x1 - 240, 700 + 6 * math.sin(tq * 2.4)); c.scale(1.35, 1.35)
    chars.almond(c, tq, b, warm, blink=1.0 if (tq % 2.6) < 0.1 else 0.0, arm_up=0.6, mood='grin' if warm > 0.3 else 'smile')
    c.restore()
    hx, hy = x1 + 110, 520
    if warm > 0:
        glow(c, hx, hy, 360 * warm, hexc('#ffb3a0'), 0.55 * warm)
    c.save(); c.translate(hx, hy); c.rotate(-6 + 4 * math.sin(tq * 1.6)); c.scale(1.35 + 0.05 * math.sin(t * 5) * warm, 1.35 + 0.05 * math.sin(t * 5) * warm)
    for sd_ in (-1, 1):
        c.save(); c.translate(sd_ * 40 * (1 - join), 10 * (1 - join) * sd_); c.rotate(sd_ * 12 * (1 - join))
        piece(c, _heart_half(sd_), C['red'], 3920 + sd_, 2.0)
        crayon(c, p_circle(-sd_ * -50, -40, 26), C['pink'], 3922 + sd_, 0.4)
        c.restore()
    for k, (tx, ty, rot) in enumerate([(0, -30, 80), (0, 30, 100), (0, 80, 70)]):
        t0 = t_heal + 0.35 + k * 0.25
        u = prog(t, t0, t0 + 0.22, ease_out)
        if u <= 0: continue
        tape(c, tx + (1 - u) * 260, ty - (1 - u) * 160, 110, 34, rot + (1 - u) * 90, 3930 + k, alpha=0.8)
    c.restore()
    if warm > 0:
        props.sparkle(c, hx, hy, 220, t_heal + 1.0, t, b, 3940, C['gold'])

def scene_G(c, t, f):
    background(c, C['kraft'], 3799)
    cam = keyframes(t, G_KEYS)
    c.save(); cam.apply(c)
    theory_board(c, t, f)
    c.restore()

def slide_in(c, t, f, drawA, drawB, t0, t1):
    """Sheet B slides in from the right over A, casting a shadow (like laying down a new page)."""
    u = prog(t, t0, t1, ease_io)
    drawA(c, t, f)
    if u <= 0: return
    img = render_image(drawB, t, f)
    x = (1 - u) * (W + 120)
    c.save(); c.translate(x, 0); c.rotate(-3 * (1 - u))
    page = _torn_page()
    shadow(c, page, 6.0, 0.45)
    c.drawPath(page, skia.Paint(AntiAlias=True, Color=C['white']))
    c.save(); c.clipPath(_torn_page_inner(), skia.ClipOp.kIntersect, True)
    c.drawImage(img, 0, 0)
    c.restore()
    c.restore()

@lru
def _torn_page():
    return torn_path(p_rect(-30, -60, W + 400, H + 120), 3990, 4.0)

@lru
def _torn_page_inner():
    return torn_path(p_rect(-24, -60, W + 400, H + 120), 3991, 3.0)

# ======================================================================= H + I: morning, the dream slips away, one scrap remains
T_MORNING = ph(9, 0)
T_GONE = ph(9, 1)
T_BREAKFAST = ph(9, 1, end=True) - 0.45
T_TITLE = 55.6
FILM_END = 59.0

MEM_ITEMS = [('school', (10, 30), 0.26), ('star', (-170, -80), 0.9), ('cat', (190, 70), 0.9), ('boat', (160, -90), 0.9), ('moon', (-220, 50), 0.9), ('fish', (-60, -110), 1.0)]

def _mem_draw(c, kind, t, b, s):
    c.save(); c.scale(s, s)
    if kind == 'school':
        chars.props_school_icon(c, t, b)
    elif kind == 'star':
        props.star(c, 0, 0, 36, t, 4001, C['gold'], b, spark=False)
    elif kind == 'cat':
        c.scale(0.4, 0.4); c.translate(0, 120); props.cat(c, t, b, 0, eyes='open')
    elif kind == 'boat':
        c.scale(0.45, 0.45); c.translate(0, 80); props.toy_boat(c, t, b)
    elif kind == 'moon':
        props.moon(c, 0, 0, 30, t, b)
    elif kind == 'fish':
        c.scale(0.55, 0.55); props.fish(c, t, b, 900, C['coral'], wiggle=0.6)
    c.restore()

WINDOW_EXIT = (330, 300)

def _item_state(i, t):
    """0 = in the cloud, (0,1) = flying out of the window, 1 = gone"""
    t0 = T_GONE + 0.1 + i * 0.3
    return prog(t, t0, t0 + 0.9, ease_in)

def fish_path(t):
    """The one scrap that stays: released when the cloud pops, it see-saws down into the hand.
    Ends exactly on the in-hand pose (position, rotation and the bed's 1.22 scale) so the hand-off is seamless."""
    cx, cy = CLOUD[0], CLOUD[1]
    sx, sy = cx - 60, cy - 110
    hand = (969.9, 659.8)          # world position of the fish when resting in the hand
    u = prog(t, T_BREAKFAST - 0.35, T_BREAKFAST + 1.6)
    e = smooth(u)
    x = lerp(sx, hand[0], e) + 70 * math.sin(u * math.pi * 3) * (1 - e)
    y = lerp(sy, hand[1], e)
    rot = 25 * math.sin(u * math.pi * 3) * (1 - e) - 16 * e
    sc = lerp(1.0, 1.22, e)
    return x, y, rot, u, sc

def scene_H(c, t, f):
    b = boil_of(f)
    dawn = prog(t, T_MORNING - 0.3, T_MORNING + 1.4, smooth)
    sun = prog(t, T_MORNING, T_MORNING + 1.8, ease_out)
    ring = 1.0 if T_MORNING + 0.1 < t < T_MORNING + 1.0 else 0.0
    wake = prog(t, T_MORNING + 0.55, T_MORNING + 0.65)
    yawn = prog(t, T_MORNING + 0.8, T_MORNING + 1.1) * (1 - prog(t, T_MORNING + 1.5, T_MORNING + 1.8))
    stretch = prog(t, T_MORNING + 0.8, T_MORNING + 1.2, ease_out) * (1 - prog(t, T_MORNING + 1.6, T_MORNING + 2.0, ease_io))
    pop_t = T_BREAKFAST - 0.4
    grow = 1.0 - prog(t, pop_t - 0.25, pop_t + 0.05, ease_in)
    bubbles = 1.0 - prog(t, pop_t - 0.1, pop_t + 0.25)
    toast = max(0.0, t - T_BREAKFAST)
    fx, fy, frot, fu, fsc = fish_path(t)
    landed = fu >= 1
    # face: asleep -> blink awake -> yawn -> watch the dream float away -> smile at the little fish
    if wake < 1:
        head = dict(eyes='closed', mouth_kind='o', breath=breath_of(t))
    else:
        look = (-1.0, -0.6) if t < T_GONE + 1.6 else ((0.3, -0.8) if t < pop_t + 0.4 else (0.6, 0.8))
        blink = 1.0 if (T_MORNING + 0.6 < t < T_MORNING + 0.7) or (54.9 < t < 55.0) else 0.0
        eyes = 'happy' if t > T_TITLE - 0.9 else 'open'
        mouth = 'yawn' if yawn > 0.05 else ('smile' if t > pop_t + 1.4 else 'o')
        head = dict(eyes=eyes, mouth_kind=mouth, breath=yawn, look=look, blink=blink, sway=0.3 * math.sin(t))
    # camera: gentle push toward the face and hand at the end
    push = prog(t, 54.2, 57.2, ease_io)
    cam = Cam(lerp(W / 2, 840, push), lerp(H / 2, 610, push), lerp(1.0, 1.55, push))

    def content(cc):
        for i, (kind, pos, s) in enumerate(MEM_ITEMS):
            if kind == 'fish': continue
            if _item_state(i, t) > 0: continue
            cc.save(); cc.translate(pos[0] + 6 * math.sin(t * 1.5 + i), pos[1] + 6 * math.cos(t * 1.3 + i)); cc.rotate(6 * math.sin(t + i))
            _mem_draw(cc, kind, t, b, s)
            cc.restore()
        if t < pop_t - 0.25:
            cc.save(); cc.translate(-60, -110); cc.rotate(-10)
            _mem_draw(cc, 'fish', t, b, 1.0)
            cc.restore()

    def front(cc, tt, bb):
        cx, cy = CLOUD[0], CLOUD[1]
        for i, (kind, pos, s) in enumerate(MEM_ITEMS):
            if kind == 'fish': continue
            u = _item_state(i, t)
            if 0 < u < 1:
                sx, sy = cx + pos[0], cy + pos[1]
                x = lerp(sx, WINDOW_EXIT[0], u) + 40 * math.sin(u * 9 + i)
                y = lerp(sy, WINDOW_EXIT[1], u) - 120 * math.sin(u * math.pi)
                cc.save(); cc.translate(x, y); cc.rotate(u * 300 * (1 if i % 2 else -1)); sc = 1 - 0.75 * u
                cc.scale(sc, sc)
                _mem_draw(cc, kind, t, bb, s)
                cc.restore()
        # puff when the cloud pops
        pu = prog(t, pop_t - 0.05, pop_t + 0.6)
        if 0 < pu < 1:
            for k in range(8):
                a = math.radians(k * 45 + 10)
                rr = 80 + 260 * ease_out(pu)
                cc.save(); cc.translate(cx + math.cos(a) * rr, cy + math.sin(a) * rr * 0.6); sc = 1.2 * (1 - pu)
                cc.scale(sc, sc)
                piece(cc, _puff(k), C['cream'], 4010 + k, 1.0)
                cc.restore()
        if t >= pop_t - 0.25:
            # same layer before and after landing so there is no pop in colour or position
            wig_ = (8 * math.sin(max(0.0, t - 55.9) * 9) * (1 - prog(t, 56.2, 56.8))) if landed else 0.0
            cc.save(); cc.translate(fx, fy); cc.rotate(frot + wig_); cc.scale(fsc, fsc)
            _mem_draw(cc, 'fish', t, bb, 1.0)
            cc.restore()
        # end title
        if t > T_TITLE:
            u = prog(t, T_TITLE, T_TITLE + 0.6, ease_out)
            inv = 1.0 / cam.zoom
            # draw in screen space
            cc.save(); cc.resetMatrix()
            cc.translate(W / 2, H - 150 + (1 - u) * 320); cc.rotate(-2.5)
            piece(cc, _title_strip(), C['cream'], 4020, 3.0, 0.4)
            hand_text(cc, 'The End', 0, 8, 92, C['ink'], TITLE, 4021, bb, reveal=prog(t, T_TITLE + 0.35, T_TITLE + 0.85), jitter=0.8)
            hand_text(cc, 'new show tonight', 0, 66, 40, C['coral2'], HAND, 4025, bb, reveal=prog(t, T_TITLE + 0.85, T_TITLE + 1.3), jitter=0.6)
            tape(cc, -300, -58, 110, 36, -28, 4022)
            tape(cc, 300, -58, 110, 36, 26, 4023)
            s_ = spring(t - (T_TITLE + 1.35), 1.6, 5.0) if t > T_TITLE + 1.35 else 0.0
            if s_ > 0:
                cc.save(); cc.translate(250, 52); cc.scale(s_, s_); props.moon(cc, 0, 0, 26, t, bb); cc.restore()
            cc.restore()

    def in_hand(cc):
        return

    bedroom(c, t, f, cam, head_kw=head, cloud_grow=grow, cloud_bubbles=bubbles, cloud_content=content,
            dawn=dawn, sun=sun, ring=ring, toast=toast, lamp=1.0 - dawn, night_tint=1.0 - dawn, arm_raise=stretch,
            extra_front=front, hand_item=in_hand)
    # fade out at the very end
    fo = prog(t, FILM_END - 0.55, FILM_END - 0.02)
    if fo > 0:
        c.drawRect(skia.Rect.MakeWH(W, H), skia.Paint(Color=with_alpha(hexc('#120d1c'), fo)))

@lru
def _puff(k):
    return torn_path(p_circle(0, 0, 34 + (k % 3) * 8), 4030 + k, 3.0)

@lru
def _title_strip():
    return torn_path(p_rect(-340, -86, 680, 190), 4031, 2.6)

def iris_transition(c, t, f, drawA, drawB, t0, t1, center=(960, 540)):
    """B is revealed through a growing hole cut in paper sheet A (rough edge, soft inner shadow)."""
    u = prog(t, t0, t1, ease_io)
    drawB(c, t, f)
    if u >= 1: return
    imgA = render_image(drawA, t, f)
    r = 2300 * u
    hole = _iris_hole()
    c.save()
    M = skia.Matrix.Translate(center[0], center[1]); M.preScale(max(r, 0.01) / 100, max(r, 0.01) / 100)
    hp = skia.Path(hole); hp.transform(M)
    sheet = p_diff(p_rect(-50, -50, W + 100, H + 100), hp)
    shadow(c, sheet, 4.0, 0.5)
    c.clipPath(sheet, skia.ClipOp.kIntersect, True)
    c.drawImage(imgA, 0, 0)
    c.restore()

@lru
def _iris_hole():
    return torn_path(p_circle(0, 0, 100), 4040, 2.0)
