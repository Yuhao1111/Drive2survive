"""Assemble the offline research page; preserve prior dashboard as a read-only copy."""
from prepare import *
import html

def main():
 code=Path(__file__).parent
 for name in ['index.html','research.css','research.js']:shutil.copyfile(code/name,O/name)
 media=read(O/'data/media_index.json');montages=read(O/'data/montages.json');panels=read(O/'data/panels.json');cases=read(O/'data/cases.json')
 (O/'data/media_data.js').write_text('window.MEDIA_INDEX='+json.dumps(media,separators=(',',':'))+';window.MONTAGES='+json.dumps(montages,separators=(',',':'))+';',encoding='utf-8')
 bundle=read(S/'02_tables/data_bundle.json');save(O/'data/horizon_comparison.json',bundle['horizon_effects'])
 contacts=list(csv.DictReader((O/'data/all_collision_cases.csv').open(encoding='utf-8-sig')));summ=read(O/'data/summary.json');bins=[]
 for row in summ:
  rr=[r for r in contacts if r['scope']==row['scope'] and r['model']==row['model']]
  for b in ['[0,1)','[1,2)','[2,3]','(3,4]','EXACTLY_3S','EXACTLY_4S']:
   ne=row['horizon_s']==3 and b in ['(3,4]','EXACTLY_4S'];n=sum(r['bin']==b for r in rr) if b.startswith(('(','[')) else sum(abs(float(r['first_contact_s'])-(3 if b=='EXACTLY_3S' else 4))<1e-8 for r in rr)
   bins.append({'scope':row['scope'],'model':row['model'],'bank':'Dev100','horizon_s':row['horizon_s'],'valid_n':100,'time_bin':b,'count':None if ne else n,'status':'NOT_EVALUATED' if ne else 'OBSERVED'})
 csvout(O/'data/contact_time_bins.csv',bins)
 tw=[]
 for p in panels.values():
  if p['meta']['metric'] not in ['TET','TIT']:continue
  for group in p['distribution']:
   tw.append({**p['meta'],**{k:group[k] for k in ['group','n','n_finite','n_censored','n_na','n_incomplete','n_zero','mean','median','min','max']}})
 csvout(O/'data/tet_window_summary.csv',tw)
 # Reconcile movement context directly from each saved result, rather than copying slide numbers.
 progress=[]
 for key,src in read(O/'data/run_sources.json').items():
  scope,m,t=key.split('|');x=read(local(src['path']));v=x['rollout']['route_progress_m'];progress.append({'scope':scope,'model':m,'token':t,'progress_m':v[-1] if isinstance(v,list) else v,'window':'FULL_ROLLOUT','horizon_s':x['rollout']['times_s'][-1]})
 csvout(O/'data/progress_scene_context.csv',progress)
 pg=[]
 for scope in SCOPES:
  for m in MODELS:
   rr=[r for r in progress if r['scope']==scope and r['model']==m];pg.append({'scope':scope,'model':m,'n':len(rr),'mean_progress_m':float(np.mean([r['progress_m'] for r in rr]))})
 save(O/'data/progress_summary.json',pg)
 # Original dashboard is byte-preserved with all its asset directories. Do not nest its previous archive.
 copied=[]
 for p in S.rglob('*'):
  if not p.is_file() or p.name in ['Four_Model_Risk_Dashboard_English.zip','Four_Model_Risk_Dashboard_English.zip.sha256']:continue
  dest=O/'legacy'/p.relative_to(S);dest.parent.mkdir(parents=True,exist_ok=True)
  if not dest.exists() or dest.stat().st_size!=p.stat().st_size:shutil.copyfile(p,dest)
  copied.append({'path':p.relative_to(S).as_posix(),'bytes':p.stat().st_size})
 assert sha(S/'index.html')==sha(O/'legacy/index.html')
 save(O/'validation/legacy_preservation.json',{'index_sha256':sha(S/'index.html'),'original_html_byte_identical':True,'copied_files':len(copied),'bytes':sum(x['bytes'] for x in copied),'omitted_redundant_previous_archive_only':True})
 (O/'index_original.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><title>Original dashboard</title><meta http-equiv="refresh" content="0;url=legacy/index.html"><a href="legacy/index.html">Open the original four-model dashboard, preserved byte-for-byte with its assets.</a></html>',encoding='utf-8')
 excerpt=read(O/'source/proposal_research_extract.json');excerpt=[x for x in excerpt if x['paragraph_index']!=20]
 for x in excerpt:
  if x['paragraph_index']==38:x['text']=x['text'].split('. ')[0]+'.'
 save(O/'source/proposal_research_extract.json',excerpt)
 # Complete source registry includes every execution, map and verified image.
 reg=list(csv.DictReader((O/'source/source_register.csv').open(encoding='utf-8-sig')))
 for k,s in read(O/'data/run_sources.json').items():reg.append({'path':s['path'],'sha256':s['sha256'],'role':k})
 for c in cases:
  reg.append({'path':str(S/f"05_map_context/{c['token']}.json"),'sha256':c['map_sha256'],'role':'Real map geometry'})
  for cam in c['cameras']:reg.append({'path':cam['source_path'],'sha256':cam['sha256'],'role':'Verified official t0 scene camera'})
 reg.append({'path':str(S/'index.html'),'sha256':sha(S/'index.html'),'role':'Prior four-model dashboard'})
 unique={r['path']+'|'+r['role']:r for r in reg};csvout(O/'source_register.csv',list(unique.values()))
 cards=[]
 for r in media:
  cards.append(f'<article class="video-card"><video controls preload="none" poster="{r["poster"]}"><source src="{r["mp4"]}" type="video/mp4"></video><div class="video-info"><h3>{r["name"]} — {r["horizon_s"]:g} s</h3><p>{r["token"]} · first sampled contact {r["first_contact_s"]:.1f} s</p><p>{"ORION AS-RETURNED DIAGNOSTIC / UNRESOLVED" if r["model"]=="orion" else "Original saved ego / actor motion"}</p><a href="{r["mp4"]}">MP4</a> · <a href="{r["gif"]}">GIF</a> · <a href="{r["keyframes"]}">Four keyframes</a></div></article>')
 (O/'videos.html').write_text('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Drive2Survive | Input + execution videos</title><link rel="stylesheet" href="research.css"></head><body><main><section><a href="index.html">← Research dashboard</a><h1>Input observation + saved execution</h1><p>38 unique contact executions across common 3 s and available-horizon views. Three verified t0 images stay static. The physical clock advances through original 0.1 s execution samples. Real maps; blue ego; yellow vehicles; red contact outline.</p><div class="download-grid">'+''.join(f'<a href="{r["mp4"]}">{r["scope"]} / {r["model"]} / {r["scenes"]} scenes</a>' for r in montages)+'</div><div class="video-grid">'+''.join(cards)+'</div></section></main></body></html>',encoding='utf-8')
 targets=read(O/'data/targets.json');lines=['# Drive2Survive：四模型研究结果 / Four-model research evidence','','## 研究目标 / Research objective','','根据上传的研究方案，本项目要回答：VLA 规划在长尾危险场景中是否保有安全间隔，累计近失风险是否能补充单纯碰撞计数，以及在保留进度和舒适性的前提下能否识别并减少后续接触。此页面仅使用现有 Dev100 证据；不能据此声称已覆盖全部长尾分布。','','The proposal motivates a reproducible benchmark of VLA driving behavior in long-tail situations. Pre-crash precursor metrics complement contact counts; progress and comfort discourage a trivial stop-to-be-safe solution. Current saved Dev100 evidence supports descriptive comparisons and exploratory threshold analysis, not population-level validation.','','## 执行与接触 / Execution and contact','','|Model|Common 3 s|Available horizon|Available contacts|Valid n in each view|','|---|---:|---:|---:|---:|']
 for m,name in zip(MODELS,NAMES):
  a=next(r for r in summ if r['scope']==SCOPES[0] and r['model']==m);b=next(r for r in summ if r['scope']==SCOPES[1] and r['model']==m);lines.append(f'|{name}|{a["contact_scenes"]}|{b["horizon_s"]:g} s|{b["contact_scenes"]}|100|')
 lines+=['','每模型每视图均成功100、失败0、未运行0。接触是实际采样时刻的 OBB 接触或重叠，按场景计数，不是 native NC。ORION 保留 AS-RETURNED DIAGNOSTIC / UNRESOLVED。4 s 比较不是公平排行榜。','','All models retain 100/100 valid scenes, with zero failed or not-run statuses in these saved banks. ORION remains diagnostic. Independent 3 s and 4 s executions have different prefixes for AutoVLA and ORION; a count difference is not the last-second increment.','','## 五个指标 / Five metrics','','TTC uses the existing frozen-heading, constant-velocity OBB collision search (3 s search horizon). DRAC retains the existing aligned closing-conflict definition. PET retains the saved conflict-zone definition and applicability. The proposal contains simplified motivation formulas; they do not replace the saved operational implementation.','','PDF = a density histogram conditional on finite values; all models use common bins determined from feature values only. ECDF is finite-conditional except TTC: its denominator also retains right-censored scenes and only the range below 3 s is identified. N/A, censoring and incomplete values remain distinct. No curve is P(contact | threshold). TET is discrete at 0.1 s, so its density histogram is a binning display, not an assumed continuous law.','','TET = Σ Δt·1[0 ≤ TTC < 3 s]; TIT = Σ Δt·max(0,3−TTC). Right endpoint integration, t0 has Δt=0. Unknown TTC remains unknown; known censoring beyond the search window adds no below-threshold exposure.','','|Model|Mean TET full (s)|Mean TET pre-contact (s)|Mean TIT full (s²)|TTC finite / censored|','|---|---:|---:|---:|---|']
 for m,name in zip(MODELS,NAMES):
  def group(w,k):return next(x for x in panels[f'saved_common3s|{m}|{w}|{k}']['distribution'] if x['group']=='all')
  a,b,c,d=group('FULL_ROLLOUT','TET'),group('PRE_FIRST_CONTACT','TET'),group('FULL_ROLLOUT','TIT'),group('FULL_ROLLOUT','TTC');lines.append(f'|{name}|{a["mean"]:.3f}|{b["mean"]:.3f}|{c["mean"]:.3f}|{d["n_finite"]} / {d["n_censored"]}|')
 lines+=['','Full and pre-contact statistics are not interchangeable. Full windows include post-contact TTC=0; strict pre-contact windows are outcome-dependent and retrospective. Neither is a uniform early-prediction window.','','## 固定时点阈值 / Fixed-landmark threshold selection','','先观察 [0,L]，排除首次接触≤L的场景，再预测首次接触在 (L,U] 的目标。PET 在截止时刻无法合法获得时标 N/A。全部目标接触覆盖率包括指标不适用的接触；metric-eligible recall 分母不同。','','Reference rule: common 3 s; L=1 s; future interval (1,3]; TIT > 1 s² observed only in [0,1]. AutoVLA 1/2 selected with coverage 1/2; Impromptu 2/4 with coverage 2/6; ORION 3/4 with coverage 3/3; OpenDriveVLA 1/2 with coverage 1/2. No model reaches 80% under this shared rule.','','The same-bank original threshold grid may reach the following targets. The largest selected set that meets each target is retained; thresholds were not altered to obtain a preferred result.','','|Model|Metric|Target|Threshold|k/n|All-target coverage|Wilson 95%|Status|','|---|---|---:|---|---|---|---|---|']
 for t in targets:
  if t['scope']!='saved_common3s' or t['window']!='L1_TO_HORIZON':continue
  val='N/A' if t['threshold'] is None else f'{t["operator"]} {t["threshold"]:.6g}';kn='N/A' if t['n'] is None else f'{t["k"]}/{t["n"]}';cov='N/A' if t['k'] is None else f'{t["k"]}/{t["all_target_contacts"]}';ci='N/A' if t['n'] is None else f'{100*t["wilson_lower"]:.1f}–{100*t["wilson_upper"]:.1f}%';lines.append(f'|{NAMES[MODELS.index(t["model"])]}|{t["metric"]}|{100*t["target"]:.0f}%|{val}|{kn}|{cov}|{ci}|{t["status"]}|')
 lines+=['','所有达到目标的参考窗口候选均只有1–5个选中场景；没有一个候选的 Wilson 95% 下界达到其80%/90%目标。单一1/1、3/3、4/5不能解释为稳定危险概率。Wilson区间也没有校正选阈值偏差与共享日志的相关性。','','Selected groups are small and thresholds are explored on the same bank. Wilson intervals are descriptive, not a calibrated prediction guarantee, and do not correct for threshold selection or shared-log dependence.','','## 视频 / Videos','','38 unique saved contact executions, 38 H.264 MP4, 38 GIF, 38 posters and 38 four-time keyframe sheets. The common-3 s view references 13 model-scene contacts; the available view references 33. Impromptu and OpenDriveVLA reuse identical 3 s executions across views; 8 references are shared. Ten compilations cover both scopes, four models plus all-model compilation in each.','','21 unique scene tokens have 63 source-hash-verified real t0 camera images and real nuPlan map geometry. All 38 replays combine three held t0 views with original 0.1 s ego/actor states, physical time, contact actor/type/relative sector, five timelines and contact marker. No interpolation or fabricated future camera frames. Cameras are verified scene observations, not proof of identical model input preprocessing.','','## 可总结的规律 / Patterns with limits','','1. 时域增加会改变执行与暴露机会；两套结果必须分开。 / Horizon affects both execution and exposure; keep the two views separate.','2. TTC多数为右删失；DRAC和PET适用面不同，因此密度曲线的分母不相同。 / TTC has a large censored tail; DRAC/PET have narrower applicability.','3. TET的时长与TIT的严重程度互补；零风险质量和尾部应一起报告。 / Duration and accumulated severity are complementary; retain zero mass and tails.','4. 高精度往往来自很小选中集；覆盖率和不确定性必须同时看。 / High selected fractions can rely on very small groups; report coverage and uncertainty.','5. 下一步应在独立bank增加接触样本、验证阈值迁移，再结合进度与舒适性测试干预。 / Next steps are held-out threshold validation and intervention evaluation with progress and comfort.','','Existing plans were executed using saved official-backend results. This page does not imply fresh VLA replanning, a newly completed larger bank, causal intervention benefits, or certified ORION native coordinates/timing.']
 (O/'reports/RESEARCH_SUMMARY_CN_EN.md').write_text('\n'.join(lines),encoding='utf-8')
 guide='''# 推荐汇报顺序 / Recommended presentation sequence

1. F2_contact_times_saved_common3s: 先讲相同时域的接触数量与首次时刻。 / Start with equal-horizon outcomes and first contact times.
2. F3_compact_saved_common3s_PRE_FIRST_CONTACT: 四模型紧凑密度与ECDF，说明删失与适用分母；强调这是回顾性窗口。 / Compact distributions with censoring and applicability; explicitly retrospective.
3. F4_TET_TIT: 暴露时长与累计严重程度不是同一个概念。 / Explain exposure duration versus accumulated severity.
4. F5_fixed_landmark_support: 使用真实k/n、全部目标覆盖和区间，回答提前观察能支持多强的结论。 / Connect early features to later contact, with counts, coverage and uncertainty.
5. F6_contact_matrix: 说明模型共享与不同的失败场景，不等同于模型公平排名。 / Show shared and distinct contact cases without overstating a ranking.

Recommended videos: OpenDriveVLA 6ec9c290f821534d (3 s endpoint contact), AutoVLA 9513ed317ce95815 (3 s), ORION 9513ed317ce95815 (3 s, diagnostic). Use corresponding saved scope; do not substitute a 4 s execution while discussing the 3 s result.

All figures are PNG + editable SVG. Dashboard controls export the selected two-panel distribution SVG. The offline videos.html contains all 38 unique runs.
'''
 (O/'reports/FIGURE_GUIDE_CN_EN.md').write_text(guide,encoding='utf-8')
 (O/'README_CN_EN.md').write_text('''# Drive2Survive · Four-model research dashboard

解压完整ZIP后，用本机浏览器打开 index.html。保留全部子目录。页面英文，研究说明附中英双语。
Extract the complete package, preserve subdirectories, and open index.html locally. No server or CDN is needed.

New: compact four-model PDF/ECDF; contact/group distributions; TET; fixed-landmark thresholds with counts, coverage, intervals and selected tokens; all contact videos with verified t0 input observations and real map replay.

Original dashboard: legacy/index.html, preserved byte-for-byte. index_original.html is a convenience redirect. The prior redundant whole-dashboard archive is omitted; its unpacked files are retained.

38 unique contact MP4 + 38 GIF + 10 MP4 compilations. Common-3 s view: 13 references; available view: 33 references. The 3 s executions shared between views use the same media.

The original VLA predictions, official execution results and previous webpages remain read-only. Reproduction code is in source/. Source paths in the audit registry describe the original machine and do not affect offline viewing.

Use validation.json for actual checks and limits. Reports are in reports/. Content SHA256 hashes are in MANIFEST_SHA256.txt; the package SHA256 is distributed alongside the ZIP.
''',encoding='utf-8')
 for p in code.iterdir():
  if p.is_file():shutil.copyfile(p,O/'source'/p.name)
 print('WEB ASSEMBLED',len(media),'videos;',len(copied),'legacy files',flush=True)
if __name__=='__main__':main()
