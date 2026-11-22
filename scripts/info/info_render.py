"""Render the 30 s info video: background shots -> assemble -> overlay (piped RGBA) + audio mix -> 4K MP4."""
import glob, json, math, os, re, subprocess, sys
from PIL import Image, ImageOps

S = '/tmp/claude-0/-home-user-raungcamp/b0706bff-2b10-5382-a9f0-3081491f33ef/scratchpad'
B = f'{S}/build3'; os.makedirs(f'{B}/shots', exist_ok=True)
W, H, FPS = 2160, 3840, 30
exec(open(f'{S}/scripts/info_shots.py').read())   # defines SHOTS

def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode: print(r.stderr[-3000:]); raise SystemExit(1)
    return r

GRADE = "curves=all='0/0 0.25/0.245 0.6/0.61 0.85/0.83 1/0.95',eq=contrast=1.03:saturation={sat}"
for i, (a, b, pre, si, fl) in enumerate(SHOTS):
    NF = round(b * FPS) - round(a * FPS); D = NF / FPS
    out = f'{B}/shots/{i:02d}.mkv'
    if os.path.exists(out) and os.path.getsize(out) > 0: continue
    src = glob.glob(f'{S}/raw/{pre}*')[0]
    sat = 0.96 if pre.startswith(('IMG_0001', 'IMG_9982', 'IMG_0056')) else 1.04
    codecs = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'a', '-show_entries', 'stream=codec_name',
                             '-of', 'csv=p=0', src], capture_output=True, text=True).stdout.split()
    amap = f"0:a:{codecs.index('aac')}"
    inputs = ['-ss', str(si), '-t', str(D + 0.1), '-i', src]
    m = subprocess.run(['ffmpeg', '-hide_banner', '-ss', str(si), '-t', str(D), '-i', src, '-map', amap,
                        '-af', 'volumedetect', '-f', 'null', '-'], capture_output=True, text=True).stderr
    mv = float(re.search(r'mean_volume: (-?[\d.]+)', m).group(1))
    g_db = max(-12, min(12, -26 - mv)) + 20 * math.log10(fl.get('nat', 0.3))
    af = f"volume={g_db:.2f}dB,afade=t=in:d=0.03,afade=t=out:st={D-0.04}:d=0.04"
    vf = f"scale={W}:{H}:flags=lanczos"
    if 'crop' in fl:
        cx, cy, f = fl['crop']; cw = int(W / f) // 2 * 2; ch = int(H / f) // 2 * 2
        vf += f",crop={cw}:{ch}:{max(0, min(W-cw, cx-cw//2))}:{max(0, min(H-ch, cy-ch//2))},scale={W}:{H}:flags=lanczos"
    if fl.get('zoom'):
        vf += (f",scale=w='trunc({W}*(1+0.05*t/{D})/2)*2':h='trunc({H}*(1+0.05*t/{D})/2)*2'"
               f":eval=frame:flags=bicubic,crop={W}:{H}")
    vf += f",fps={FPS}," + GRADE.format(sat=sat)
    if fl.get('dim'):   # background for map / data cards: blurred + darkened
        vf += f",gblur=sigma=28,eq=brightness=-0.30:saturation=0.55:contrast=0.9"
    vf += ",setsar=1,format=yuv420p"
    run(['ffmpeg', '-y', '-v', 'error', *inputs, '-map', '0:v:0', '-map', amap, '-vf', vf,
         '-af', af + ',aresample=48000,aformat=channel_layouts=stereo', '-t', str(D), '-frames:v', str(NF),
         '-c:v', 'libx264', '-preset', 'fast', '-crf', '12', '-c:a', 'pcm_s16le', out])
    print('shot', i, pre, NF, flush=True)

with open(f'{B}/list.txt', 'w') as f:
    for i in range(len(SHOTS)): f.write(f"file '{B}/shots/{i:02d}.mkv'\n")
run(['ffmpeg', '-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', f'{B}/list.txt', '-c', 'copy', f'{B}/assembled.mkv'])

# audio: nat + score, two-pass loudnorm
mixf = ("[0:a]aformat=channel_layouts=stereo:sample_rates=48000[nat];[1:a]volume=0.85[mus];"
        "[nat][mus]amix=inputs=2:normalize=0:duration=first[mix]")
pre = run(['ffmpeg', '-hide_banner', '-i', f'{B}/assembled.mkv', '-i', f'{B}/score_info.wav', '-filter_complex',
           mixf + ";[mix]loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", '-vn', '-f', 'null', '-'])
m = json.loads(re.search(r'\{[^{}]*"input_i"[^{}]*\}', pre.stderr).group(0))
ln = (f"loudnorm=I=-14:TP=-1.5:LRA=11:linear=true:measured_I={m['input_i']}:measured_TP={m['input_tp']}"
      f":measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}")
run(['ffmpeg', '-y', '-v', 'error', '-i', f'{B}/assembled.mkv', '-i', f'{B}/score_info.wav', '-filter_complex',
     mixf + f";[mix]{ln},aresample=48000[aout]", '-map', '[aout]', '-c:a', 'pcm_s16le', f'{B}/audio.wav'])

# overlay composite: python writes raw RGBA frames into ffmpeg
out = f'{B}/info_master_2160x3840.mp4'
ov = subprocess.Popen([sys.executable, '-I', f'{S}/scripts/info_overlay.py'], stdout=subprocess.PIPE)
run(['ffmpeg', '-y', '-v', 'error', '-i', f'{B}/assembled.mkv', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', f'{W}x{H}',
     '-r', str(FPS), '-i', 'pipe:0', '-i', f'{B}/audio.wav',
     '-filter_complex', '[0:v][1:v]overlay=0:0:format=auto,format=yuv420p[v]', '-map', '[v]', '-map', '2:a',
     '-t', '30', '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-profile:v', 'high', '-level', '5.1',
     '-pix_fmt', 'yuv420p', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709',
     '-r', str(FPS), '-c:a', 'aac', '-b:a', '320k', '-movflags', '+faststart', out], stdin=ov.stdout)
ov.wait(); print('wrote', out)
