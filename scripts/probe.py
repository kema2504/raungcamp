import json, subprocess, sys, os
for fn in sorted(os.listdir(sys.argv[1])):
    p=os.path.join(sys.argv[1],fn)
    if fn.lower().endswith('.jpg'): print(fn,'PHOTO'); continue
    j=json.loads(subprocess.run(['ffprobe','-v','error','-print_format','json','-show_streams','-show_format',p],capture_output=True,text=True).stdout or '{}')
    if not j: print(fn,'UNREADABLE'); continue
    v=[s for s in j['streams'] if s['codec_type']=='video'][0]
    a=[s for s in j['streams'] if s['codec_type']=='audio']
    rot=next((sd.get('rotation') for sd in v.get('side_data_list',[]) if 'rotation' in sd),0)
    tags=j['format'].get('tags',{})
    print(f"{fn:28s} {float(j['format']['duration']):6.1f}s {v['codec_name']} {v['width']}x{v['height']} rot={rot} fps={v['r_frame_rate']} trc={v.get('color_transfer')} audio={len(a)} date={tags.get('com.apple.quicktime.creationdate',tags.get('creation_time'))} model={tags.get('com.apple.quicktime.model')}")
