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
        window.clanTest={api,data};show('clanoverlay');api.set(data,'browse');api.renderClan();
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
      const crest=page.locator('.clan-foundation-preview .clan-crest');
      // The heading and back button must stay within the outer border while the form scrolls.
      const header=page.locator('#clanoverlay .club-head'),shell=page.locator('#clanoverlay .clan-shell'),scroll=page.locator('#clanscroll');
      await scroll.evaluate(el=>el.scrollTop=el.scrollHeight);
      const [hb,sb,cb]=await Promise.all([header.boundingBox(),shell.boundingBox(),scroll.boundingBox()]);
      assert(hb.y>=sb.y+8&&hb.y+hb.height<=cb.y+1,'header overlaps scroll or border at '+width);
      assert(hb.x>=sb.x+8&&hb.x+hb.width<=sb.x+sb.width-8,'header outside frame at '+width);
      assert(cb.y+cb.height<=sb.y+sb.height-8,'scroll content outside frame at '+width);
      assert(await scroll.evaluate(el=>el.scrollTop>0),'form should scroll');
      await page.setViewportSize({width,height:540});
      const [hs,ss,cs]=await Promise.all([header.boundingBox(),shell.boundingBox(),scroll.boundingBox()]);
      assert(ss.y>=0&&ss.y+ss.height<=541,'short viewport shell clipped');
      assert(hs.y>=ss.y+8&&hs.y+hs.height<=cs.y+1,'short viewport heading clipped');
      await page.setViewportSize({width,height:800});
      await scroll.evaluate(el=>el.scrollTop=0);
      await page.getByLabel('Estilo da moldura').selectOption('ornate');
      await page.getByRole('button',{name:'Cor do símbolo · Rubi',exact:true}).click();
      await page.getByRole('button',{name:'Cor da moldura · Prata',exact:true}).click();
      await page.getByRole('button',{name:'Cor do fundo · Vinho',exact:true}).click();
      assert.equal(await crest.getAttribute('data-frame'),'ornate');
      assert.equal(await crest.getAttribute('data-symbol-color'),'crimson');
      assert.equal(await crest.getAttribute('data-frame-color'),'silver');
      assert.equal(await crest.getAttribute('data-background-color'),'wine');
      await page.getByLabel('Brasão da ordem').selectOption('jerusalem');
      assert.equal(await crest.getAttribute('data-emblem'),'jerusalem');
      assert.equal(await crest.locator('svg.clan-jerusalem-cross path').count(),5);
      assert.equal(await crest.locator('svg.clan-jerusalem-cross').evaluate(el=>getComputedStyle(el).fill),'rgb(165, 45, 67)');
      await page.getByLabel('Brasão da ordem').selectOption('knight');
      assert.equal(await crest.locator('svg.clan-jerusalem-cross').count(),0);
      const shapes=new Set();
      for(const style of ['royal','fortress','dark','sacred','ancient','ornate']){
        await page.getByLabel('Estilo da moldura').selectOption(style);
        shapes.add(await crest.locator('.crest-outer').getAttribute('d'));
        assert((await crest.locator('svg.clan-crest-metal path').count())>=7);
        assert.equal(await crest.locator('.crest-field').getAttribute('fill'),'#672e42');
      }
      assert.equal(shapes.size,6);
      for(const label of ['Cor do símbolo','Cor da moldura','Cor do fundo'])await page.getByRole('button',{name:label+' · Ouro',exact:true}).click();
      assert(!(await page.getByRole('button',{name:'Fundar ordem',exact:true}).isDisabled()));
      assert.equal(await page.locator('.clan-foundation-form input[type=number]').count(),7);
      assert(await page.locator('#clanoverlay .clan-shell').evaluate(el=>el.scrollWidth<=el.clientWidth+2),'creation horizontal overflow');
      await page.evaluate(()=>{const {api,data}=window.clanTest;api.set({...data,mine:{id:'c',name:'Chama Eterna',tag:'CE',owner:'me',description:'Teste',emblem:'knight',crest:{symbol:'knight',symbol_color:'violet',frame_style:'dark',frame_color:'silver',background_color:'wine'},count:1,capacity:30,level:5,requirements:{},checks:[],members:[data.me]}},'personalize');api.renderClan()});
      const admin=page.locator('.clan-crest-admin-preview .clan-crest');
      assert.equal(await admin.getAttribute('data-frame'),'dark');
      assert.equal(await admin.getAttribute('data-symbol-color'),'violet');
      await page.getByLabel('Estilo da moldura').selectOption('sacred');
      assert.equal(await admin.getAttribute('data-frame'),'sacred');
      await page.getByLabel('Brasão da ordem').selectOption('jerusalem');
      assert.equal(await admin.locator('svg.clan-jerusalem-cross path').count(),5);
      assert(await page.getByRole('button',{name:'Salvar brasão',exact:true}).isVisible());
      await page.evaluate(()=>{
        const {api,data}=window.clanTest;
        const member=(id,role)=>({id,name:id,role,points:1000,wins:0,losses:0,draws:0,rate:null,level:1});
        const members=[member('king','king'),member('vice','vice'),member('captain','captain'),member('member','member')];
        window.roleFixture=(role,tab)=>{
          const me=members.find(p=>p.role===role);
          api.set({...data,me:{...me,xp:0},mine:{id:'c',name:'Ordem',tag:'ORD',owner:'king',role,description:'Teste',emblem:'shield',count:4,capacity:30,level:1,requirements:{},checks:[],members,reports:[{id:'r',author:'captain',author_name:'captain',target:'member',target_name:'member',status:'open',history:[{kind:'report',name:'captain',text:'Motivo',at:1}],can_decide:role==='king',can_reply:false,can_reopen:false}]},decisions:[]},tab);api.renderClan();
        };
        window.roleFixture('member','home');
      });
      const tab=label=>page.locator('#clantabs').getByRole('button',{name:label,exact:true});
      assert.equal(await tab('Administração').count(),0);assert.equal(await tab('Personalização').count(),0);assert.equal(await tab('Denúncias').count(),0);assert(await tab('Torneios').isVisible());
      await page.evaluate(()=>window.roleFixture('member','members'));
      const plates=page.locator('.clan-nameplate');
      assert.equal(await plates.count(),4);
      for(let i=0;i<4;i++){let plate=plates.nth(i);let name=await plate.locator('.clan-person-name').boundingBox(),badge=await plate.locator('.clan-role-badge').boundingBox();assert(badge.y>=name.y+name.height-1,'cargo must be below name')}
      assert.equal(await page.getByRole('button',{name:'Enviar convite real',exact:true}).count(),0);
      await page.evaluate(()=>window.roleFixture('king','members'));
      assert(await page.getByRole('button',{name:'Enviar convite real',exact:true}).isVisible());
      await page.evaluate(()=>window.roleFixture('captain','manage'));
      assert(await tab('Administração').isVisible());assert(await tab('Denúncias').isVisible());assert.equal(await tab('Personalização').count(),0);
      assert.equal(await page.getByRole('button',{name:'Remover',exact:true}).count(),0);
      assert.equal(await page.getByText('Denunciar jogador',{exact:true}).count(),1);
      await page.evaluate(()=>window.roleFixture('vice','personalize'));
      assert(await tab('Personalização').isVisible());assert(await page.getByRole('button',{name:'Salvar brasão',exact:true}).isVisible());
      await page.evaluate(()=>window.roleFixture('king','manage'));
      assert.equal(await page.getByRole('button',{name:'Salvar cargo',exact:true}).count(),3);
      await page.evaluate(()=>window.roleFixture('king','reports'));
      assert(await page.getByRole('button',{name:'Devolver para esclarecimentos',exact:true}).isVisible());
      assert(await page.getByRole('button',{name:'Registrar decisão',exact:true}).isVisible());
      console.log('CLAN UI OK:',width,'px; search, live preview, validation, responsive layout');
      await page.close();
    }
  }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
