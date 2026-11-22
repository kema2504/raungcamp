"""Animated RGBA overlay for the 30 s info video. Writes raw rgba frames (2160x3840, 30 fps) to stdout.
Usage: info_overlay.py [--still t1,t2,... outdir]"""
import json, math, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

S = '/tmp/claude-0/-home-user-raungcamp/b0706bff-2b10-5382-a9f0-3081491f33ef/scratchpad'
IMG = '/tmp/claude-0/-home-user-raungcamp/b0706bff-2b10-5382-a9f0-3081491f33ef/images'
W, H, FPS, DUR = 2160, 3840, 30, 30.0
SAFE_L, SAFE_R, SAFE_T, SAFE_B = 120, 1860, 440, 3000
CX = (SAFE_L + SAFE_R) // 2
ORANGE = (252, 76, 2); WHITE = (255, 255, 255); GREY = (200, 200, 200)
BAR = f'{S}/fonts/BarlowCondensed-ExtraBold.ttf'; DMS = f'{S}/fonts/DMSans%5Bopsz,wght%5D.ttf'
_fc = {}
def font(path, size, wght=None):
    k = (path, size, wght)
    if k not in _fc:
        f = ImageFont.truetype(path, size)
        if wght: f.set_variation_by_axes([14, wght])
        _fc[k] = f
    return _fc[k]
from fontTools.ttLib import TTFont
BAR_CMAP = set(TTFont(BAR).getBestCmap())
def bar(s): return font(BAR, s)
def gf(f, c):
    if f.path == BAR and ord(c) not in BAR_CMAP:
        return font(DMS, int(f.size * 0.82), 700)
    return f
def dms(s, w=500): return font(DMS, s, w)

# ---------------- text cards (cached, with soft shadow) ----------------
_cards = {}
def card(lines, align='c', key=None):
    """lines: [(text, font, color, tracking, gap_after)] -> RGBA image (padded)."""
    k = key or repr([(l[0], id(l[1]), l[2], l[3], l[4]) for l in lines]) + align
    if k in _cards: return _cards[k]
    pad = 70
    meas = []
    for txt, f, col, tr, gap in lines:
        w = sum(gf(f, c).getlength(c) for c in txt) + tr * max(0, len(txt) - 1)
        a, d = f.getmetrics(); meas.append((w, a + d))
    tw = int(max(m[0] for m in meas)) + 2 * pad; th = int(sum(m[1] + l[4] for m, l in zip(meas, lines))) + 2 * pad
    mask_all = Image.new('L', (tw, th), 0); color = Image.new('RGBA', (tw, th), (0, 0, 0, 0))
    y = pad
    for (txt, f, col, tr, gap), (w, h) in zip(lines, meas):
        x = {'c': (tw - w) / 2, 'l': pad, 'r': tw - pad - w}[align]
        m = Image.new('L', (tw, th), 0); d = ImageDraw.Draw(m)
        for c in txt:
            g = gf(f, c); oy = (f.getmetrics()[0] - g.getmetrics()[0]) if g is not f else 0
            d.text((x, y + oy), c, font=g, fill=255); x += g.getlength(c) + tr
        color.paste(col + (255,), mask=m); mask_all = Image.fromarray(np.maximum(np.asarray(mask_all), np.asarray(m)))
        y += h + gap
    sh = mask_all.filter(ImageFilter.GaussianBlur(20)).point(lambda v: int(v * 0.6))
    out = Image.new('RGBA', (tw, th), (0, 0, 0, 0)); sh2 = Image.new('L', (tw, th), 0); sh2.paste(sh, (0, 7))
    out.paste((0, 0, 0, 255), mask=sh2); out.alpha_composite(color)
    _cards[k] = (out, pad); return _cards[k]

def put(canvas, cardinfo, x, y, alpha=1.0, anchor='c', scale=1.0):
    """anchor: 'c' centre at (x,y); 'l' left-middle; 'r' right-middle (text edge, excluding pad)."""
    if alpha <= 0.003: return
    im, pad = cardinfo
    if scale != 1.0:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BICUBIC); pad = int(pad * scale)
    if alpha < 0.999:
        a = np.asarray(im.getchannel('A')).astype(np.float32) * alpha
        im = im.copy(); im.putalpha(Image.fromarray(a.astype(np.uint8)))
    if anchor == 'c': px, py = x - im.width // 2, y - im.height // 2
    elif anchor == 'l': px, py = x - pad, y - im.height // 2
    else: px, py = x - im.width + pad, y - im.height // 2
    canvas.alpha_composite(im, (int(px), int(py)))

def ease(p): p = min(1, max(0, p)); return 1 - (1 - p) ** 3
def fade_win(t, a, b, fin=0.4, fout=0.3, hard_out=False):
    if t < a or t >= b: return 0.0, 0.0
    al = ease((t - a) / fin) if fin > 0 else 1.0
    if not hard_out and fout > 0: al *= min(1, (b - t) / fout)
    dy = 46 * (1 - ease((t - a) / max(fin, 1e-3)))
    return al, dy

# ---------------- route diagram (schematic, equal spacing) ----------------
NODES = [("Basecamp", None), ("Pos 1½", "40 min"), ("Camp 2", "36 min"), ("Camp 3", "45 min"),
         ("Camp 4", "1 jam 19 min"), ("Camp 5", "1 jam 20 min"), ("Camp 6", "1 jam 9 min"), ("Camp 7", "2 jam"),
         ("Camp 8", "1 jam 30 min"), ("Camp 9", "25 min"), ("Puncak Bendera", "10 min"), ("Puncak Sejati", "3 jam 30 min")]
NN = len(NODES)
Y0, Y1, X0, X1 = 2420, 1090, 520, 1500
pts = [(X0 + (X1 - X0) * i / (NN - 1) + (95 if i % 2 else -95) * (0.4 + 0.6 * math.sin(i * 1.3) ** 2), Y0 - (Y0 - Y1) * i / (NN - 1)) for i in range(NN)]
def catmull(p, n=40):
    out = []; P = [p[0]] + p + [p[-1]]
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = map(np.array, P[i-1:i+3])
        for s in np.linspace(0, 1, n, endpoint=False):
            out.append(0.5 * ((2*p1) + (-p0+p2)*s + (2*p0-5*p1+4*p2-p3)*s*s + (-p0+3*p1-3*p2+p3)*s**3))
    out.append(np.array(p[-1])); return np.array(out)
rng = np.random.default_rng(3)
CURVE = catmull(pts)
CURVE = CURVE + np.c_[np.convolve(rng.normal(0, 7, len(CURVE)), np.ones(5)/5, 'same'), np.convolve(rng.normal(0, 4, len(CURVE)), np.ones(5)/5, 'same')]
for i in range(NN): CURVE[i * 40] = pts[i]
SEG = np.r_[0, np.cumsum(np.linalg.norm(np.diff(CURVE, axis=0), axis=1))]
NODE_S = [SEG[i * 40] for i in range(NN)]

# light-up times per node (s); draw between previous node time and this one
LIT = {0: 4.40}
day1 = [40, 36, 45, 79, 80, 69, 120]; k = 5.0 / sum(day1); tcur = 4.40
for i, m in enumerate(day1, start=1):
    tcur += m * k; LIT[i] = tcur
    if i == 4: tcur += 0.70                     # Camp 4 lunch pause
PAUSE4 = (LIT[4], LIT[4] + 0.70)
LIT[8] = 12.40 + 0.90; LIT[9] = LIT[8] + 0.45; LIT[10] = LIT[9] + 0.35   # Camp 8, 9, Bendera
LIT[11] = 19.65                                                       # Puncak Sejati
DRAW_START = {i: (LIT[i-1] if i not in (5, 8, 11) else {5: PAUSE4[1], 8: 12.40, 11: 19.15}[i]) for i in range(1, NN)}
MAP_WINDOWS = [(4.0, 12.0), (12.0, 15.6), (19.1, 21.0)]

def route_progress(t):
    """arc length drawn at time t."""
    s = 0.0
    for i in range(1, NN):
        a, b = DRAW_START[i], LIT[i]
        if t >= b: s = NODE_S[i]
        elif t > a: s = NODE_S[i-1] + (NODE_S[i] - NODE_S[i-1]) * ((t - a) / (b - a)); break
        else: break
    return s

def draw_route(cv, t, win_a):
    d = ImageDraw.Draw(cv, 'RGBA')
    # faint full path preview
    pv = [tuple(p) for p in CURVE[::3]]
    d.line(pv, fill=(255, 255, 255, 40), width=8, joint='curve')
    s = route_progress(t)
    n = int(np.searchsorted(SEG, s))
    if n >= 2:
        seg = [tuple(p) for p in CURVE[:n]]
        if s > SEG[n-1] and n < len(CURVE):
            f = (s - SEG[n-1]) / (SEG[n] - SEG[n-1]); seg.append(tuple(CURVE[n-1] + f * (CURVE[n] - CURVE[n-1])))
        d.line(seg, fill=ORANGE + (70,), width=48, joint='curve')
        d.line(seg, fill=ORANGE + (255,), width=20, joint='curve')
        hx, hy = seg[-1]; d.ellipse([hx-16, hy-16, hx+16, hy+16], fill=WHITE + (255,))
    for i, (x, y) in enumerate(pts):
        if t >= LIT[i]:
            age = t - LIT[i]
            if age < 0.6:
                r = 24 + 70 * ease(age / 0.6); al = int(200 * (1 - age / 0.6))
                d.ellipse([x-r, y-r, x+r, y+r], outline=ORANGE + (al,), width=8)
            d.ellipse([x-24, y-24, x+24, y+24], fill=ORANGE + (255,), outline=WHITE + (255,), width=6)
        else:
            d.ellipse([x-15, y-15, x+15, y+15], outline=(255, 255, 255, 110), width=5)

def node_label(cv, i, t, alpha):
    name, leg = NODES[i]; x, y = pts[i]
    right = x < 1080
    lines = [(name, bar(96), WHITE, 0, 0)] + ([("+" + leg, dms(54), ORANGE, 1, 0)] if leg else [])
    c = card(lines, 'l' if right else 'r')
    al, dy = alpha
    put(cv, c, x + (62 if right else -62), y + dy * 0.5, al, 'l' if right else 'r')

def labels(cv, t):
    lit = [i for i in range(NN) if t >= LIT[i]]
    if not lit: return
    cur = lit[-1]
    show = [cur] + ([cur - 1] if cur >= 1 else [])          # max two labels
    for i in show:
        a0 = LIT[i]; al = ease((t - a0) / 0.3)
        if i != cur:                                         # previous label fades when the next lights
            al *= max(0.0, 1 - (t - LIT[cur]) / 0.5) * 0.85
        node_label(cv, i, t, (al, 30 * (1 - ease((t - a0) / 0.3))))
    if PAUSE4[0] <= t < PAUSE4[1] + 0.9:
        al = ease((t - PAUSE4[0]) / 0.3) * min(1, (PAUSE4[1] + 0.9 - t) / 0.3)
        c = card([("Rehat makan tengah hari", dms(56, 600), WHITE, 1, 0)])
        x, y = pts[4]; im, pad = c
        bw, bh = im.width - 2 * pad + 70, im.height - 2 * pad + 36
        px = x + 62; py = y + 150
        box = Image.new('RGBA', cv.size, (0, 0, 0, 0)); bd = ImageDraw.Draw(box)
        bd.rounded_rectangle([px, py - bh // 2, px + bw, py + bh // 2], radius=bh // 2, fill=ORANGE + (int(230 * al),))
        cv.alpha_composite(box); put(cv, c, px + bw // 2, py, al)

def map_frame(cv, t):
    day = 1 if t < 12.0 else 2
    hdr_t = 4.05 if day == 1 else (12.05 if t < 15.6 else 19.1)
    al, dy = fade_win(t, hdr_t, 99, 0.45 if hdr_t != 19.1 else 0.0)
    if day == 1:
        put(cv, card([("HARI 1", bar(110), ORANGE, 4, 0), ("BASECAMP KALIBARU → CAMP 7", bar(118), WHITE, 0, 0)]), CX, 640 + dy, al)
        a2, d2 = fade_win(t, 4.35, 99, 0.45)
        put(cv, card([("Via Kalibaru, Banyuwangi", dms(62), GREY, 1, 0)]), CX, 880 + d2, a2)
    else:
        put(cv, card([("HARI 2", bar(110), ORANGE, 4, 0), ("CAMP 7 → PUNCAK SEJATI", bar(118), WHITE, 0, 0)]), CX, 640 + dy, al)
    draw_route(cv, t, None); labels(cv, t)
    put(cv, card([("Ilustrasi laluan · tidak ikut skala", dms(44, 400), (220, 220, 220), 1, 0)]), SAFE_L + 30, 2940, 0.75, 'l')
    if day == 1:
        a3, d3 = fade_win(t, 10.20, 12.0, 0.45, 0.25)
        put(cv, card([("7 jam 49 minit", bar(150), WHITE, 0, 0)]), CX, 2700 + d3, a3)
        put(cv, card([("• belum termasuk lunch", dms(58), GREY, 1, 0)]), CX, 2840 + d3, a3)
    elif t < 15.6:
        a3, d3 = fade_win(t, LIT[10] + 0.10, 15.6, 0.35, 0, hard_out=True)
        sc = 1.0 + 0.12 * (1 - ease((t - LIT[10] - 0.1) / 0.3)) if a3 > 0 else 1.0
        put(cv, card([("3 JAM 30 MINIT", bar(190), ORANGE, 2, 0)]), CX, 2660, a3, scale=sc)
        put(cv, card([("lagi ke Puncak Sejati", dms(64), WHITE, 1, 0)]), CX, 2830 + d3, a3)
    else:
        a3, d3 = fade_win(t, LIT[11] + 0.10, 21.0, 0.3, 0.0, hard_out=True)
        put(cv, card([("5 jam 35 minit", bar(170), ORANGE, 0, 0)]), CX, 2670 + d3, a3)
        put(cv, card([("Jumlah Hari 2 · Camp 7 → Puncak Sejati", dms(56), WHITE, 1, 0)]), CX, 2830 + d3, a3)

# ---------------- Strava card ----------------
prof = json.load(open(f'{S}/info/profile.json'))
KM = np.array(prof['km']); EL = np.array(prof['m'])
EL = EL.min() + (EL - EL.min()) * (3259 - EL.min()) / (EL.max() - EL.min())
CH = (360, 840, 1830, 1560)   # chart box x0, y0, x1, y1
trace = Image.open(f'{IMG}/2.jpg').convert('RGB').crop((100, 120, 990, 1340))
ta = np.asarray(trace).astype(int); tmask = ((ta[:, :, 0] > 180) & (ta[:, :, 1] < 140)).astype(np.uint8) * 255
TRACE = Image.new('RGBA', trace.size, ORANGE + (0,)); TRACE.putalpha(Image.fromarray(tmask).filter(ImageFilter.MaxFilter(3)))
TRACE = TRACE.resize((int(trace.width * 0.5), int(trace.height * 0.5)), Image.LANCZOS)

def strava_frame(cv, t):
    al, dy = fade_win(t, 21.05, 99, 0.4)
    put(cv, card([("DATA RAKAMAN STRAVA", bar(120), WHITE, 3, 0)]), CX, 580 + dy, al)
    put(cv, card([("Profil elevasi · seluruh perjalanan naik & turun", dms(48, 400), GREY, 1, 0)]), CX, 720 + dy, al)
    # chart
    x0, y0, x1, y1 = CH; d = ImageDraw.Draw(cv, 'RGBA')
    p = ease((t - 21.25) / 1.6)
    if t >= 21.15:
        a = ease((t - 21.15) / 0.3)
        for e in (1000, 2000, 3000):
            yy = y1 - (e - 500) / 3000 * (y1 - y0)
            d.line([(x0, yy), (x1, yy)], fill=(255, 255, 255, int(45 * a)), width=3)
            put(cv, card([(f"{e:,} m", dms(38, 400), GREY, 0, 0)]), x0 - 20, yy, a * 0.8, 'r')
        put(cv, card([("0 km", dms(38, 400), GREY, 0, 0)]), x0, y1 + 50, a * 0.8, 'l')
        put(cv, card([("39.3 km", dms(38, 400), GREY, 0, 0)]), x1, y1 + 50, a * 0.8, 'r')
    if p > 0:
        n = max(2, int(len(KM) * p))
        xs = x0 + KM[:n] / 39.3 * (x1 - x0); ys = y1 - (EL[:n] - 500) / 3000 * (y1 - y0)
        poly = [(xs[0], y1)] + list(zip(xs, ys)) + [(xs[-1], y1)]
        d.polygon(poly, fill=ORANGE + (85,))
        d.line(list(zip(xs, ys)), fill=ORANGE + (255,), width=12, joint='curve')
        pk = int(np.argmax(EL))
        if n > pk:
            a = ease((t - (21.25 + 1.6 * pk / len(KM))) / 0.3)
            px, py = x0 + KM[pk] / 39.3 * (x1 - x0), y1 - (EL[pk] - 500) / 3000 * (y1 - y0)
            d.ellipse([px-18, py-18, px+18, py+18], fill=WHITE + (int(255 * a),))
    # trace thumbnail
    a = ease((t - 21.3) / 0.4)
    if a > 0:
        th = TRACE.copy(); th.putalpha(Image.fromarray((np.asarray(TRACE.getchannel('A')) * a * 0.9).astype(np.uint8)))
        cv.alpha_composite(th, (SAFE_R - th.width - 20, 1960))
        put(cv, card([("Trek Strava", dms(40, 500), GREY, 1, 0)]), SAFE_R - th.width // 2 - 20, 1960 + th.height + 40, a * 0.8)
    # three stats with count-up
    stats = [(22.55, "Jarak direkod", 39.30, "{:.2f} km"), (23.35, "Jumlah kenaikan elevasi", 3366, "+{:,.0f} m"), (24.15, "Elevasi maksimum direkod", 3259, "{:,.0f} m")]
    for j, (ts, lab, val, fmt) in enumerate(stats):
        a, dy = fade_win(t, ts, 99, 0.35)
        if a <= 0: continue
        v = val * ease((t - ts) / 0.6)
        y = 1900 + j * 360
        put(cv, card([(lab, dms(56), GREY, 1, 0)]), SAFE_L + 140, y + dy, a, 'l')
        put(cv, card([(fmt.format(v), bar(190), WHITE if j else ORANGE, 0, 0)], key=f"st{j}{fmt.format(v)}"), SAFE_L + 140, y + 150 + dy, a, 'l')
    put(cv, card([("Sumber: rakaman Strava (Hike)", dms(40, 400), (190, 190, 190), 1, 0)]), SAFE_L + 140, 2960, ease((t - 24.6) / 0.4) * 0.8, 'l')

# ---------------- hook + summit ----------------
def hook_frame(cv, t):
    if t < 1.6:
        al, dy = fade_win(t, 0.12, 1.6, 0.35, 0, hard_out=True)
        put(cv, card([("Camp 9 → Puncak Bendera:", bar(140), WHITE, 0, 10), ("10 minit.", bar(200), ORANGE, 0, 0)]), CX, 1450 + dy, al)
    elif t < 4.0:
        a1, d1 = fade_win(t, 1.66, 4.0, 0.3, 0.25)
        put(cv, card([("Puncak Sejati?", bar(150), WHITE, 0, 0)]), CX, 1200 + d1, a1)
        a2, _ = fade_win(t, 2.05, 4.0, 0.12, 0.25)
        if a2 > 0:
            sc = 1.0 + 0.22 * (1 - ease((t - 2.05) / 0.28))
            put(cv, card([("3 JAM 30 MINIT", bar(250), ORANGE, 2, 0)]), CX, 1460, a2, scale=sc)
        a3, d3 = fade_win(t, 2.35, 4.0, 0.3, 0.25)
        put(cv, card([("lagi.", dms(80, 600), WHITE, 1, 0)]), CX, 1690 + d3, a3)

def summit_frame(cv, t):
    al, dy = fade_win(t, 26.08, 30.5, 0.5)
    put(cv, card([("JALUR EKSTREM MENUJU", bar(130), WHITE, 3, 6), ("PUNCAK SEJATI", bar(240), WHITE, 2, 0), ("GUNUNG RAUNG", bar(240), WHITE, 2, 0)]), CX, 1200 + dy, al)
    a2, d2 = fade_win(t, 26.75, 30.5, 0.45)
    put(cv, card([("3,344 mdpl", bar(150), ORANGE, 2, 0)]), CX, 1720 + d2, a2)

def frame(t):
    cv = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    if t < 4.0: hook_frame(cv, t)
    elif t < 15.6 or 19.1 <= t < 21.0: map_frame(cv, t)
    elif 21.0 <= t < 26.0: strava_frame(cv, t)
    elif t >= 26.0: summit_frame(cv, t)
    return cv

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--still':
        for tt in sys.argv[2].split(','):
            frame(float(tt)).save(f'{sys.argv[3]}/ov_{tt}.png')
    else:
        out = sys.stdout.buffer
        for i in range(int(DUR * FPS)):
            out.write(frame(i / FPS).tobytes())
