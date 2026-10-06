"""Read real local camera sequences; create a video-only revision of the v4 page."""
from pathlib import Path
import os,json,hashlib,shutil,sqlite3,csv,bisect,pickle,datetime
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
OLD=ROOT/'outputs/multivla_research_dashboard_v4_en'
NEW=ROOT/'outputs/multivla_research_dashboard_v4_camera_playback_v1'
E=Path('E:/Drive2Survive_Recovery_20260908') if os.name=='nt' else Path('/mnt/e/Drive2Survive_Recovery_20260908')
NUPLAN=Path('E:/nuplan_local') if os.name=='nt' else Path('/mnt/e/nuplan_local')
CAMERAS=['CAM_L1','CAM_F0','CAM_R1']
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def save(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,allow_nan=False,indent=2),encoding='utf-8')
def local(p):
 p=str(p).replace('\\','/')
 if os.name=='nt' and p.startswith('/mnt/'):return Path(p[5].upper()+':/'+p[7:])
 if os.name!='nt' and len(p)>2 and p[1]==':':return Path('/mnt/'+p[0].lower()+p[2:])
 return Path(p)

def main():
 cases=read(OLD/'data/cases.json');tokens={}
 for c in cases:
  t=c['token'];tokens.setdefault(t,dict(token=t,log_name=c['cameras'][0]['relative_path'].split('/')[0],t0_us=int(c['cameras'][0]['timestamp_us']),max_horizon_s=c['horizon_s'],cameras=c['cameras']));tokens[t]['max_horizon_s']=max(tokens[t]['max_horizon_s'],c['horizon_s'])
 NEW.mkdir(parents=True,exist_ok=True)
 (NEW/'camera_playback').mkdir(exist_ok=True)
 dbs={};sources=[];manifest={};perstate=[]
 metaroot=NUPLAN/'vla_workspace/realdata_preflight_v1/downloads/extracted/openscene-v1.1'
 meta_verified=read(E/'analysis/autovla_local_navsim4s_execution_v2/02_data_cache/verified_logs.json')
 for log in {x['log_name'] for x in tokens.values()}:
  p=NUPLAN/f'dataset/nuplan-v1.1/splits/mini/{log}.db';assert p.exists();dbs[log]=sqlite3.connect(p.resolve().as_uri()+'?mode=ro',uri=True)
  sources.append({'role':'Original nuPlan camera exposure timestamps','path':str(p),'sha256':sha(p),'bytes':p.stat().st_size})
  p=metaroot/f'meta_datas/mini/{log}.pkl';assert sha(p)==meta_verified[log]['sha256'];frames=pickle.loads(p.read_bytes());lookup={f['token']:int(f['timestamp']) for f in frames}
  for t in tokens.values():
   if t['log_name']==log:assert lookup[t['token']]==t['t0_us']
  sources.append({'role':'Verified original scene anchor','path':str(p),'sha256':sha(p)})
 roots=[metaroot/'sensor_blobs/mini',NUPLAN/'dataset/nuplan-v1.1/sensor_blobs',NUPLAN/'extracted/mini/data/sets/nuplan/nuplan-v1.1/sensor_blobs']
 try:
  for token,t in tokens.items():
   views={};t0=t['t0_us'];h=t['max_horizon_s']
   for camera in CAMERAS:
    rows=dbs[t['log_name']].execute('SELECT i.timestamp,i.filename_jpg FROM image i JOIN camera c ON c.token=i.camera_token WHERE c.channel=? AND i.timestamp BETWEEN ? AND ? ORDER BY i.timestamp',(camera,t0-600000,t0+int(h*1e6))).fetchall()
    available=[];missing=0
    for stamp,name in rows:
     src=next((r/name for r in roots if (r/name).is_file()),None)
     if src is None:missing+=1;continue
     dest=NEW/'camera_playback'/token/camera/Path(name).name;dest.parent.mkdir(parents=True,exist_ok=True)
     if not dest.exists():shutil.copyfile(src,dest)
     with Image.open(dest) as im:im.verify()
     digest=sha(src);assert sha(dest)==digest
     available.append({'capture_timestamp_us':int(stamp),'relative_capture_s':(int(stamp)-t0)/1e6,'relative_source_path':name,'source_path':str(src),'path':dest.relative_to(NEW).as_posix(),'sha256':digest})
    assert available and len(available)>=int(h*2)+1
    actual=[f['relative_capture_s'] for f in available]
    original=next(c for c in t['cameras'] if c['camera']==camera)
    anchor=next(f for f in available if f['relative_source_path']==original['relative_path']);assert anchor['sha256']==original['sha256'],'Original metadata-linked image must retain its verified bytes'
    # Metadata camera association may have a slightly later exposure than lidar t0.
    # The playback uses actual exposure times and holds the latest prior capture.
    for c in [c for c in cases if c['token']==token]:
     for i in range(int(c['horizon_s']*10)+1):
      tick=i/10;ix=bisect.bisect_right(actual,tick+1e-10)-1;assert ix>=0;f=available[ix];age=tick-f['relative_capture_s'];assert -1e-9<=age<=.6,(token,camera,tick,age)
      perstate.append({'run_id':c['run_id'],'token':token,'camera':camera,'physical_t_s':tick,'source_capture_s':f['relative_capture_s'],'source_age_s':age,'file':f['path'],'source_sha256':f['sha256']})
    views[camera]={'frames':available,'available_count':len(available),'unavailable_db_frames':missing,'native_available_period_s':sorted(round(b-a,6) for a,b in zip(actual,actual[1:])),'selection_rule':'Latest real capture <= displayed physical time; repeat until next real frame; no interpolation','last_capture_s':actual[-1],'original_metadata_linked_anchor_capture_s':anchor['relative_capture_s']}
   manifest[token]={k:v for k,v in t.items() if k!='cameras'};manifest[token]['views']=views
   print('CAMERA TIMELINE PASS',token,[(c,views[c]['available_count']) for c in CAMERAS],flush=True)
 finally:
  for con in dbs.values():con.close()
 save(NEW/'data/camera_playback_manifest.json',manifest);save(NEW/'camera_playback/source_registry.json',sources)
 with (NEW/'camera_playback/physical_time_alignment.csv').open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,perstate[0].keys());w.writeheader();w.writerows(perstate)
 # Full real copies prevent edits of a hardlinked file from changing the previous delivery.
 for p in OLD.rglob('*'):
  if not p.is_file():continue
  dest=NEW/p.relative_to(OLD);dest.parent.mkdir(parents=True,exist_ok=True)
  if not dest.exists():shutil.copyfile(p,dest)
 protect=[]
 for p in OLD.rglob('*'):
  if p.is_file():protect.append({'path':p.relative_to(OLD).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size})
 save(NEW/'validation/camera_playback_original_snapshot.json',protect)
 save(NEW/'validation/camera_playback_preparation.json',{'status':'PASS','scene_tokens':len(tokens),'camera_views':len(tokens)*3,'real_images':sum(v['available_count'] for t in manifest.values() for v in t['views'].values()),'physical_alignment_rows':len(perstate),'max_age_s':max(r['source_age_s'] for r in perstate),'native_available_frequency':'approximately 2 Hz; no fabricated intermediate images','logged_ego_vs_model_ego':'Original recorded camera viewpoint; BEV retains model-specific saved execution','source_hashes':sources})
 print('PREPARE PASS',len(tokens),'SCENES',len(perstate),'ALIGNMENTS',flush=True)
if __name__=='__main__':main()
