'use strict';
const assert=require('node:assert/strict');
const {spawn}=require('node:child_process');
const {chromium}=require('playwright');
const server=spawn('python',['-u','-c',"import servidor as s,tempfile; from pathlib import Path; root=s.BASE; s.BASE=Path(tempfile.mkdtemp()); s.DATABASE_URL=''; [ (s.BASE/p.name).symlink_to(p) for p in root.iterdir() if p.is_file() and p.suffix in ('.html','.js','.css','.svg','.json','.png','.webp','.jpg') ]; s.setup(); h=s.ThreadingHTTPServer(('127.0.0.1',0),s.Handler); print(h.server_address[1],flush=True); h.serve_forever()"],{stdio:['ignore','pipe','inherit']});
(async()=>{
 let browser;
 try{
  const port=await new Promise((resolve,reject)=>{let timer=setTimeout(()=>reject(Error('server startup timeout')),10000);server.stdout.once('data',x=>{clearTimeout(timer);resolve(Number(String(x).trim()))});server.once('error',reject);server.once('exit',code=>reject(Error('server exited '+code)))});
  browser=await chromium.launch({headless:true});const page=await browser.newPage({viewport:{width:1280,height:800}});
  let errors=[];page.on('pageerror',e=>errors.push(e.message));await page.route('**/*',r=>r.request().url().startsWith('http://127.0.0.1:')?r.continue():r.abort());
  await page.addInitScript(()=>{localStorage.setItem('damas-name','Teste IA');localStorage.setItem('damas-profile-token','bot-ui-test-token-012345678901234567890123')});
  await page.goto('http://127.0.0.1:'+port,{waitUntil:'domcontentloaded'});
  await page.waitForFunction(()=>document.getElementById('clubnavprofile').textContent.startsWith('Teste IA ·'),{},{timeout:15000});
  assert(!(await page.locator('#clubmenu').isVisible()));
  await page.locator('#start').click();
  await page.waitForFunction(()=>botGame&&turn===mySide&&!animating&&!movePending,{},{timeout:15000});
  assert.equal(await page.evaluate(()=>botGame.level),'medium');
  const before=await page.evaluate(()=>sequence);
  const m=await page.evaluate(()=>legal(b,turn)[0]);
  await page.locator('#board [data-square="'+m.from+'"]').click();
  for(const square of m.path)await page.locator('#board [data-square="'+square+'"]').click();
  await page.waitForFunction(seq=>sequence>=seq+2&&!animating&&!movePending,before,{timeout:15000});
  await page.locator('#focusresign').click();await page.locator('#resignconfirm').click();
  await page.waitForFunction(()=>confirmedResult?.bot&&winner&&document.getElementById('resultpoints').textContent.includes('10 PH'),{},{timeout:15000});
  assert.equal(await page.evaluate(()=>confirmedResult.coins),0);
  await page.locator('#closevictory').click();
  await page.evaluate(()=>{setFocus(false);document.querySelector('[data-level=easy]').click();document.getElementById('start').click()});
  await page.waitForFunction(()=>offlineStarted&&!thinking&&!animating,{},{timeout:15000});
  assert.equal(await page.evaluate(()=>botGame),null);
  await page.evaluate(()=>{setFocus(false);document.querySelector('[data-level=hard]').click();document.getElementById('start').click()});
  await page.waitForFunction(()=>botGame?.level==='hard'&&turn===mySide&&!animating&&!movePending,{},{timeout:15000});
  await page.locator('#focusresign').click();await page.locator('#resignconfirm').click();
  await page.waitForFunction(()=>confirmedResult?.bot&&winner&&document.getElementById('resultpoints').textContent.includes('20 PH'),{},{timeout:15000});
  const profile=await page.evaluate(async()=>{const r=await fetch('/api/profile',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({profileToken:profileToken()})});return r.json()});
  assert.equal(profile.points,970);assert.equal(profile.losses,2);
  await page.locator('#closevictory').click();
  // Exercise the real local board at desktop and mobile widths. Keep the
  // old orientation until the last animation (including chained jumps) ends.
  const orientation=()=>page.evaluate(()=>({turn,flipped,first:Number(document.querySelector('#board').firstElementChild.dataset.square),sequence}));
  async function localMove(){const m=await page.evaluate(()=>legal(b,turn)[0]);await page.locator('#board [data-square="'+m.from+'"]').click();for(const square of m.path){await page.locator('#board [data-square="'+square+'"]').click();await page.waitForFunction(()=>!animating)}}
  for(const width of [1280,375]){
    await page.setViewportSize({width,height:800});
    await page.evaluate(()=>{setFocus(false);setMode('local');setRules('official');reset();startFocus()});
    assert.deepEqual(await orientation(),{turn:1,flipped:false,first:0,sequence:0});
    // Hold a single animation deliberately to verify the orientation timing.
    await page.evaluate(()=>{window.savedMoveFX=window.clubMoveFX;window.clubMoveFX=()=>new Promise(resolve=>window.releaseLocalFX=resolve)});
    const m=await page.evaluate(()=>legal(b,turn)[0]);
    await page.locator('#board [data-square="'+m.from+'"]').click();
    await page.locator('#board [data-square="'+m.path[0]+'"]').click();
    await page.waitForFunction(()=>animating&&typeof window.releaseLocalFX==='function');
    assert.deepEqual(await orientation(),{turn:-1,flipped:false,first:0,sequence:1});
    await page.evaluate(()=>{window.clubMoveFX=window.savedMoveFX;window.releaseLocalFX()});
    await page.waitForFunction(()=>!animating&&flipped);
    assert.deepEqual(await orientation(),{turn:-1,flipped:true,first:63,sequence:1});
    await localMove();
    assert.deepEqual(await orientation(),{turn:1,flipped:false,first:0,sequence:2});
    // Multi-capture: the intermediate hop must never turn the board.
    await page.evaluate(()=>{reset();startFocus();b=Array(64).fill(0);b[42]=1;b[35]=-1;b[21]=-1;b[3]=-1;b[56]=1;repeats=new Map([[key(),1]]);render()});
    await page.locator('#board [data-square="42"]').click();
    await page.locator('#board [data-square="28"]').click();
    await page.waitForFunction(()=>!animating&&prefix.length===1);
    assert.deepEqual(await orientation(),{turn:1,flipped:false,first:0,sequence:0});
    await page.locator('#board [data-square="14"]').click();
    await page.waitForFunction(()=>!animating&&flipped);
    assert.deepEqual(await orientation(),{turn:-1,flipped:true,first:63,sequence:1});
    await page.evaluate(()=>{reset();startFocus()});
    assert.deepEqual(await orientation(),{turn:1,flipped:false,first:0,sequence:0});
    console.log('LOCAL UI OK: '+width+'px; automatic turn orientation, animation, multi-capture and reset');
  }
  assert.deepEqual(errors,[]);
  console.log('BOT UI OK: server moves, medium/hard rewards, easy practice, profile persistence');
 }finally{if(browser)await browser.close();server.kill()}
})().catch(e=>{console.error(e);process.exitCode=1});
