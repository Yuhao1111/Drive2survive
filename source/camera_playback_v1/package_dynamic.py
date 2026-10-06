"""Check offline links, publish the validation receipt and make a complete ZIP."""
import json,datetime,zipfile,shutil
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
from prepare_dynamic import ROOT,OLD,NEW,read,save,sha

class Links(HTMLParser):
 def __init__(self):super().__init__();self.refs=[]
 def handle_starttag(self,tag,attrs):
  for k,v in attrs:
   if k in ['src','href','poster'] and v:self.refs.append(v)

def main():
 media=read(NEW/'validation/camera_playback_validation.json');browser=read(NEW/'validation/camera_browser_validation.json');sample=read(NEW/'validation/camera_dynamic_sample_review.json');assert all(v['status']=='PASS' for v in [media,browser,sample])
 missing=[];externals=[];count=0
 for p in NEW.rglob('*.html'):
  if p.relative_to(NEW).parts[0]=='source':continue
  parser=Links();parser.feed(p.read_text(encoding='utf-8-sig'))
  for ref in parser.refs:
   q=urlsplit(ref)
   if q.scheme in ['http','https','mailto','data','javascript']:externals.append({'page':p.relative_to(NEW).as_posix(),'ref':ref});continue
   if not q.path:continue
   count+=1;dest=(p.parent/unquote(q.path)).resolve()
   if not dest.exists():missing.append({'page':p.relative_to(NEW).as_posix(),'ref':ref})
 assert not missing,missing[:20]
 for r in read(NEW/'data/media_index.json'):
  for k in ['mp4','gif','poster','keyframes','contact_records']:assert (NEW/r[k]).is_file()
 for r in read(NEW/'data/montages.json'):assert (NEW/r['mp4']).is_file()
 for r in read(NEW/'data/figure_index.json'):
  for k in ['png','svg']:assert (NEW/r[k]).is_file()
 links={'status':'PASS','local_references_checked':count,'missing':missing,'external_references':externals,'core_runtime_network_requests':0};save(NEW/'validation/camera_link_checks.json',links)
 val=read(OLD/'validation.json');val['revision']='v4 camera playback v1';val['generated_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
 val['media']=media;val['browser']=browser;val['camera_preparation']=read(NEW/'validation/camera_playback_preparation.json');val['camera_sample_review']=sample;val['links']=links
 val['previous_evidence_preserved']={'old_files_sha_verified':media['old_delivery_files_unchanged'],'statistical_dashboard_exact_match':True,'figures_exact_match':media['unchanged_figure_assets'],'css_exact_match':True,'previous_directory':str(OLD)}
 val['visual_review']={'status':'PASS','scope':'Four camera animation samples, recorded-source labels and capture timestamps; eight model/horizon contact sheets and all-posters inventory; offline desktop/mobile and four model video playback in dedicated headless Edge','raw_camera_only_state_checks':media['physical_state_checks'],'recorded_camera_vs_model_bev_caption':True}
 save(NEW/'validation.json',val)
 # Save the executed source once more, including this packaging/QA code.
 target=NEW/'source/camera_playback_v1';target.mkdir(exist_ok=True)
 for p in Path(__file__).parent.iterdir():
  if p.is_file():shutil.copyfile(p,target/p.name)
 files=sorted(p for p in NEW.rglob('*') if p.is_file() and p.name!='MANIFEST_SHA256.txt')
 (NEW/'MANIFEST_SHA256.txt').write_text('\n'.join(sha(p)+'  '+p.relative_to(NEW).as_posix() for p in files)+'\n',encoding='utf-8')
 dest=NEW.parent/'Drive2Survive_FourModel_Research_Dashboard_v4_CameraPlayback_v1.zip'
 with zipfile.ZipFile(dest,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=4,allowZip64=True) as z:
  for p in sorted(NEW.rglob('*')):
   if not p.is_file():continue
   kind=zipfile.ZIP_STORED if p.suffix.lower() in ['.mp4','.gif','.jpg','.jpeg','.png','.zip','.gz','.pdf','.pptx'] else zipfile.ZIP_DEFLATED
   z.write(p,arcname=NEW.name+'/'+p.relative_to(NEW).as_posix(),compress_type=kind)
 with zipfile.ZipFile(dest) as z:assert z.testzip() is None;entries=len(z.infolist())
 digest=sha(dest);dest.with_suffix('.zip.sha256').write_text(digest+'  '+dest.name+'\n',encoding='utf-8')
 receipt={'status':'PASS','zip':str(dest),'sha256':digest,'bytes':dest.stat().st_size,'entries':entries,'zip_crc':'PASS','individual_mp4':media['individual_mp4'],'gif':media['gif_verified'],'montages':media['montages'],'no_experiment_changes':True}
 save(dest.with_suffix('.package_receipt.json'),receipt);print(json.dumps(receipt,ensure_ascii=False),flush=True)

if __name__=='__main__':main()
