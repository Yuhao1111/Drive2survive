// Offline artifact QA fallback: browser plugin bootstrap is unavailable on this host.
// Dedicated headless instance; does not attach to or control the user's browser.
const fs=require('fs'),path=require('path'),assert=require('assert');
const {chromium}=require('C:/Users/Yuhao/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const root=path.resolve(__dirname,'../../outputs/multivla_research_dashboard_v4_en'),vp=path.join(root,'validation');
let runningBrowser;
(async()=>{
 const browser=runningBrowser=await chromium.launch({headless:true,executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',args:['--disable-gpu']});
 const page=await browser.newPage({viewport:{width:1600,height:1100}}),errors=[],network=[],failed=[];
 page.on('pageerror',e=>errors.push(String(e)));page.on('request',r=>{if(/^https?:/.test(r.url()))network.push(r.url());});page.on('requestfailed',r=>{if(r.failure().errorText!=='net::ERR_ABORTED')failed.push({url:r.url(),error:r.failure()});});
 await page.route(/^https?:/,r=>r.abort());await page.goto('file:///'+root.replace(/\\/g,'/')+'/index.html',{waitUntil:'load',timeout:120000});await page.waitForFunction(()=>window.RESEARCH_TEST);
 const dataCheck=await page.evaluate(()=>{let count=0;const failures=[];for(const p of Object.values(RESEARCH_DATA.panels))for(const c of p.curves){const z=RESEARCH_TEST.stats(p,p.meta.metric,c.threshold);count++;if(z.n!==c.n_selected||z.k!==c.n_contact_selected||z.ee.length!==c.n_metric_eligible||z.pos!==c.n_contact_cohort||Math.abs((z.q||0)-(c.precision||0))>1e-10||Math.abs((z.ci[0]||0)-(c.wilson_lower||0))>1e-10)failures.push({meta:p.meta,c,z});}return{thresholds:count,mismatches:failures.slice(0,5)};});assert.equal(dataCheck.mismatches.length,0,JSON.stringify(dataCheck));
 let distributions=0,risks=0;
 for(const sc of ['saved_common3s','available_horizon']){
  await page.selectOption('#scope',sc);assert.equal(await page.locator('.video-card').count(),sc==='saved_common3s'?13:33);
  for(const k of ['TTC','TIT','DRAC','PET','TET']){
   await page.locator(`[data-metric="${k}"]`).click();
   for(const w of ['FULL_ROLLOUT','PRE_FIRST_CONTACT','L1_NEXT1S','L1_TO_HORIZON','L2_NEXT1S','L2_TO_HORIZON'])for(const g of ['all','contact','no_contact']){
    await page.selectOption('#dist-window',w);await page.selectOption('#dist-group',g);assert.equal(await page.locator('#distribution-counts tbody tr').count(),4);const svg=await page.locator('#density-charts').innerHTML();assert(!/\bNaN\b|Infinity/.test(svg));distributions++;
   }
   await page.selectOption('#risk-metric',k);
   for(const w of ['L1_NEXT1S','L1_TO_HORIZON','L2_NEXT1S','L2_TO_HORIZON']){
    await page.selectOption('#risk-window',w);assert.equal(await page.locator('#risk-table tbody tr').count(),4);assert.equal(await page.locator('#target-table tbody tr').count(),8);assert.equal(await page.locator('#threshold-slider').isDisabled(),k==='PET');risks++;
   }
  }
 }
 await page.selectOption('#scope','saved_common3s');await page.selectOption('#dist-window','PRE_FIRST_CONTACT');await page.selectOption('#dist-group','all');await page.locator('[data-metric="TTC"]').click();await page.selectOption('#risk-metric','TIT');await page.selectOption('#risk-window','L1_TO_HORIZON');
 const reference=await page.locator('#risk-table').innerText();for(const s of ['1/2','2/4','3/4'])assert(reference.includes(s));
 await page.evaluate(()=>scrollTo(0,0));await page.screenshot({path:path.join(vp,'web_01_purpose.png')});
 for(const [id,name] of [['contacts','02_contacts'],['distributions','03_density_ecdf'],['tet','04_tet'],['landmark','05_fixed_landmark']]){await page.locator('#'+id).evaluate(e=>e.scrollIntoView({block:'start',behavior:'instant'}));await page.screenshot({path:path.join(vp,'web_'+name+'.png')});}
 const tokenLink=page.locator('#selected-tokens a[data-case]').first();await tokenLink.click();assert.equal(await page.locator('.video-card.highlight').count(),1);await page.locator('.video-card.highlight').screenshot({path:path.join(vp,'web_06_input_and_execution.png')});
 const playback=[];
 for(const m of ['autovla','impromptu','orion','opendrivevla']){
  await page.selectOption('#video-model',m);
  playback.push(await page.locator('.video-card video').first().evaluate(async v=>{v.muted=true;v.load();await new Promise((res,rej)=>{v.onloadeddata=res;v.onerror=()=>rej(Error(v.error?.message));setTimeout(()=>rej(Error('media timeout')),20000);});await v.play();await new Promise(r=>setTimeout(r,600));let z={src:v.querySelector('source').getAttribute('src'),width:v.videoWidth,height:v.videoHeight,duration:v.duration,currentTime:v.currentTime,playing:!v.paused};v.pause();if(!(z.currentTime>0))throw Error('No playback');return z;}));
 }
 await page.selectOption('#video-model','all');await page.setViewportSize({width:390,height:844});await page.locator('#distributions').scrollIntoViewIfNeeded();await page.screenshot({path:path.join(vp,'web_07_mobile.png')});const mobile=await page.evaluate(()=>({width:innerWidth,scrollWidth:document.documentElement.scrollWidth}));assert(mobile.scrollWidth<=mobile.width,'Mobile page overflow '+JSON.stringify(mobile));
 const broken=await page.evaluate(()=>Array.from(document.images).filter(i=>i.complete&&!i.naturalWidth).map(i=>i.src));assert.equal(broken.length,0);assert.equal(network.length,0);assert.equal(errors.length,0,JSON.stringify(errors));assert.equal(failed.length,0,JSON.stringify(failed));
 fs.writeFileSync(path.join(vp,'browser_validation.json'),JSON.stringify({status:'PASS',method:'Dedicated offline headless Edge fallback after unavailable browser-plugin bootstrap; did not attach to user browser',protocol:'file://',dataCheck,distribution_combinations:distributions,risk_combinations:risks,playback,mobile,broken,network,errors,failed},null,2));console.log('BROWSER PASS',distributions,'distributions',risks,'risk windows',playback.length,'model playback checks');await browser.close();
})().catch(async e=>{console.error(e);if(runningBrowser)await runningBrowser.close();process.exitCode=1;});
