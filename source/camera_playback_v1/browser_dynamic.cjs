// Offline artifact QA only. Browser plugin bootstrap failed on this host.
// This is a dedicated headless Edge instance, never the user's browser session.
const fs=require('fs'),path=require('path'),assert=require('assert');
const {chromium}=require('C:/Users/Yuhao/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const root=path.resolve(__dirname,'../../outputs/multivla_research_dashboard_v4_camera_playback_v1');
const previous=path.resolve(__dirname,'../../outputs/multivla_research_dashboard_v4_en');
const vp=path.join(root,'validation'),read=p=>JSON.parse(fs.readFileSync(p,'utf8').replace(/^\uFEFF/,''));
let browser;
(async()=>{
 browser=await chromium.launch({headless:true,executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',args:['--disable-gpu']});
 const page=await browser.newPage({viewport:{width:1600,height:1100}}),errors=[],network=[],failed=[];
 page.on('pageerror',e=>errors.push(String(e)));page.on('request',r=>{if(/^https?:/.test(r.url()))network.push(r.url())});
 page.on('requestfailed',r=>{if(r.failure().errorText!=='net::ERR_ABORTED')failed.push({url:r.url(),error:r.failure()})});
 await page.route(/^https?:/,r=>r.abort());
 await page.goto('file:///'+root.replace(/\\/g,'/')+'/index.html',{waitUntil:'load',timeout:120000});await page.waitForFunction(()=>window.RESEARCH_TEST);
 // Data and risk code were not recalculated. Check the original research object exactly.
 const previousData=JSON.parse(fs.readFileSync(path.join(previous,'data/dashboard_data.js'),'utf8').split('=').slice(1).join('=').trim().replace(/;$/,''));
 const actualData=await page.evaluate(()=>JSON.parse(JSON.stringify(window.RESEARCH_DATA)));
 delete actualData.meta.camera_note;delete previousData.meta.camera_note;assert.deepStrictEqual(actualData,JSON.parse(JSON.stringify(previousData)));
 const counts=[];for(const scope of ['saved_common3s','available_horizon']){
  await page.selectOption('#scope',scope);
  assert.equal(await page.locator('.video-card').count(),scope==='saved_common3s'?13:33);
  const expected=scope==='saved_common3s'?[2,6,3,2]:[12,6,13,2];let i=0;
  for(const m of ['autovla','impromptu','orion','opendrivevla']){
   await page.selectOption('#video-model',m);const n=await page.locator('.video-card').count();assert.equal(n,expected[i++]);counts.push({scope,model:m,n});
  }
  await page.selectOption('#video-model','all');
 }
 await page.selectOption('#scope','saved_common3s');await page.selectOption('#risk-metric','TIT');await page.selectOption('#risk-window','L1_TO_HORIZON');
 const reference=await page.locator('#risk-table').innerText();for(const s of ['1/2','2/4','3/4'])assert(reference.includes(s));
 await page.evaluate(()=>scrollTo(0,0));await page.screenshot({path:path.join(vp,'camera_web_01_unchanged_design.png')});
 await page.locator('#distributions').evaluate(e=>e.scrollIntoView({block:'start',behavior:'instant'}));await page.screenshot({path:path.join(vp,'camera_web_02_unchanged_statistics.png')});
 await page.selectOption('#scope','available_horizon');
 const playback=[];
 for(const m of ['autovla','impromptu','orion','opendrivevla']){
  await page.selectOption('#video-model',m);const video=page.locator('.video-card video').first();const src=await video.locator('source').getAttribute('src');
  const record=read(path.join(root,'data/media_index.json')).find(r=>r.mp4===src);assert(record);
  const start=record.sample_sequence.indexOf(0)/30+.20,late=record.sample_sequence.indexOf(20)/30+.015;
  await video.scrollIntoViewIfNeeded();
  const result=await video.evaluate(async(v)=>{
   const wait=ms=>new Promise(r=>setTimeout(r,ms));v.muted=true;v.load();
   await new Promise((resolve,reject)=>{if(v.readyState>=2)return resolve();v.onloadeddata=resolve;v.onerror=()=>reject(Error(v.error?.message));setTimeout(()=>reject(Error('Video load timeout')),20000)});
   await v.play();await wait(650);const playing=!v.paused,advanced=v.currentTime;v.pause();
   return {src:v.querySelector('source').getAttribute('src'),width:v.videoWidth,height:v.videoHeight,duration:v.duration,playing,advanced};
  });
  // file:// media keeps its normal origin restrictions. Inspect native screenshots
  // rather than disabling security to read a video through a canvas.
  const seek=async(t,label)=>{await video.evaluate(async(v,t)=>{await new Promise((resolve,reject)=>{v.onseeked=resolve;v.currentTime=t;setTimeout(()=>reject(Error('Seek timeout')),15000)});await new Promise(r=>setTimeout(r,200));},t);const p=path.join(vp,'camera_playback_'+m+'_'+label+'.png');await video.screenshot({path:p});return p;};
  const first=await seek(start,'t0'),later=await seek(late,'physical_2s');
  const script="from PIL import Image,ImageStat;import sys,json,hashlib;aa=Image.open(sys.argv[1]).convert('RGB');bb=Image.open(sys.argv[2]).convert('RGB');assert aa.width==bb.width;s=aa.width/1920;boxes=[tuple(round(q*s) for q in (24,y,454,y+242)) for y in (157,441,725)];assert all(max(ImageStat.Stat(im.crop(box)).stddev)>10 for im in (aa,bb) for box in boxes),'Camera screenshot has no real image';a=[hashlib.sha256(aa.crop(box).tobytes()).hexdigest() for box in boxes];b=[hashlib.sha256(bb.crop(box).tobytes()).hexdigest() for box in boxes];print(json.dumps({'camera_hashes_at_t0':a,'camera_hashes_at_physical_2s':b,'camera_views_changed':[x!=y for x,y in zip(a,b)]}))";
  const hashes=JSON.parse(require('child_process').execFileSync('C:/Users/Yuhao/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe',['-X','utf8','-c',script,first,later],{encoding:'utf8'}));
  assert(result.playing&&result.advanced>0);assert(hashes.camera_views_changed.every(Boolean));assert.equal(result.width,1920);assert.equal(result.height,1080);playback.push({model:m,...result,start_seek_s:start,later_seek_s:late,...hashes});
  await page.locator('.video-card').first().screenshot({path:path.join(vp,'camera_web_'+m+'_physical_2s.png')});
 }
 await page.selectOption('#video-model','all');await page.setViewportSize({width:390,height:844});await page.locator('#videos').evaluate(e=>e.scrollIntoView({block:'start',behavior:'instant'}));
 await page.screenshot({path:path.join(vp,'camera_web_mobile.png')});const mobile=await page.evaluate(()=>({width:innerWidth,scrollWidth:document.documentElement.scrollWidth}));assert(mobile.scrollWidth<=mobile.width);
 const broken=await page.evaluate(()=>Array.from(document.images).filter(i=>i.complete&&!i.naturalWidth).map(i=>i.src));assert.equal(broken.length,0);assert.equal(errors.length,0);assert.equal(network.length,0);assert.equal(failed.length,0,JSON.stringify(failed));
 fs.writeFileSync(path.join(vp,'camera_browser_validation.json'),JSON.stringify({status:'PASS',method:'Dedicated offline headless Edge artifact QA after browser-plugin bootstrap unavailable; no attachment to user session',protocol:'file://',all_numeric_dashboard_data_unchanged:true,counts,reference,playback,mobile,broken,network,errors,failed},null,2));
 console.log('OFFLINE CAMERA BROWSER PASS',playback.length,'models;',playback.reduce((a,r)=>a+r.camera_views_changed.filter(Boolean).length,0),'camera views advance');await browser.close();
})().catch(async e=>{console.error(e);if(browser)await browser.close();process.exitCode=1});
