from prepare import *
from PIL import Image,ImageDraw,ImageFont
import subprocess,re
FF='/opt/d2s-recovery/envs/navsim4s_v2/lib/python3.10/site-packages/imageio_ffmpeg/binaries/ffmpeg-linux64-v4.2.2'

def main():
 media=read(O/'data/media_index.json');montages=read(O/'data/montages.json');checks=[]
 for c in media+montages:
  p=O/c['mp4'];r=subprocess.run([FF,'-hide_banner','-v','error','-threads','2','-i',str(p),'-f','null','-'],capture_output=True,text=True);assert r.returncode==0 and not r.stderr,(p,r.stderr)
  info=subprocess.run([FF,'-hide_banner','-i',str(p)],capture_output=True,text=True).stderr;assert 'h264' in info and '1920x1080' in info and '30 fps' in info
  if 'gif' in c:
   im=Image.open(O/c['gif']);assert im.n_frames==c['physical_states'];assert len(c['physical_times_s'])==c['physical_states'];assert abs(c['physical_times_s'][-1]-c['horizon_s'])<1e-9;assert c['sample_sequence']==sorted(c['sample_sequence']);assert set(c['sample_sequence'])==set(range(c['physical_states']));assert c['camera_count']==3 and c['map_status']=='MAP_AVAILABLE';assert sha(p)==c['mp4_sha256']
  checks.append({'file':c['mp4'],'decode':'PASS','codec':'H264','dimensions':'1920x1080','fps':30,'physical_states':c.get('physical_states'),'sha256':sha(p)})
  print('DECODE PASS',p.name,c.get('run_id',c.get('model')),flush=True)
 source=read(O/'data/run_sources.json');unique={v['path']:v['sha256'] for v in source.values()};source_checks=[]
 for p,h in unique.items():assert sha(local(p))==h;source_checks.append({'path':p,'sha256':h,'unchanged':True})
 cases=read(O/'data/cases.json');camera={cam['source_path']:cam for c in cases for cam in c['cameras']}
 for p,c in camera.items():assert sha(local(p))==c['sha256']==sha(O/c['path'])
 for c in cases:assert sha(O/c['map_path'])==c['map_sha256'];assert sha(O/c['result_path'])==c['source_sha256']
 save(O/'validation/media_validation.json',{'status':'PASS','mp4_decoded':len(checks),'individual_mp4':len(media),'gif_verified':len(media),'montages':len(montages),'real_map_runs':len(media),'verified_real_t0_images':len(camera),'frame_interpolation':False,'simulation_rerun':False,'records':checks})
 save(O/'validation/source_unchanged.json',{'status':'PASS','view_scene_sources':len(source),'unique_source_paths':len(unique),'camera_source_hashes':len(camera),'records':source_checks})
 font=ImageFont.truetype('/mnt/c/Windows/Fonts/segoeui.ttf',18)
 sheet=Image.new('RGB',(1920,math.ceil(len(media)/4)*305),'#0a101a');d=ImageDraw.Draw(sheet)
 for j,c in enumerate(media):
  x=j%4*480;y=j//4*305;im=Image.open(O/c['poster']).resize((480,270));sheet.paste(im,(x,y));d.text((x+8,y+273),c['model']+f" {c['horizon_s']:g}s "+c['token'][:8],font=font,fill='#dce7f5')
 sheet.save(O/'validation/all_38_posters.jpg',quality=95)
 print('MEDIA VALIDATION PASS',len(checks),flush=True)
if __name__=='__main__':main()
