"""Sound design + final mix.

Every effect is synthesised here (paper, pencil, taps, chimes, sea, birds...), placed on the same cue
times the animation uses, panned to where it happens on screen, and mixed under the narration and score.
"""
import os, sys, json, wave, subprocess, math
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve, resample_poly

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))
SR = 48000
RNG = np.random.default_rng(2024)

# ------------------------------------------------------------------ dsp helpers
def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], 'bandpass', fs=SR, output='sos'), x)

def lp(x, f, order=2):
    return sosfilt(butter(order, f, 'lowpass', fs=SR, output='sos'), x)

def hp(x, f, order=2):
    return sosfilt(butter(order, f, 'highpass', fs=SR, output='sos'), x)

def noise(d):
    return RNG.standard_normal(int(d * SR))

def tvec(d):
    return np.arange(int(d * SR)) / SR

def env_ad(d, a, dec_tau):
    t = tvec(d)
    e = np.where(t < a, t / max(a, 1e-4), np.exp(-(t - a) / dec_tau))
    return e

def env_bell(d, peak=0.5, power=2.0):
    t = tvec(d) / d
    return np.clip(np.sin(np.pi * np.clip(t, 0, 1)) ** power, 0, 1)

def norm(x, peak=1.0):
    m = np.max(np.abs(x)) + 1e-9
    return x / m * peak

def crackle(d, rate, decay=0.002, lo=1500, hi=7000):
    n = int(d * SR); out = np.zeros(n)
    k = RNG.poisson(rate * d)
    pos = RNG.integers(0, max(1, n - 200), k)
    L = int(decay * SR * 6)
    kern = np.exp(-np.arange(L) / (decay * SR)) * RNG.standard_normal(L)
    for p in pos:
        a = RNG.uniform(0.2, 1.0)
        e = min(n, p + L); out[p:e] += a * kern[:e - p]
    return bp(out, lo, hi)

# ------------------------------------------------------------------ effects
def paper_rustle(d=0.5, bright=1.0):
    x = bp(noise(d), 1200, 7000) * 0.35 + crackle(d, 90, 0.0015) * 1.2
    return norm(x * env_bell(d, power=1.2), 0.8 * bright)

def paper_slide(d=0.7):
    x = bp(noise(d), 250, 3500) * 0.8 + crackle(d, 40, 0.002, 800, 5000) * 0.6
    return norm(x * env_bell(d, power=0.8), 0.7)

def paper_tear(d=0.75):
    n = int(d * SR)
    x = np.zeros(n)
    t = 0.0
    while t < d - 0.02:
        seg = crackle(0.03, 900, 0.0008, 1500, 9000)
        i = int(t * SR); x[i:i + len(seg)] += seg[:max(0, min(len(seg), n - i))] * RNG.uniform(0.6, 1.0)
        t += RNG.uniform(0.008, 0.03)
    body = bp(noise(d), 700, 5000) * 0.5
    e = np.clip(tvec(d) / 0.05, 0, 1) * np.exp(-tvec(d) / (d * 0.8))
    return norm((x + body) * e, 0.9)

def pencil_scratch(d=2.0, rate=7.0):
    t = tvec(d)
    strokes = np.abs(np.sin(np.pi * rate * t + 0.8 * np.sin(2 * np.pi * 1.3 * t))) ** 0.6
    grain = hp(noise(d), 2500) * 0.5 + crackle(d, 400, 0.0006, 2500, 11000)
    x = bp(grain, 2000, 10000) * strokes
    fade = np.clip(t / 0.05, 0, 1) * np.clip((d - t) / 0.08, 0, 1)
    return norm(x * fade, 0.6)

def thunk(f=95, d=0.35):
    t = tvec(d)
    body = np.sin(2 * np.pi * f * t * (1 - 0.3 * t)) * np.exp(-t / 0.06)
    wood = bp(noise(d), 300, 2200) * np.exp(-t / 0.02)
    click = hp(noise(d), 3000) * np.exp(-t / 0.004)
    return norm(body * 0.9 + wood * 0.6 + click * 0.25, 0.9)

def pop(f0=420, f1=950, d=0.12):
    t = tvec(d)
    f = f0 + (f1 - f0) * np.clip(t / 0.035, 0, 1)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return norm(np.sin(ph) * np.exp(-t / 0.03) + 0.2 * hp(noise(d), 2000) * np.exp(-t / 0.004), 0.8)

def chime(f=1320, d=1.6, bright=1.0):
    t = tvec(d)
    x = np.zeros_like(t)
    for ratio, amp, tau in [(1, 1.0, 0.9), (2.76, 0.45 * bright, 0.35), (5.40, 0.22 * bright, 0.18), (8.93, 0.10 * bright, 0.08)]:
        x += amp * np.sin(2 * np.pi * f * ratio * t) * np.exp(-t / tau)
    x *= np.clip(t / 0.002, 0, 1)
    return norm(x, 0.7)

def shimmer(base=1046.5, n=6, gap=0.07, d=2.0):
    scale = [1, 1.25, 1.5, 2.0, 2.5, 3.0, 4.0]
    out = np.zeros(int(d * SR) + int(n * gap * SR) + 10)
    for k in range(n):
        c = chime(base * scale[k % len(scale)], d, 0.6) * (0.9 - 0.08 * k)
        i = int(k * gap * SR); out[i:i + len(c)] += c
    return norm(out, 0.6)

def whoosh(d=0.8, lo=300, hi=2600):
    n = int(d * SR); x = noise(d)
    out = np.zeros(n); blk = 1024
    for i in range(0, n, blk):
        u = i / n
        fc = lo + (hi - lo) * math.sin(math.pi * u)
        seg = x[max(0, i - 2048):i + blk]
        y = bp(seg, fc * 0.6, min(fc * 1.6, SR / 2 - 100))
        out[i:i + blk] = y[-min(blk, n - i):]
    return norm(out * env_bell(d, power=1.5), 0.7)

def clunk(d=0.5):
    t = tvec(d)
    x = (np.sin(2 * np.pi * 150 * t) * 0.8 + np.sin(2 * np.pi * 520 * t) * 0.35 + np.sin(2 * np.pi * 1230 * t) * 0.15) * np.exp(-t / 0.07)
    x += hp(noise(d), 2500) * np.exp(-t / 0.006) * 0.5
    return norm(x, 0.9)

def power_hum(d=1.2):
    t = tvec(d)
    f = 60 + 60 * np.clip(t / 0.5, 0, 1)
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(ph) + 0.4 * np.sin(2 * ph) + 0.2 * np.sin(3 * ph)
    return norm(lp(x, 900) * np.clip(t / 0.3, 0, 1) * np.exp(-t / 0.6), 0.5)

def drawer(d=0.45):
    t = tvec(d)
    x = lp(noise(d), 1200) * (0.6 + 0.4 * np.sin(2 * np.pi * 23 * t)) * env_bell(d, power=0.7)
    knock = thunk(140, 0.2) * 0.5
    out = np.concatenate([x, np.zeros(int(0.2 * SR))])
    i = int((d - 0.05) * SR); out[i:i + len(knock)] += knock
    return norm(out, 0.7)

def click(f=2400):
    d = 0.06; t = tvec(d)
    return norm(np.sin(2 * np.pi * f * t) * np.exp(-t / 0.006) + hp(noise(d), 4000) * np.exp(-t / 0.002) * 0.5, 0.7)

def splash(d=0.7):
    t = tvec(d)
    x = bp(noise(d), 500, 6000) * np.exp(-t / 0.12) * np.clip(t / 0.01, 0, 1)
    for k in range(8):
        i = int(RNG.uniform(0.02, 0.4) * SR); f = RNG.uniform(1200, 2600); dd = 0.05
        tt = tvec(dd); drop = np.sin(2 * np.pi * (f + 3000 * tt) * tt) * np.exp(-tt / 0.012)
        x[i:i + len(drop)] += drop * 0.35
    return norm(x, 0.7)

def bloop(d=0.18):
    t = tvec(d)
    f = 300 + 900 * t / d
    return norm(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.05), 0.6)

def waves(d):
    n = int(d * SR)
    x = lp(noise(d), 450) * 0.7 + bp(noise(d), 3500, 7000) * 0.12
    t = tvec(d)
    sw = 0.55 + 0.45 * np.sin(2 * np.pi * 0.23 * t) ** 2 + 0.2 * np.sin(2 * np.pi * 0.11 * t + 1)
    return norm(x * sw, 0.6)

def crickets(d):
    t = tvec(d); out = np.zeros_like(t)
    for (fc, rate, period, ph) in [(4300, 32, 0.9, 0.0), (4700, 28, 1.3, 0.4), (3900, 36, 1.7, 0.9)]:
        chirp_on = ((t + ph) % period) < 0.12
        pulses = (np.sin(2 * np.pi * rate * t) > 0.3).astype(float)
        out += np.sin(2 * np.pi * fc * t) * pulses * chirp_on * 0.3
    return norm(lp(out, 7000) * np.clip(t / 0.5, 0, 1), 0.4)

def room_tone(d):
    return norm(lp(noise(d), 400) * 0.5 + lp(noise(d), 120), 0.25)

def school_bell(n=4, gap=0.19):
    out = np.zeros(int((n * gap + 2.0) * SR))
    for k in range(n):
        c = chime(987.8, 1.8, 0.9) * (1 - 0.12 * k)
        i = int(k * gap * SR); out[i:i + len(c)] += c
    return norm(out, 0.6)

def birds(d):
    out = np.zeros(int(d * SR))
    t_ = 0.1
    while t_ < d - 0.5:
        for k in range(RNG.integers(2, 5)):
            dd = RNG.uniform(0.05, 0.12)
            tt = tvec(dd)
            f0 = RNG.uniform(2800, 4200); f1 = f0 * RNG.uniform(0.6, 1.4)
            f = f0 + (f1 - f0) * tt / dd + 180 * np.sin(2 * np.pi * 40 * tt)
            ch = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * tt / dd) ** 2
            i = int((t_ + k * 0.14) * SR)
            if i + len(ch) < len(out): out[i:i + len(ch)] += ch * RNG.uniform(0.5, 1.0)
        t_ += RNG.uniform(0.7, 1.4)
    return norm(out, 0.4)

def tape_rip(d=0.22):
    t = tvec(d)
    x = crackle(d, 1800, 0.0005, 1500, 9000) + bp(noise(d), 2000, 7000) * 0.4
    return norm(x * np.clip(t / 0.01, 0, 1) * np.exp(-t / 0.09), 0.7)

def snore(d=1.1):
    t = tvec(d)
    x = bp(noise(d), 120, 700) * (1 + 0.6 * np.sin(2 * np.pi * 28 * t))
    return norm(x * env_bell(d, power=1.4), 0.5)

def alarm_ding(n=6, gap=0.13):
    out = np.zeros(int((n * gap + 1.2) * SR))
    for k in range(n):
        c = chime(1760 if k % 2 == 0 else 1568, 0.9, 0.5) * 0.8
        i = int(k * gap * SR); out[i:i + len(c)] += c
    return norm(out, 0.5)

def boing(d=0.5, f=330):
    t = tvec(d)
    fr = f * (1 + 0.25 * np.exp(-t / 0.08) * np.sin(2 * np.pi * 18 * t))
    return norm(np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t / 0.15), 0.6)

def slack(d=0.7):
    # soft descending plucked string (Karplus-Strong with pitch glide)
    n = int(d * SR); out = np.zeros(n)
    f0 = 330.0
    buf = RNG.uniform(-1, 1, int(SR / f0))
    pos = 0.0
    for i in range(n):
        f = f0 * (1 - 0.45 * min(1.0, i / (0.5 * SR)))
        L = SR / f
        j = int(pos) % len(buf)
        out[i] = buf[j]
        buf[j] = 0.5 * (buf[j] + buf[(j + 1) % len(buf)]) * 0.996
        pos += len(buf) / L
    return norm(lp(out, 3000) * np.exp(-tvec(d) / 0.3), 0.6)

def poof(d=0.5):
    t = tvec(d)
    return norm(lp(noise(d), 1500) * np.clip(t / 0.01, 0, 1) * np.exp(-t / 0.12), 0.6)

def reverb_ir(d=1.4, decay=0.35):
    t = tvec(d)
    L = RNG.standard_normal(len(t)) * np.exp(-t / decay)
    R = RNG.standard_normal(len(t)) * np.exp(-t / decay)
    L = lp(L, 6000); R = lp(R, 6000)
    return L / np.sqrt(np.sum(L ** 2)), R / np.sqrt(np.sum(R ** 2))

# ------------------------------------------------------------------ timeline of cues
def cue_sheet():
    import scenes as S, scenes2 as S2, scenes3 as S3, film as F
    ph = S.ph
    cues = []   # (time, sound, gain_db, pan -1..1)
    add = lambda t, snd, g=0.0, pan=0.0: cues.append((t, snd, g, pan))
    # A: night exterior
    add(0.45, chime(2093, 1.6, 0.4), -26, 0.1)                   # shooting star twinkle
    for i, tl in enumerate(S.LIGHTS_OFF):
        add(tl, click(1800 + 150 * i), -30, -0.7 if i < 3 else 0.7)   # lights clicking off
    add(3.25, whoosh(0.9, 400, 2400), -24, 0.2)                    # push through the window
    # B: bedroom, film, clapper, star
    t_b = ph(1, 2) + 0.12
    for k in range(3): add(t_b + k * 0.16, pop(500 + 120 * k, 900 + 150 * k), -24, 0.0)
    add(t_b + 0.45, paper_rustle(0.5), -22, 0.1)
    add(t_b + 0.9, paper_slide(0.4), -26, -0.3)
    add(t_b + 0.9 + 0.55, thunk(160, 0.25), -18, -0.35)            # clapper clap
    add(t_b + 0.9 + 0.55, click(3200), -20, -0.35)
    add(ph(1, 3) + 0.02, shimmer(1318.5, 5, 0.06), -22, 0.15)      # starring you
    add(6.85, paper_slide(0.55), -25, 0.1)
    add(7.0, whoosh(0.9, 300, 2000), -24, 0.1)
    # C: sleep chart
    add(7.95, pencil_scratch(2.15, 6.5), -21, -0.2)
    add(8.8, pencil_scratch(0.5, 9), -25, -0.3)
    add(9.0, pencil_scratch(0.6, 11), -27, -0.3)
    for k in range(4):
        tk = 10.35 + k * 0.36
        add(tk, hp(thunk(120 + 8 * k), 110), -19, -0.6 + 0.4 * k)
    for k in range(4):
        add(12.45 + k * 0.26, pop(450 + 90 * k, 1000 + 120 * k), -21, -0.6 + 0.4 * k)
        add(12.47 + k * 0.26, chime(1568 * (1.122 ** k), 1.2, 0.5), -28, -0.6 + 0.4 * k)
    add(F.T_TEAR[0] - 0.02, paper_tear(1.0), -14, 0.0)
    # D: brain studio
    add(15.05, whoosh(1.2, 250, 1800), -24, 0.0)
    add(S.ph(3, 0) + 0.35, paper_rustle(0.3), -24, -0.4)              # brainstem label
    add(S.T_LEVER - 0.02, hp(thunk(260, 0.18), 150), -20, 0.2)     # wooden lever clack
    add(S.T_LEVER - 0.01, click(2600), -22, 0.2)
    add(S.T_LEVER + 0.02, paper_rustle(0.18), -26, 0.2)
    add(S.T_LEVER + 0.05, power_hum(1.2), -27, 0.1)
    add(S.T_LEVER + 0.12, shimmer(880, 6, 0.08), -22, 0.0)
    add(S.T_LEVER + 0.35, whoosh(1.4, 400, 3500), -24, 0.0)
    add(ph(4, 0) + 0.15, paper_rustle(0.3), -24, 0.0)                  # hippocampus label
    add(S.T_TODAY, drawer(), -18, 0.3)
    add(S.T_LONG, drawer(), -18, 0.3)
    add(S.T_LONG + 0.1, poof(0.5), -24, 0.3)
    for k in range(6):
        t0 = (S.T_TODAY + 0.25 + k * 0.3) if k < 3 else (S.T_LONG + 0.25 + (k - 3) * 0.28)
        add(t0, paper_rustle(0.45, 0.8), -22, 0.2 - 0.1 * k)
        add(t0 + 0.6, click(2200), -26, -0.4 + 0.12 * k)
    add(24.2, whoosh(0.9, 300, 2000), -26, 0.3)
    add(ph(5, 0) + 0.2, paper_rustle(0.3), -24, 0.0)
    add(S.T_GLOW - 0.05, shimmer(1046.5, 7, 0.07, 2.4), -19, 0.1)
    add(S.T_GLOW, whoosh(1.2, 200, 1400), -24, 0.0)
    add(27.0, whoosh(1.0, 300, 2000), -26, 0.4)
    for k in range(3):
        add(S.T_PFC + 0.65 * (k + 1) - 0.05, pencil_scratch(0.18, 20), -22, 0.0)
    add(ph(5, 2) + 0.05, paper_rustle(0.3), -24, 0.0)
    add(S.T_DOZE + 0.3, snore(1.0), -24, 0.1)
    add(S.T_DOZE + 1.35, snore(0.9), -27, 0.1)
    # curtains + dream
    add(S2.T_CURTAIN_CLOSE - 0.05, whoosh(0.6, 200, 1500), -20, 0.0)
    add(S2.T_CURTAIN_CLOSE + 0.4, thunk(70, 0.3), -26, 0.0)
    add(S2.T_CURTAIN_OPEN, whoosh(0.8, 200, 1600), -20, 0.0)
    add(33.6, school_bell(4, 0.2), -26, 0.0)
    for (t0, x0, col) in S2.DREAM_FISH:
        pan = (x0 + 165 - 960) / 960
        if t0 < S2.T_F:
            add(t0, bloop(), -26, pan)
            add(t0 + 1.05, splash(), -22, pan)
    add(S2.T_F, whoosh(1.2, 300, 2200), -22, 0.0)
    add(S2.T_LIMP, slack(0.8), -14, 0.0)
    add(S2.T_LIMP + 0.05, paper_rustle(0.5, 0.6), -22, 0.1)     # twine settling onto the quilt
    # why we dream
    add(S3.T_G - 0.05, paper_slide(0.8), -16, 0.4)
    add(S3.T_G + 0.35, pop(300, 600, 0.15), -20, 0.0)
    add(S3.T_G + 0.9, pop(500, 900), -22, -0.5)
    add(S3.T_G + 1.5, pop(520, 950), -22, 0.5)
    add(ph(8, 1) - 0.5, whoosh(0.9, 300, 2000), -26, 0.4)
    for i in range(6):
        add(ph(8, 1) + 0.15 + i * 0.24, paper_rustle(0.35, 0.7), -24, -0.2 + 0.1 * i)
    add(ph(8, 2) - 0.45, whoosh(0.8, 300, 2000), -26, 0.4)
    for k in range(3):
        add(ph(8, 2) + 0.35 + k * 0.25, tape_rip(), -21, 0.1)
    add(ph(8, 2) + 1.0, shimmer(1318.5, 6, 0.07, 2.2), -21, 0.1)
    add(F.T_IRIS[0], whoosh(0.9, 400, 2600), -22, -0.4)
    # morning
    add(S3.T_MORNING + 0.1, alarm_ding(7, 0.12), -26, 0.75)
    add(S3.T_MORNING + 0.2, birds(5.5), -30, -0.6)
    for i in range(5):
        add(S3.T_GONE + 0.1 + i * 0.3, paper_rustle(0.6, 0.8), -22, -0.2 - 0.1 * i)
    pop_t = S3.T_BREAKFAST - 0.4
    add(pop_t - 0.05, poof(0.6), -20, 0.1)
    add(S3.T_BREAKFAST, boing(0.6, 300), -21, 0.75)
    add(S3.T_BREAKFAST + 0.02, click(1800), -20, 0.75)
    add(S3.T_BREAKFAST + 1.6, click(2600), -28, 0.0)        # fish lands in the hand
    add(S3.T_TITLE, paper_slide(0.6), -22, 0.0)
    add(S3.T_TITLE + 0.35, pencil_scratch(0.5, 8), -24, 0.0)
    add(S3.T_TITLE + 0.85, pencil_scratch(0.45, 11), -27, 0.0)
    add(S3.T_TITLE + 1.35, chime(2093, 2.0, 0.5), -24, 0.3)
    # beds of ambience: (start, end, sound_fn, gain, pan)
    beds = [(0.0, 4.4, crickets, -34, 0.0), (0.0, 4.4, lambda d: lp(noise(d), 500) * 0.4, -40, 0.0),
            (4.1, 7.9, room_tone, -40, 0.0), (32.4, 37.9, waves, -32, 0.0), (37.2, 41.9, room_tone, -40, 0.0),
            (49.2, 59.0, room_tone, -42, 0.0), (14.7, 31.9, lambda d: lp(noise(d), 180) * 0.6, -40, 0.0)]
    return cues, beds

def place(buf, t, snd, gain_db, pan):
    g = 10 ** (gain_db / 20)
    i = int(t * SR)
    if i >= buf.shape[1]: return
    n = min(len(snd), buf.shape[1] - i)
    lg = math.cos((pan + 1) * math.pi / 4); rg = math.sin((pan + 1) * math.pi / 4)
    buf[0, i:i + n] += snd[:n] * g * lg * 1.414
    buf[1, i:i + n] += snd[:n] * g * rg * 1.414

def read_audio(path, ch=2):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-f', 'f32le', '-ac', str(ch), '-ar', str(SR), '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, ch).T.astype(np.float64)

def compress(x, thr_db=-20, ratio=2.5, att=0.005, rel=0.12):
    """simple feed-forward RMS compressor on a mono/stereo signal"""
    mono = np.sqrt(np.mean(np.atleast_2d(x) ** 2, axis=0))
    a_a = math.exp(-1 / (att * SR)); a_r = math.exp(-1 / (rel * SR))
    lvl = mono
    env = np.zeros_like(lvl); e = 0.0
    for i in range(0, len(lvl), 64):
        v = lvl[i:i + 64].max()
        e = a_a * e + (1 - a_a) * v if v > e else a_r ** 64 * e + (1 - a_r ** 64) * v
        env[i:i + 64] = e
    db = 20 * np.log10(env + 1e-9)
    gr = np.where(db > thr_db, (thr_db - db) * (1 - 1 / ratio), 0.0)
    return x * 10 ** (gr / 20)

def main():
    import film as F, pyloudnorm as pyln
    DUR = F.DURATION
    N = int(DUR * SR)
    # --- narration (mono -> centred)
    vo = read_audio(os.path.join(ROOT, 'build', 'vo', 'narration.wav'), 1)[0]
    vo = np.concatenate([vo, np.zeros(max(0, N - len(vo)))])[:N]
    vo = compress(vo, -24, 2.2)
    # gentle presence + warmth
    vo = vo + 0.2 * bp(vo, 2800, 5000) + 0.08 * lp(vo, 250)
    # --- music
    mus = read_audio(os.path.join(ROOT, 'assets', 'audio', 'music_lyria.mp3'), 2)
    mus = np.concatenate([mus, np.zeros((2, max(0, N - mus.shape[1])))], 1)[:, :N]
    fade = np.ones(N); fl = int(0.8 * SR); fade[-fl:] = np.linspace(1, 0, fl) ** 1.5
    mus *= fade
    mus = compress(mus, -20, 2.0, 0.02, 0.4)
    # carve a little room for the voice in the music (static mid dip)
    mus = mus - 0.25 * bp(mus, 1500, 4000)
    # sidechain duck from narration envelope
    venv = np.abs(vo)
    k = int(0.02 * SR)
    venv = np.convolve(venv, np.ones(k) / k, 'same')
    act = (venv > 0.012).astype(float)
    # smooth attack 80 ms / release 450 ms
    sm = np.zeros_like(act); e = 0.0
    aa = math.exp(-1 / (0.08 * SR / 64)); rr = math.exp(-1 / (0.45 * SR / 64))
    for i in range(0, N, 64):
        v = act[i:i + 64].max()
        e = aa * e + (1 - aa) * v if v > e else rr * e + (1 - rr) * v
        sm[i:i + 64] = e
    duck_db = -7.5 * sm
    mus *= 10 ** (duck_db / 20)
    self_duck = 10 ** (-3.5 * sm / 20)
    # --- sfx
    sfx = np.zeros((2, N))
    cues, beds = cue_sheet()
    for (t, snd, g, pan) in cues:
        place(sfx, t, snd, g, pan)
    for (a, b_, fn, g, pan) in beds:
        d = b_ - a
        x = fn(d)
        x = x * np.clip(tvec(d) / 0.6, 0, 1)[:len(x)] * np.clip((d - tvec(d)) / 0.6, 0, 1)[:len(x)]
        place(sfx, a, norm(x, 1.0), g, pan)
    # light room reverb on sfx for a shared space
    irL, irR = reverb_ir(1.2, 0.28)
    wetL = fftconvolve(sfx[0], irL)[:N]; wetR = fftconvolve(sfx[1], irR)[:N]
    sfx = (sfx * 0.85 + np.stack([wetL, wetR]) * 0.18) * self_duck
    # --- levels (set against LUFS of each stem)
    meter = pyln.Meter(SR)
    def lufs(x):
        return meter.integrated_loudness(np.atleast_2d(x).T)
    vo_st = np.stack([vo, vo])
    vo_l = lufs(vo_st); mus_l = lufs(mus); sfx_l = lufs(sfx)
    print(f'stems LUFS  vo {vo_l:.1f}  music {mus_l:.1f}  sfx {sfx_l:.1f}')
    vo_st *= 10 ** ((-17.0 - vo_l) / 20)
    mus *= 10 ** ((-27.5 - mus_l) / 20)
    sfx *= 10 ** ((-30.0 - sfx_l) / 20)
    mix = vo_st + mus + sfx
    # master: loudness to -16 LUFS, true-peak safe
    L = lufs(mix)
    mix *= 10 ** ((-16.0 - L) / 20)
    pk = np.max(np.abs(mix))
    if pk > 0.89:
        # soft limit the rare peaks
        mix = np.tanh(mix / 0.89 * 1.0) * 0.89 if pk > 1.2 else mix * (0.89 / pk)
    print(f'mix LUFS {lufs(mix):.1f}  peak {20 * np.log10(np.max(np.abs(mix))):.2f} dBFS')
    out = os.path.join(ROOT, 'build', 'mix.wav')
    w = wave.open(out, 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(mix.T, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
    for name, x in [('stem_vo', vo_st), ('stem_music', mus), ('stem_sfx', sfx)]:
        w = wave.open(os.path.join(ROOT, 'build', name + '.wav'), 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x.T, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
    print('wrote', out)

if __name__ == '__main__':
    main()
