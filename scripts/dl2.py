import gdown, os, sys, subprocess
out=sys.argv[1]
fs=gdown.download_folder('https://drive.google.com/drive/folders/1yWzfc9qu4KY59KxwPCjwI6DYc9YLd0pB', skip_download=True, quiet=True)
for f in fs:
    base=os.path.basename(f.path); stem,ext=os.path.splitext(base)
    pre='REF_' if f.path.startswith('Reference') else ''
    dst=os.path.join(out, f"{pre}{stem}__{f.id[:6]}{ext}")
    if os.path.exists(dst) and os.path.getsize(dst)>100000: continue
    url=f"https://drive.usercontent.google.com/download?id={f.id}&export=download&confirm=t"
    for i in range(4):
        r=subprocess.run(["curl","-sS","-L","--fail","-o",dst,url])
        if r.returncode==0: break
    print("done", dst, os.path.getsize(dst) if os.path.exists(dst) else -1, flush=True)
