'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const {chromium}=require('playwright');
const html=fs.readFileSync('index.html','utf8');
const source=fs.readFileSync('clube.js','utf8');
const ui=source.slice(source.indexOf('/* Clan social beta:'),source.indexOf("let saved=localStorage.getItem('damas-name');"));
const staticHtml=html.replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi,'').replace(/<link\b[^>]*href="([^"]+)"[^>]*>/gi,(tag,url)=>{
  if(!url.startsWith('/')||!url.split('?')[0].endsWith('.css'))return '';
  const path=url.split('?')[0].slice(1);return fs.existsSync(path)?'<style>'+fs.readFileSync(path,'utf8')+'</style>':'';
});
const data={me:{id:'me',name:'Fundador',level:5,xp:800},account:true,mine:null,clans:[],requests:[]};
(async()=>{
  const browser=await chromium.launch({headless:true});
  try{
    for(const width of [375,758,1280]){
      const page=await browser.newPage({viewport:{width,height:800}});
      await page.route('**/*',r=>r.abort());
      await page.setContent(staticHtml);
      await page.evaluate(({ui,data})=>{
        const E=id=>document.getElementById(id),S={registered:true,data:{players:[]}};
        function node(t,c,txt){let e=document.createElement(t);if(c)e.className=c;if(txt!==undefined)e.textContent=txt;return e}
        function button(l,fn,primary){let b=node('button',primary?'primary':'secondary',l);b.type='button';b.onclick=fn;return b}
        const show=id=>{document.querySelectorAll('.club-overlay').forEach(el=>el.classList.add('hidden'));E(id).classList.remove('hidden')};
        const api=new Function('E','S','node','button','profileToken','request','poll','show','status','confirm',ui+';return {renderClan,set:(d,t)=>{clanData=d;clanTab=t}}')(E,S,node,button,()=>'token',async()=>data,()=>{},show,()=>{},()=>true);
        show('clanoverlay');api.set(data,'browse');api.renderClan();
      },{ui,data});
      const search=page.locator('.clan-directory-search input'),label=page.locator('.clan-directory-search .clan-field-label'),btn=page.locator('.clan-directory-search button');
      const [a,b,c]=await Promise.all([search.boundingBox(),label.boundingBox(),btn.boundingBox()]);
      assert(a.width>=130,'search input too narrow at '+width);
      assert(b.height<=34,'search label wrapped into vertical letters at '+width);
      assert(a.x+a.width<=c.x+1,'search input overlaps button at '+width);
      assert.equal(await page.locator('#menuclans').getAttribute('class'),'secondary');
      assert(await page.locator('#clanoverlay .clan-shell').evaluate(el=>el.scrollWidth<=el.clientWidth+2),'horizontal overflow');
      await page.getByRole('button',{name:'Criar clã',exact:true}).click();
      await page.getByLabel('Nome do clã',{exact:true}).fill('Chama Eterna');
      await page.getByLabel('Sigla · 2–6 letras ou números').fill('C.T');
      assert(await page.getByRole('button',{name:'Fundar ordem',exact:true}).isDisabled());
      await page.getByLabel('Sigla · 2–6 letras ou números').fill('ce');
      await page.getByLabel('Descrição',{exact:true}).fill('Honra, lealdade e glória.');
      await page.getByLabel('Brasão da ordem').selectOption('knight');
      assert.equal(await page.locator('.clan-preview-name').textContent(),'Chama Eterna');
      assert.equal(await page.locator('.clan-preview-tag').textContent(),'[ CE ]');
      assert.equal(await page.locator('.clan-preview-description').textContent(),'Honra, lealdade e glória.');
      assert.equal(await page.locator('.clan-foundation-preview .clan-crest').getAttribute('data-emblem'),'knight');
      assert(!(await page.getByRole('button',{name:'Fundar ordem',exact:true}).isDisabled()));
      assert.equal(await page.locator('.clan-foundation-form input[type=number]').count(),7);
      assert(await page.locator('#clanoverlay .clan-shell').evaluate(el=>el.scrollWidth<=el.clientWidth+2),'creation horizontal overflow');
      console.log('CLAN UI OK:',width,'px; search, live preview, validation, responsive layout');
      await page.close();
    }
  }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
