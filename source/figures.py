"""Compact scientific figures from saved row-level features, never from HTML summaries."""
import os,json,collections,math,csv
os.environ['MPLCONFIGDIR']=str(__import__('pathlib').Path(__file__).parent/'mpl_cache')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from prepare import *
BG='#0A101A';FG='#DCE7F5';MUTED='#AAC0DA';COLORS=['#68BAFF','#49C6B7','#B899FF','#F2C94C']
plt.rcParams.update({'figure.facecolor':BG,'axes.facecolor':BG,'axes.edgecolor':'#34445B','axes.labelcolor':MUTED,'text.color':FG,'xtick.color':MUTED,'ytick.color':MUTED,'grid.color':'#34445B','font.family':'DejaVu Sans','font.size':10,'savefig.facecolor':BG,'svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False})
P=read(O/'data/panels.json');B=read(O/'data/histogram_bins.json');SUMMARY=read(O/'data/summary.json');CONTACTS=list(csv.DictReader((O/'data/all_collision_cases.csv').open(encoding='utf-8-sig')))
records=[]
def export(fig,name):
 fig.savefig(O/f'figures/{name}.png',dpi=170,bbox_inches='tight');fig.savefig(O/f'figures/{name}.svg',bbox_inches='tight');plt.close(fig);records.append({'name':name,'png':f'figures/{name}.png','svg':f'figures/{name}.svg'})
def pair(scope,window,metric,axs):
 edges=B[f'{scope}|{window}|{metric}'];ns=[]
 for m,c,name in zip(MODELS,COLORS,NAMES):
  pp=P[f'{scope}|{m}|{window}|{metric}'];rr=included(pp);vv=sorted(r['value'] for r in rr if r['status']=='FINITE');nc=sum(r['status']=='RIGHT_CENSORED_3S' for r in rr);den=len(vv)+nc if metric=='TTC' else len(vv)
  ns.append(f'{name.replace("Impromptu-VLA","Imp.").replace("OpenDriveVLA","ODVLA")}: {len(vv)}/{len(rr)} finite')
  if not vv:continue
  counts,_=np.histogram(vv,edges);density=counts/len(vv)/np.diff(edges)
  axs[0].stairs(density,edges,color=c,lw=1.8,label=name+('*' if m=='orion' else ''))
  xs=sorted(set(vv));xs=[v for v in xs if metric!='TTC' or v<3];ys=[sum(v<=x for v in vv)/den for x in xs]
  if xs:axs[1].step([min(0,xs[0])]+xs,[0]+ys,where='post',color=c,lw=1.8)
 for a in axs:a.grid(alpha=.35);a.set_xlabel(metric+' ('+UNITS[metric]+')');a.tick_params(labelsize=9)
 axs[0].set_ylabel('Density (finite only)');axs[1].set_ylabel('ECDF');axs[1].set_ylim(-.02,1.02)
 if metric=='TTC':axs[1].set_xlim(0,3);axs[0].set_xlim(0,3)
 axs[0].set_title('Probability density'+(' / discrete TET bins' if metric=='TET' else ''),fontsize=11);axs[1].set_title('ECDF'+(' · unidentified tail preserved' if metric=='TTC' else ' · finite observations'),fontsize=11)
 return ns
def main():
 for scope in SCOPES:
  for win in ['FULL_ROLLOUT','PRE_FIRST_CONTACT','L1_TO_HORIZON']:
   fig,axs=plt.subplots(5,2,figsize=(11,13));fig.subplots_adjust(hspace=.62,wspace=.28,top=.86,bottom=.04)
   for i,metric in enumerate(METRICS):
    ns=pair(scope,win,metric,axs[i]);axs[i,0].text(0,1.26,metric,transform=axs[i,0].transAxes,fontsize=13,fontweight='bold');axs[i,1].text(0,-.40,' | '.join(n.replace(': ',':') for n in ns),transform=axs[i,1].transAxes,fontsize=7.1,color=MUTED)
   handles,labels=axs[0,0].get_legend_handles_labels();fig.legend(handles,labels,loc='upper center',bbox_to_anchor=(.5,.941),ncol=4,fontsize=9,frameon=False)
   fig.suptitle('Four-model density and ECDF | '+('Common 3 s' if scope==SCOPES[0] else 'Available 4 / 3 / 4 / 3 s')+'\n'+win+' · Dev100 · ORION diagnostic',fontsize=15,y=.99)
   export(fig,f'F3_compact_{scope}_{win}')
   for metric in METRICS:
    fig,axs=plt.subplots(1,2,figsize=(10.5,3.1));ns=pair(scope,win,metric,axs);fig.suptitle(metric+' | '+scope+' | '+win+' | Dev100',fontsize=12);axs[0].legend(loc='upper right',fontsize=7,frameon=False);fig.tight_layout();export(fig,f'pair_{scope}_{win}_{metric}')
 for scope in SCOPES:
  fig,axs=plt.subplots(1,2,figsize=(11.5,3.8),gridspec_kw={'width_ratios':[1,1.6]});counts=[next(r['contact_scenes'] for r in SUMMARY if r['scope']==scope and r['model']==m) for m in MODELS]
  axs[0].bar(range(4),counts,color=COLORS,width=.6);axs[0].set_xticks(range(4),['Auto','Imp.','ORION*','ODVLA']);axs[0].set_ylabel('Contact scenes / 100 valid');axs[0].set_ylim(0,max(counts)+3)
  for i,n in enumerate(counts):axs[0].text(i,n+.25,f'{n}/100',ha='center',fontsize=11)
  for j,(m,col) in enumerate(zip(MODELS,COLORS)):
   rr=[r for r in CONTACTS if r['scope']==scope and r['model']==m];tt=sorted(float(r['first_contact_s']) for r in rr);seen=collections.Counter()
   for t in tt:
    k=seen[t];seen[t]+=1;offset=(k-(tt.count(t)-1)/2)*.09
    axs[1].scatter(t,j+offset,c=col,s=47,marker='D' if abs(t-3)<1e-8 or abs(t-4)<1e-8 else 'o',edgecolor=FG,lw=.4)
   h=next(r['horizon_s'] for r in SUMMARY if r['scope']==scope and r['model']==m)
   if h==3:axs[1].plot([3,4],[j,j],lw=22,color='#263141',alpha=.5,zorder=0);axs[1].text(3.48,j,'not evaluated',ha='center',va='center',fontsize=8,color=MUTED)
  axs[1].set_yticks(range(4),['AutoVLA','Impromptu-VLA','ORION*','OpenDriveVLA']);axs[1].invert_yaxis();axs[1].set_xlim(0,4.1);axs[1].set_xlabel('First sampled contact time (s)');axs[1].grid(axis='x',alpha=.5)
  for t in [1,2,3,4]:axs[1].axvline(t,color='#55677D',ls=':',lw=.8,zorder=0)
  fig.suptitle('F2 | Contact counts and first sampled contact times\n'+scope+' · Dev100 · diamonds mark exactly 3 or 4 s · ORION diagnostic',fontsize=12);fig.tight_layout();export(fig,f'F2_contact_times_{scope}')
 # Exposure duration versus accumulated severity; preserve all values including zeros.
 fig,axs=plt.subplots(1,2,figsize=(11.5,4.2))
 for ax,win in zip(axs,['FULL_ROLLOUT','PRE_FIRST_CONTACT']):
  for m,col,name in zip(MODELS,COLORS,NAMES):
   tet=P[f'saved_common3s|{m}|{win}|TET']['rows'];tit={r['token']:r for r in P[f'saved_common3s|{m}|{win}|TIT']['rows']}
   for y,marker in [(0,'o'),(1,'X')]:
    rr=[r for r in tet if r['status']=='FINITE' and r['y']==y];ax.scatter([r['value'] for r in rr],[tit[r['token']]['value'] for r in rr],s=38 if y else 18,color=col,marker=marker,alpha=.9 if y else .55,label=name+('*' if m=='orion' else '') if not y else None)
  ax.set_title(win,fontsize=11);ax.set_xlabel('TET (s): duration of TTC < 3 s');ax.set_ylabel('TIT (s²): accumulated shortfall');ax.grid(alpha=.35)
 axs[0].legend(fontsize=8,frameon=False);fig.suptitle('F4 | Duration and severity describe different aspects of risk\nCommon 3 s · n=100/model · X = contact · overlap at zero retained',fontsize=12);fig.tight_layout();export(fig,'F4_TET_TIT')
 # Fixed-landmark shared rule, selected count and coverage are separate.
 fig,axs=plt.subplots(1,2,figsize=(11.5,4.1))
 fixed=[]
 for j,(m,col,name) in enumerate(zip(MODELS,COLORS,NAMES)):
  p=P[f'saved_common3s|{m}|L1_TO_HORIZON|TIT'];c=next(c for c in p['curves'] if abs(c['threshold']-1)<1e-10);k,n=c['n_contact_selected'],c['n_selected'];q=k/n;lo,hi=wilson(k,n);fixed.append(dict(c))
  axs[0].errorbar(j,q,yerr=[[q-lo],[hi-q]],fmt='o',color=col,capsize=5,ms=8);axs[0].text(j,q+.07,f'{k}/{n}',ha='center',fontsize=11)
  den=c['n_contact_cohort'];axs[1].bar(j,k/den,color=col,width=.6);axs[1].text(j,k/den+.03,f'{k}/{den}',ha='center',fontsize=11)
 for ax in axs:ax.set_xticks(range(4),['Auto','Imp.','ORION*','ODVLA']);ax.set_ylim(0,1.2);ax.grid(axis='y',alpha=.3)
 axs[0].set_title('Contact / selected + Wilson 95%',fontsize=11);axs[0].axhline(.8,color='#AAC0DA',ls=':',lw=1);axs[0].axhline(.9,color='#AAC0DA',ls='--',lw=1);axs[0].set_ylabel('Empirical contact fraction')
 axs[1].set_title('Coverage of all future-contact scenes',fontsize=11);axs[1].set_ylabel('Selected future contacts / all future contacts')
 fig.suptitle('F5 | TIT > 1.0 s² observed in [0,1] s → first contact in (1,3] s\nCommon 3 s · eligible n=100/model · small selected groups; no stable 80%/90% claim',fontsize=12);fig.tight_layout();export(fig,'F5_fixed_landmark_support')
 tokens=sorted(set(r['token'] for r in CONTACTS));fig,axs=plt.subplots(2,1,figsize=(12,6.2),sharex=True)
 for ax,scope in zip(axs,SCOPES):
  mat=np.zeros((4,len(tokens)))
  for r in CONTACTS:
   if r['scope']==scope:mat[MODELS.index(r['model']),tokens.index(r['token'])]=1
  ax.imshow(mat,cmap=matplotlib.colors.ListedColormap(['#182334','#FF6677']),vmin=0,vmax=1,aspect='auto');ax.set_yticks(range(4),NAMES);ax.set_title(scope,fontsize=11)
 axs[1].set_xticks(range(len(tokens)),[t[:6] for t in tokens],rotation=60,ha='right',fontsize=8);fig.suptitle('F6 | Contact matrix across 21 scene tokens\nRed = sampled contact · blank = no contact · all 100 valid scenes retained in source tables',fontsize=12);fig.tight_layout();export(fig,'F6_contact_matrix')
 save(O/'data/figure_index.json',records)
 print('FIGURES',len(records),'PNG + SVG',flush=True)
if __name__=='__main__':main()
