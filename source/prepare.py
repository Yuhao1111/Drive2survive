"""Saved-result postprocessing for the four-model research dashboard; no simulator."""
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET
import json,csv,hashlib,shutil,math,collections,gzip,os
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
S=ROOT/'outputs/multivla_risk_dashboard_v3_en'
O=ROOT/'outputs/multivla_research_dashboard_v4_en'
if Path(__file__).parent.name=='source':
 O=Path(__file__).resolve().parent.parent;ROOT=O.parent.parent;S=O/'legacy'
E=Path('E:/Drive2Survive_Recovery_20260908') if os.name=='nt' else Path('/mnt/e/Drive2Survive_Recovery_20260908')
DOC=(Path('E:/') if os.name=='nt' else Path('/mnt/e'))/'微信/xwechat_files/wxid_637fok0o4o4x12_7073/msg/file/2026-09/Drive2Survive - NAIRR Start-Up Proposal (with References)(1).docx'
MODELS=['autovla','impromptu','orion','opendrivevla'];NAMES=['AutoVLA','Impromptu-VLA','ORION','OpenDriveVLA']
METRICS=['TTC','TIT','DRAC','PET','TET'];SCOPES=['saved_common3s','available_horizon'];WINDOWS=['FULL_ROLLOUT','PRE_FIRST_CONTACT','L1_NEXT1S','L1_TO_HORIZON','L2_NEXT1S','L2_TO_HORIZON']
UNITS={'TTC':'s','TIT':'s²','DRAC':'m/s²','PET':'s','TET':'s'}
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,allow_nan=False,indent=2),encoding='utf-8')
def csvout(p,rows):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,list(dict.fromkeys(k for r in rows for k in r)));w.writeheader();w.writerows([{k:json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else v for k,v in r.items()} for r in rows])
def local(p):
 p=str(p).replace('\\','/')
 if os.name=='nt' and p.startswith('/mnt/'):return Path(p[5].upper()+':/'+p[7:])
 if os.name!='nt' and len(p)>2 and p[1]==':':return Path('/mnt/'+p[0].lower()+p[2:])
 return Path(p)
def commonpath(m,t):
 if m=='opendrivevla':return S/f'01_runs/OPENDRIVEVLA_3S/{t}/result.json'
 if m=='orion':return E/f'analysis/orion_return100_analysis_v2/05_remote_local_repro/as_returned_replay/{t}.json'
 return E/f'analysis/multivla_remote_20260918_v1/03_local_common3s/{m}/{t}.json'
def included(p):return [r for r in p['rows'] if r['cohort_status']=='INCLUDED']
def eligible(r,metric):return r['cohort_status']=='INCLUDED' and (r['status']=='FINITE' or metric=='TTC' and r['status']=='RIGHT_CENSORED_3S')
def select(r,metric,a):return eligible(r,metric) and r['status']=='FINITE' and (r['value']<a if metric in ('TTC','PET') else r['value']>a)
def wilson(k,n):
 if not n:return [None,None]
 z=1.959963984540054;q=k/n;den=1+z*z/n;cen=(q+z*z/(2*n))/den;half=z*math.sqrt(q*(1-q)/n+z*z/(4*n*n))/den
 return [max(0,cen-half),min(1,cen+half)]

def main():
 for d in ['data','figures','media','cameras','source','validation','reports','legacy']:(O/d).mkdir(parents=True,exist_ok=True)
 source=[]
 def register(p,role):source.append({'path':str(p),'sha256':sha(p),'role':role})
 panelpath=S/'02_stats_new/dashboard_data.json';bundlepath=S/'02_tables/data_bundle.json';camsrc=E/'analysis/autovla_local_navsim4s_execution_v2/07_visualizations/camera_history.json'
 for p,role in [(DOC,'Research purpose, sections A and E; resource discussion omitted'),(panelpath,'All four models: saved metric features and thresholds'),(bundlepath,'Available-horizon contact and driving metrics'),(camsrc,'Verified scene t0 camera provenance')]:register(p,role)
 src=read(panelpath);bundle=read(bundlepath);cameras=read(camsrc);panels={};histograms={};distro=[];curves=[];targets=[];validation=[]
 for scope in SCOPES:
  for win in WINDOWS:
   for metric in METRICS:
    keys=[f'{scope}|{m}|{win}|{metric}' for m in MODELS]
    vals=[r['value'] for k in keys for r in included(src[k]) if r['status']=='FINITE']
    if metric=='TTC':edges=np.arange(0,3.0001,.25)
    elif metric=='TET':edges=np.arange(-.05,max([r['window_end'] for k in keys for r in included(src[k])],default=3)+.1001,.1)
    elif vals:
     n=len(np.histogram_bin_edges(vals,bins='fd'))-1;edges=np.linspace(min(0,min(vals)),max(vals) or 1,min(24,max(6,n))+1)
    else:edges=np.array([0.,1.])
    histograms[f'{scope}|{win}|{metric}']=[round(float(v),12) for v in edges]
    for m,key in zip(MODELS,keys):
     p=src[key];rr=p['rows'];assert len(rr)==100
     out={'meta':p['meta'],'rows':rr,'curves':p['curves'],'pr_points':p['pr_points'],'pr_summary':p['pr_summary'],'distribution':p['distribution']}
     panels[key]=out
     for c in p['curves']:
      chosen=[r for r in rr if select(r,metric,c['threshold'])];k=sum(r['y'] for r in chosen);assert (k,len(chosen))==(c['n_contact_selected'],c['n_selected'])
      assert sum(r['y'] for r in rr if r['cohort_status']=='INCLUDED')==c['n_contact_cohort']
      cc=dict(c,all_target_coverage=k/c['n_contact_cohort'] if c['n_contact_cohort'] else None,selected_tokens=[r['token'] for r in chosen]);curves.append(cc)
     for group in ('all','contact','no_contact'):
      rows=[r for r in included(p) if group=='all' or r['y']==int(group=='contact')];vv=sorted(r['value'] for r in rows if r['status']=='FINITE');old=next(z for z in p['distribution'] if z['group']==group)
      assert len(vv)==old['n_finite'];assert old['mean'] is None if not vv else abs(float(np.mean(vv))-old['mean'])<1e-9
      count,_=np.histogram(vv,edges);assert sum(count)==len(vv)
      distro.append({**p['meta'],'group':group,'n':len(rows),'finite':len(vv),'censored':old['n_censored'],'not_applicable':old['n_na'],'incomplete':old['n_incomplete'],'zero':old['n_zero'],'mean':old['mean'],'median':old['median'],'unit':UNITS[metric],'bin_edges':edges.tolist(),'bin_counts':count.tolist(),'density_rule':'POOLED_X_ONLY_SHARED_BINS_FINITE_CONDITIONAL; TET discrete 0.1s bins; no KDE'})
     for target in (.8,.9):
      hits=[c for c in p['curves'] if c['precision'] is not None and c['precision']+1e-12>=target]
      best=max(hits,key=lambda c:c['n_selected']) if hits else None
      base=p['curves'][0]
      targets.append({**p['meta'],'target':target,'status':('LOW_SUPPORT' if best['n_selected']<10 else 'EMPIRICAL_POINT_ONLY') if best else 'NOT_REACHED' if base['n_metric_eligible'] else 'NO_ELIGIBLE_DATA','threshold':best['threshold'] if best else None,'operator':base['operator'],'k':best['n_contact_selected'] if best else None,'n':best['n_selected'] if best else None,'eligible_n':base['n_metric_eligible'],'eligible_contacts':base['n_contact_eligible'],'all_target_contacts':base['n_contact_cohort'],'all_target_coverage':best['n_contact_selected']/base['n_contact_cohort'] if best and base['n_contact_cohort'] else None,'wilson_lower':best['wilson_lower'] if best else None,'wilson_upper':best['wilson_upper'] if best else None,'selected_tokens':[r['token'] for r in rr if select(r,metric,best['threshold'])] if best else [],'lower_bound_reaches_target':bool(best and best['wilson_lower']>=target)})
     validation.append({'panel':key,'n_rows':len(rr),'thresholds_recounted':len(p['curves']),'status':'PASS'})
 summary=[];contactrows=[];cases={};source_run={};tetchecks=[];tetseries=[]
 for scope in SCOPES:
  for m,name in zip(MODELS,NAMES):
   pp=panels[f'{scope}|{m}|FULL_ROLLOUT|TTC'];rows=pp['rows'];h=rows[0]['horizon_s'];summ=next(x for x in bundle['summaries'] if x['model']==m)
   summary.append({'scope':scope,'model':m,'model_display':name,'horizon_s':h,'success':100,'failed':0,'not_run':0,'valid_n':len(rows),'contact_scenes':sum(r['full_contact'] for r in rows),'contract':'AS-RETURNED DIAGNOSTIC / UNRESOLVED' if m=='orion' else summ['contract_status']})
   for rr in rows:
    t=rr['token'];p=commonpath(m,t) if scope=='saved_common3s' else S/f"01_runs/{summ['condition']}/{t}/result.json";x=read(p);r=x['rollout'];times=r['times_s'];ts=x['metrics']['ttc_series'];assert len(times)==int(h*10)+1
    totals=[];total=0;unknown=0
    for i,(tm,z) in enumerate(zip(times,ts)):
     dt=tm-times[i-1] if i else 0;v=z['ttc_s'];st=z.get('status',z.get('ttc_status'))
     if v is not None and 0<=v<3:total+=dt
     elif v is None and st!='RIGHT_CENSORED_3S':unknown+=dt
     totals.append({'time_s':tm,'ttc_s':v,'ttc_status':st,'tet_s':round(total,12) if unknown==0 else None,'unknown_duration_s':unknown})
    tetseries += [dict(scope=scope,model=m,token=t,**q) for q in totals]
    for window in WINDOWS:
     z=next(z for z in panels[f'{scope}|{m}|{window}|TET']['rows'] if z['token']==t)
     cutoff=z['window_end'];observed=next(q['tet_s'] for q in totals if abs(q['time_s']-cutoff)<1e-8)
     assert z['value'] is None or abs(observed-z['value'])<1e-8,(scope,m,t,window)
    feature=next(z for z in panels[f'{scope}|{m}|FULL_ROLLOUT|TET']['rows'] if z['token']==t)
    assert unknown==0 and abs(total-feature['value'])<1e-8
    tetchecks.append({'scope':scope,'model':m,'token':t,'horizon_s':h,'states':len(times),'tet_recomputed_s':round(total,12),'tet_saved_s':feature['value'],'status':'PASS'})
    rid=f'{m}_{int(h)}s_{t}';source_run[scope+'|'+m+'|'+t]={'path':str(p),'sha256':sha(p),'run_id':rid}
    if not rr['full_contact']:continue
    first=rr['first_contact_s'];idx=next(i for i,tm in enumerate(times) if abs(tm-first)<1e-7)
    cc={'scope':scope,'model':m,'name':name,'token':t,'horizon_s':h,'first_contact_s':first,'exactly_3s':abs(first-3)<1e-8,'exactly_4s':abs(first-4)<1e-8,'bin':'[0,1)' if first<1 else '[1,2)' if first<2 else '[2,3]' if first<=3 else '(3,4]','run_id':rid}
    contactrows.append(cc)
    if rid in cases:
     oldroll=read(O/cases[rid]['result_path'])['rollout']
     assert oldroll['ego']==r['ego'] and oldroll['actors']==r['actors'] and oldroll['times_s']==r['times_s'],'Cannot alias distinct executions'
     cases[rid]['scopes'].append(scope);continue
    folder=O/'data/runs'/rid;folder.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,folder/'result.json')
    mp=S/f'05_map_context/{t}.json';assert mp.is_file();mapmeta=read(mp);assert mapmeta['status']=='MAP_AVAILABLE'
    # Preserve map geometry once per scene and the authoritative source file hash.
    localmap=O/f'data/maps/{t}.json';localmap.parent.mkdir(parents=True,exist_ok=True)
    if not localmap.exists():shutil.copyfile(mp,localmap)
    camp=[]
    for cam in sorted(cameras[t],key=lambda c:['CAM_L1','CAM_F0','CAM_R1'].index(c['camera'])):
     cp=local(cam['path']);assert cp.is_file() and sha(cp)==cam['sha256'] and cam['status']=='VERIFIED_OFFICIAL_T0_IMAGE' and cam['time_relative_s']==0
     dest=O/f'cameras/{t}/{cam["camera"]}.jpg';dest.parent.mkdir(parents=True,exist_ok=True)
     if not dest.exists():shutil.copyfile(cp,dest)
     camp.append(dict(cam,path=dest.relative_to(O).as_posix(),source_path=str(cp)))
    assert len(camp)==3
    tc={'model':m,'name':name,'token':t,'horizon_s':h,'run_id':rid,'first_contact_s':first,'first_index':idx,'scopes':[scope],'source':str(p),'source_sha256':sha(p),'result_path':(folder/'result.json').relative_to(O).as_posix(),'map_path':localmap.relative_to(O).as_posix(),'map_sha256':sha(mp),'map_status':mapmeta['status'],'cameras':camp,'timeline':totals,'contract':summary[-1]['contract']}
    # Keep all original contact-event fields, with no fabricated actor ID.
    tc['contact_events']=x.get('collision_events',x['metrics'].get('collision_events',[]));cases[rid]=tc
 for rid,cc in cases.items():register(Path(cc['source']),rid)
 with ZipFile(DOC) as z:
  ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'};tree=ET.fromstring(z.read('word/document.xml'));paras=[''.join(el.itertext()) for el in tree.findall('.//w:body/w:p',ns)]
  excerpts=[{'paragraph_index':i,'text':p} for i,p in enumerate(paras) if i in [0,1,2,5,6,7,8,9,10,11,12,13,14,15,16,19,20,37,38]]
 save(O/'source/proposal_research_extract.json',excerpts)
 meta={'title':'Drive2Survive | Four-model research evidence','models':MODELS,'names':dict(zip(MODELS,NAMES)),'units':UNITS,'scopes':SCOPES,'windows':WINDOWS,'metric_threshold_s':3,'integration':'RIGHT_ENDPOINT','bank':'Dev100','valid_each':100,'proposal_sha256':sha(DOC),'default_scope':'saved_common3s','default_window':'PRE_FIRST_CONTACT','camera_note':'Verified t0 scene observations held during the simulation replay. Not a claim of identical camera selection or preprocessing inside all four models.'}
 save(O/'data/summary.json',summary);save(O/'data/cases.json',list(cases.values()));save(O/'data/panels.json',panels);save(O/'data/histogram_bins.json',histograms);save(O/'data/targets.json',targets);save(O/'data/meta.json',meta)
 csvout(O/'data/model_horizon_summary.csv',summary);csvout(O/'data/all_collision_cases.csv',contactrows);csvout(O/'data/five_metric_distributions.csv',distro);csvout(O/'data/threshold_curves.csv',curves);csvout(O/'data/threshold_80_90.csv',targets);csvout(O/'data/tet_reconciliation.csv',tetchecks);csvout(O/'source/source_register.csv',source)
 with gzip.open(O/'data/tet_timeseries.csv.gz','wt',encoding='utf-8',newline='') as f:
  writer=csv.DictWriter(f,list(tetseries[0]));writer.writeheader();writer.writerows(tetseries)
 save(O/'validation/statistics_checks.json',{'status':'PASS','panels':validation,'thresholds_recounted':len(curves),'tet_reconciled':len(tetchecks),'unique_collision_runs':len(cases),'source_inputs_unchanged':True})
 save(O/'data/run_sources.json',source_run)
 # One small offline script contains rows and original curves; no HTTP fetch is needed.
 payload={'meta':meta,'summary':summary,'panels':panels,'bins':histograms,'targets':targets,'contacts':contactrows,'cases':list(cases.values())}
 (O/'data/dashboard_data.js').write_text('window.RESEARCH_DATA='+json.dumps(payload,ensure_ascii=False,separators=(',',':'),allow_nan=False)+';',encoding='utf-8')
 print(json.dumps({'status':'PASS','panels':len(panels),'threshold_checks':len(curves),'tet_checks':len(tetchecks),'unique_collision_runs':len(cases),'case_counts':collections.Counter(c['model'] for c in cases.values()),'camera_scenes':len(set(c['token'] for c in cases.values()))},ensure_ascii=False),flush=True)
if __name__=='__main__':main()
