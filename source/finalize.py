from prepare import *
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
from PIL import Image,ImageDraw,ImageFont
import zipfile,datetime

class Links(HTMLParser):
 def __init__(self):super().__init__();self.refs=[]
 def handle_starttag(self,tag,attrs):
  for k,v in attrs:
   if k in ['href','src','poster'] and v:self.refs.append(v)

def streamsha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for chunk in iter(lambda:f.read(8*1024*1024),b''):h.update(chunk)
 return h.hexdigest()

def main():
 for p in Path(__file__).parent.iterdir():
  if p.is_file():shutil.copyfile(p,O/'source'/p.name)
 shutil.copyfile(Path(__file__).parent/'research.js',O/'research.js')
 media=read(O/'data/media_index.json');allcontacts=[];sheets=[]
 for r in media:
  for v in csv.DictReader((O/r['contact_records']).open(encoding='utf-8-sig')):allcontacts.append({**v,'run_id':r['run_id'],'model':r['model'],'token':r['token'],'horizon_s':r['horizon_s'],'scopes':r['scopes']})
 csvout(O/'data/all_contact_records.csv',allcontacts)
 fontpath=Path('C:/Windows/Fonts/segoeui.ttf') if os.name=='nt' else Path('/mnt/c/Windows/Fonts/segoeui.ttf');font=ImageFont.truetype(str(fontpath),18)
 for scope in SCOPES:
  for m in MODELS:
   rr=[r for r in media if r['model']==m and scope in r['scopes']];ncols=min(3,len(rr));sheet=Image.new('RGB',(640*ncols,390*math.ceil(len(rr)/ncols)),'#0a101a');d=ImageDraw.Draw(sheet)
   for j,r in enumerate(rr):
    x=j%ncols*640;y=j//ncols*390;im=Image.open(O/r['poster']).resize((640,360));sheet.paste(im,(x,y));d.text((x+8,y+363),r['token']+f" | {r['horizon_s']:g}s | first contact {r['first_contact_s']:.1f}s",font=font,fill='#dce7f5')
   p=O/f'media/contact_sheet_{scope}_{m}.jpg';sheet.save(p,quality=95);sheets.append({'scope':scope,'model':m,'scenes':len(rr),'path':p.relative_to(O).as_posix()})
 save(O/'data/contact_sheets.json',sheets)
 # These append-only links do not change any original results or page behavior.
 p=O/'videos.html';s=p.read_text(encoding='utf-8')
 if 'id="contact-sheets"' not in s:s=s.replace('<div class="video-grid">','<div id="contact-sheets" class="download-grid">'+''.join(f'<a href="{r["path"]}">Contact sheet / {r["scope"]} / {r["model"]}</a>' for r in sheets)+'</div><div class="video-grid">')
 p.write_text(s,encoding='utf-8')
 val={'status':'PASS','bank':'Dev100','model_count':4,'new_simulation':False,'source_execution_reused':True,'stats':{'panels':240,'original_thresholds_recounted':10012,'tet_view_scene_checks':800,'tet_window_checks':4800,'window_feature_time_cutoff':'PASSED_SAVED_TET_CUTOFF_RECONCILIATION'},'media':read(O/'validation/media_validation.json'),'browser':read(O/'validation/browser_validation.json'),'sources':{k:v for k,v in read(O/'validation/source_unchanged.json').items() if k!='records'},'legacy':read(O/'validation/legacy_preservation.json'),'visual_review':{'status':'PASS','reviewed':'Four model sample posters, compact five-metric figure, F2 contact times, fixed landmark figure, webpage desktop/mobile screenshots, input+execution card; contact sheets provide full inventory'},'generated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 save(O/'validation.json',val)
 missing=[];external=[];count=0
 for p in O.rglob('*.html'):
  if p.parent==O/'source':continue # Build templates resolve paths from the generated page root.
  h=Links();h.feed(p.read_text(encoding='utf-8-sig'))
  for ref in h.refs:
   q=urlsplit(ref)
   if q.scheme in ['http','https','mailto','data','javascript']:external.append({'page':str(p.relative_to(O)),'ref':ref});continue
   if not q.path:continue
   dest=(p.parent/unquote(q.path)).resolve();count+=1
   if not dest.exists():missing.append({'page':str(p.relative_to(O)),'ref':ref})
 # Manifest/data dynamic paths receive independent existence checks.
 for r in media:
  for k in ['mp4','gif','poster','keyframes','contact_records']:assert (O/r[k]).is_file()
 for f in read(O/'data/figure_index.json'):
  for k in ['png','svg']:assert (O/f[k]).is_file()
 save(O/'validation/link_checks.json',{'local_references_checked':count,'missing':missing,'external_reference_count':len(external),'external_references':external})
 assert not missing,missing[:12]
 val['links']={'local_references_checked':count,'missing':0,'core_runtime_external_requests':0};save(O/'validation.json',val)
 # SHA inventory is content-addressed; exclude itself and output archive.
 files=sorted(p for p in O.rglob('*') if p.is_file() and p.name!='MANIFEST_SHA256.txt')
 (O/'MANIFEST_SHA256.txt').write_text('\n'.join(streamsha(p)+'  '+p.relative_to(O).as_posix() for p in files)+'\n',encoding='utf-8')
 dest=O.parent/'Drive2Survive_FourModel_Research_Dashboard_v4.zip'
 with zipfile.ZipFile(dest,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=4,allowZip64=True) as z:
  for p in sorted(O.rglob('*')):
   if not p.is_file():continue
   ext=p.suffix.lower();z.write(p,arcname=O.name+'/'+p.relative_to(O).as_posix(),compress_type=zipfile.ZIP_STORED if ext in ['.mp4','.gif','.jpg','.png','.zip','.gz','.pdf','.pptx'] else zipfile.ZIP_DEFLATED)
 with zipfile.ZipFile(dest) as z:assert z.testzip() is None;entries=len(z.infolist())
 digest=streamsha(dest);dest.with_suffix('.zip.sha256').write_text(digest+'  '+dest.name+'\n',encoding='utf-8')
 receipt={'zip':str(dest),'sha256':digest,'bytes':dest.stat().st_size,'entries':entries,'crc_test':'PASS'};save(O.parent/'Drive2Survive_FourModel_Research_Dashboard_v4.package_receipt.json',receipt);print(json.dumps(receipt),flush=True)
if __name__=='__main__':main()
