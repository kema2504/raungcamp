"""Original procedural score v2 for the Raung trailer (60 s, 48 kHz stereo).
0.0/0.7/1.4 PAP hits (carabiner click, boot scrape, boom) | 1.4-4.0 music down, wind up
| 3.6-4.0 reverse whoosh into the rewind | 4-9 soft pulse montage | 9-22.75 drums build
| 22.75-35 rope/ridge ostinato | 35.0-37.5 riser | 37.5-38.0 music silent, wind only
| 38.0 bass hit + reveal chord | 48.5-57.5 descent reprise | 57.5 soft hit, fade."""
import sys, numpy as np
from scipy.signal import butter, sosfilt
from scipy.io import wavfile

SR = 48000; DUR = 60.0; N = int(SR * DUR)
rng = np.random.default_rng(11)
t = np.arange(N) / SR
L = np.zeros(N); R = np.zeros(N)
REVEAL = 38.0; SIL0 = 37.5

def lp(x, f, o=2): return sosfilt(butter(o, f, 'low', fs=SR, output='sos'), x)
def hp(x, f, o=2): return sosfilt(butter(o, f, 'high', fs=SR, output='sos'), x)
def bp(x, a, b, o=2): return sosfilt(butter(o, [a, b], 'band', fs=SR, output='sos'), x)
def add(sig, start, gain=1.0, pan=0.0):
    i = int(round(start * SR)); n = min(len(sig), N - i)
    if n <= 0: return
    L[i:i+n] += sig[:n] * gain * np.sqrt(0.5 * (1 - pan))
    R[i:i+n] += sig[:n] * gain * np.sqrt(0.5 * (1 + pan))
def env(n, a, r):
    e = np.ones(n); na = int(a*SR); nr = int(r*SR)
    if na: e[:na] = np.linspace(0, 1, na)
    if nr: e[-nr:] *= np.linspace(1, 0, nr)
    return e
def auto(points): xs, ys = zip(*points); return np.interp(t, xs, ys)
def note(m): return 440.0 * 2 ** ((m - 69) / 12)
def tt_(d): return np.arange(int(d * SR)) / SR

# ---------------- music bus ----------------
mL = np.zeros(N); mR = np.zeros(N)
def madd(sig, start, gain=1.0, pan=0.0):
    i = int(round(start * SR)); n = min(len(sig), N - i)
    if n <= 0: return
    mL[i:i+n] += sig[:n] * gain * np.sqrt(0.5 * (1 - pan))
    mR[i:i+n] += sig[:n] * gain * np.sqrt(0.5 * (1 + pan))

def pad_chord(notes, dur, cutoff=1400, att=0.35, rel=0.4):
    tt = tt_(dur); s = np.zeros(len(tt))
    for m in notes:
        for det in (-0.006, 0.0, 0.006):
            s += 2 * ((tt * note(m) * (1 + det)) % 1) - 1
    s = lp(s / (len(notes) * 3), cutoff, 4)
    return s * env(len(tt), dur * att, dur * rel)
def kick(f0=55, dec=0.45, click=0.3):
    tt = tt_(0.9); f = f0 + 90 * np.exp(-tt * 30)
    return np.sin(2*np.pi*np.cumsum(f)/SR) * np.exp(-tt/dec) + click * hp(rng.standard_normal(len(tt)), 2000) * np.exp(-tt*120)
def tom(f0=90, dec=0.35):
    tt = tt_(0.8)
    return np.sin(2*np.pi*np.cumsum(f0 + 40*np.exp(-tt*20))/SR) * np.exp(-tt/dec) + 0.15 * bp(rng.standard_normal(len(tt)), 200, 1200) * np.exp(-tt*25)
def shaker():
    tt = tt_(0.12); return hp(rng.standard_normal(len(tt)), 5000) * np.exp(-tt*40)
def boom(f0=36, dec=1.4, sweep=60):
    tt = tt_(5.0)
    return np.sin(2*np.pi*np.cumsum(f0 + sweep*np.exp(-tt*8))/SR) * np.exp(-tt/dec)

beat = 0.625
# dark drone under the hook hold (kept very low: "music down")
madd(pad_chord([33, 40, 45], 2.9, 500, 0.3, 0.3), 1.4, 0.10)
# 4-9 rewind montage: pad + soft pulse every 2 beats
chords = [[45, 57, 60, 64], [41, 53, 57, 60], [48, 55, 60, 64], [43, 55, 59, 62]]
madd(pad_chord(chords[0], 5.4, 900), 4.0, 0.15, -0.2)
for b in np.arange(4.0, 9.0, beat * 2): madd(kick(50, 0.5, 0.1), b, 0.45)
# 9-22.75 climb: drums enter and build
k = 1
for st in np.arange(9.0, 22.75, 2.5 * 2):
    madd(pad_chord(chords[k % 4], 5.8, 900 + 45 * (st - 9)), st, 0.15, 0.2 if k % 2 else -0.2); k += 1
for i, b in enumerate(np.arange(9.0, 22.75, beat)):
    dens = (b - 9.0) / 13.75
    madd(kick(), b, 0.55 if i % 4 == 0 else 0.32)
    if i % 2 == 1: madd(tom(85), b, 0.30 + 0.1 * dens, -0.3)
    if b > 14.0 and i % 4 == 3: madd(tom(120), b + beat / 2, 0.28, 0.3)
    if b > 16.5: madd(shaker(), b + beat / 2, 0.11, 0.5)
# 22.75-35 rope + ridge: 8th-note ostinato, heavier kick
for i, b in enumerate(np.arange(22.75, 35.0, beat / 2)):
    tt = tt_(0.25); m = 33 if (i // 8) % 2 == 0 else 34
    madd(lp(2 * ((tt * note(m)) % 1) - 1, 500, 2) * np.exp(-tt * 10), b, 0.22 + 0.14 * (b - 22.75) / 12.25)
    if i % 2 == 0: madd(kick(48, 0.35, 0.2), b, 0.48)
    if i % 4 == 2: madd(tom(70, 0.3), b, 0.30, -0.2)
madd(pad_chord([45, 52, 57], 12.5, 700, 0.5, 0.2), 22.75, 0.10)
# riser 35.0 -> 37.5, hard stop
n = int((SIL0 - 35.0) * SR); tt = np.arange(n) / SR; prog = tt / tt[-1]
noise = rng.standard_normal(n); sweep = np.zeros(n); blk = 2400
for j in range(0, n, blk):
    fc = 300 + 7000 * prog[j] ** 2
    seg = noise[j:j+blk]; sweep[j:j+len(seg)] = bp(seg, max(80, fc * 0.6), min(20000, fc * 1.4), 1)
tone = np.sin(2 * np.pi * np.cumsum(note(45) * 2 ** (prog * 2)) / SR)
r = (0.8 * sweep + 0.25 * tone) * prog ** 2; r[-int(0.01*SR):] *= np.linspace(1, 0, int(0.01*SR))
madd(r, 35.0, 0.38)
# REVEAL 38.0: sub boom + impact + wide chord, then hold
madd(boom(36, 1.8, 60), REVEAL, 1.0)
madd(lp(rng.standard_normal(int(4 * SR)), 1800, 2) * np.exp(-tt_(4.0) * 6), REVEAL, 0.38)
madd(pad_chord([45, 52, 57, 60, 64, 69], 10.0, 2200, 0.05, 0.4), REVEAL, 0.26)
for b in np.arange(40.5, 48.5, beat * 4): madd(kick(45, 0.6, 0.0), b, 0.22)
# 48.5-57.5 descent reprise: abseil gets low pulse + toms, then settles
madd(pad_chord([41, 48, 57, 60, 65], 9.5, 1300), 48.5, 0.17)
for i, b in enumerate(np.arange(48.5, 55.0, beat)):
    madd(kick(50, 0.4, 0.1), b, 0.35 if i % 2 == 0 else 0.18)
    if i % 4 == 2: madd(tom(80, 0.3), b, 0.22, 0.2)
madd(kick(42, 0.9, 0.05), 57.5, 0.45)
madd(pad_chord([45, 52, 57, 64], 3.0, 1200, 0.1, 0.6), 57.5, 0.14)

music_gain = auto([(0, 1), (1.4, 1), (1.45, 0.35), (3.6, 0.35), (4.0, 1.0),
                   (35.0, 1.0), (SIL0 - 0.001, 1.0), (SIL0, 0.0), (REVEAL - 0.001, 0.0), (REVEAL, 1.0),
                   (58.4, 1.0), (60, 0.0)])
L += mL * music_gain; R += mR * music_gain

# ---------------- sound design (not ducked) ----------------
# PAP1 0.0: carabiner click - sharp transient + metallic ring partials, plus low thud
tt = tt_(0.5)
ring = sum(a * np.sin(2*np.pi*f*tt) * np.exp(-tt*d) for f, a, d in ((3150, 0.5, 28), (4720, 0.35, 34), (6980, 0.22, 45), (2280, 0.25, 22)))
click = hp(rng.standard_normal(len(tt)), 3000) * np.exp(-tt * 400)
add(0.55 * ring + 0.9 * click, 0.0, 0.55, 0.15)
add(0.6 * ring + 0.7 * click, 0.09, 0.30, 0.15)            # the gate snapping shut
add(kick(48, 0.35, 0.0), 0.0, 0.6)
# PAP2 0.7: boot scrape on gravel - grainy band-passed noise bursts
d = 0.45; tt = tt_(d); n = len(tt)
grains = (rng.random(n) < 0.004).astype(float); grains = np.convolve(grains, np.exp(-np.arange(240)/30), 'same')
scrape = bp(rng.standard_normal(n), 900, 5200, 2) * (0.35 + grains) * env(n, 0.02, 0.25) * (1 - tt / d) ** 0.5
add(scrape, 0.70, 0.75, -0.1)
add(kick(52, 0.3, 0.0), 0.70, 0.55)
# PAP3 1.4: deep boom + whoosh leading into the cut
tt = tt_(0.35); wsh = bp(rng.standard_normal(len(tt)), 400, 3000, 1) * (tt / tt[-1]) ** 2.5
add(wsh, 1.05, 0.35)
add(boom(34, 1.6, 50), 1.4, 0.95)
add(lp(rng.standard_normal(int(2*SR)), 1200, 2) * np.exp(-tt_(2.0) * 7), 1.4, 0.3)
# 3.6-4.0 reverse "rewind" whoosh
tt = tt_(0.4); rw = bp(rng.standard_normal(len(tt)), 600, 6000, 1) * (tt / tt[-1]) ** 3
rw *= 1 + 0.5 * np.sin(2*np.pi*30*tt); add(rw, 3.6, 0.32)

# ---------------- wind bed ----------------
for ch, seed in ((0, 1), (1, 2)):
    nz = np.random.default_rng(seed).standard_normal(N)
    gust = 0.55 + 0.45 * np.sin(2*np.pi*0.13*t + seed) * np.sin(2*np.pi*0.037*t + 1.3*seed)
    w = bp(nz, 180, 1400) * gust + 0.4 * lp(nz, 300)
    w *= auto([(0, 0.3), (1.4, 0.4), (1.9, 2.2), (3.9, 2.8), (4.2, 0.3), (22.75, 0.3), (31.5, 0.6),
               (34.0, 0.7), (36.25, 0.9), (SIL0, 3.2), (REVEAL, 3.4), (38.5, 0.4), (55, 0.35), (60, 0.0)])
    (L if ch == 0 else R)[:] += w * 0.065

mix = np.stack([L, R], 1); mix /= np.max(np.abs(mix)) / 0.89
wavfile.write(sys.argv[1], SR, (mix * 32767).astype(np.int16))
print('wrote', sys.argv[1])
