"""Original procedural score for the 30 s info video (48 kHz stereo).
0-1.6 tension tick + low drone | 1.6 PAP hit (hard cut) | 2.05 number slam | 2.1-4.0 wind swell, music out
| 4-12 info bed + checkpoint blips, thins at Camp 4 lunch | 12-15.6 bed continues, low hit at Bendera hold
| 15.6-19.1 drums drive (rope / ridge / abseil) | 19.65 Sejati chime | 21-26 data bed + stat ticks
| 26.0 bass hit + chord for the summit title, fade 29-30."""
import sys, json, numpy as np
from scipy.signal import butter, sosfilt
from scipy.io import wavfile
sys.path.insert(0, sys.argv[2] if len(sys.argv) > 2 else '.')
SR = 48000; DUR = 30.0; N = int(SR * DUR)
rng = np.random.default_rng(21)
t = np.arange(N) / SR
L = np.zeros(N); R = np.zeros(N); mL = np.zeros(N); mR = np.zeros(N)

def lp(x, f, o=2): return sosfilt(butter(o, f, 'low', fs=SR, output='sos'), x)
def hp(x, f, o=2): return sosfilt(butter(o, f, 'high', fs=SR, output='sos'), x)
def bp(x, a, b, o=2): return sosfilt(butter(o, [a, b], 'band', fs=SR, output='sos'), x)
def _add(bl, br, sig, start, gain, pan):
    i = int(round(start * SR)); n = min(len(sig), N - i)
    if n <= 0: return
    bl[i:i+n] += sig[:n] * gain * np.sqrt(0.5 * (1 - pan)); br[i:i+n] += sig[:n] * gain * np.sqrt(0.5 * (1 + pan))
def sfx(sig, st, g=1.0, pan=0.0): _add(L, R, sig, st, g, pan)
def mus(sig, st, g=1.0, pan=0.0): _add(mL, mR, sig, st, g, pan)
def tt_(d): return np.arange(int(d * SR)) / SR
def env(n, a, r):
    e = np.ones(n); na, nr = int(a * SR), int(r * SR)
    if na: e[:na] = np.linspace(0, 1, na)
    if nr: e[-nr:] *= np.linspace(1, 0, nr)
    return e
def auto(pts): xs, ys = zip(*pts); return np.interp(t, xs, ys)
def note(m): return 440.0 * 2 ** ((m - 69) / 12)
def pad(notes, dur, cut=1200, att=0.3, rel=0.4):
    tt = tt_(dur); s = np.zeros(len(tt))
    for m in notes:
        for det in (-0.006, 0, 0.006): s += 2 * ((tt * note(m) * (1 + det)) % 1) - 1
    return lp(s / (len(notes) * 3), cut, 4) * env(len(tt), dur * att, dur * rel)
def kick(f0=55, dec=0.4, click=0.25):
    tt = tt_(0.8); return np.sin(2*np.pi*np.cumsum(f0 + 90*np.exp(-tt*30))/SR)*np.exp(-tt/dec) + click*hp(rng.standard_normal(len(tt)), 2000)*np.exp(-tt*120)
def tom(f0=90, dec=0.3):
    tt = tt_(0.7); return np.sin(2*np.pi*np.cumsum(f0 + 40*np.exp(-tt*20))/SR)*np.exp(-tt/dec) + 0.15*bp(rng.standard_normal(len(tt)), 200, 1200)*np.exp(-tt*25)
def hat():
    tt = tt_(0.08); return hp(rng.standard_normal(len(tt)), 6000) * np.exp(-tt * 60)
def boom(f0=36, dec=1.5, sw=60):
    tt = tt_(4.5); return np.sin(2*np.pi*np.cumsum(f0 + sw*np.exp(-tt*8))/SR)*np.exp(-tt/dec)
def impact(d=2.0, cut=1600, k=7): return lp(rng.standard_normal(int(d * SR)), cut, 2) * np.exp(-tt_(d) * k)
def blip(m, d=0.35):
    tt = tt_(d); return (np.sin(2*np.pi*note(m)*tt) + 0.3*np.sin(2*np.pi*note(m+12)*tt)) * np.exp(-tt*9) * env(len(tt), 0.004, 0.05)
def whoosh(d, lo=500, hi=5000, p=2.5):
    tt = tt_(d); return bp(rng.standard_normal(len(tt)), lo, hi, 1) * (tt / tt[-1]) ** p

beat = 60 / 104
# --- 0-1.6 hook tension: ticking + drone
mus(pad([33, 40], 1.7, 450, 0.4, 0.05), 0.0, 0.16)
for b in np.arange(0.0, 1.6, beat / 2): mus(hat(), b, 0.18)
sfx(whoosh(0.3), 1.30, 0.35)
# --- 1.6 PAP (hard cut) + 2.05 number slam
sfx(boom(34, 1.4, 55), 1.60, 0.95); sfx(impact(1.6, 1800, 8), 1.60, 0.35)
sfx(kick(48, 0.3, 0.3), 2.05, 0.7); sfx(impact(0.8, 3000, 14), 2.05, 0.25)
# --- 3.65-4.0 transition whoosh into the map
sfx(whoosh(0.35, 700, 7000, 3), 3.65, 0.3)
# --- 4-15.6 info bed: kick/hat groove + pad
chords = [[45, 57, 60, 64], [41, 53, 57, 60], [48, 55, 60, 64], [43, 55, 59, 62]]
for j, st in enumerate(np.arange(4.0, 15.6, beat * 8)):
    mus(pad(chords[j % 4], beat * 8 + 0.5, 1000 + 60 * j), st, 0.13, 0.2 if j % 2 else -0.2)
for i, b in enumerate(np.arange(4.0, 15.6, beat)):
    mus(kick(52, 0.35, 0.15), b, 0.42 if i % 2 == 0 else 0.22)
    mus(hat(), b + beat / 2, 0.10, 0.4)
    if i % 4 == 3: mus(tom(110), b, 0.18, -0.3)
# checkpoint blips (rising), from the overlay timing
import importlib.util
spec = importlib.util.spec_from_file_location('ov', sys.argv[2] + '/info_overlay.py') if len(sys.argv) > 2 else None
LIT = {0: 4.40}
day1 = [40, 36, 45, 79, 80, 69, 120]; k = 5.0 / sum(day1); tc = 4.40
for i, m in enumerate(day1, 1):
    tc += m * k; LIT[i] = tc
    if i == 4: tc += 0.70
LIT[8] = 13.30; LIT[9] = 13.75; LIT[10] = 14.10; LIT[11] = 19.65
scale = [57, 59, 60, 62, 64, 65, 67, 69, 71, 72, 74, 76]
for i, tl in LIT.items(): sfx(blip(scale[i]), tl, 0.20 if i not in (7, 10, 11) else 0.30, 0.15)
# Camp 4 lunch pause: soft two-note chime
sfx(blip(76, 0.6), LIT[4] + 0.12, 0.12); sfx(blip(79, 0.6), LIT[4] + 0.30, 0.10)
# Bendera hold: low hit, groove drops out
sfx(boom(40, 0.9, 40), 14.20, 0.55); sfx(kick(46, 0.35, 0.2), 14.20, 0.5)
# --- 15.6-19.1 drive: rope / ridge / abseil
for i, b in enumerate(np.arange(15.6, 19.1, beat / 2)):
    tt = tt_(0.22); m = 33 if (i // 8) % 2 == 0 else 34
    mus(lp(2 * ((tt * note(m)) % 1) - 1, 520, 2) * np.exp(-tt * 10), b, 0.26)
    if i % 2 == 0: mus(kick(48, 0.32, 0.25), b, 0.55)
    if i % 4 == 2: mus(tom(72, 0.28), b, 0.34, -0.2)
mus(pad([45, 52, 57], 3.6, 800, 0.3, 0.2), 15.6, 0.10)
sfx(boom(36, 0.8, 50), 15.60, 0.5)
sfx(whoosh(0.3), 18.75, 0.25)
# --- 19.1-21 resolve: Sejati chime
mus(pad([45, 52, 57, 64], 2.2, 1500, 0.1, 0.4), 19.1, 0.14)
sfx(blip(81, 0.9), 19.65, 0.22); sfx(blip(88, 0.9), 19.72, 0.12)
# --- 21-26 data bed + ticks on stats
mus(pad([41, 48, 57, 60], 5.2, 1100, 0.2, 0.3), 21.0, 0.13)
for i, b in enumerate(np.arange(21.0, 26.0, beat)):
    mus(kick(50, 0.35, 0.1), b, 0.30 if i % 2 == 0 else 0.15); mus(hat(), b + beat / 2, 0.08, 0.4)
for ts in (22.55, 23.35, 24.15):
    for q in range(8): sfx(blip(84 + q % 3, 0.06), ts + q * 0.07, 0.05)
    sfx(blip(79, 0.4), ts + 0.6, 0.12)
sfx(whoosh(0.4, 400, 4000, 3), 25.6, 0.3)
# --- 26.0 summit: bass hit + wide chord
sfx(boom(36, 1.8, 60), 26.0, 1.0); sfx(impact(3.0, 1800, 6), 26.0, 0.35)
mus(pad([45, 52, 57, 60, 64, 69], 4.0, 2200, 0.05, 0.5), 26.0, 0.24)

music_gain = auto([(0, 1), (1.6, 1), (1.62, 0.0), (3.6, 0.0), (4.0, 1.0), (14.18, 1.0), (14.22, 0.25),
                   (15.58, 0.25), (15.6, 1.0), (29.0, 1.0), (30, 0)])
L += mL * music_gain; R += mR * music_gain
# wind bed: up after the PAP hit, low under the info bed
for ch, seed in ((0, 5), (1, 6)):
    nz = np.random.default_rng(seed).standard_normal(N)
    gust = 0.55 + 0.45 * np.sin(2*np.pi*0.17*t + seed) * np.sin(2*np.pi*0.05*t + seed)
    w = bp(nz, 180, 1400) * gust + 0.4 * lp(nz, 300)
    w *= auto([(0, 0.5), (1.6, 0.6), (2.0, 1.0), (2.4, 3.0), (3.8, 3.2), (4.1, 0.35), (15.6, 0.4), (16.6, 1.2), (18.6, 1.2),
               (19.1, 0.35), (26.0, 0.6), (29, 0.6), (30, 0)])
    (L if ch == 0 else R)[:] += w * 0.065
mix = np.stack([L, R], 1); mix /= np.max(np.abs(mix)) / 0.89
wavfile.write(sys.argv[1], SR, (mix * 32767).astype(np.int16)); print('wrote', sys.argv[1])
