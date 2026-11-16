(()=>{
'use strict';
const C=window.ChessEngine,$=id=>document.getElementById(id);
// Original carved chess set. One shared SVG definition sheet, no images or filters.
const NS='http://www.w3.org/2000/svg';
const shape={
 p:'<path d="M26 55 Q29 49 31 42 L33 33 Q24 30 24 22 A12 12 0 1 1 48 22 Q48 30 39 33 L41 42 Q43 49 46 55Z"/><path d="M27 35 Q36 39 45 35 L43 40 Q36 43 29 40Z" class="chess-carved-band"/><path d="M30 19 Q31 13 37 12" class="chess-carved-light"/>',
 r:'<path d="M22 55 L27 47 L28 30 L20 26 L20 11 L28 11 L28 18 L33 18 L33 11 L39 11 L39 18 L44 18 L44 11 L52 11 L52 26 L44 30 L45 47 L50 55Z"/><path d="M21 26 H51 L44 32 H28Z" class="chess-carved-band"/><path d="M32 34 L31 46 M40 34 L41 46 M25 21 H47" class="chess-carved-detail"/>',
 n:'<path d="M20 55 Q24 48 26 42 Q27 36 35 30 L30 31 L23 37 L14 33 L15 27 L26 16 L29 6 L36 12 L44 9 Q53 15 55 28 Q57 40 48 55Z"/><path d="M40 15 Q49 22 49 32 Q49 42 41 49 L46 54 H52 Q58 41 55 28 Q53 15 44 9Z" class="chess-carved-band"/><path d="M17 28 L26 25 L30 18 M19 33 L24 31 M38 24 Q41 32 34 40" class="chess-carved-detail"/><circle cx="29" cy="22" r="2.2" class="chess-carved-eye"/><path d="M34 13 Q41 17 44 25" class="chess-carved-light"/>',
 b:'<path d="M22 55 Q30 48 30 35 L26 31 Q18 24 26 14 L36 4 L46 14 Q54 24 46 31 L42 35 Q42 48 50 55Z"/><path d="M28 13 L40 25" class="chess-carved-cut"/><path d="M25 31 Q36 36 47 31 L44 38 Q36 41 28 38Z" class="chess-carved-band"/><path d="M37 8 L44 16 M34 41 L31 50" class="chess-carved-light"/>',
 q:'<path d="M21 55 Q29 47 30 35 L20 21 L13 10 L26 19 L36 7 L46 19 L59 10 L52 21 L42 35 Q43 47 51 55Z"/><circle cx="13" cy="10" r="4"/><circle cx="36" cy="7" r="4"/><circle cx="59" cy="10" r="4"/><path d="M20 23 Q36 28 52 23 L45 33 Q36 37 27 33Z" class="chess-carved-band"/><path d="M36 13 V23 M25 24 L29 31 M47 24 L43 31" class="chess-carved-detail"/><path d="M33 40 Q33 47 28 51" class="chess-carved-light"/>',
 k:'<path d="M21 55 Q28 47 29 36 Q19 31 21 22 Q23 14 32 19 L32 12 H25 V7 H32 V1 H40 V7 H47 V12 H40 V19 Q49 14 51 22 Q53 31 43 36 Q44 47 51 55Z"/><path d="M23 29 Q36 35 49 29 L43 38 Q36 42 29 38Z" class="chess-carved-band"/><path d="M36 4 V19 M29 10 H43 M36 22 V31" class="chess-carved-detail"/><path d="M32 41 Q32 47 27 51" class="chess-carved-light"/>'
};
function installArt(){
 const svg=document.createElementNS(NS,'svg');svg.setAttribute('aria-hidden','true');svg.classList.add('chess-art-defs');
 const palettes={white:['#fff4d8','#ddba82','#94602f','#71491f','#fff1c5','#b37a3b'],black:['#b78a58','#67452f','#2b1b16','#d1a16c','#e4ba80','#3b251b']};
 let defs='';
 for(const [color,c] of Object.entries(palettes)){
 defs+='<linearGradient id="chess-'+color+'-wood" x1="0" y1="0" x2="1" y2=".2"><stop stop-color="'+c[2]+'"/><stop offset=".28" stop-color="'+c[1]+'"/><stop offset=".46" stop-color="'+c[0]+'"/><stop offset=".73" stop-color="'+c[1]+'"/><stop offset="1" stop-color="'+c[2]+'"/></linearGradient><linearGradient id="chess-'+color+'-base" x1="0" y1="0" x2="0" y2="1"><stop stop-color="'+c[0]+'"/><stop offset=".38" stop-color="'+c[1]+'"/><stop offset="1" stop-color="'+c[2]+'"/></linearGradient>';
 for(const [type,body] of Object.entries(shape)){
 const stylized=body.replaceAll('class="chess-carved-band"','fill="url(#chess-'+color+'-base)" stroke="'+c[3]+'"').replaceAll('class="chess-carved-light"','fill="none" stroke="'+c[4]+'" stroke-width="1.8" opacity=".8"').replaceAll('class="chess-carved-detail"','fill="none" stroke="'+c[3]+'" stroke-width="1.8"').replaceAll('class="chess-carved-cut"','fill="none" stroke="'+c[5]+'" stroke-width="4"').replaceAll('class="chess-carved-eye"','fill="'+c[5]+'" stroke="'+c[4]+'" stroke-width=".7"');
 defs+='<symbol id="chess-art-'+color+'-'+type+'" viewBox="0 0 72 78"><ellipse cx="36" cy="70" rx="27" ry="5" fill="#21140c" opacity=".34"/><g transform="translate(0 3)" fill="url(#chess-'+color+'-wood)" stroke="'+c[3]+'" stroke-width="1.5" stroke-linejoin="round" stroke-linecap="round">'+stylized+'<path d="M20 52 Q36 56 52 52 L56 58 L54 61 H18 L16 58Z" fill="url(#chess-'+color+'-base)"/><path d="M18 60 H54 Q60 62 60 67 L58 70 H14 L12 67 Q12 62 18 60Z" fill="url(#chess-'+color+'-base)"/><path d="M17 65 Q36 67 55 65 M22 55 Q36 58 50 55" fill="none" stroke="'+c[4]+'" opacity=".68" stroke-width="1.2"/></g></symbol>';
 }}
 svg.innerHTML='<defs>'+defs+'</defs>';document.body.prepend(svg);
}
function pieceArt(p){
 const color=C.side(p)===1?'white':'black',svg=document.createElementNS(NS,'svg'),use=document.createElementNS(NS,'use');
 svg.setAttribute('viewBox','0 0 72 78');svg.setAttribute('aria-hidden','true');svg.setAttribute('class','chess-piece '+color);svg.dataset.piece=p;use.setAttribute('href','#chess-art-'+color+'-'+p.toLowerCase());svg.append(use);return svg;
}
installArt();
const pieceNames={k:'Rei',q:'Dama',r:'Torre',b:'Bispo',n:'Cavalo',p:'Peão'};
const start=()=>C.parseFen(C.START),savedKey='chess-local-v1';
let history=[start()],moves=[],selected=-1,promotion=null,flipped=false,claimed='',auto=true,profile=null,fetching=false,mode='local',level='medium',remote=null,queued=false,localMinutes=0,localRemaining={w:0,b:0},localClockAt=performance.now(),clockStarted=false,clockAt=performance.now(),botTimer=null,rankData=null,motionRun=null,deferredData=null;
const sideKey=()=>game().t===1?'w':'b',game=()=>history.at(-1);
function rebuild(keys){let h=[start()],ms=[];for(let u of keys){let g=h.at(-1),m=C.legal(g).find(m=>C.key(m)===u);if(!m)throw Error('Lance inválido no histórico');ms.push({key:u,label:C.san(g,m),side:g.t,full:g.full,from:m[0],to:m[1]});h.push(C.apply(g,m))}history=h;moves=ms}
function restore(){history=[start()];moves=[];claimed='';selected=-1;promotion=null;flipped=false;clockStarted=false;localMinutes=0;localRemaining={w:0,b:0};
 try{let x=JSON.parse(sessionStorage.getItem(savedKey)||'null');if(x&&Array.isArray(x.moves)&&x.moves.length<=1000){rebuild(x.moves);auto=x.auto!==false;flipped=auto?game().t===-1:!!x.flipped;claimed=typeof x.claimed==='string'?x.claimed.slice(0,100):'';localMinutes=[0,1,3,5,10,15,30].includes(x.minutes)?x.minutes:0;localRemaining={w:Math.max(0,Number(x.remaining?.w??localMinutes*60)),b:Math.max(0,Number(x.remaining?.b??localMinutes*60))};clockStarted=!!x.started}}catch{}localClockAt=performance.now();$('chess-time').value=String(localMinutes)}
function save(){if(mode!=='local')return;try{sessionStorage.setItem(savedKey,JSON.stringify({moves:moves.map(m=>m.key),auto,flipped,claimed,minutes:localMinutes,remaining:localRemaining,started:clockStarted}))}catch{}}
function element(tag,cls,text){let e=document.createElement(tag);if(cls)e.className=cls;if(text!==undefined)e.textContent=text;return e}
function button(label,fn,cls){let b=element('button',cls,label);b.type='button';b.onclick=fn;return b}
function open(id){for(let d of document.querySelectorAll('dialog[open]'))d.close();$(id).showModal();if(id==='friends-dialog'||id==='ranking-dialog')poll()}
const ended=()=>!!claimed||(mode==='local'?C.status(history).done:!!remote?.result);
const canPlay=()=>!ended()&&(mode==='local'||!!remote&&sideKey()===remote.side&&!fetching);
const activeRemote=()=>!!remote&&!remote.result;
function msg(t){$('chess-message').textContent=t}
function remoteText(r){if(!r)return '';let winner=r.winner==='w'?'Brancas':r.winner==='b'?'Pretas':'';const reasons={checkmate:'xeque-mate',timeout:'tempo',resign:'desistência',stalemate:'afogamento',insufficient_material:'material insuficiente',fivefold_repetition:'repetição quíntupla',seventyfive_moves:'75 lances',claimed_draw:'empate reivindicado',agreement:'acordo'};return winner?winner+' venceram · '+(reasons[r.reason]||r.reason):'Empate · '+(reasons[r.reason]||r.reason)}
function statusText(){if(claimed)return claimed;if(remote?.result&&mode!=='local')return remoteText(remote.result);if(mode!=='local'&&!remote)return queued?'Buscando adversário…':'Escolha uma partida';if(mode==='ai'&&remote&&sideKey()!==remote.side)return 'Vez do Computador';return C.status(history).text}
function updateControls(){
 const playing=activeRemote(),locked=playing||queued;
 $('chess-mode-label').textContent=mode==='ai'?'COMPUTADOR':mode==='online'?'ONLINE':'LOCAL';
 document.querySelectorAll('[data-chess-mode]').forEach(b=>{let on=b.dataset.chessMode===mode;b.classList.toggle('active',on);b.setAttribute('aria-pressed',String(on));b.disabled=locked&&!on});
 document.querySelectorAll('[data-chess-level]').forEach(b=>{let on=b.dataset.chessLevel===level;b.classList.toggle('active',on);b.setAttribute('aria-pressed',String(on));b.disabled=locked});
 $('chess-difficulty').hidden=mode!=='ai';$('chess-online-settings').hidden=mode!=='online';$('chess-auto-field').hidden=mode!=='local';
 $('chess-time').disabled=locked||mode==='local'&&clockStarted&&!ended();$('chess-ranked').disabled=locked;
 $('chess-rewardhint').textContent=level==='easy'?'Fácil · treino, sem PH ou moedas.':level==='medium'?'Médio · 50% de PH e moedas.':'Difícil · 100% de PH e moedas.';
 $('chess-side-hint').textContent=mode==='local'?'Local: as brancas começam.':remote?'Suas peças: '+(remote.side==='w'?'brancas':'pretas')+'.':'As cores serão sorteadas ao iniciar.';
 $('chess-search').disabled=locked||fetching;$('chess-cancel-search').hidden=!queued;$('chess-challenge').disabled=locked||fetching;
 $('sidebar-new').disabled=locked||mode==='online';$('chess-new').disabled=locked||mode==='online';$('sidebar-new').textContent=mode==='online'?'Use Buscar partida ou Desafiar':'Nova partida';
 $('chess-back').disabled=mode!=='local'||!moves.length&&!claimed;$('chess-resign').disabled=$('sidebar-resign').disabled=mode==='local'?ended():!playing;
 $('chess-draw-actions').hidden=mode!=='online'||!playing;$('chess-offer').textContent=remote?.offer&&remote.offer!==remote.side?'Aceitar empate':'Oferecer empate';$('chess-offer').disabled=!!remote?.offer&&remote.offer===remote.side;$('chess-decline').hidden=!(remote?.offer&&remote.offer!==remote.side);
 $('white-name').textContent=mode==='local'?(profile?.name||'Brancas'):(remote?.names.w||'Brancas');$('black-name').textContent=mode==='local'?'Pretas':(remote?.names.b||'Pretas');
}
// The game state is authoritative; only transient SVG copies move above the grid.
function stopMotion(){
 if(!motionRun)return;const run=motionRun;motionRun=null;for(const a of run.animations)a.cancel();run.layer.remove();for(const p of run.hidden)p.style.visibility='';
 const data=deferredData;deferredData=null;if(data)queueMicrotask(()=>{if(remote?.id===data.match?.id&&data.match.moves.length>moves.length)applyData(data)});
}
function animateMove(board,{before,move,viewFlip}){
 if(document.hidden||matchMedia('(prefers-reduced-motion: reduce)').matches||!Element.prototype.animate)return false;
 const [from,to,promo,flag]=move,p=before.b[from],br=board.getBoundingClientRect();
 if(!br.width)return false;
 const cell=i=>board.querySelector('[data-square="'+C.sq(i)+'"]');
 const rect=i=>{const r=cell(i).getBoundingClientRect();return{x:r.left-br.left-board.clientLeft,y:r.top-br.top-board.clientTop,w:r.width,h:r.height}};
 const layer=element('div','chess-motion-layer');layer.setAttribute('aria-hidden','true');board.append(layer);
 const run={layer,animations:[],hidden:[]};motionRun=run;
 const ghost=(piece,i)=>{const r=rect(i),el=element('div','chess-motion-ghost');el.style.cssText='left:'+(r.x+r.w*.06)+'px;top:'+(r.y+r.h*.04)+'px;width:'+(r.w*.88)+'px;height:'+(r.h*.92)+'px';el.append(pieceArt(piece));layer.append(el);return el};
 const hide=i=>{const el=cell(i).querySelector('.chess-piece');if(el){el.style.visibility='hidden';run.hidden.push(el)}};
 const duration=p.toLowerCase()==='n'?400:340;
 const captured=flag==='ep'?to+16*before.t:to;
 if(before.b[captured]!=='.'){const el=ghost(before.b[captured],captured);run.animations.push(el.animate([{opacity:1,transform:'scale(1)'},{opacity:1,offset:.45,transform:'scale(1)'},{opacity:0,transform:'scale(.7) translateY(6px)'}],{duration,fill:'forwards',easing:'ease-out'}))}
 const slide=(piece,a,b,jump=false,promote=false)=>{
  const r=rect(a),d=rect(b),dx=d.x-r.x,dy=d.y-r.y,el=ghost(piece,a);hide(b);
  const dest='translate('+dx+'px,'+dy+'px)';
  let frames=jump?[{transform:'translate(0px,0px)'},{transform:'translate('+dx*.5+'px,'+(dy*.5-r.h*.20)+'px) scale(1.07)',offset:.5},{transform:dest}]:[{transform:'translate(0px,0px)'},{transform:dest}];
  if(promote){frames=[{transform:'translate(0px,0px)'},{transform:dest,offset:.78,opacity:1},{transform:dest+' scale(.8)',opacity:0}];const crowned=ghost(game().b[b],b);run.animations.push(crowned.animate([{opacity:0,transform:'scale(.75)'},{opacity:0,transform:'scale(.75)',offset:.72},{opacity:1,transform:'scale(1.12)',offset:.9},{opacity:1,transform:'scale(1)'}],{duration:duration+120,fill:'forwards',easing:'ease-out'}))}
  run.animations.push(el.animate(frames,{duration:promote?duration+120:duration,easing:'cubic-bezier(.25,.7,.2,1)',fill:'forwards'}));
 };
 slide(p,from,to,p.toLowerCase()==='n',!!promo);
 if(flag==='castle'){const a=to>from?from+3:from-4,b=to>from?from+1:from-1;slide(before.b[a],a,b)}
 Promise.allSettled(run.animations.map(a=>a.finished)).then(()=>{if(motionRun!==run)return;stopMotion();if(viewFlip!==flipped)render();});
 return true;
}
function render(motion=null){
 stopMotion();
 const g=game(),st=C.status(history),done=ended(),legal=canPlay()?C.legal(g):[],targets=new Set(legal.filter(m=>m[0]===selected).map(m=>m[1])),last=moves.at(-1),board=$('chess-board'),playable=new Set(legal.map(m=>m[0]));
 const check=C.checked(g)?g.b.indexOf(g.t===1?'K':'k'):-1,viewFlip=motion?motion.viewFlip:flipped;
 board.replaceChildren();
 for(let n=0;n<64;n++){let j=viewFlip?63-n:n,i=(j>>3)*16+(j&7),p=g.b[i],coord=C.sq(i);
 let cell=button('',()=>click(i),'chess-square '+(((i>>4)+(i&7))%2?'dark':'light'));
 cell.dataset.square=coord;cell.setAttribute('aria-label',coord+(p!=='.'?' '+pieceNames[p.toLowerCase()]+' '+(C.side(p)===1?'branco':'preto'):' vazia'));
 if(p!=='.'){cell.classList.add('occupied');cell.append(pieceArt(p))}
 if(last&&(last.from===i||last.to===i))cell.classList.add('last');if(i===selected)cell.classList.add('selected');if(playable.has(i))cell.classList.add('playable');if(targets.has(i))cell.classList.add('target');if(check===i)cell.classList.add('check');
 if(n%8===0)cell.append(element('span','chess-coordinate rank',coord[1]));if(n>=56)cell.append(element('span','chess-coordinate file',coord[0]));board.append(cell)}
 $('chess-status').textContent=$('chess-side-status').textContent=statusText();$('white-player').classList.toggle('active',!done&&g.t===1);$('black-player').classList.toggle('active',!done&&g.t===-1);
 const hint=done?'Partida encerrada.':promotion?'Escolha a peça da promoção.':mode!=='local'&&!remote?'Inicie uma partida para jogar.':mode!=='local'&&sideKey()!==remote?.side?'Aguarde o adversário.':selected!==-1?'Escolha uma casa destacada.':'Selecione uma peça e escolha um destino disponível.';
 $('chess-hint').textContent=$('chess-side-detail').textContent=hint;$('chess-auto').checked=auto;
 $('chess-claim').hidden=done||!st.claim||!canPlay();$('chess-claim').textContent=st.claim?'Reivindicar empate · '+st.claim:'Reivindicar empate';
 $('chess-promote').hidden=!promotion;$('promotion-choices').replaceChildren();
 if(promotion){for(let m of promotion){let choice=button('',()=>play(m),'chess-promotion-choice');choice.append(pieceArt(g.t===1?m[2].toUpperCase():m[2]),element('span','',pieceNames[m[2]]));$('promotion-choices').append(choice)}$('promotion-choices').append(button('Cancelar',()=>{promotion=null;render()}))}
 const log=$('chess-history');log.replaceChildren();if(!moves.length)log.append(element('li','','Nenhum lance registrado.'));for(let m of moves.slice(-60))log.append(element('li','',m.full+(m.side===1?'. ':'... ')+m.label));log.scrollTop=log.scrollHeight;
 updateControls();paintClock();save();
 if(motion&&!animateMove(board,motion)&&viewFlip!==flipped)render();
}
function paintClock(){
 let minutes=mode==='local'?localMinutes:remote?.minutes||0,remaining=mode==='local'?localRemaining:remote?.remaining;
 for(let c of ['w','b']){let el=$('chess-clock-'+c);el.hidden=!minutes;if(minutes&&remaining){let t=remaining[c];if(mode!=='local'&&!ended()&&sideKey()===c&&!(mode==='ai'&&c!==remote.side))t-=Math.max(0,(performance.now()-clockAt)/1000);let n=Math.max(0,Math.ceil(t));el.textContent=Math.floor(n/60)+':'+String(n%60).padStart(2,'0')}}
}
function tickLocal(){if(mode!=='local'||!localMinutes||!clockStarted||ended())return;let now=performance.now(),c=sideKey();localRemaining[c]=Math.max(0,localRemaining[c]-(now-localClockAt)/1000);localClockAt=now;if(localRemaining[c]<=0){claimed=(c==='w'?'Pretas':'Brancas')+' venceram por tempo.';selected=-1;promotion=null;render()}else paintClock()}
setInterval(()=>{if(mode==='local')tickLocal();else paintClock()},200);
function click(i){if(motionRun||!canPlay()||promotion)return;let g=game(),legal=C.legal(g);if(C.side(g.b[i])===g.t){selected=selected===i?-1:i;render();return}let choices=legal.filter(m=>m[0]===selected&&m[1]===i);if(choices.length>1){promotion=choices;render()}else if(choices.length)play(choices[0])}
function play(m){let g=game(),found=C.legal(g).find(x=>C.key(x)===C.key(m));if(motionRun||!found||!canPlay())return;
 if(mode!=='local'){promotion=null;selected=-1;request('move',{match:remote.id,sequence:moves.length,move:C.key(found)});return}
 tickLocal();if(ended())return;localClockAt=performance.now();clockStarted=true;
 const viewFlip=flipped;moves.push({key:C.key(found),label:C.san(g,found),side:g.t,full:g.full,from:found[0],to:found[1]});history.push(C.apply(g,found));selected=-1;promotion=null;if(auto&&!ended())flipped=game().t===-1;render({before:g,move:found,viewFlip});poll()}
function resetLocal(){if(moves.length&&!ended()&&!confirm('Começar uma nova partida?'))return;history=[start()];moves=[];claimed='';selected=-1;promotion=null;flipped=false;localMinutes=Number($('chess-time').value);localRemaining={w:localMinutes*60,b:localMinutes*60};clockStarted=true;localClockAt=performance.now();render();poll()}
function switchMode(next){if(next===mode)return true;if(activeRemote()||queued){msg('Conclua a partida ou cancele a busca antes de trocar de modo.');return false}if(mode==='local'){tickLocal();save()}mode=next;remote=null;selected=-1;promotion=null;claimed='';history=[start()];moves=[];flipped=false;if(mode==='local')restore();render();return true}
function newGame(){if(mode==='local')resetLocal();else if(mode==='ai'&&!activeRemote())request('start',{level,minutes:Number($('chess-time').value),nonce:crypto.randomUUID()})}
function resign(){if(ended()||mode!=='local'&&!activeRemote())return;if(!confirm('Confirmar desistência?'))return;if(mode==='local'){claimed=(game().t===1?'Pretas':'Brancas')+' venceram por desistência.';selected=-1;promotion=null;render();poll()}else request('resign',{match:remote.id})}
$('chess-new').onclick=$('sidebar-new').onclick=newGame;
$('menu-local').onclick=()=>{$('menu-dialog').close();if(switchMode('local'))resetLocal()};
$('menu-computer').onclick=()=>{$('menu-dialog').close();switchMode('ai')};$('menu-online').onclick=()=>{$('menu-dialog').close();switchMode('online')};
document.querySelectorAll('[data-chess-mode]').forEach(b=>b.onclick=()=>switchMode(b.dataset.chessMode));document.querySelectorAll('[data-chess-level]').forEach(b=>b.onclick=()=>{if(!activeRemote()){level=b.dataset.chessLevel;updateControls()}});
$('chess-time').onchange=()=>{if(mode==='local'&&!clockStarted){localMinutes=Number($('chess-time').value);localRemaining={w:localMinutes*60,b:localMinutes*60};render()}};
$('chess-back').onclick=()=>{if(mode!=='local')return;if(claimed)claimed='';else if(moves.length){history.pop();moves.pop()}selected=-1;promotion=null;if(auto)flipped=game().t===-1;localClockAt=performance.now();render();poll()};
$('chess-resign').onclick=$('sidebar-resign').onclick=resign;
$('chess-claim').onclick=()=>{let st=C.status(history);if(!ended()&&st.claim){if(mode!=='local')request('claim',{match:remote.id,sequence:moves.length});else{claimed='Empate por '+st.claim+'.';selected=-1;promotion=null;render();poll()}}};
$('chess-offer').onclick=()=>request('draw',{match:remote.id,accept:true});$('chess-decline').onclick=()=>request('draw',{match:remote.id,accept:false});
$('chess-search').onclick=()=>request('queue',{minutes:Number($('chess-time').value),ranked:$('chess-ranked').value==='ranked'});
$('chess-cancel-search').onclick=()=>request('cancel');$('chess-challenge').onclick=()=>open('friends-dialog');
$('chess-flip').onclick=()=>{flipped=!flipped;render()};$('chess-auto').onchange=()=>{auto=$('chess-auto').checked;if(auto)flipped=game().t===-1;render()};
$('chess-menu').onclick=()=>open('menu-dialog');$('chess-friends').onclick=$('menu-friends').onclick=()=>open('friends-dialog');$('chess-profile').onclick=$('menu-profile').onclick=()=>open('profile-dialog');$('menu-rules').onclick=$('sidebar-rules').onclick=()=>open('rules-dialog');
$('chess-ranking-open').onclick=()=>open('ranking-dialog');document.querySelectorAll('[data-close]').forEach(e=>e.onclick=()=>$(e.dataset.close).close());
$('return-damas').onclick=e=>{if(activeRemote()||queued){e.preventDefault();msg('Conclua a partida ou cancele a busca antes de retornar às Damas.')}else{tickLocal();save()}};
function label(p){return !p.online?'Offline':(p.game==='chess'?'Xadrez':'Damas')+' · '+(p.busy?'Em partida':'Disponível')}
function rankRows(id,rows){let el=$(id);el.replaceChildren();if(!rows.length){el.append(element('p','chess-note','Nenhum jogador no ranking ainda.'));return}rows.forEach((p,i)=>{let row=element('div','chess-rank-row'+(p.own?' own':'')),info=element('div');info.append(element('b','',p.name),element('small','',p.wins+' V · '+p.losses+' D · '+p.draws+' E'+(p.own?' · SEU PERFIL':'')));row.append(element('span','rank-medal',i+1),info,element('strong','',p.points.toLocaleString('pt-BR')+' PH'));el.append(row)})}
function drawRanking(data){if(!data.profile)return;rankData=data.profile;let p=data.profile,text='Sua posição: #'+p.rank+' · '+p.points.toLocaleString('pt-BR')+' PH';$('chess-rank-own').textContent=$('chess-rank-full-own').textContent=$('chess-personal-rank').textContent=text;$('chess-profile-stats').textContent=p.points+' PH · '+p.coins+' moedas · '+p.wins+' V / '+p.losses+' D / '+p.draws+' E';rankRows('chess-ranking-top',data.ranking.slice(0,3));rankRows('chess-ranking-full',data.ranking)}
function drawSocial(data){profile=data.me;$('chess-profile').textContent=profile.name;$('chess-profile-name').textContent=profile.name;$('chess-player-name').value=profile.name;
 const list=$('chess-friend-list');list.replaceChildren();let accepted=data.friends.filter(p=>p.relation==='friend');$('friend-count').textContent=accepted.filter(p=>p.online).length?'('+accepted.filter(p=>p.online).length+' online)':'';
 const people=[...data.friends,...(data.players||[]).filter(p=>!data.friends.some(f=>f.id===p.id))];
 for(let p of people){let row=element('div','chess-friend-row'),info=element('div');info.append(element('b','',p.name),element('small','',label(p)+(p.relation==='incoming'?' · Pedido de amizade':p.relation==='outgoing'?' · Pedido enviado':p.relation==='friend'?' · Amigo':'')));row.append(element('span','chess-dot '+(p.online?(p.busy?'busy':'online'):'')),info);let invite=button('Desafiar',()=>{if(switchMode('online'))request('invite',{target:p.id,minutes:Number($('chess-time').value),ranked:$('chess-ranked').value==='ranked'})});invite.disabled=!p.online||p.busy||activeRemote()||queued;row.append(invite);list.append(row)}
 if(!people.length)list.append(element('p','','Nenhum jogador disponível.'));
 const invites=$('chess-invites');invites.replaceChildren();
 for(let x of data.chess_invites||[]){let card=element('div','chess-invite');card.append(element('b','','Convite de Xadrez · '+x.name),element('p','',(x.ranked?'Ranqueada':'Casual')+' · '+(x.minutes?x.minutes+' min':'Sem limite')),button('Aceitar',()=>{if(activeRemote()||queued)return;if(mode==='local'&&moves.length&&!ended()&&!confirm('Sua partida Local ficará salva. Aceitar desafio?'))return;request('respond',{invite:x.id,accept:true})},'gold'),button('Recusar',()=>request('respond',{invite:x.id,accept:false})));invites.append(card)}
 for(let x of data.invites||[]){let card=element('div','chess-invite');card.append(element('b','','Convite de Damas · '+x.name),element('p','','Abra Damas para escolher a modalidade e aceitar.'),button('Ver convite em Damas',()=>{if(activeRemote()||queued){msg('Conclua a partida atual.');return}tickLocal();save();sessionStorage.setItem('damas-open-friends','1');location.href='/'}));invites.append(card)}
 $('chess-social-status').textContent='Conectado · lista compartilhada';
}
function applyData(data){if(motionRun&&remote&&data.match?.id===remote.id&&data.match.moves.length>moves.length){deferredData=data;return}drawRanking(data);if(data.me)drawSocial(data);queued=!!data.queued;const g=data.match;
 if(g&&(!g.result||mode!=='local'&&remote?.id===g.id)){
  const same=remote?.id===g.id, before=game(), viewFlip=flipped, nextMove=same&&g.moves.length===moves.length+1?C.legal(before).find(m=>C.key(m)===g.moves.at(-1)):null;
  const changed=!remote||remote.id!==g.id||remote.moves.length!==g.moves.length||JSON.stringify(remote.result)!==JSON.stringify(g.result)||remote.offer!==g.offer;
  if(mode==='local'){tickLocal();save()}
  if(!remote||remote.id!==g.id){flipped=g.side==='b';selected=-1;promotion=null}
  remote=g;mode=g.mode;level=g.level||level;clockAt=performance.now();$('chess-time').value=String(g.minutes);$('chess-ranked').value=g.ranked?'ranked':'casual';
  if(changed){rebuild(g.moves);selected=-1;promotion=null;claimed='';if(g.result){let r=g.result.rewards[g.side];msg(remoteText(g.result)+(g.ranked&&r?' · '+(r.delta>=0?'+':'')+r.delta+' PH · +'+r.coins+' moedas':''))}else msg('');render(nextMove?{before,move:nextMove,viewFlip}:null)}else{updateControls();paintClock()}
 }else{if(mode==='local')$('white-name').textContent=profile?.name||'Brancas';updateControls();paintClock()}
 if(g&&g.mode==='ai'&&!g.result&&sideKey()!==g.side){clearTimeout(botTimer);botTimer=setTimeout(()=>request('bot',{match:g.id,sequence:g.moves.length}),motionRun?520:120)}
}
async function request(op,body={}){if(fetching){if(op!=='state')msg('Aguarde a sincronização e tente novamente.');return}const token=localStorage.getItem('damas-profile-token');if(!token){msg('Entre no Clube de Honra das Damas para conectar sua conta.');return}fetching=true;updateControls();try{let r=await fetch('/api/social/chess/'+op,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({profileToken:token,busy:mode==='local'&&moves.length>0&&!ended(),...body})});let data=await r.json();if(!r.ok)throw Error(data.error||'Servidor indisponível.');fetching=false;applyData(data);if(op==='invite')msg('Convite enviado. Aguarde a resposta.');if(op==='respond'&&body.accept){$('friends-dialog').close();msg('Partida iniciada.')}if(op!=='state')setTimeout(poll,80)}catch(e){msg(e.message);$('chess-social-status').textContent='Não foi possível conectar ao clube. Local continua disponível.';fetching=false;updateControls()}finally{fetching=false}}
function poll(){if(!fetching&&!document.hidden)request('state')}
window.addEventListener('focus',poll);document.addEventListener('visibilitychange',()=>{if(!document.hidden)poll();else if(mode==='local'){tickLocal();save()}});setInterval(poll,1800);
$('white-icon').append(pieceArt('K'));$('black-icon').append(pieceArt('k'));
$('chess-focus').onclick=()=>{let on=document.body.classList.toggle('chess-focus');$('chess-focus').textContent=on?'Mostrar painéis':'Modo concentração';$('chess-focus').setAttribute('aria-pressed',String(on));if(on)window.scrollTo(0,0);if(motionRun)render()};
window.addEventListener('resize',()=>{if(motionRun)render()});
restore();render();if(sessionStorage.getItem('chess-open-friends')==='1'){sessionStorage.removeItem('chess-open-friends');open('friends-dialog')}poll();
})();
