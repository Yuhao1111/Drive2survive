"""Render only saved states and true t0 images; no model, simulation, or motion interpolation."""
import sys,os,math,json,hashlib,subprocess,argparse,collections
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageOps
import imageio_ffmpeg
from prepare import O,E,read,save,sha,MODELS,NAMES,csvout
sys.path.insert(0,str(E/'work/four_vla_handoff_v3/drive2survive_four_vla_handoff_v3'))
from d2s import metrics as M
FF=imageio_ffmpeg.get_ffmpeg_exe();FONT='/mnt/c/Windows/Fonts/segoeui.ttf';BOLD='/mnt/c/Windows/Fonts/segoeuib.ttf'
BG='#0A101A';FG='#DCE7F5';MUTED='#AAC0DA';PANEL='#141D2B';COLORS=dict(zip(MODELS,['#68BAFF','#49C6B7','#B899FF','#F2C94C']))
FONTS={}
def tx(d,xy,s,n=24,color=FG,b=False,anchor=None):
 key=(n,b)
 if key not in FONTS:FONTS[key]=ImageFont.truetype(BOLD if b else FONT,n)
 d.text(xy,str(s),font=FONTS[key],fill=color,anchor=anchor)
def corners(a):
 u,v=M.axes(a);return [(a['x']+i*a['length']/2*u[0]+j*a['width']/2*v[0],a['y']+i*a['length']/2*u[1]+j*a['width']/2*v[1]) for i,j in [(-1,-1),(1,-1),(1,1),(-1,1)]]
def plot(d,box,values,times,label,color,i,first):
 x,y,w,h=box;d.rounded_rectangle((x,y,x+w,y+h),8,fill=PANEL)
 vals=[v for v in values if v is not None];top=max(vals,default=1);top=max(top,3 if label.startswith('TTC') else .1)*1.1
 tx(d,(x+10,y+7),label,22,b=True);px=x+40;py=y+45;pw=w-53;ph=h-74
 for q in [0,.5,1]:
  yy=py+ph*(1-q);d.line((px,yy,px+pw,yy),fill='#34445B');tx(d,(px-4,yy),f'{q*top:.1f}',15,MUTED,anchor='rm')
 points=[]
 for t,v in zip(times,values):
  if v is None:
   if len(points)>1:d.line(points,fill=color,width=3)
   points=[];continue
  points.append((px+pw*t/times[-1],py+ph*(1-v/top)))
 if len(points)>1:d.line(points,fill=color,width=3)
 xx=px+pw*first/times[-1];d.line((xx,py,xx,py+ph),fill='#FF6677',width=2)
 xx=px+pw*times[i]/times[-1];d.line((xx,py,xx,py+ph),fill='#FFFFFF',width=2)
 for t in range(int(times[-1])+1):tx(d,(px+pw*t/times[-1],py+ph+4),str(t),15,MUTED,anchor='mt')

class Scene:
 def __init__(self,c):
  self.c=c;self.x=read(O/c['result_path']);self.r=self.x['rollout'];self.tt=self.r['times_s'];self.n=len(self.tt);self.ego=self.r['ego'];self.actors=self.r['actors'];self.map=read(O/c['map_path']);self.contacts=[];self.records=[];self.drac=[];self.tit=[0.];self.ttc=[q['ttc_s'] for q in c['timeline']];self.tet=[q['tet_s'] for q in c['timeline']]
  self.speed=[math.hypot(a['vx'],a['vy']) for a in self.ego]
  for i,(ego,actors) in enumerate(zip(self.ego,self.actors)):
   hits=[a for a in actors if M.collision(ego,a)];self.contacts.append({a['id'] for a in hits})
   ds=[(M.drac(ego,a),a['id']) for a in actors];ds=[d for d in ds if d[0] is not None];self.drac.append(max(ds)[0] if ds else None)
   for a in hits:
    angle=(math.atan2(a['y']-ego['y'],a['x']-ego['x'])-ego['heading']+math.pi)%(2*math.pi)-math.pi
    sector='FRONT' if abs(angle)<math.pi/4 else 'REAR' if abs(angle)>3*math.pi/4 else 'LEFT' if angle>0 else 'RIGHT'
    self.records.append({'model':c['model'],'token':c['token'],'run_id':c['run_id'],'horizon_s':self.tt[-1],'time_s':self.tt[i],'actor_id':a['id'],'actor_type':a['type'],'sector':sector})
   if i:self.tit.append(self.tit[-1]+(max(0,3-self.ttc[i]) if self.ttc[i] is not None else 0)*(self.tt[i]-self.tt[i-1]))
  got=[t for t,ids in zip(self.tt,self.contacts) if ids];want=self.x['metrics']['collision_times_s'];assert got==want and abs(got[0]-c['first_contact_s'])<1e-8
  assert abs(self.tit[-1]-self.x['metrics']['tit_s2'])<1e-8
  self.first=next(r for r in self.records if abs(r['time_s']-c['first_contact_s'])<1e-8)
  pr=self.map['projection'];self.origin=pr['origin_world'];self.angle=pr['heading_rad'];local=[self.xy((a['x'],a['y'])) for a in self.ego]
  for i,aa in enumerate(self.actors):
   for a in aa:
    if a['id']==self.first['actor_id']:local.append(self.xy((a['x'],a['y'])))
  xs,ys=zip(*local);spanx=max(32,max(xs)-min(xs)+14);spany=max(35,max(ys)-min(ys)+16);self.center=((max(xs)+min(xs))/2,(max(ys)+min(ys))/2);self.scale=min(870/spanx,540/spany)
  self.bg=Image.new('RGB',(900,580),'#101B2B');self.mapdraw();self.base=Image.new('RGB',(1920,1080),BG);self.base_draw()
 def xy(self,p):
  x,y=p[0]-self.origin[0],p[1]-self.origin[1];h=self.angle
  return math.sin(h)*x-math.cos(h)*y,math.cos(h)*x+math.sin(h)*y
 def screen(self,p):
  x,y=self.xy(p);return 450+(x-self.center[0])*self.scale,290-(y-self.center[1])*self.scale
 def mapdraw(self):
  d=ImageDraw.Draw(self.bg);order={'INTERSECTION':0,'ROADBLOCK':1,'ROADBLOCK_CONNECTOR':2,'LANE':3,'LANE_CONNECTOR':4,'CROSSWALK':5}
  for f in sorted(self.map['features'],key=lambda f:order.get(f['properties']['layer'],9)):
   layer=f['properties']['layer'];g=f['geometry'];polys=[g['coordinates']] if g['type']=='Polygon' else g['coordinates'] if g['type']=='MultiPolygon' else []
   for rings in polys:
    pts=[self.screen(p) for p in rings[0]]
    if not pts:continue
    xx,yy=zip(*pts)
    if max(xx)<0 or min(xx)>900 or max(yy)<0 or min(yy)>580:continue
    color='#2C3A4B' if layer in ['LANE','LANE_CONNECTOR'] else '#354657' if layer=='CROSSWALK' else '#243141'
    d.polygon(pts,fill=color)
    for hole in rings[1:]:d.polygon([self.screen(p) for p in hole],fill='#101B2B')
    if layer in ['LANE','LANE_CONNECTOR','CROSSWALK']:d.line(pts,fill='#68798B',width=1)
  for f in self.map['features']:
   p=f['properties'];bl=p.get('baseline')
   if bl and p.get('trusted_route_id'):d.line([self.screen(q) for q in bl['coordinates']],fill='#3D8590',width=2)
  d.line((20,550,20+10*self.scale,550),fill=FG,width=3);tx(d,(20,514),'10 m',22)
 def base_draw(self):
  d=ImageDraw.Draw(self.base);c=self.c
  title=c['name']+(' AS-RETURNED' if c['model']=='orion' else '')+f" | {self.tt[-1]:.0f} s saved execution"
  tx(d,(24,18),title,42,COLORS[c['model']],True);tx(d,(1890,30),c['token'],28,MUTED,anchor='ra')
  tx(d,(24, eighty:=80),'Verified scene observation at t0',26,b=True);tx(d,(480,80),'Real nuPlan map and executed traffic world',28,b=True)
  for j,cam in enumerate(c['cameras']):
   yy=125+j*284;tx(d,(24,yy),cam['camera']+' | t = 0.0 s',23,MUTED)
   im=Image.open(O/cam['path']).convert('RGB');im=ImageOps.contain(im,(430,242));self.base.paste(im,(24+(430-im.width)//2,yy+32))
  tx(d,(24,985),'Camera images stay at t0.',23,'#F2C94C');tx(d,(24,1018),'No synthetic future camera frames.',22,MUTED)
  tx(d,(480,714),'Blue: ego   Yellow: vehicles   Orange: pedestrians/cyclists   Red outline: current contact',22,MUTED)
  tx(d,(480,747),'Past executed path in blue; road geometry and trusted route come from the local map.',20,MUTED)
  tx(d,(480,1023),'0.1 s physical samples. Slow playback repeats frames. Red lines mark first sampled contact.',22,MUTED)
  tx(d,(480,1051),'ORION native contract: UNRESOLVED. Diagnostic returned labels.' if c['model']=='orion' else 'Contact is sampled OBB touch/overlap. Timeline curves are retrospective context.',20,MUTED)
 def frame(self,i):
  im=self.base.copy();d=ImageDraw.Draw(im);mapim=self.bg.copy();md=ImageDraw.Draw(mapim)
  ids=self.contacts[i];e=self.ego[i]
  for a in self.actors[i]:
   pts=[self.screen(p) for p in corners(a)];col='#F2C94C' if a['type']=='VEHICLE' else '#F2994A' if a['type'] in ['PEDESTRIAN','BICYCLE','CYCLIST'] else '#AAB5C1'
   md.polygon(pts,fill=col);md.line(pts+[pts[0]],fill='#FF6677' if a['id'] in ids else col,width=4 if a['id'] in ids else 1)
  path=[self.screen((a['x'],a['y'])) for a in self.ego[:i+1]]
  if len(path)>1:md.line(path,fill='#68BAFF',width=4)
  pts=[self.screen(p) for p in corners(e)];md.polygon(pts,fill='#2F80ED');md.line(pts+[pts[0]],fill='#FF6677' if ids else '#C7E3FF',width=4)
  ctr=self.screen((e['x'],e['y']));tip=self.screen((e['x']+2*math.cos(e['heading']),e['y']+2*math.sin(e['heading'])));md.line([ctr,tip],fill='white',width=2)
  im.paste(mapim,(480,125));t=self.tt[i];x=1420
  tx(d,(x,129),f'Physical t = {t:.1f} s',35,b=True);tx(d,(x,185),'CONTACT NOW' if ids else 'No contact at this sample',27,'#FF6677' if ids else '#AAC0DA',True)
  tx(d,(x,235),f"First contact: {self.c['first_contact_s']:.1f} s",28,b=True)
  def fmt(v):return f'{v:.2f}' if v is not None else 'N/A'
  current=[('TTC',f'{self.ttc[i]:.2f} s' if self.ttc[i] is not None else '>3 s, right-censored'),('TET',f'{self.tet[i]:.2f} s'),('TIT',f'{self.tit[i]:.2f} s²'),('DRAC',fmt(self.drac[i])+' m/s²'),('Speed',f'{self.speed[i]:.2f} m/s')]
  for j,(k,v) in enumerate(current):tx(d,(x,294+j*54),k,25,MUTED);tx(d,(1890,294+j*54),v,27,anchor='ra')
  tx(d,(x,587),'First contact actor',22,MUTED);tx(d,(x,619),self.first['actor_id'],25);tx(d,(x,653),self.first['actor_type']+' / '+self.first['sector'],24,'#F2C94C')
  for j,(vals,label,col) in enumerate([(self.ttc,'TTC (s)','#68BAFF'),(self.tet,'TET (s)','#49C6B7'),(self.tit,'TIT (s²)','#B899FF'),(self.drac,'DRAC (m/s²)','#F2C94C'),(self.speed,'Speed (m/s)','#A2C5FF')]):plot(d,(480+j*285,792,275,211),vals,self.tt,label,col,i,self.c['first_contact_s'])
  return im

def render(c):
 folder=O/'media'/c['run_id'];folder.mkdir(parents=True,exist_ok=True);receipt=folder/'receipt.json'
 if receipt.exists() and read(receipt).get('renderer_sha256')==sha(__file__):return read(receipt)
 sc=Scene(c);frames=[sc.frame(i) for i in range(sc.n)];seq=[0]*15+[i for i in range(sc.n) for _ in range(8+(30 if i==c['first_index'] else 0))]+[sc.n-1]*15
 output=folder/'execution.mp4';cmd=[FF,'-y','-hide_banner','-loglevel','error','-f','rawvideo','-vcodec','rawvideo','-s','1920x1080','-pix_fmt','rgb24','-r','30','-i','-','-an','-c:v','libx264','-threads','2','-preset','fast','-crf','22','-pix_fmt','yuv420p','-movflags','+faststart',str(output)]
 proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
 for idx in seq:proc.stdin.write(frames[idx].tobytes())
 proc.stdin.close();assert proc.wait()==0
 gifframes=[im.resize((960,540),Image.Resampling.LANCZOS) for im in frames];durations=[270]*sc.n;durations[0]+=500;durations[-1]+=500;durations[c['first_index']]+=1000
 gifframes[0].save(folder/'execution.gif',save_all=True,append_images=gifframes[1:],duration=durations,loop=0,optimize=False)
 frames[c['first_index']].save(folder/'poster.jpg',quality=94);frames[0].save(folder/'input_and_t0.jpg',quality=94)
 indices=[0,max(0,c['first_index']-1),c['first_index'],sc.n-1];sheet=Image.new('RGB',(1920,1136),BG);ds=ImageDraw.Draw(sheet)
 for j,idx in enumerate(indices):
  xx=(j%2)*960;yy=(j//2)*568;tx(ds,(xx+8,yy),['t0','Last pre-contact sample','First contact','Horizon end'][j]+f' | t={sc.tt[idx]:.1f} s',22);sheet.paste(frames[idx].resize((960,540)),(xx,yy+28))
 sheet.save(folder/'four_keyframes.jpg',quality=94);csvout(folder/'contacts.csv',sc.records)
 first=sc.first;rec={**{k:c[k] for k in ['model','name','token','horizon_s','run_id','first_contact_s','scopes','source_sha256','map_sha256','map_status']},'first_actor':first,'mp4':output.relative_to(O).as_posix(),'gif':(folder/'execution.gif').relative_to(O).as_posix(),'poster':(folder/'poster.jpg').relative_to(O).as_posix(),'keyframes':(folder/'four_keyframes.jpg').relative_to(O).as_posix(),'contact_records':(folder/'contacts.csv').relative_to(O).as_posix(),'renderer_sha256':sha(__file__),'metric_code_sha256':sha(Path(M.__file__)),'mp4_sha256':sha(output),'fps':30,'encoded_frames':len(seq),'physical_states':sc.n,'sample_sequence':seq,'physical_times_s':sc.tt,'camera_count':3,'camera_status':'VERIFIED_T0_HELD','interpolation':False,'simulation':False,'sampled_contact_check':'MATCHES_SAVED_RESULT','first_precontact_sample_s':sc.tt[max(0,c['first_index']-1)]}
 save(receipt,rec);print('MEDIA PASS',c['run_id'],flush=True);return rec
def main():
 p=argparse.ArgumentParser();p.add_argument('--samples',action='store_true');args=p.parse_args();cases=read(O/'data/cases.json')
 if args.samples:
  chosen=[next(c for c in cases if c['model']==m and 'available_horizon' in c['scopes']) for m in MODELS]
  for c in chosen:render(c)
  return
 assert (O/'validation/media_sample_review.json').exists(),'Review four samples first'
 records=[render(c) for c in cases];save(O/'data/media_index.json',records);montages=[]
 for scope in ['saved_common3s','available_horizon']:
  for model in MODELS+['all']:
   rr=[r for r in records if scope in r['scopes'] and (model=='all' or model==r['model'])];listing=O/f'validation/concat_{scope}_{model}.txt';listing.write_text('\n'.join("file '"+str(O/r['mp4'])+"'" for r in rr),encoding='utf-8')
   dest=O/f'media/{scope}_{model}_all_contacts.mp4';subprocess.run([FF,'-y','-hide_banner','-loglevel','error','-f','concat','-safe','0','-i',str(listing),'-c','copy','-movflags','+faststart',str(dest)],check=True);montages.append({'scope':scope,'model':model,'scenes':len(rr),'mp4':dest.relative_to(O).as_posix()})
 save(O/'data/montages.json',montages)
 csvout(O/'data/video_index.csv',[{k:v for k,v in r.items() if k not in ['sample_sequence','physical_times_s']} for r in records])
 print('ALL MEDIA',len(records),'MONTAGES',len(montages),flush=True)
if __name__=='__main__':main()
