"""Hand-made paper collage animation engine (Skia + NumPy).

Everything visual in the film is built from a few primitives defined here:
  * procedural paper textures (fibres, grain, embossed tooth) applied with an overlay blend
  * rough 'scissor cut' / 'torn' paper pieces with layered soft + contact shadows
  * boiling ink / pencil lines (line boil at 8 fps, the way hand-drawn frames flicker)
  * crayon grain fills, washi tape, handwritten text with per-letter jitter
  * a parallax camera and post (vignette, grain, exposure flicker)
"""
import os, math, functools
import numpy as np
import skia

W, H, FPS = 1920, 1080, 24
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(ROOT, 'assets', 'fonts')
CACHE = os.path.join(ROOT, 'build', 'cache')
os.makedirs(CACHE, exist_ok=True)

# ------------------------------------------------------------------ colours
def hexc(h, a=1.0):
    h = h.lstrip('#')
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return skia.ColorSetARGB(int(round(a * 255)), r, g, b)

def rgba(r, g, b, a=1.0):
    return skia.ColorSetARGB(int(round(a * 255)), int(r), int(g), int(b))

def mix(c1, c2, t):
    t = max(0.0, min(1.0, t))
    a = [skia.ColorGetA(c1), skia.ColorGetR(c1), skia.ColorGetG(c1), skia.ColorGetB(c1)]
    b = [skia.ColorGetA(c2), skia.ColorGetR(c2), skia.ColorGetG(c2), skia.ColorGetB(c2)]
    v = [int(round(x + (y - x) * t)) for x, y in zip(a, b)]
    return skia.ColorSetARGB(*v)

def with_alpha(c, a):
    return skia.ColorSetARGB(int(round(a * 255)), skia.ColorGetR(c), skia.ColorGetG(c), skia.ColorGetB(c))

# Film palette (kept in one place so every scene shares it)
PAL = dict(
    night='#222a4e', night2='#2c3866', night3='#3a4a80', ink='#2a2433', cream='#f4ead5', cream2='#e9dcc0',
    kraft='#c9a57a', mustard='#eab54a', gold='#f6cf62', coral='#e2725b', coral2='#c9573f', pink='#eea3a6',
    pink2='#d97f8c', rose='#f5c4bd', sage='#8fb59b', teal='#2c5a60', teal2='#3f7571', deepteal='#1c3a44',
    blue='#6e8cc4', blue2='#4f6aa3', lav='#a99bd1', skin='#f0c3a0', skin2='#dfa27e', cheek='#e9836f',
    hair='#4a3226', wood='#8a5a3c', wood2='#6b4230', red='#c8433a', white='#fbf6ea', sky='#f6c9a0',
    sky2='#f3a988', sun='#f7c65a', grey='#8e8a96', brick='#b5523b', leaf='#6f9c6c', sea='#3b6ea0', sea2='#2f5a8a',
    sea3='#5a8cc0', foam='#e8f0ee', wall='#39426f', wall2='#434e82', floor='#5e4236')
C = {k: hexc(v) for k, v in PAL.items()}

# ------------------------------------------------------------------ easing / timing
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x

def lerp(a, b, t):
    return a + (b - a) * t

def smooth(t):
    t = clamp(t); return t * t * (3 - 2 * t)

def ease_io(t):
    t = clamp(t); return 4 * t ** 3 if t < .5 else 1 - (-2 * t + 2) ** 3 / 2

def ease_out(t):
    t = clamp(t); return 1 - (1 - t) ** 3

def ease_in(t):
    t = clamp(t); return t ** 3

def ease_out_back(t, s=1.9):
    t = clamp(t) - 1; return 1 + (s + 1) * t ** 3 + s * t ** 2

def prog(t, t0, t1, ease=None):
    if t1 == t0:
        v = 1.0 if t >= t1 else 0.0
    else:
        v = clamp((t - t0) / (t1 - t0))
    return ease(v) if ease else v

def spring(t, f=1.6, d=5.5):
    """0 -> 1 with a lively overshoot; t in seconds since start."""
    if t <= 0: return 0.0
    return 1 - math.exp(-d * t) * math.cos(2 * math.pi * f * t)

def pop(t, t0, f=1.8, d=6.5):
    return spring(t - t0, f, d)

def tw(t):
    """quantise to twos (12 fps) for stop-motion character timing"""
    return math.floor(t * 12 + 1e-6) / 12.0

# ------------------------------------------------------------------ noise
_NT = np.random.default_rng(1234).random(8192) * 2 - 1

def noise1(x, seed=0):
    x = np.asarray(x, dtype=np.float64) + seed * 131.713
    i = np.floor(x).astype(np.int64); f = x - i
    a = _NT[i & 8191]; b = _NT[(i + 1) & 8191]
    u = f * f * (3 - 2 * f)
    return a + (b - a) * u

def wig(t, freq=1.0, seed=0):
    return float(noise1(t * freq, seed))

def rnd(seed):
    return np.random.default_rng(seed)

# ------------------------------------------------------------------ textures
def _fft_noise(n, beta, rng):
    w = rng.standard_normal((n, n))
    F = np.fft.fft2(w)
    fx = np.fft.fftfreq(n)
    f = np.sqrt(fx[None, :] ** 2 + fx[:, None] ** 2); f[0, 0] = 1.0
    F = F / f ** beta
    out = np.real(np.fft.ifft2(F))
    out -= out.mean(); out /= out.std() + 1e-9
    return out

def _draw_fibres(n, rng, count, light):
    s = skia.Surface.MakeRaster(skia.ImageInfo.Make(n, n, skia.ColorType.kRGBA_8888_ColorType, skia.AlphaType.kPremul_AlphaType))
    c = s.getCanvas(); c.clear(skia.ColorSetARGB(255, 128, 128, 128))
    for i in range(count):
        x, y = rng.random(2) * n
        ang = rng.random() * math.pi * 2
        L = rng.uniform(8, 40)
        bend = rng.uniform(-0.6, 0.6)
        pts = []
        for k in range(8):
            u = k / 7
            a = ang + bend * u
            pts.append((x + math.cos(a) * L * u, y + math.sin(a) * L * u))
        p = skia.Path(); p.moveTo(*pts[0])
        for q in pts[1:]: p.lineTo(*q)
        v = 255 if (light and rng.random() < 0.6) else 0
        paint = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=rng.uniform(0.5, 1.3),
                           Color=skia.ColorSetARGB(int(rng.uniform(10, 30)), v, v, v))
        for dx in (-n, 0, n):
            for dy in (-n, 0, n):
                c.save(); c.translate(dx, dy); c.drawPath(p, paint); c.restore()
    return s.makeImageSnapshot().toarray()[..., 0].astype(np.float32) / 255.0 - 0.5

def _make_textures():
    fn = os.path.join(CACHE, 'tex_v3.npz')
    if os.path.exists(fn):
        d = np.load(fn); return {k: d[k] for k in d.files}
    n = 1024; rng = rnd(7)
    low = _fft_noise(n, 1.9, rng)       # cloudy mottling
    mid = _fft_noise(n, 1.1, rng)       # paper tooth
    fine = _fft_noise(n, 0.35, rng)     # speckle grain
    fib = _draw_fibres(n, rng, 2600, True)
    height = 0.55 * mid + 0.35 * fine
    shade = (np.roll(height, -1, 1) - np.roll(height, 1, 1)) * 0.5 + (np.roll(height, -1, 0) - np.roll(height, 1, 0)) * 0.5
    paper = 0.5 + 0.030 * low + 0.020 * mid + 0.022 * fine + 0.030 * shade + 0.55 * fib
    paper = np.clip(paper, 0, 1)
    # grain alpha for pencil / crayon (coarse-ish tooth)
    g1 = _fft_noise(n, 0.6, rng)
    g2 = _fft_noise(n, 1.2, rng)
    crayon = np.clip(0.62 + 0.30 * g1 + 0.18 * g2, 0, 1)
    pencil = np.clip(0.55 + 0.45 * _fft_noise(n, 0.25, rng), 0, 1)
    film = np.clip(0.5 + 0.5 * _fft_noise(n, 0.15, rng) * 0.35, 0, 1)
    out = dict(paper=paper.astype(np.float32), crayon=crayon.astype(np.float32), pencil=pencil.astype(np.float32),
               film=film.astype(np.float32), low=low.astype(np.float32))
    np.savez_compressed(fn, **out)
    return out

_TEX = None
_IMG = {}
SAMP = skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear)

def _gray_img(a):
    v = (np.clip(a, 0, 1) * 255).astype(np.uint8)
    arr = np.dstack([v, v, v, np.full_like(v, 255)])
    return skia.Image.fromarray(arr, colorType=skia.ColorType.kRGBA_8888_ColorType)

def _alpha_img(a):
    v = (np.clip(a, 0, 1) * 255).astype(np.uint8)
    arr = np.dstack([np.full_like(v, 255)] * 3 + [v])
    return skia.Image.fromarray(arr, colorType=skia.ColorType.kRGBA_8888_ColorType, alphaType=skia.AlphaType.kUnpremul_AlphaType)

def tex(name):
    global _TEX
    if name in _IMG: return _IMG[name]
    if _TEX is None: _TEX = _make_textures()
    if name == 'paper': img = _gray_img(_TEX['paper'])
    elif name == 'paper_soft': img = _gray_img(0.5 + (_TEX['paper'] - 0.5) * 0.55)
    elif name == 'crayon': img = _alpha_img(_TEX['crayon'])
    elif name == 'pencil': img = _alpha_img(_TEX['pencil'])
    elif name == 'film': img = _gray_img(_TEX['film'])
    elif name == 'wash':
        img = _alpha_img(np.clip(0.75 + 0.25 * _TEX['low'], 0, 1))
    else: raise KeyError(name)
    try:
        img = img.withDefaultMipmaps()
    except Exception:
        pass
    _IMG[name] = img
    return img

def tex_shader(name, off=(0, 0), scale=1.0, rot=0.0):
    m = skia.Matrix.Translate(off[0], off[1])
    if rot: m.preRotate(rot)
    m.preScale(scale, scale)
    return tex(name).makeShader(skia.TileMode.kRepeat, skia.TileMode.kRepeat, SAMP, m)

def paper_tex_paint(seed=0, scale=1.0, soft=False, alpha=1.0):
    r = rnd(seed)
    off = (float(r.uniform(0, 1024)), float(r.uniform(0, 1024)))
    ts = tex_shader('paper_soft' if soft else 'paper', off, scale, float(r.uniform(0, 360)))
    p = skia.Paint(AntiAlias=True, Shader=ts, BlendMode=skia.BlendMode.kOverlay)
    if alpha < 1: p.setAlphaf(alpha)
    return p

def fill_paper(c, path, color, seed=0, scale=1.0, soft=False, alpha=1.0):
    """Solid colour + overlay paper texture (two passes; avoids slow shader composition)."""
    base = skia.Paint(AntiAlias=True, Color=color)
    if alpha < 1: base.setAlphaf(alpha * skia.ColorGetA(color) / 255)
    c.drawPath(path, base)
    c.drawPath(path, paper_tex_paint(seed, scale, soft, alpha))

def grain_paint(color, kind='crayon', seed=0, scale=1.0, alpha=1.0):
    r = rnd(seed)
    ts = tex_shader(kind, (float(r.uniform(0, 1024)), float(r.uniform(0, 1024))), scale)
    cf = skia.ColorFilters.Blend(with_alpha(color, alpha * skia.ColorGetA(color) / 255), skia.BlendMode.kSrcIn)
    return skia.Paint(AntiAlias=True, Shader=ts, ColorFilter=cf)

# ------------------------------------------------------------------ geometry helpers
def catmull(pts, n=12, closed=False):
    """Catmull-Rom spline through control points -> dense polyline (numpy Nx2)."""
    P = np.asarray(pts, dtype=np.float64)
    if closed: P = np.vstack([P[-1], P, P[0], P[1]])
    else: P = np.vstack([P[0] * 2 - P[1], P, P[-1] * 2 - P[-2]])
    out = []
    t = np.linspace(0, 1, n, endpoint=False)[:, None]
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        seg = 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t ** 2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3)
        out.append(seg)
    if not closed: out.append(P[-2][None, :])
    return np.vstack(out)

def arc(cx, cy, rx, ry, a0, a1, n=40):
    a = np.linspace(math.radians(a0), math.radians(a1), n)
    return np.stack([cx + np.cos(a) * rx, cy + np.sin(a) * ry], 1)

def resample(P, spacing, closed):
    P = np.asarray(P, dtype=np.float64)
    if closed: Q = np.vstack([P, P[:1]])
    else: Q = P
    d = np.sqrt(((Q[1:] - Q[:-1]) ** 2).sum(1))
    s = np.concatenate([[0], np.cumsum(d)])
    L = s[-1]
    if L < 1e-6: return P, np.zeros(len(P))
    n = max(4, int(L / spacing))
    ss = np.linspace(0, L, n, endpoint=not closed)
    x = np.interp(ss, s, Q[:, 0]); y = np.interp(ss, s, Q[:, 1])
    return np.stack([x, y], 1), ss

def normals(P, closed):
    if closed: T = np.roll(P, -1, 0) - np.roll(P, 1, 0)
    else: T = np.gradient(P, axis=0)
    T = T / (np.linalg.norm(T, axis=1, keepdims=True) + 1e-9)
    return np.stack([-T[:, 1], T[:, 0]], 1)

def to_path(P, closed=True):
    pts = [skia.Point(float(x), float(y)) for x, y in P]
    return skia.Path.Polygon(pts, closed)

def path_points(path, spacing=3.0):
    """Sample every contour of a skia.Path -> list of Nx2 arrays (closed contours)."""
    out = []
    pm = skia.PathMeasure(path, True, 1.0)
    while True:
        L = pm.getLength()
        if L > 1e-3:
            n = max(8, int(L / spacing))
            pts = []
            for k in range(n):
                pos, _ = pm.getPosTan(L * k / n)
                pts.append((pos.x(), pos.y()))
            out.append(np.array(pts))
        if not pm.nextContour(): break
    return out

def roughen(P, closed=True, seed=0, amp=1.0, wl=38.0, hi=0.35, spacing=3.0):
    """Hand-cut edge: low-frequency wobble + slight high-frequency fibre."""
    Q, s = resample(P, spacing, closed)
    N = normals(Q, closed)
    d = amp * (1.5 * noise1(s / wl, seed) + hi * 1.4 * noise1(s / 5.0, seed + 17))
    return Q + N * d[:, None]

def rough_path(path, seed=0, amp=1.0, wl=38.0, hi=0.35):
    res = skia.Path()
    for P in path_points(path):
        res.addPath(to_path(roughen(P, True, seed, amp, wl, hi)))
        seed += 3
    res.setFillType(path.getFillType())
    return res

def torn_path(path, seed=0, amp=2.4):
    """Torn paper: jagged, fibrous edge."""
    res = skia.Path()
    for P in path_points(path, 2.0):
        Q, s = resample(P, 2.0, True)
        N = normals(Q, True)
        d = amp * (1.2 * noise1(s / 22, seed) + 0.9 * noise1(s / 6.0, seed + 5) + 0.6 * noise1(s / 2.1, seed + 9))
        res.addPath(to_path(Q + N * d[:, None]))
        seed += 3
    res.setFillType(path.getFillType())
    return res

# ---- primitive shapes (plain skia paths, before roughening)
def p_circle(x, y, r):
    p = skia.Path(); p.addCircle(x, y, r); return p

def p_ellipse(x, y, rx, ry):
    p = skia.Path(); p.addOval(skia.Rect.MakeXYWH(x - rx, y - ry, 2 * rx, 2 * ry)); return p

def p_rect(x, y, w, h, r=0):
    p = skia.Path()
    if r: p.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r))
    else: p.addRect(skia.Rect.MakeXYWH(x, y, w, h))
    return p

def p_poly(pts):
    return to_path(np.asarray(pts, dtype=float), True)

def p_blob(pts, n=10):
    return to_path(catmull(pts, n, closed=True), True)

def p_star(x, y, r1, r2, k=5, rot=-90):
    pts = []
    for i in range(k * 2):
        a = math.radians(rot + i * 180 / k)
        r = r1 if i % 2 == 0 else r2
        pts.append((x + math.cos(a) * r, y + math.sin(a) * r))
    return p_poly(pts)

def p_union(*ps):
    out = ps[0]
    for q in ps[1:]: out = skia.Op(out, q, skia.PathOp.kUnion_PathOp)
    return out

def p_diff(a, b):
    return skia.Op(a, b, skia.PathOp.kDifference_PathOp)

def p_inter(a, b):
    return skia.Op(a, b, skia.PathOp.kIntersect_PathOp)

def p_cloud(x, y, w, h, bumps=5, seed=0):
    r = rnd(seed)
    ps = [p_ellipse(x, y + h * 0.18, w * 0.5, h * 0.32)]
    for i in range(bumps):
        u = (i + 0.5) / bumps
        bx = x - w * 0.42 + u * w * 0.84
        br = h * (0.30 + 0.22 * math.sin(u * math.pi)) * r.uniform(0.85, 1.15)
        ps.append(p_circle(bx, y + h * 0.05 - br * 0.35, br))
    return p_union(*ps)

# ------------------------------------------------------------------ drawing: paper pieces
SHADOW = hexc('#140f2a')
LIGHT_DIR = (0.55, 1.0)

def _mscale(M):
    return math.sqrt(abs(M.getScaleX() * M.getScaleY() - M.getSkewX() * M.getSkewY())) or 1.0

_BLUR = {}
def _blur(sig):
    k = round(sig * 4) / 4
    if k not in _BLUR: _BLUR[k] = skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, max(0.3, k), False)
    return _BLUR[k]

def shadow(c, path, elev=1.0, alpha=0.30, color=None):
    if elev <= 0 or alpha <= 0: return
    M = c.getTotalMatrix(); s = _mscale(M)
    col = color if color is not None else SHADOW
    # soft cast shadow
    dx, dy = LIGHT_DIR[0] * elev * 5 * s, LIGHT_DIR[1] * elev * 5 * s
    c.save(); c.setMatrix(skia.Matrix.Concat(skia.Matrix.Translate(dx, dy), M))
    c.drawPath(path, skia.Paint(AntiAlias=True, Color=with_alpha(col, alpha), MaskFilter=_blur((2.0 + elev * 3.2) * s)))
    c.restore()
    # tight contact shadow (reads as paper thickness)
    c.save(); c.setMatrix(skia.Matrix.Concat(skia.Matrix.Translate(0.8 * s, 1.4 * s), M))
    c.drawPath(path, skia.Paint(AntiAlias=True, Color=with_alpha(col, min(0.5, alpha * 1.2)), MaskFilter=_blur(1.1 * s)))
    c.restore()

def piece(c, path, color, seed=0, elev=1.0, shadow_alpha=0.30, tex_scale=1.0, soft=False, edge=True):
    """Draw one cut-paper piece: shadow, textured fill, faint lit edge."""
    shadow(c, path, elev, shadow_alpha)
    fill_paper(c, path, color, seed, tex_scale, soft)
    if edge:
        M = c.getTotalMatrix(); s = _mscale(M)
        c.save(); c.clipPath(path, skia.ClipOp.kIntersect, True)
        c.setMatrix(skia.Matrix.Concat(skia.Matrix.Translate(1.1 * s, 1.6 * s), M))
        c.drawPath(path, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=2.2 * s / s,
                                    Color=skia.ColorSetARGB(38, 255, 250, 235)))
        c.restore()

def flat(c, path, color):
    c.drawPath(path, skia.Paint(AntiAlias=True, Color=color))

def crayon(c, path, color, seed=0, alpha=0.8, scale=1.0, blur=0.0):
    p = grain_paint(color, 'crayon', seed, scale, alpha)
    if blur: p.setMaskFilter(_blur(blur * _mscale(c.getTotalMatrix())))
    c.drawPath(path, p)

def glow(c, x, y, r, color, alpha=0.6, mode=skia.BlendMode.kScreen):
    sh = skia.GradientShader.MakeRadial(skia.Point(x, y), max(1.0, r),
                                        [with_alpha(color, alpha), with_alpha(color, alpha * 0.35), with_alpha(color, 0)],
                                        [0.0, 0.45, 1.0])
    c.drawCircle(x, y, r, skia.Paint(AntiAlias=True, Shader=sh, BlendMode=mode))

# ------------------------------------------------------------------ drawing: ink & pencil
INK = C['ink']
_STROKE_CACHE = {}

def ink_path(P, w=4.0, seed=0, boil=0, taper=(0.25, 0.25), jitter=0.9, closed=False, press=0.28, spacing=2.5):
    key = (id(P) if not isinstance(P, tuple) else P, w, seed, boil, taper, jitter, closed, press)
    Q, s = resample(P, spacing, closed)
    if len(Q) < 2: return skia.Path()
    bs = seed + boil * 97
    N = normals(Q, closed)
    Q = Q + N * (jitter * (noise1(s / 30.0, bs) + 0.35 * noise1(s / 7.0, bs + 3)))[:, None]
    L = s[-1] if len(s) else 1
    u = s / max(L, 1e-6)
    width = w * (1 + press * noise1(s / 45.0, bs + 11))
    if not closed:
        t0, t1 = taper
        env = np.ones_like(u)
        if t0 > 0: env = np.minimum(env, 0.18 + 0.82 * np.clip(u / t0, 0, 1) ** 0.6)
        if t1 > 0: env = np.minimum(env, 0.18 + 0.82 * np.clip((1 - u) / t1, 0, 1) ** 0.6)
        width = width * env
    N = normals(Q, closed)
    left = Q + N * (width / 2)[:, None]
    right = Q - N * (width / 2)[:, None]
    if closed:
        p = to_path(left, True); p.addPath(to_path(right[::-1], True))
        p.setFillType(skia.PathFillType.kEvenOdd)
        return p
    # round-ish caps
    poly = np.vstack([left, right[::-1]])
    return to_path(poly, True)

def ink(c, P, w=4.0, seed=0, boil=0, color=None, alpha=0.95, **kw):
    p = ink_path(np.asarray(P, dtype=float), w, seed, boil, **kw)
    c.drawPath(p, skia.Paint(AntiAlias=True, Color=with_alpha(color if color is not None else INK, alpha)))

def pencil(c, P, w=2.0, seed=0, boil=0, color=None, alpha=0.7, passes=2, **kw):
    col = color if color is not None else hexc('#3b3a4a')
    for k in range(passes):
        p = ink_path(np.asarray(P, dtype=float), w * (1 - 0.25 * k), seed + k * 7, boil, jitter=1.3 + k, **kw)
        c.drawPath(p, grain_paint(col, 'pencil', seed + k, 1.0, alpha * (1 - 0.35 * k)))

def ink_dots(c, pts, r=2.5, seed=0, boil=0, color=None, alpha=0.9):
    col = with_alpha(color if color is not None else INK, alpha)
    rr = rnd(seed + boil * 13)
    for (x, y) in pts:
        c.drawCircle(x + rr.uniform(-0.6, 0.6), y + rr.uniform(-0.6, 0.6), r * rr.uniform(0.8, 1.2), skia.Paint(AntiAlias=True, Color=col))

def stitches(c, P, seed=0, boil=0, dash=10, gap=8, w=2.0, color=None, alpha=0.75, closed=False):
    Q, s = resample(np.asarray(P, float), 2.0, closed)
    L = s[-1]; pos = 0.0
    while pos < L - dash:
        m = (s >= pos) & (s <= pos + dash)
        if m.sum() >= 2:
            ink(c, Q[m], w, seed + int(pos), boil, color, alpha, taper=(0.3, 0.3), jitter=0.4)
        pos += dash + gap

def hatch(c, clip, angle, spacing, seed=0, boil=0, w=1.4, color=None, alpha=0.35, bbox=None):
    """Pencil hatching clipped to a path."""
    c.save(); c.clipPath(clip, skia.ClipOp.kIntersect, True)
    b = bbox or clip.getBounds()
    cx, cy = b.centerX(), b.centerY()
    R = math.hypot(b.width(), b.height()) / 2 + 10
    a = math.radians(angle)
    d = np.array([math.cos(a), math.sin(a)]); nrm = np.array([-d[1], d[0]])
    k = -R
    i = 0
    while k < R:
        p0 = np.array([cx, cy]) + nrm * k - d * R
        p1 = np.array([cx, cy]) + nrm * k + d * R
        pencil(c, np.stack([p0, p1]), w, seed + i, boil, color, alpha, passes=1, taper=(0.1, 0.1))
        k += spacing; i += 1
    c.restore()

# ------------------------------------------------------------------ text
_TF = {}
def typeface(name):
    if name not in _TF:
        _TF[name] = skia.Typeface.MakeFromFile(os.path.join(FONTS, name))
    return _TF[name]

HAND = 'Kalam-Bold.ttf'
HAND2 = 'Caveat.ttf'
TITLE = 'CaveatBrush-Regular.ttf'

def text_width(s, size, font=HAND):
    f = skia.Font(typeface(font), size)
    return f.measureText(s)

def hand_text(c, s, x, y, size=48, color=None, font=HAND, seed=0, boil=0, align='center', reveal=1.0,
              jitter=1.0, rot=0.0, alpha=1.0, spacing=0.0):
    """Handwritten text: every glyph slightly rotated / shifted, boils, optional write-on reveal."""
    f = skia.Font(typeface(font), size); f.setSubpixel(True)
    col = with_alpha(color if color is not None else INK, alpha)
    widths = [f.measureText(ch) + spacing for ch in s]
    total = sum(widths)
    x0 = x - total / 2 if align == 'center' else (x - total if align == 'right' else x)
    r = rnd(seed * 31 + boil * 7 + 1)
    n = len(s); shown = reveal * n
    c.save(); c.translate(x, y); c.rotate(rot); c.translate(-x, -y)
    cx = x0
    for i, ch in enumerate(s):
        a = clamp(shown - i)
        if a > 0 and ch != ' ':
            c.save()
            c.translate(cx + widths[i] / 2 + r.uniform(-0.6, 0.6) * jitter, y + r.uniform(-1.2, 1.2) * jitter)
            c.rotate(r.uniform(-3.0, 3.0) * jitter)
            sc = 0.6 + 0.4 * ease_out_back(a) if a < 1 else 1.0
            c.scale(sc, sc)
            c.drawString(ch, -widths[i] / 2 + spacing / 2, 0, f, skia.Paint(AntiAlias=True, Color=with_alpha(col, skia.ColorGetA(col) / 255 * min(1, a * 1.5))))
            c.restore()
        else:
            r.uniform(); r.uniform(); r.uniform()
        cx += widths[i]
    c.restore()
    return total

# ------------------------------------------------------------------ collage extras
def tape(c, x, y, w, h, rot=0.0, seed=0, color=None, alpha=0.55):
    col = color if color is not None else hexc('#efe2b8')
    c.save(); c.translate(x, y); c.rotate(rot)
    p = _tape_path(round(w), round(h), seed)
    c.drawPath(p, skia.Paint(AntiAlias=True, Color=with_alpha(skia.ColorBLACK, 0.10), MaskFilter=_blur(2.0 * _mscale(c.getTotalMatrix()))))
    fill_paper(c, p, col, seed, 1.0, True, alpha)
    c.restore()

@functools.lru_cache(None)
def _tape_path(w, h, seed):
    r = rnd(seed)
    L = []
    n = 7
    for i in range(n + 1):  # left zigzag edge
        L.append((-w / 2 + r.uniform(-3, 3), -h / 2 + h * i / n))
    R = []
    for i in range(n + 1):
        R.append((w / 2 + r.uniform(-3, 3), h / 2 - h * i / n))
    return p_poly(L + R)

def label(c, s, x, y, size=40, rot=0.0, seed=0, boil=0, reveal=1.0, paper=None, ink_col=None, elev=0.8, scale=1.0, font=HAND):
    """Handwritten word on a torn paper strip, taped down."""
    if scale <= 0.001: return
    w = text_width(s, size, font) + size * 1.0
    h = size * 1.25
    c.save(); c.translate(x, y); c.rotate(rot); c.scale(scale, scale)
    p = _label_path(round(w), round(h), seed)
    piece(c, p, paper if paper is not None else C['cream'], seed, elev)
    hand_text(c, s, 0, size * 0.33, size, ink_col, font, seed, boil, reveal=reveal, jitter=0.7)
    tape(c, -w / 2 + 6, -h / 2 + 4, size * 0.9, size * 0.42, -35, seed + 3)
    c.restore()

@functools.lru_cache(None)
def _label_path(w, h, seed):
    return torn_path(p_rect(-w / 2, -h / 2, w, h), seed, 1.6)

# ------------------------------------------------------------------ camera
class Cam:
    def __init__(self, x=W / 2, y=H / 2, zoom=1.0, rot=0.0):
        self.x, self.y, self.zoom, self.rot = x, y, zoom, rot

    def apply(self, c, depth=1.0):
        z = 1 + (self.zoom - 1) * depth
        cx = W / 2 + (self.x - W / 2) * depth
        cy = H / 2 + (self.y - H / 2) * depth
        c.translate(W / 2, H / 2)
        if self.rot: c.rotate(self.rot * depth)
        c.scale(z, z)
        c.translate(-cx, -cy)

# ------------------------------------------------------------------ surfaces / post
def new_surface(w=W, h=H):
    return skia.Surface.MakeRaster(skia.ImageInfo.Make(w, h, skia.ColorType.kRGBA_8888_ColorType, skia.AlphaType.kPremul_AlphaType))

def background(c, color, seed=0, scale=1.0):
    fill_paper(c, p_rect(-4, -4, W + 8, H + 8), color, seed, scale)

_VIG = None
def post(c, frame, strength=1.0):
    global _VIG
    # vignette
    sh = skia.GradientShader.MakeRadial(skia.Point(W / 2, H / 2), W * 0.75,
                                        [skia.ColorSetARGB(0, 0, 0, 0), skia.ColorSetARGB(0, 0, 0, 0), skia.ColorSetARGB(int(72 * strength), 20, 14, 30)],
                                        [0.0, 0.6, 1.0])
    c.drawRect(skia.Rect.MakeWH(W, H), skia.Paint(Shader=sh, BlendMode=skia.BlendMode.kMultiply))
    # global paper tooth + film grain on twos
    r = rnd(frame // 2 + 999)
    g = tex_shader('film', (float(r.uniform(0, 1024)), float(r.uniform(0, 1024))), 1.0)
    p = skia.Paint(Shader=g, BlendMode=skia.BlendMode.kOverlay); p.setAlphaf(0.35 * strength)
    c.drawRect(skia.Rect.MakeWH(W, H), p)
    # exposure flicker (stop-motion lights)
    fl = float(noise1(frame / 2.0 * 0.9, 42)) * 0.018
    if fl > 0: c.drawRect(skia.Rect.MakeWH(W, H), skia.Paint(Color=skia.ColorSetARGB(int(fl * 255), 255, 244, 220), BlendMode=skia.BlendMode.kScreen))
    else: c.drawRect(skia.Rect.MakeWH(W, H), skia.Paint(Color=skia.ColorSetARGB(int(-fl * 255), 0, 0, 0)))

def boil_of(frame, rate=3):
    return (frame // rate) % 3
