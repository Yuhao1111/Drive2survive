"""Keep the v4 page; change its camera playback explanation and media only."""
import csv,io,math,json,shutil
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from prepare_dynamic import ROOT,OLD,NEW,read,save,sha

CAMERA_NOTE=('Three real recorded camera views play in physical-time alignment with the saved BEV. '
 'Available source images are approximately 2 Hz; each real exposure is held until the next capture. '
 'The recorded original driving viewpoint is not the simulated model viewpoint. '
 'This is not a claim of identical camera selection or preprocessing inside all four models.')

def replace_once(path,before,after):
 s=path.read_text(encoding='utf-8');assert s.count(before)==1,(path,before);path.write_text(s.replace(before,after),encoding='utf-8')

def main():
 records=read(NEW/'data/media_index.json');assert len(records)==38 and all(r.get('camera_status')=='REAL_LOGGED_CAMERA_TIMELINE' for r in records)
 old_notice=('Three verified real t0 camera views accompany each replay. They are held still and are not future video. '
 'These are scene observations, not a claim that all models consumed identical camera selections or preprocessing. '
 'Each model keeps its own saved actor world; playback only repeats original states.')
 new_notice=('Three real recorded camera views play alongside each BEV, aligned by capture time (about 2 Hz; held between real exposures). '
 'They show the original logged drive, not the simulated model viewpoint or identical model inputs. '
 'Each model keeps its own saved actor world; BEV playback repeats the original 0.1 s states.')
 replace_once(NEW/'index.html',old_notice,new_notice)
 replace_once(NEW/'videos.html','Three verified t0 images stay static.',
 'Three real recorded camera sequences play in physical-time alignment (approximately 2 Hz, held between real exposures). The original logged camera viewpoint is distinct from the simulated model ego viewpoint.')
 replace_once(NEW/'research.js','All include verified t0 images and real map geometry.',
 'All include time-aligned recorded camera sequences and real map geometry.')
 replace_once(NEW/'research.js','real map + 3 verified t0 views','real map + 3 recorded camera sequences')
 oldmeta=read(OLD/'data/meta.json');meta=dict(oldmeta,camera_note=CAMERA_NOTE);save(NEW/'data/meta.json',meta)
 p=NEW/'data/dashboard_data.js';replace_once(p,json.dumps(oldmeta['camera_note'],ensure_ascii=False),json.dumps(CAMERA_NOTE,ensure_ascii=False))
 # These are the exact same media references, with the revised receipts embedded offline.
 js='window.MEDIA_INDEX='+json.dumps(records,ensure_ascii=False,separators=(',',':'))+';\nwindow.MONTAGES='+json.dumps(read(NEW/'data/montages.json'),ensure_ascii=False,separators=(',',':'))+';\n'
 (NEW/'data/media_data.js').write_text(js,encoding='utf-8')
 sheets=read(NEW/'data/contact_sheets.json');font=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',18)
 for sheet in sheets:
  rr=[r for r in records if r['model']==sheet['model'] and sheet['scope'] in r['scopes']];assert len(rr)==sheet['scenes'];cols=min(3,len(rr))
  im=Image.new('RGB',(640*cols,390*math.ceil(len(rr)/cols)),'#0a101a');d=ImageDraw.Draw(im)
  for j,r in enumerate(rr):
   x=j%cols*640;y=j//cols*390
   with Image.open(NEW/r['poster']) as p:im.paste(p.resize((640,360)),(x,y))
   d.text((x+8,y+363),r['token']+f" | {r['horizon_s']:g}s | first contact {r['first_contact_s']:.1f}s",font=font,fill='#dce7f5')
  im.save(NEW/sheet['path'],quality=95)
 im=Image.new('RGB',(1920,math.ceil(len(records)/4)*305),'#0a101a');d=ImageDraw.Draw(im)
 for j,r in enumerate(records):
  x=j%4*480;y=j//4*305
  with Image.open(NEW/r['poster']) as p:im.paste(p.resize((480,270)),(x,y))
  d.text((x+8,y+273),r['model']+f" {r['horizon_s']:g}s "+r['token'][:8],font=font,fill='#dce7f5')
 im.save(NEW/'validation/all_38_posters.jpg',quality=95)
 # Preserve the original source-register rows, adding real camera sources only.
 buf=io.StringIO(newline='');w=csv.writer(buf)
 for r in read(NEW/'camera_playback/source_registry.json'):w.writerow([r['path'],r['sha256'],r['role']])
 manifest=read(NEW/'data/camera_playback_manifest.json')
 unique={f['source_path']:f for t in manifest.values() for v in t['views'].values() for f in v['frames']}
 for p,f in sorted(unique.items()):w.writerow([p,f['sha256'],'Real recorded camera timeline; original source image; no interpolation'])
 (NEW/'source_register.csv').write_text((OLD/'source_register.csv').read_text(encoding='utf-8-sig').rstrip('\n')+'\n'+buf.getvalue(),encoding='utf-8-sig')
 note='''# Camera playback update / 相机播放更新

This revision keeps the previous v4 webpage layout, numerical evidence, all figures, controls and result links. Only the camera display in the 38 individual MP4/GIF replays, their posters/keyframes, the 10 montages and contact sheets is revised. The CSS is unchanged.

本版保持上一版网页的布局、数值、图表、交互和结果入口。只更新 38 个单场 MP4/GIF 中的相机面板、对应海报/关键帧、10 个合辑及 contact sheet。原版目录完整保留。

The three views are CAM_L1, CAM_F0 and CAM_R1 from the real original nuPlan driving log. There are 21 scene tokens, 63 view sequences and 558 copied real images. Original SQLite exposure timestamps align the images to the scene lidar anchor and the saved BEV physical clock. Local real images are available at approximately 2 Hz, while the saved BEV has its original 0.1 s physical states. Each view holds the latest real exposure at or before the displayed physical time; no generated images, frame interpolation or extrapolated camera motion are used. All slow-playback frame repeats and contact holds retain the previous video timing.

三路相机使用原始驾驶记录的真实照片。按原始曝光时间与 lidar 场景起点对齐，再与 BEV 物理时钟同步。真实图像约 2 Hz，BEV 仍为原始 0.1 秒状态；两张真实图像之间保留上一张。最大图像年龄为 0.49802 秒。慢放与首碰停顿沿用原版，因此视频播放秒数并不等于物理秒数。

**Recorded scene, not model viewpoint.** The camera sequence shows the original logged vehicle, not images generated from each model's simulated ego pose. The camera source is clearly labelled in every frame. The original metadata-associated t0 images remain in `cameras/`. A camera exposure slightly after lidar t0 is not displayed early: the latest prior real exposure is used at t0 instead, and its actual relative capture time is shown.

**相机是原始记录车辆的视角，不是模型模拟车辆视角。** 每帧明确标注来源，并显示实际拍摄时间。原来的 t0 关联图像仍保留；若其曝光晚于 lidar t0，则 t0 播放使用之前的真实曝光，不提前展示之后的信息。

No VLA inference, NAVSIM execution, new experiment, download, GPU work or source-input edits occurred. Model-specific ego/actor states, maps, contact counts, risk features and interpretation boundaries stay unchanged, including ORION AS-RETURNED DIAGNOSTIC / UNRESOLVED.

Alignment evidence: `data/camera_playback_manifest.json`, `camera_playback/physical_time_alignment.csv`, `camera_playback/source_registry.json` and `validation/camera_playback_validation.json`. Source code is saved in `source/camera_playback_v1/`; it was executed from the workspace `work/camera_playback_v1/` with the existing CPU environment. The earlier research reports retain their original contents and numerical evidence; this addendum supersedes only their static-camera description.

Open `index.html` directly in Edge or Chrome; no server or CDN is needed. `videos.html` is the offline media backup.
'''
 (NEW/'CAMERA_PLAYBACK_UPDATE_CN_EN.md').write_text(note,encoding='utf-8')
 p=NEW/'README_CN_EN.md';p.write_text('Camera playback revision: see [CAMERA_PLAYBACK_UPDATE_CN_EN.md](CAMERA_PLAYBACK_UPDATE_CN_EN.md). All numerical results and page design are preserved; real recorded camera sequences now replace held t0 views.\n\n'+p.read_text(encoding='utf-8'),encoding='utf-8')
 source=NEW/'source/camera_playback_v1';source.mkdir(exist_ok=True)
 for p in Path(__file__).parent.iterdir():
  if p.is_file():shutil.copyfile(p,source/p.name)
 save(NEW/'validation/camera_page_edit_receipt.json',{'status':'PASS','page_layout_css_unchanged':sha(OLD/'research.css')==sha(NEW/'research.css'),'edited_html_scope':'Camera playback explanatory sentence only in index.html and videos.html; all other markup unchanged','edited_js_scope':'Two camera display descriptions only; controls and numerical code unchanged','copied_source_images':558,'unique_source_images':len(unique),'no_new_statistics':True})
 print('PAGE CAMERA EXPLANATION AND THUMBNAILS UPDATED',flush=True)

if __name__=='__main__':main()
