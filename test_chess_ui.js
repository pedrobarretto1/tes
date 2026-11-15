'use strict';
const assert=require('node:assert/strict');
const {spawn}=require('node:child_process');
const {chromium}=require('playwright');
const server=spawn('python',['-u','-c',"import servidor as s,tempfile; from pathlib import Path; root=s.BASE; s.BASE=Path(tempfile.mkdtemp()); s.DATABASE_URL=''; [ (s.BASE/p.name).symlink_to(p) for p in root.iterdir() if p.is_file() and p.suffix in ('.html','.js','.css','.svg','.json','.png','.webp','.jpg') ]; s.setup(); h=s.ThreadingHTTPServer(('127.0.0.1',0),s.Handler); print(h.server_address[1],flush=True); h.serve_forever()"],{stdio:['ignore','pipe','inherit']});
(async()=>{
 let browser;
 try{
  const port=await new Promise((resolve,reject)=>{let timer=setTimeout(()=>reject(Error('server startup timeout')),10000);server.stdout.once('data',x=>{clearTimeout(timer);resolve(Number(String(x).trim()))});server.once('error',reject);server.once('exit',code=>reject(Error('server exited '+code)))});
  browser=await chromium.launch({headless:true});const page=await browser.newPage({viewport:{width:1280,height:800}}),base='http://127.0.0.1:'+port;
  const errors=[];page.on('pageerror',e=>errors.push(e.message));await page.route('**/*',r=>r.request().url().startsWith(base)?r.continue():r.abort());
  await page.addInitScript(()=>{localStorage.setItem('damas-name','Teste Portal');localStorage.setItem('damas-profile-token','chess-ui-test-token-012345678901234567890123')});
  await page.goto(base,{waitUntil:'domcontentloaded'});
  await page.waitForFunction(()=>!document.getElementById('clubmenu').classList.contains('hidden'));
  assert(await page.locator('#enter-xadrez').isVisible());await page.locator('#enter-xadrez').click();
  await page.waitForURL('**/xadrez.html');await page.waitForFunction(()=>document.getElementById('chess-profile').textContent==='Teste Portal');
  assert.equal(await page.locator('#chess-board button').count(),64);assert.equal(await page.locator('#chess-board button').first().getAttribute('data-square'),'a8');
  assert.equal(await page.locator('[data-square=d1] .chess-piece').textContent(),'♕');
  assert.equal(await page.locator('[data-square=h1]').evaluate(el=>el.classList.contains('light')),true);
  await page.locator('#chess-menu').click();assert(await page.getByRole('button',{name:'♞ Partida Local Dois jogadores'}).isVisible());assert.equal(await page.locator('#menu-dialog').getByText('Torre dos Reis').count(),0);await page.locator('[data-close=menu-dialog]').click();
  await page.locator('[data-square=e2]').click();assert(await page.locator('[data-square=e4]').evaluate(el=>el.classList.contains('target')));await page.locator('[data-square=e4]').click();
  assert.equal(await page.locator('#chess-board button').first().getAttribute('data-square'),'h1');assert.equal(await page.locator('#chess-status').textContent(),'Pretas jogam');
  await page.locator('[data-square=e7]').click();await page.locator('[data-square=e5]').click();assert.equal(await page.locator('#chess-board button').first().getAttribute('data-square'),'a8');
  await page.reload();assert.equal(await page.locator('[data-square=e4] .chess-piece').textContent(),'♙');assert.equal(await page.locator('[data-square=e5] .chess-piece').textContent(),'♟︎');
  await page.locator('#chess-back').click();assert.equal(await page.locator('#chess-status').textContent(),'Pretas jogam');
  await page.locator('#chess-friends').click();assert(await page.locator('#friends-dialog').isVisible());await page.locator('[data-close=friends-dialog]').click();
  await page.setViewportSize({width:375,height:780});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));assert.equal(await page.locator('#chess-board button').count(),64);
  await page.locator('#return-damas').click();await page.waitForURL(base+'/');assert.equal(await page.locator('h1').first().textContent(),'Casa de Damas');
  assert.deepEqual(errors,[]);console.log('CHESS UI OK: portal, separate menu, 64 squares, legal moves, rotation, save, mobile and return');
 }finally{if(browser)await browser.close();server.kill()}
})().catch(e=>{console.error(e);process.exitCode=1});
