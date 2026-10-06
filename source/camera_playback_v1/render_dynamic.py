"""Revise only the camera pixels of the existing saved-state renderer."""
import sys,os,math,json,bisect,subprocess,argparse
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageOps
from prepare_dynamic import ROOT,OLD,NEW,read,save,sha
sys.path.insert(0,str(ROOT/'work/research_v4'))
import render_media as base
base.O=NEW
FF=base.FF
MANIFEST=None

class DynamicScene(base.Scene):
 def __init__(self,c):
  super().__init__(c);self.sequence=MANIFEST[c['token']]['views'];self.image_cache={};self.camera_selections={v:[] for v in self.sequence};self.mask_checks=0
 def frame(self,i):
  original=super().frame(i);im=original.copy();d=ImageDraw.Draw(im);t=self.tt[i]
  d.rectangle((24,76,478,123),fill=base.BG)
  base.tx(d,(24,76),'Recorded camera sequence',24,b=True)
  base.tx(d,(24,105),'Original driving log, time-aligned',15,base.MUTED)
  for j,camera in enumerate(['CAM_L1','CAM_F0','CAM_R1']):
   view=self.sequence[camera];ff=view['frames'];ix=bisect.bisect_right([f['relative_capture_s'] for f in ff],t+1e-10)-1;assert ix>=0;f=ff[ix];age=t-f['relative_capture_s'];assert -1e-9<=age<=.6
   yy=125+j*284;d.rectangle((24,yy,478,yy+274),fill=base.BG);base.tx(d,(24,yy),camera+f" | capture {f['relative_capture_s']:+.2f} s",23,base.MUTED)
   p=NEW/f['path']
   if p not in self.image_cache:
    with Image.open(p) as src:img=ImageOps.contain(src.convert('RGB'),(430,242),Image.Resampling.LANCZOS)
    self.image_cache[p]=img
   img=self.image_cache[p];im.paste(img,(24+(430-img.width)//2,yy+32))
   self.camera_selections[camera].append({'physical_t_s':t,'capture_t_s':f['relative_capture_s'],'age_s':age,'frame':f['path'],'frame_sha256':f['sha256']})
  d.rectangle((24,981,478,1049),fill=base.BG)
  base.tx(d,(24,985),'Recorded scene, not model viewpoint.',21,'#F2C94C')
  base.tx(d,(24,1018),'Real frames only; BEV: saved execution.',20,base.MUTED)
  # In raw render space, every pixel outside the camera panel is unchanged.
  a=np.asarray(original);b=np.asarray(im);diff=np.any(a!=b,axis=2);diff[76:1050,24:479]=False;assert not diff.any(),'Only the camera panel may change'
  self.mask_checks+=1
  return im

def render(c):
 folder=NEW/'media'/c['run_id'];old=read(OLD/f'media/{c["run_id"]}/receipt.json');receipt=folder/'receipt.json'
 if receipt.exists() and read(receipt).get('camera_renderer_sha256')==sha(__file__):return read(receipt)
 sc=DynamicScene(c);frames=[sc.frame(i) for i in range(sc.n)];seq=old['sample_sequence'];assert set(seq)==set(range(sc.n))
 output=folder/'execution.mp4';cmd=[FF,'-y','-hide_banner','-loglevel','error','-f','rawvideo','-vcodec','rawvideo','-s','1920x1080','-pix_fmt','rgb24','-r','30','-i','-','-an','-c:v','libx264','-threads','2','-preset','fast','-crf','22','-pix_fmt','yuv420p','-movflags','+faststart',str(output)]
 proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
 for idx in seq:proc.stdin.write(frames[idx].tobytes())
 proc.stdin.close();assert proc.wait()==0
 gifs=[im.resize((960,540),Image.Resampling.LANCZOS) for im in frames];durations=[270]*sc.n;durations[0]+=500;durations[-1]+=500;durations[c['first_index']]+=1000
 gifs[0].save(folder/'execution.gif',save_all=True,append_images=gifs[1:],duration=durations,loop=0,optimize=False)
 frames[c['first_index']].save(folder/'poster.jpg',quality=94);frames[0].save(folder/'input_and_t0.jpg',quality=94)
 indices=[0,max(0,c['first_index']-1),c['first_index'],sc.n-1];sheet=Image.new('RGB',(1920,1136),base.BG);d=ImageDraw.Draw(sheet)
 for j,idx in enumerate(indices):
  xx=(j%2)*960;yy=(j//2)*568;base.tx(d,(xx+8,yy),['t0','Last pre-contact sample','First contact','Horizon end'][j]+f' | t={sc.tt[idx]:.1f} s',22);sheet.paste(frames[idx].resize((960,540)),(xx,yy+28))
 sheet.save(folder/'four_keyframes.jpg',quality=94)
 rec=dict(old,camera_renderer_sha256=sha(__file__),renderer_sha256=old['renderer_sha256'],mp4_sha256=sha(output),camera_status='REAL_LOGGED_CAMERA_TIMELINE',camera_selection=sc.camera_selections,camera_reference='Recorded original driving, not a rendering of the simulated model ego viewpoint',camera_native_rate='approximately 2 Hz, held between real exposures',camera_source_manifest='data/camera_playback_manifest.json',camera_only_pixel_checks=sc.mask_checks,original_mp4_sha256=old['mp4_sha256'],original_saved_state_sequence_unchanged=True)
 save(receipt,rec);print('DYNAMIC VIDEO PASS',c['run_id'],'states',sc.n,flush=True);return rec

def main():
 global MANIFEST
 p=argparse.ArgumentParser();p.add_argument('--samples',action='store_true');args=p.parse_args();MANIFEST=read(NEW/'data/camera_playback_manifest.json');cases=read(NEW/'data/cases.json')
 if args.samples:
  for m in ['autovla','impromptu','orion','opendrivevla']:render(next(c for c in cases if c['model']==m and 'available_horizon' in c['scopes']))
  return
 assert (NEW/'validation/camera_dynamic_sample_review.json').exists(),'Review the four model samples before full render'
 records=[render(c) for c in cases];save(NEW/'data/media_index.json',records)
 for c in read(NEW/'data/montages.json'):
  rr=[r for r in records if c['scope'] in r['scopes'] and (c['model']=='all' or c['model']==r['model'])];assert len(rr)==c['scenes'];listing=NEW/f'validation/dynamic_concat_{c["scope"]}_{c["model"]}.txt';listing.write_text('\n'.join("file '"+str(NEW/r['mp4'])+"'" for r in rr),encoding='utf-8')
  subprocess.run([FF,'-y','-hide_banner','-loglevel','error','-f','concat','-safe','0','-i',str(listing),'-c','copy','-movflags','+faststart',str(NEW/c['mp4'])],check=True)
 base.csvout(NEW/'data/video_index.csv',[{k:v for k,v in r.items() if k not in ['sample_sequence','physical_times_s','camera_selection']} for r in records])
 print('ALL DYNAMIC VIDEOS',len(records),'MONTAGES',10,flush=True)
if __name__=='__main__':main()
