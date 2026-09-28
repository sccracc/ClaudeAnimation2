"""Master timeline: which scene draws each frame (and the handmade transitions between them)."""
import math
from engine import *
import scenes as S
import scenes2 as S2
import scenes3 as S3

DURATION = S3.FILM_END
T_TEAR = (13.95, 14.95)
T_SLIDE = (S3.T_G - 0.15, S3.T_G + 0.8)
T_IRIS = (49.2, 49.95)

def draw_frame(c, t, f):
    if t < S.A_ENTER:
        S.scene_A(c, t, f)
    elif t < S.C_T0:
        S.scene_B(c, t, f)
    elif t < T_TEAR[0]:
        S.scene_C(c, t, f)
    elif t < T_TEAR[1]:
        S.tear_transition(c, t, f, S.scene_C, S.scene_D, *T_TEAR)
    elif t < S2.T_CURTAIN_OPEN - 0.03:
        S.scene_D(c, t, f)
    elif t < S2.T_F:
        S2.scene_E(c, t, f)
    elif t < T_SLIDE[0]:
        S2.scene_F(c, t, f)
    elif t < T_SLIDE[1]:
        S3.slide_in(c, t, f, S2.scene_F, S3.scene_G, *T_SLIDE)
    elif t < T_IRIS[0]:
        S3.scene_G(c, t, f)
    elif t < T_IRIS[1]:
        S3.iris_transition(c, t, f, S3.scene_G, S3.scene_H, *T_IRIS, center=(1050, 520))
    else:
        S3.scene_H(c, t, f)
    if S2.T_CURTAIN_CLOSE - 0.3 < t < S2.T_CURTAIN_OPEN + 1.2:
        S2.curtains_big(c, t, f)
    post(c, f)
    if t < 0.6:   # open from black
        c.drawRect(skia.Rect.MakeWH(W, H), skia.Paint(Color=with_alpha(hexc('#120d1c'), 1 - smooth(t / 0.6))))
