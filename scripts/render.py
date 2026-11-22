"""Render the Raung trailer: per-shot 2160x3840 intermediates -> concat -> text overlays + audio mix."""
import glob, json, os, re, subprocess, sys
from PIL import Image, ImageOps, ImageDraw, ImageFont, ImageFilter

S = '/tmp/claude-0/-home-user-raungcamp/b0706bff-2b10-5382-a9f0-3081491f33ef/scratchpad'
B = f'{S}/build'; os.makedirs(f'{B}/shots', exist_ok=True); os.makedirs(f'{B}/text', exist_ok=True)
exec(open(f'{S}/scripts/shots.py').read())
W, H, FPS = 2160, 3840, 30
ONLY_TEXT = '--text-only' in sys.argv

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode: print(r.stderr[-3000:]); raise SystemExit(1)
    return r

def nat_gain(t):  # natural-sound level per section (linear)
    if t < 4: return 1.0
    if t < 14: return 0.30
    if t < 30: return 0.40
    if t < 41.25: return 0.55
    if t < 45: return 0.85
    if t < 55: return 0.22
    if t < 57.6: return 0.35
    return 0.45

GRADE = "curves=all='0/0 0.25/0.245 0.6/0.61 0.85/0.83 1/0.95',eq=contrast=1.03:saturation={sat}"

# ---------- 1. per-shot intermediates ----------
if not ONLY_TEXT:
  for i, (a, b, pre, si, fl) in enumerate(SHOTS):
    D = round(b - a, 4); src = glob.glob(f'{S}/raw/{pre}*')[0]
    out = f'{B}/shots/{i:02d}.mkv'
    if os.path.exists(out) and os.path.getsize(out) > 0: continue
    sat = 0.96 if pre.startswith(('IMG_0001', 'IMG_9982', 'IMG_0056')) else 1.04
    if fl.get('photo'):
        jp = f'{B}/shots/{i:02d}_photo.png'
        ImageOps.exif_transpose(Image.open(src)).convert('RGB').save(jp)
        inputs = ['-loop', '1', '-framerate', str(FPS), '-t', str(D), '-i', jp,
                  '-f', 'lavfi', '-t', str(D), '-i', 'anullsrc=r=48000:cl=stereo']
        vf = f"scale=-2:{H}:flags=lanczos,crop={W}:{H}"; amap = '1:a'; af = 'anull'
    else:
        inputs = ['-ss', str(si), '-t', str(D + 0.1), '-i', src]
        vf = f"scale={W}:{H}:flags=lanczos"
        codecs = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'a', '-show_entries', 'stream=codec_name',
                                 '-of', 'csv=p=0', src], capture_output=True, text=True).stdout.split()
        amap = f"0:a:{codecs.index('aac')}"
        # measure loudness of the segment and normalise nat sound to ~-26 dB mean
        m = subprocess.run(['ffmpeg', '-hide_banner', '-ss', str(si), '-t', str(D), '-i', src, '-map', amap,
                            '-af', 'volumedetect', '-f', 'null', '-'], capture_output=True, text=True).stderr
        mv = float(re.search(r'mean_volume: (-?[\d.]+)', m).group(1))
        g_db = max(-12, min(12, -26 - mv)) + 20 * __import__('math').log10(nat_gain(a))
        af = f"volume={g_db:.2f}dB,afade=t=in:d=0.03,afade=t=out:st={D-0.04}:d=0.04"
    if fl.get('zoom'):
        vf += (f",scale=w='trunc({W}*(1+0.05*t/{D})/2)*2':h='trunc({H}*(1+0.05*t/{D})/2)*2'"
               f":eval=frame:flags=bicubic,crop={W}:{H}")
    vf += f",fps={FPS}," + GRADE.format(sat=sat) + ",setsar=1,format=yuv420p"
    run(['ffmpeg', '-y', '-v', 'error', *inputs, '-map', '0:v:0', '-map', amap,
         '-vf', vf, '-af', af + ',aresample=48000,aformat=channel_layouts=stereo',
         '-t', str(D), '-frames:v', str(round(D * FPS)),
         '-c:v', 'libx264', '-preset', 'fast', '-crf', '12', '-c:a', 'pcm_s16le', out])
    print('shot', i, pre, D, flush=True)

  with open(f'{B}/list.txt', 'w') as f:
    for i in range(len(SHOTS)): f.write(f"file '{B}/shots/{i:02d}.mkv'\n")
  run(['ffmpeg', '-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', f'{B}/list.txt', '-c', 'copy', f'{B}/assembled.mkv'])

# ---------- 2. text cards (Pillow, cropped RGBA with soft shadow) ----------
BAR = f'{S}/fonts/BarlowCondensed-ExtraBold.ttf'
DMS = f'{S}/fonts/DMSans%5Bopsz,wght%5D.ttf'
def font(path, size, medium=False):
    f = ImageFont.truetype(path, size)
    if medium: f.set_variation_by_axes([14, 500])
    return f
SAFE_L, SAFE_R = 120, W - 300          # keep clear of the right-hand button rail
CX = (SAFE_L + SAFE_R) // 2

def card(name, lines, cy):
    """lines: list of (text, font, tracking_px, gap_after). Returns (png, x, y)."""
    pad = 80
    sizes = []
    for txt, f, tr, gap in lines:
        w = sum(f.getlength(c) for c in txt) + tr * (len(txt) - 1)
        asc, desc = f.getmetrics(); sizes.append((w, asc + desc, gap))
    tw = int(max(s[0] for s in sizes)) + 2 * pad
    th = int(sum(s[1] + s[2] for s in sizes)) + 2 * pad
    txt_l = Image.new('L', (tw, th), 0); d = ImageDraw.Draw(txt_l)
    y = pad
    for (txt, f, tr, gap), (w, h, _) in zip(lines, sizes):
        x = (tw - w) / 2
        for c in txt: d.text((x, y), c, font=f, fill=255); x += f.getlength(c) + tr
        y += h + gap
    shadow = txt_l.filter(ImageFilter.GaussianBlur(22)).point(lambda v: int(v * 0.55))
    sh2 = Image.new('L', (tw, th), 0); sh2.paste(shadow, (0, 8))
    img = Image.new('RGBA', (tw, th), (0, 0, 0, 0))
    img.paste((0, 0, 0, 255), mask=sh2)
    img.paste((255, 255, 255, 255), mask=txt_l)
    p = f'{B}/text/{name}.png'; img.save(p)
    return p, CX - tw // 2, cy - th // 2

TEXTS = [  # (png info, t_in, t_out)
    (card('hook', [('Kalau kau kat sini,', font(BAR, 190), 0, 10), ('kau teruskan tak?', font(BAR, 190), 0, 0)], 1450), 0.30, 3.80),
    (card('surabaya', [('Semuanya bermula di Surabaya.', font(BAR, 138), 0, 0)], 2700), 6.60, 10.90),
    (card('lbl_cp7', [('Basecamp  →  CP7', font(DMS, 66, True), 4, 0)], 2860), 14.15, 17.00),
    (card('lbl_camp', [('CP7  ·  Campsite', font(DMS, 66, True), 4, 0)], 2860), 24.10, 27.60),
    (card('lbl_push', [('04:57  ·  Menuju puncak', font(DMS, 66, True), 4, 0)], 2860), 30.10, 33.60),
    (card('title', [('GUNUNG RAUNG', font(BAR, 290), 6, 0)], 1250), 45.35, 54.60),
    (card('subtitle', [('Jawa Timur, Indonesia', font(DMS, 84, True), 10, 0)], 1455), 45.95, 54.60),
    (card('day1', [('Hari 1  •  Kuala Lumpur ke Surabaya', font(BAR, 112), 0, 0)], 2760), 57.85, 60.00),
]
if ONLY_TEXT:
    print(json.dumps([(p, x, y, a, b) for (p, x, y), a, b in TEXTS], indent=1)); raise SystemExit

# ---------- 3. final composite + audio mix ----------
inp = ['-i', f'{B}/assembled.mkv', '-i', f'{B}/score.wav']
fc = []; last = '0:v'
RISE, FIN, FOUT = 46, 0.6, 0.35
for k, ((p, x, y), a, b) in enumerate(TEXTS):
    inp += ['-loop', '1', '-framerate', str(FPS), '-t', '60', '-i', p]
    j = k + 2
    fo = '' if b >= 59.99 else f",fade=t=out:st={b - FOUT}:d={FOUT}:alpha=1"
    fc.append(f"[{j}:v]format=rgba,fade=t=in:st={a}:d={FIN}:alpha=1{fo}[t{k}]")
    yexpr = f"{y}+{RISE}*pow(1-min(1\\,max(0\\,(t-{a})/{FIN}))\\,3)"
    fc.append(f"[{last}][t{k}]overlay=x={x}:y='{yexpr}':enable='between(t,{a},{b})':eval=frame[v{k}]")
    last = f'v{k}'
fc.append(f"[{last}]format=yuv420p[vout]")
fc.append("[0:a]aformat=channel_layouts=stereo:sample_rates=48000[nat];[1:a]volume=0.80[mus];"
          "[nat][mus]amix=inputs=2:normalize=0:duration=first[mix]")
# two-pass loudnorm to -14 LUFS / -1.5 dBTP
pre = run(['ffmpeg', '-hide_banner', *inp[:4], '-filter_complex', fc[-1] + ";[mix]loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json",
           '-vn', '-f', 'null', '-'])
m = json.loads(re.search(r'\{[^{}]*"input_i"[^{}]*\}', pre.stderr).group(0))
ln = (f"loudnorm=I=-14:TP=-1.5:LRA=11:linear=true:measured_I={m['input_i']}:measured_TP={m['input_tp']}"
      f":measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}")
fc[-1] += f";[mix]{ln},aresample=48000[aout]"
out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else f'{B}/raung_trailer_2160x3840.mp4'
run(['ffmpeg', '-y', '-v', 'error', *inp, '-filter_complex', ';'.join(fc), '-map', '[vout]', '-map', '[aout]',
     '-t', '60', '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-profile:v', 'high', '-level', '5.1',
     '-pix_fmt', 'yuv420p', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709',
     '-r', str(FPS), '-c:a', 'aac', '-b:a', '320k', '-movflags', '+faststart', out])
print('wrote', out)
