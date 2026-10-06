"""Decode every revised MP4 and verify real timing, saved states and old evidence."""
import json,subprocess,re,bisect,datetime
from pathlib import Path
from PIL import Image
from prepare_dynamic import ROOT,OLD,NEW,read,save,sha,local

FF='/opt/d2s-recovery/envs/navsim4s_v2/lib/python3.10/site-packages/imageio_ffmpeg/binaries/ffmpeg-linux64-v4.2.2'

def main():
 media=read(NEW/'data/media_index.json');original={r['run_id']:r for r in read(OLD/'data/media_index.json')};montages=read(NEW/'data/montages.json');manifest=read(NEW/'data/camera_playback_manifest.json');checks=[];states=0;selections=0;changed_images=[]
 for r in media:
  o=original[r['run_id']]
  for k in o:
   if k in ['mp4_sha256','camera_status']:continue
   assert r[k]==o[k],(r['run_id'],'original receipt field changed',k)
  assert r['camera_renderer_sha256']==sha(Path(__file__).parent/'render_dynamic.py')
  assert r['camera_only_pixel_checks']==r['physical_states'];states+=r['camera_only_pixel_checks']
  assert all(abs(t-i/10)<1e-9 for i,t in enumerate(r['physical_times_s']))
  assert sha(NEW/r['contact_records'])==sha(OLD/r['contact_records'])
  im=Image.open(NEW/r['gif']);assert im.n_frames==r['physical_states'];im.close()
  for cam,selected in r['camera_selection'].items():
   assert len(selected)==r['physical_states'];ff=manifest[r['token']]['views'][cam]['frames'];tt=[f['relative_capture_s'] for f in ff]
   unique=set()
   for s in selected:
    ix=bisect.bisect_right(tt,s['physical_t_s']+1e-10)-1;f=ff[ix]
    assert s['frame']==f['path'] and s['frame_sha256']==f['sha256'];assert -1e-9<=s['age_s']<=.5
    assert abs(s['physical_t_s']-s['capture_t_s']-s['age_s'])<1e-9;unique.add(s['frame_sha256']);selections+=1
   assert len(unique)>=6,(r['run_id'],cam,'Camera not advancing');changed_images.append({'run_id':r['run_id'],'camera':cam,'distinct_real_images':len(unique)})
 for r in media+montages:
  p=NEW/r['mp4'];proc=subprocess.run([FF,'-hide_banner','-v','error','-threads','2','-i',str(p),'-f','null','-'],capture_output=True,text=True);assert proc.returncode==0 and not proc.stderr,(p,proc.stderr)
  info=subprocess.run([FF,'-hide_banner','-i',str(p)],capture_output=True,text=True).stderr
  assert 'h264' in info and '1920x1080' in info and '30 fps' in info
  rr=[r] if 'run_id' in r else [v for v in media if r['scope'] in v['scopes'] and (r['model']=='all' or r['model']==v['model'])]
  expected=sum(v['encoded_frames'] for v in rr)/30
  mm=re.search(r'Duration: (\d+):(\d+):(\d+\.\d+)',info);assert mm
  duration=int(mm[1])*3600+int(mm[2])*60+float(mm[3]);assert abs(duration-expected)<.035,(p,duration,expected)
  digest=sha(p)
  if 'run_id' in r:assert digest==r['mp4_sha256'] and digest!=r['original_mp4_sha256']
  checks.append({'file':r['mp4'],'decode':'PASS','codec':'H264','dimensions':'1920x1080','fps':30,'duration_s':duration,'expected_duration_s':expected,'sha256':digest})
  print('DYNAMIC DECODE PASS',r.get('run_id',r.get('scope','')+'_'+r.get('model','')),flush=True)
 # Every real camera copy equals its read-only original source; no images are synthesized.
 images=0;unique_sources={}
 for t in manifest.values():
  for view in t['views'].values():
   for f in view['frames']:
    assert sha(NEW/f['path'])==f['sha256'];unique_sources[f['source_path']]=f['sha256'];images+=1
 for p,h in unique_sources.items():assert sha(local(p))==h
 for r in read(NEW/'camera_playback/source_registry.json'):assert sha(local(r['path']))==r['sha256']
 sources=read(NEW/'data/run_sources.json');unique={v['path']:v['sha256'] for v in sources.values()}
 for p,h in unique.items():assert sha(local(p))==h
 original_snapshot=read(NEW/'validation/camera_playback_original_snapshot.json');changed=[];unchanged=[]
 allowed={'index.html','videos.html','research.js','source_register.csv','README_CN_EN.md','MANIFEST_SHA256.txt','validation.json','validation/all_38_posters.jpg',
 'data/meta.json','data/dashboard_data.js','data/media_index.json','data/media_data.js','data/video_index.csv'}
 for s in original_snapshot:
  p=s['path'];assert sha(OLD/p)==s['sha256'],'Previous delivery modified: '+p
  assert (NEW/p).is_file();h=sha(NEW/p)
  if h==s['sha256']:unchanged.append(p);continue
  valid=p in allowed or (p.startswith('media/') and (p.endswith('.mp4') or p.endswith('.gif') or p.endswith('.jpg') or p.endswith('/receipt.json')))
  assert valid,'Unexpected previous artifact changed: '+p;changed.append(p)
 # Numerical data, SVG/PNG figures, controls, maps, saved rollouts, and CSS stay exact.
 a=read(OLD/'data/meta.json');b=read(NEW/'data/meta.json');a.pop('camera_note');b.pop('camera_note');assert a==b
 def dashboard(p):return json.loads(p.read_text(encoding='utf-8').split('=',1)[1].rstrip().rstrip(';'))
 a=dashboard(OLD/'data/dashboard_data.js');b=dashboard(NEW/'data/dashboard_data.js');a['meta'].pop('camera_note');b['meta'].pop('camera_note');assert a==b
 assert sha(OLD/'research.css')==sha(NEW/'research.css')
 figures=[p for p in unchanged if p.startswith('figures/')];data=[p for p in unchanged if p.startswith('data/')]
 out={'status':'PASS','generated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'mp4_decoded':len(checks),'individual_mp4':len(media),'gif_verified':len(media),'montages':len(montages),'real_map_runs':len(media),
 'physical_state_checks':states,'camera_alignment_checks':selections,'real_images_copied':images,'unique_original_image_sources':len(unique_sources),'source_execution_files_unchanged':len(unique),'old_delivery_files_unchanged':len(original_snapshot),'new_copy_untouched_original_files':len(unchanged),'unchanged_figure_assets':len(figures),'unchanged_data_files':len(data),
 'css_unchanged':True,'all_numerical_dashboard_data_unchanged':True,'raw_render_change_scope':'Only x=24..478, y=76..1049 camera panel; outside pixels checked exactly at every physical state','simulation_rerun':False,'vla_inference':False,'frame_interpolation':False,'camera_native_rate':'approximately 2 Hz; latest capture <= physical time; hold between exposures','maximum_real_image_age_s':max(s['age_s'] for r in media for v in r['camera_selection'].values() for s in v),'recorded_view_not_model_view':True,'records':checks,'camera_advancement':changed_images,'changed_original_copy_paths':changed}
 save(NEW/'validation/camera_playback_validation.json',out)
 print('CAMERA PLAYBACK VALIDATION PASS',len(checks),'MP4',states,'states',selections,'alignments',len(original_snapshot),'original files protected',flush=True)

if __name__=='__main__':main()
