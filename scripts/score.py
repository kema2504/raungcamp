"""Original procedural cinematic-adventure score for the Raung trailer (60 s, 48 kHz stereo).
Sections: 0-4 wind | 4-14 slow pulse + pad | 14-30 drums build | 30-42 tension ostinato
| 42-45 music dips + riser | 45 bass hit + reveal chord | 55-60 outro."""
import sys, numpy as np
from scipy.signal import butter, sosfilt
from scipy.io import wavfile

SR = 48000; DUR = 60.0; N = int(SR * DUR)
rng = np.random.default_rng(7)
t = np.arange(N) / SR
L = np.zeros(N); R = np.zeros(N)

def lp(x, f, o=2): return sosfilt(butter(o, f, 'low', fs=SR, output='sos'), x)
def hp(x, f, o=2): return sosfilt(butter(o, f, 'high', fs=SR, output='sos'), x)
def bp(x, a, b, o=2): return sosfilt(butter(o, [a, b], 'band', fs=SR, output='sos'), x)
def add(sig, start, gain=1.0, pan=0.0):
    i = int(start * SR); n = min(len(sig), N - i)
    if n <= 0: return
    L[i:i+n] += sig[:n] * gain * np.sqrt(0.5 * (1 - pan))
    R[i:i+n] += sig[:n] * gain * np.sqrt(0.5 * (1 + pan))
def env(n, a, r):  # attack/release seconds, linear
    e = np.ones(n); na = int(a*SR); nr = int(r*SR)
    if na: e[:na] = np.linspace(0, 1, na)
    if nr: e[-nr:] *= np.linspace(1, 0, nr)
    return e
def fade_curve(points):  # piecewise linear automation over full timeline
    xs, ys = zip(*points); return np.interp(t, xs, ys)
def note(f): return 440.0 * 2 ** ((f - 69) / 12)

# --- Wind bed (whole piece, louder at open and before the summit)
for ch, seed in ((0, 1), (1, 2)):
    n = np.random.default_rng(seed).standard_normal(N)
    gust = 0.55 + 0.45 * np.sin(2*np.pi*0.13*t + seed) * np.sin(2*np.pi*0.037*t + 1.3*seed)
    w = bp(n, 180, 1400) * gust + 0.4 * lp(n, 300)
    w *= fade_curve([(0, 0.0), (0.4, 1.0), (4, 0.9), (6, 0.35), (30, 0.3), (40, 0.6), (44.8, 0.8), (45, 0.4), (55, 0.4), (60, 0.0)])
    (L if ch == 0 else R)[:] += w * 0.06

# --- Pad (A minor -> F -> C -> G), detuned saws, low-passed
chords = [[45, 57, 60, 64], [41, 53, 57, 60], [48, 55, 60, 64], [43, 55, 59, 62]]
def pad_chord(notes, dur, cutoff=1400):
    n = int(dur*SR); tt = np.arange(n)/SR; s = np.zeros(n)
    for m in notes:
        for det in (-0.08, 0.0, 0.08):
            f = note(m + det/12*0 ) * (1 + det*0.01)
            s += 2*((tt*f) % 1) - 1
    s = lp(s / (len(notes)*3), cutoff, 4)
    return s * env(n, dur*0.35, dur*0.4)
bar = 2.5
k = 0
for st in np.arange(4.0, 42.0, bar*2):
    add(pad_chord(chords[k % 4], bar*2 + 0.8, 900 + 40*(st-4)), st, 0.16, pan=(-0.2 if k%2 else 0.2)); k += 1

# --- Drums
def kick(f0=55, dec=0.45, click=0.3):
    n = int(0.9*SR); tt = np.arange(n)/SR
    f = f0 + 90*np.exp(-tt*30); ph = 2*np.pi*np.cumsum(f)/SR
    s = np.sin(ph)*np.exp(-tt/dec) + click*hp(rng.standard_normal(n), 2000)*np.exp(-tt*120)
    return s
def tom(f0=90, dec=0.35):
    n = int(0.8*SR); tt = np.arange(n)/SR
    ph = 2*np.pi*np.cumsum(f0 + 40*np.exp(-tt*20))/SR
    return np.sin(ph)*np.exp(-tt/dec) + 0.15*bp(rng.standard_normal(n), 200, 1200)*np.exp(-tt*25)
def shaker():
    n = int(0.12*SR); tt = np.arange(n)/SR
    return hp(rng.standard_normal(n), 5000)*np.exp(-tt*40)

beat = 0.625  # 96 BPM
# 4-14: slow heartbeat-like pulse on every 2 beats
for b in np.arange(4.0, 14.0, beat*2):
    add(kick(50, 0.5, 0.1), b, 0.5)
# 14-30: building toms + kick, gets denser
for i, b in enumerate(np.arange(14.0, 30.0, beat)):
    add(kick(), b, 0.6 if i % 4 == 0 else 0.35)
    if i % 2 == 1: add(tom(85), b, 0.35, pan=-0.3)
    if b > 20 and i % 4 == 3: add(tom(120), b + beat/2, 0.3, pan=0.3)
    if b > 22: add(shaker(), b + beat/2, 0.12, pan=0.5)
# 30-42: tense 8th-note ostinato on low A + driving kick
for i, b in enumerate(np.arange(30.0, 42.0, beat/2)):
    n = int(0.25*SR); tt = np.arange(n)/SR
    m = 33 if (i//8) % 2 == 0 else 34
    s = lp(2*((tt*note(m)) % 1)-1, 500, 2) * np.exp(-tt*10)
    add(s, b, 0.22 + 0.15*(b-30)/12)
    if i % 2 == 0: add(kick(48, 0.35, 0.2), b, 0.45)
    if i % 4 == 2: add(tom(70, 0.3), b, 0.3, pan=-0.2)

# --- Riser 41.5 -> 44.85 (noise sweep + rising tone), then short silence before hit
rs, re_ = 41.5, 44.85
n = int((re_-rs)*SR); tt = np.arange(n)/SR; prog = tt/tt[-1]
noise = rng.standard_normal(n)
sweep = np.zeros(n); blk = 2400
for j in range(0, n, blk):
    fc = 300 + 7000*prog[j]**2
    sweep[j:j+blk] = bp(noise[j:j+blk+0], max(80, fc*0.6), min(20000, fc*1.4), 1)[:len(sweep[j:j+blk])]
tone = np.sin(2*np.pi*np.cumsum(note(45) * 2**(prog*2))/SR)
riser = (0.8*sweep + 0.25*tone) * prog**2
add(riser, rs, 0.35)

# --- Reveal at 45.0: sub boom + impact + big chord
n = int(6*SR); tt = np.arange(n)/SR
boom = np.sin(2*np.pi*np.cumsum(38 + 60*np.exp(-tt*8))/SR) * np.exp(-tt/1.6)
impact = lp(rng.standard_normal(n), 1800, 2) * np.exp(-tt*6)
add(boom, 45.0, 1.0); add(impact, 45.0, 0.35)
add(pad_chord([45, 52, 57, 60, 64, 69], 10.5, 2200), 45.0, 0.26)
add(pad_chord([41, 48, 57, 60, 65], 6.0, 1500), 54.5, 0.2)
# gentle pulses under the reveal hold
for b in np.arange(47.5, 55.0, beat*4): add(kick(45, 0.6, 0.0), b, 0.25)
# final soft hit at 55 for the summit/airport cut
add(kick(42, 0.9, 0.05), 55.0, 0.45)

# master: music ducks before reveal (42-44.85), fade end
master = fade_curve([(0, 1), (42.0, 1), (42.6, 0.55), (44.85, 0.55), (44.86, 1.0), (58.5, 1.0), (60, 0.0)])
mix = np.stack([L*master, R*master], 1)
mix /= np.max(np.abs(mix)) / 0.89
wavfile.write(sys.argv[1], SR, (mix*32767).astype(np.int16))
print("wrote", sys.argv[1])
