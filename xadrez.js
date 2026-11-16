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
let journeyData=null,journeySignature='';let prefs={theme:'wood',motion:true,sound:false,volume:50};try{prefs={...prefs,...JSON.parse(localStorage.getItem('chess-preferences-v1')||'{}')}}catch{};if(!['wood','walnut','stone','crowns'].includes(prefs.theme))prefs.theme='wood';prefs.volume=Math.max(0,Math.min(100,Number(prefs.volume)||0));
function applyPrefs(){document.body.dataset.chessTheme=prefs.theme==='crowns'&&!journeyData?.complete?'wood':prefs.theme;document.body.dataset.chessMotion=prefs.motion?'on':'off';try{localStorage.setItem('chess-preferences-v1',JSON.stringify(prefs))}catch{};document.querySelectorAll('[data-chess-theme]').forEach(b=>{const on=b.dataset.chessTheme===document.body.dataset.chessTheme;if(b.dataset.chessTheme==='crowns')b.disabled=!journeyData?.complete;b.classList.toggle('active',on);b.setAttribute('aria-pressed',String(on))});$('crowns-lock').textContent=journeyData?.complete?'Conquistado':'Bloqueado';$('visual-motion').checked=!!prefs.motion;$('sound-enabled').checked=!!prefs.sound;$('sound-volume').value=prefs.volume}
let soundCtx=null;function unlockSound(){if(!prefs.sound)return;try{const Audio=window.AudioContext||window.webkitAudioContext;if(!Audio)return;soundCtx||=new Audio();if(soundCtx.state==='suspended')soundCtx.resume().catch(()=>{})}catch{}}
function playSound(capture=false,castle=false){if(!prefs.sound||!soundCtx||soundCtx.state!=='running'||!prefs.volume)return;try{const t=soundCtx.currentTime;for(let i=0;i<(castle?2:1);i++){const o=soundCtx.createOscillator(),g=soundCtx.createGain(),at=t+i*.075;o.type='triangle';o.frequency.setValueAtTime(capture?180:350,at);o.frequency.exponentialRampToValueAtTime(capture?75:140,at+.10);g.gain.setValueAtTime(.0001,at);g.gain.exponentialRampToValueAtTime(.12*prefs.volume/100,at+.009);g.gain.exponentialRampToValueAtTime(.0001,at+.13);o.connect(g);g.connect(soundCtx.destination);o.start(at);o.stop(at+.14)}}catch{}}
document.addEventListener('pointerdown',unlockSound,{passive:true});document.addEventListener('keydown',unlockSound);
const start=()=>C.parseFen(C.START),savedKey='chess-local-v1';
let history=[start()],moves=[],selected=-1,promotion=null,flipped=false,claimed='',auto=true,profile=null,fetching=false,mode='local',level='medium',remote=null,queued=false,localMinutes=0,localRemaining={w:0,b:0},localClockAt=performance.now(),clockStarted=false,clockAt=performance.now(),botTimer=null,rankData=null,motionRun=null,deferredData=null,leaving=false,fetchOp='',pendingAction=null,idlePortal=false,requestDone=Promise.resolve(),resignIntent=null,lastLocalReplay=[];
const sideKey=()=>game().t===1?'w':'b',game=()=>history.at(-1);
function rebuild(keys){let h=[start()],ms=[];for(let u of keys){let g=h.at(-1),m=C.legal(g).find(m=>C.key(m)===u);if(!m)throw Error('Lance inválido no histórico');ms.push({key:u,label:C.san(g,m),side:g.t,full:g.full,from:m[0],to:m[1]});h.push(C.apply(g,m))}history=h;moves=ms}
function restore(){history=[start()];moves=[];claimed='';selected=-1;promotion=null;flipped=false;clockStarted=false;localMinutes=0;localRemaining={w:0,b:0};
 try{let x=JSON.parse(sessionStorage.getItem(savedKey)||'null');if(x&&Array.isArray(x.moves)&&x.moves.length<=1000){rebuild(x.moves);auto=x.auto!==false;flipped=auto?game().t===-1:!!x.flipped;claimed=typeof x.claimed==='string'?x.claimed.slice(0,100):'';localMinutes=[0,1,3,5,10,15,30].includes(x.minutes)?x.minutes:0;localRemaining={w:Math.max(0,Number(x.remaining?.w??localMinutes*60)),b:Math.max(0,Number(x.remaining?.b??localMinutes*60))};clockStarted=!!x.started}}catch{}localClockAt=performance.now();$('chess-time').value=String(localMinutes)}
function save(){if(mode!=='local')return;try{sessionStorage.setItem(savedKey,JSON.stringify({moves:moves.map(m=>m.key),auto,flipped,claimed,minutes:localMinutes,remaining:localRemaining,started:clockStarted}))}catch{}}
function element(tag,cls,text){let e=document.createElement(tag);if(cls)e.className=cls;if(text!==undefined)e.textContent=text;return e}
function button(label,fn,cls){let b=element('button',cls,label);b.type='button';b.onclick=fn;return b}
function open(id){for(let d of document.querySelectorAll('dialog[open]'))d.close();$(id).showModal();if(id==='friends-dialog'||id==='ranking-dialog')poll()}
const ended=()=>!!claimed||(mode==='local'?C.status(history).done:!!remote?.result);
const canPlay=()=>!ended()&&(mode==='local'||!!remote&&!remote.paused&&sideKey()===remote.side&&(!fetching||fetchOp==='state')&&!pendingAction&&!leaving);
const activeRemote=()=>!!remote&&!remote.result;
function msg(t){$('chess-message').textContent=t}
function remoteText(r){if(!r)return '';let winner=r.winner==='w'?'Brancas':r.winner==='b'?'Pretas':'';const reasons={checkmate:'xeque-mate',timeout:'tempo',resign:'desistência',stalemate:'afogamento',insufficient_material:'material insuficiente',fivefold_repetition:'repetição quíntupla',seventyfive_moves:'75 lances',claimed_draw:'empate reivindicado',agreement:'acordo'};return winner?winner+' venceram · '+(reasons[r.reason]||r.reason):'Empate · '+(reasons[r.reason]||r.reason)}
function statusText(){if(claimed)return claimed;if(remote?.result&&mode!=='local')return remoteText(remote.result);if(mode!=='local'&&!remote)return queued?'Buscando adversário…':'Escolha uma partida';if(mode==='ai'&&remote&&sideKey()!==remote.side)return 'Vez do Computador';return C.status(history).text}
function updateControls(){
 const playing=activeRemote(),locked=playing||queued;
 const chapter=remote?.journey; $('chess-mode-label').textContent=chapter?'JORNADA':mode==='ai'?'COMPUTADOR':mode==='online'?'ONLINE':'LOCAL';
 document.querySelectorAll('[data-chess-mode]').forEach(b=>{let on=b.dataset.chessMode===mode;b.classList.toggle('active',on);b.setAttribute('aria-pressed',String(on));b.disabled=locked&&!on});
 document.querySelectorAll('[data-chess-level]').forEach(b=>{let on=b.dataset.chessLevel===level;b.classList.toggle('active',on);b.setAttribute('aria-pressed',String(on));b.disabled=locked});
 $('chess-difficulty').hidden=mode!=='ai'||!!chapter;$('chess-online-settings').hidden=mode!=='online';$('chess-auto-field').hidden=mode!=='local';
 $('chess-time').disabled=locked||mode==='local'&&clockStarted&&!ended();$('chess-ranked').disabled=locked;
 $('chess-rewardhint').textContent=level==='easy'?'Fácil · treino, sem PH ou moedas.':level==='medium'?'Médio · 50% de PH e moedas.':'Difícil · 100% de PH e moedas.';
 $('chess-side-hint').textContent=mode==='local'?'Local: as brancas começam.':remote?'Suas peças: '+(remote.side==='w'?'brancas':'pretas')+'.':'As cores serão sorteadas ao iniciar.';
 $('chess-search').disabled=locked||fetching;$('chess-cancel-search').hidden=!queued;$('chess-challenge').disabled=locked||fetching;
 $('sidebar-new').disabled=locked||mode==='online';$('chess-new').disabled=locked||mode==='online';$('sidebar-new').textContent=chapter?'Jornada do Mestre':mode==='online'?'Use Buscar partida ou Desafiar':'Nova partida';$('chess-new').textContent=chapter?'Ver jornada':'Nova partida';$('chess-settings-title').textContent=chapter?'Partida da campanha':'Escolha a partida';drawJourneyMatch();
 $('chess-back').disabled=mode!=='local'||!moves.length&&!claimed;$('chess-resign').disabled=$('sidebar-resign').disabled=mode==='local'?(ended()||!moves.length&&!clockStarted):!playing;
 $('chess-draw-actions').hidden=mode!=='online'||!playing;$('chess-offer').textContent=remote?.offer&&remote.offer!==remote.side?'Aceitar empate':'Oferecer empate';$('chess-offer').disabled=!!remote?.offer&&remote.offer===remote.side;$('chess-decline').hidden=!(remote?.offer&&remote.offer!==remote.side);
 $('white-name').textContent=mode==='local'?(profile?.name||'Brancas'):(remote?.names.w||'Brancas');$('black-name').textContent=mode==='local'?'Pretas':(remote?.names.b||'Pretas');
}
// The game state is authoritative; only transient SVG copies move above the grid.
function stopMotion(){
 if(!motionRun)return;const run=motionRun;motionRun=null;for(const a of run.animations)a.cancel();run.layer.remove();for(const p of run.hidden)p.style.visibility='';
 const data=deferredData;deferredData=null;if(data)queueMicrotask(()=>{if(remote?.id===data.match?.id&&data.match.moves.length>moves.length)applyData(data)});
}
function animateMove(board,{before,move,viewFlip}){
 if(!prefs.motion||document.hidden||matchMedia('(prefers-reduced-motion: reduce)').matches||!Element.prototype.animate)return false;
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
 $('chess-status').textContent=statusText();$('white-player').classList.toggle('active',!done&&g.t===1);$('black-player').classList.toggle('active',!done&&g.t===-1);
 const hint=done?'Partida encerrada.':promotion?'Escolha a peça da promoção.':mode!=='local'&&!remote?'Inicie uma partida para jogar.':mode!=='local'&&sideKey()!==remote?.side?'Aguarde o adversário.':selected!==-1?'Escolha uma casa destacada.':'Selecione uma peça e escolha um destino disponível.';
 $('chess-hint').textContent=hint;$('chess-auto').checked=auto;
 $('chess-claim').hidden=done||!st.claim||!canPlay();$('chess-claim').textContent=st.claim?'Reivindicar empate · '+st.claim:'Reivindicar empate';
 $('chess-promote').hidden=!promotion;$('promotion-choices').replaceChildren();
 if(promotion){for(let m of promotion){let choice=button('',()=>play(m),'chess-promotion-choice');choice.append(pieceArt(g.t===1?m[2].toUpperCase():m[2]),element('span','',pieceNames[m[2]]));$('promotion-choices').append(choice)}$('promotion-choices').append(button('Cancelar',()=>{promotion=null;render()}))}
 updateControls();paintClock();save();
 if(motion){const [f,t,,flag]=motion.move;playSound(flag==='ep'||motion.before.b[t]!=='.',flag==='castle');if(!animateMove(board,motion)&&viewFlip!==flipped)render();}
}
function paintClock(){
 let minutes=mode==='local'?localMinutes:remote?.minutes||0,remaining=mode==='local'?localRemaining:remote?.remaining;
 for(let c of ['w','b']){let el=$('chess-clock-'+c);el.hidden=!minutes;if(minutes&&remaining){let t=remote?.result?.reason==='resign'?minutes*60:remaining[c];if(mode!=='local'&&!remote?.paused&&!ended()&&sideKey()===c&&!(mode==='ai'&&c!==remote.side))t-=Math.max(0,(performance.now()-clockAt)/1000);let n=Math.max(0,Math.ceil(t));el.textContent=Math.floor(n/60)+':'+String(n%60).padStart(2,'0')}}
}
function tickLocal(){if(mode!=='local'||!localMinutes||!clockStarted||ended())return;let now=performance.now(),c=sideKey();localRemaining[c]=Math.max(0,localRemaining[c]-(now-localClockAt)/1000);localClockAt=now;if(localRemaining[c]<=0){claimed=(c==='w'?'Pretas':'Brancas')+' venceram por tempo.';selected=-1;promotion=null;render()}else paintClock()}
setInterval(()=>{if(mode==='local')tickLocal();else paintClock()},200);
function click(i){if(motionRun||!canPlay()||promotion)return;let g=game(),legal=C.legal(g);if(C.side(g.b[i])===g.t){selected=selected===i?-1:i;render();return}let choices=legal.filter(m=>m[0]===selected&&m[1]===i);if(choices.length>1){promotion=choices;render()}else if(choices.length)play(choices[0])}
function play(m){let g=game(),found=C.legal(g).find(x=>C.key(x)===C.key(m));if(motionRun||!found||!canPlay())return;
 if(mode!=='local'){promotion=null;selected=-1;request('move',{match:remote.id,sequence:moves.length,move:C.key(found)});return}
 tickLocal();if(ended())return;localClockAt=performance.now();clockStarted=true;
 const viewFlip=flipped;moves.push({key:C.key(found),label:C.san(g,found),side:g.t,full:g.full,from:found[0],to:found[1]});history.push(C.apply(g,found));selected=-1;promotion=null;if(auto&&!ended())flipped=game().t===-1;render({before:g,move:found,viewFlip});poll()}
function resetLocal(){if(moves.length&&!ended()&&!confirm('Começar uma nova partida?'))return;history=[start()];moves=[];claimed='';selected=-1;promotion=null;flipped=false;localMinutes=Number($('chess-time').value);localRemaining={w:localMinutes*60,b:localMinutes*60};clockStarted=true;localClockAt=performance.now();render();poll()}
function switchMode(next){if(next===mode&&!remote?.journey)return true;if(next===mode&&remote?.journey&&!activeRemote()){remote=null;level='medium';history=[start()];moves=[];selected=-1;promotion=null;claimed='';flipped=false;render();return true}if(activeRemote()||queued){msg('Conclua a partida ou cancele a busca antes de trocar de modo.');return false}if(mode==='local'){tickLocal();save()}mode=next;remote=null;selected=-1;promotion=null;claimed='';history=[start()];moves=[];flipped=false;if(mode==='local')restore();render();return true}
function newGame(){if(remote?.journey&&!activeRemote()){openJourney();return}if(mode==='local')resetLocal();else if(mode==='ai'&&!activeRemote())request('start',{level,minutes:Number($('chess-time').value),nonce:crypto.randomUUID()})}
function resign(){if(ended()||mode!=='local'&&!activeRemote()||mode==='local'&&!moves.length&&!clockStarted)return;resignIntent={mode,id:remote?.id};$('chess-resign-description').textContent=remote?.journey?'O mestre vencerá esta tentativa. As coroas conquistadas continuam salvas.':mode==='local'?'O outro jogador receberá a vitória. O tabuleiro será reiniciado.':'O adversário receberá a vitória e o tabuleiro voltará à posição inicial.';const points=$('chess-resign-points');points.hidden=!remote?.ranked;points.textContent='A desistência conta como derrota no Ranking de Honra.';open('chess-resign-dialog')}
function resetResignedBoard(){clearTimeout(botTimer);deferredData=null;stopMotion();history=[start()];moves=[];selected=-1;promotion=null;claimed='';flipped=false;clockStarted=false;localRemaining={w:localMinutes*60,b:localMinutes*60};localClockAt=performance.now()}
$('chess-resign-cancel').onclick=()=>$('chess-resign-dialog').close();
$('chess-resign-confirm').onclick=()=>{const intent=resignIntent;$('chess-resign-dialog').close();if(!intent||intent.mode!==mode||intent.id!==remote?.id||ended())return;if(mode==='local'){tickLocal();if(ended())return;const result=(game().t===1?'Pretas':'Brancas')+' venceram por desistência.';lastLocalReplay=moves.map(m=>m.key);resetResignedBoard();render();msg(result+' Tabuleiro reiniciado.');poll()}else if(activeRemote())request('resign',{match:remote.id})};
$('chess-resign-dialog').addEventListener('close',()=>{resignIntent=null});
$('chess-resign-dialog').addEventListener('click',e=>{if(e.target===$('chess-resign-dialog'))$('chess-resign-dialog').close()});
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
$('chess-ranking-open').onclick=$('menu-ranking').onclick=()=>open('ranking-dialog');$('menu-challenge').onclick=()=>{if(switchMode('online'))open('friends-dialog');else $('menu-dialog').close()};document.querySelectorAll('[data-close]').forEach(e=>e.onclick=()=>$(e.dataset.close).close());
function setPortalBusy(on){for(const id of ['return-damas','menu-return-damas']){const el=$(id);el.setAttribute('aria-busy',String(on));el.querySelector('small').textContent=on?'Entrando nas Damas…':'Entrar no reino'}if(on)msg('Salvando e entrando nas Damas…')}
async function returnDamas(friends=false,profilePage=false){
 if(leaving)return;
 leaving=true;clearTimeout(botTimer);setPortalBusy(true);
 const token=localStorage.getItem('damas-profile-token'),go=()=>{tickLocal();save();if(friends)sessionStorage.setItem('damas-open-friends','1');if(profilePage)sessionStorage.setItem('damas-open-profile','1');location.href='/'};
 try{
  if(!token){go();return}
  // An authoritative idle snapshot has no game, queue or outgoing invite to save.
  if(idlePortal&&!activeRemote()&&!queued&&!pendingAction&&(!fetching||fetchOp==='state')){go();return}
  // Only a pending server action needs to finish; no polling sleep or artificial delay.
  const deadline=performance.now()+5000;
  while(fetching){const remaining=deadline-performance.now();if(remaining<=0)throw Error('A conexão ainda está sincronizando. Tente voltar novamente.');let timeout;try{await Promise.race([requestDone,new Promise((_,reject)=>timeout=setTimeout(()=>reject(Error('A conexão ainda está sincronizando. Tente voltar novamente.')),remaining))])}finally{clearTimeout(timeout)}}
  if(idlePortal&&!activeRemote()&&!queued){go();return}
  let allowOnline=false;
  if(activeRemote()&&remote.mode==='online'){if(!confirm('O duelo online continuará ativo e o relógio continuará correndo. Voltar às Damas mesmo assim?')){leaving=false;setPortalBusy(false);poll();return}allowOnline=true}
  const leave=async()=>{const r=await fetch('/api/social/chess/leave',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({profileToken:token,allowOnline})});return {r,data:await r.json()}};
  let result=await leave();
  if(result.r.status===409&&!allowOnline){if(!confirm('Um duelo online está em andamento. O relógio continuará correndo. Voltar às Damas mesmo assim?')){leaving=false;setPortalBusy(false);poll();return}allowOnline=true;result=await leave()}
  if(!result.r.ok)throw Error(result.data.error||'Não foi possível salvar a partida.');
  go();
 }catch(e){leaving=false;setPortalBusy(false);msg(e.message);poll()}
}
$('return-damas').onclick=e=>{e.preventDefault();returnDamas()};
$('menu-return-damas').onclick=e=>{e.preventDefault();$('menu-dialog').close();returnDamas()};
$('menu-current-chess').onclick=e=>{e.preventDefault();$('menu-dialog').close()};
for(const [trigger,dialog] of [['chess-menu','menu-dialog'],['chess-friends','friends-dialog']]){const el=$(dialog);new MutationObserver(()=>$(trigger).setAttribute('aria-expanded',String(el.open))).observe(el,{attributes:true,attributeFilter:['open']})}
function label(p){return !p.online?'Offline':(p.game==='chess'?'Xadrez':'Damas')+' · '+(p.busy?'Em partida':'Disponível')}
function rankRows(id,rows){let el=$(id);el.replaceChildren();if(!rows.length){el.append(element('p','chess-note','Nenhum jogador no ranking ainda.'));return}rows.forEach((p,i)=>{let row=element('div','chess-rank-row'+(p.own?' own':'')),info=element('div');info.append(element('b','',p.name),element('small','',p.wins+' V · '+p.losses+' D · '+p.draws+' E'+(p.own?' · SEU PERFIL':'')));row.append(element('span','rank-medal',i+1),info,element('strong','',p.points.toLocaleString('pt-BR')+' PH'));el.append(row)})}
function drawRanking(data){if(!data.profile)return;rankData=data.profile;$('menu-honor').textContent=data.profile.points.toLocaleString('pt-BR')+' PH · '+data.profile.coins+' moedas';let p=data.profile,text='Sua posição: #'+p.rank+' · '+p.points.toLocaleString('pt-BR')+' PH';$('chess-rank-own').textContent=$('chess-rank-full-own').textContent=$('chess-personal-rank').textContent=text;$('chess-profile-stats').textContent=p.points.toLocaleString('pt-BR')+' PH · '+p.coins+' moedas · #'+p.rank+' no ranking';paintChessProfile();rankRows('chess-ranking-top',data.ranking.slice(0,3));rankRows('chess-ranking-full',data.ranking)}
function drawSocial(data){profile=data.me;paintChessProfile();$('menu-identity').textContent=profile.name;$('chess-profile').textContent=profile.name+(rankData?' · '+rankData.points.toLocaleString('pt-BR')+' PH':'');$('chess-profile-name').textContent=profile.name;$('chess-player-name').value=profile.name;
 const list=$('chess-friend-list');list.replaceChildren();let accepted=data.friends.filter(p=>p.relation==='friend');$('friend-count').textContent=accepted.filter(p=>p.online).length?'('+accepted.filter(p=>p.online).length+' online)':'';
 const people=[...data.friends,...(data.players||[]).filter(p=>!data.friends.some(f=>f.id===p.id))];
 for(let p of people){let row=element('div','chess-friend-row'),info=element('div');info.append(element('b','',p.name),element('small','',label(p)+(p.relation==='incoming'?' · Pedido de amizade':p.relation==='outgoing'?' · Pedido enviado':p.relation==='friend'?' · Amigo':'')));row.append(element('span','chess-dot '+(p.online?(p.busy?'busy':'online'):'')),info);let invite=button('Desafiar',()=>{if(switchMode('online'))request('invite',{target:p.id,minutes:Number($('chess-time').value),ranked:$('chess-ranked').value==='ranked'})});invite.disabled=!p.online||p.busy||activeRemote()||queued;row.append(invite);list.append(row)}
 if(!people.length)list.append(element('p','','Nenhum jogador disponível.'));
 const invites=$('chess-invites');invites.replaceChildren();
 for(let x of data.chess_invites||[]){let card=element('div','chess-invite');card.append(element('b','','Convite de Xadrez · '+x.name),element('p','',(x.ranked?'Ranqueada':'Casual')+' · '+(x.minutes?x.minutes+' min':'Sem limite')),button('Aceitar',()=>{if(activeRemote()||queued)return;if(mode==='local'&&moves.length&&!ended()&&!confirm('Sua partida Local ficará salva. Aceitar desafio?'))return;request('respond',{invite:x.id,accept:true})},'gold'),button('Recusar',()=>request('respond',{invite:x.id,accept:false})));invites.append(card)}
 for(let x of data.invites||[]){let card=element('div','chess-invite');card.append(element('b','','Convite de Damas · '+x.name),element('p','','Abra Damas para escolher a modalidade e aceitar.'),button('Ver convite em Damas',()=>{returnDamas(true)}));invites.append(card)}
 $('chess-social-status').textContent='Conectado · lista compartilhada';
}
function applyData(data){idlePortal=data.idle_portal===true;if(data.journey)updateJourney(data.journey);if(motionRun&&remote&&data.match?.id===remote.id&&data.match.moves.length>moves.length){deferredData=data;return}drawRanking(data);if(data.me)drawSocial(data);queued=!!data.queued;const g=data.match;
 if(g&&(!g.result||mode!=='local'&&remote?.id===g.id)){
  const same=remote?.id===g.id, before=game(), viewFlip=flipped, nextMove=same&&g.moves.length===moves.length+1?C.legal(before).find(m=>C.key(m)===g.moves.at(-1)):null;
  const changed=!remote||remote.id!==g.id||remote.moves.length!==g.moves.length||JSON.stringify(remote.result)!==JSON.stringify(g.result)||remote.offer!==g.offer;
  if(mode==='local'){tickLocal();save()}
  if(!remote||remote.id!==g.id){flipped=g.side==='b';selected=-1;promotion=null}
  remote=g;mode=g.mode;clockAt=performance.now();if(!same||!g.result){level=g.level||level;$('chess-time').value=String(g.minutes);$('chess-ranked').value=g.ranked?'ranked':'casual'}
  if(changed){if(g.result?.reason==='resign')resetResignedBoard();else rebuild(g.moves);selected=-1;promotion=null;claimed='';if(g.result){let r=g.result.rewards[g.side];msg(remoteText(g.result)+(g.journey?(g.result.winner===g.side?' · Coroa conquistada!':' · Tente novamente na jornada.'):g.ranked&&r?' · '+(r.delta>=0?'+':'')+r.delta+' PH · +'+r.coins+' moedas':''))}else msg('');render(nextMove&&g.result?.reason!=='resign'?{before,move:nextMove,viewFlip}:null)}else{updateControls();paintClock()}
 }else{if(mode==='local')$('white-name').textContent=profile?.name||'Brancas';updateControls();paintClock()}
 if(!leaving&&g&&g.mode==='ai'&&!g.paused&&!g.result&&sideKey()!==g.side){clearTimeout(botTimer);botTimer=setTimeout(()=>request('bot',{match:g.id,sequence:g.moves.length}),motionRun?520:120)}
}
async function request(op,body={},drain=false){if(leaving&&!drain)return;if(fetching){if(op==='state')return;if(fetchOp==='state'&&!pendingAction){pendingAction={op,body};return}msg('Aguarde a sincronização e tente novamente.');return}const token=localStorage.getItem('damas-profile-token');if(!token){msg('Entre no Clube de Honra das Damas para conectar sua conta.');return}fetching=true;fetchOp=op;let settle;requestDone=new Promise(r=>settle=r);if(op!=='state')idlePortal=false;updateControls();try{let r=await fetch('/api/social/chess/'+op,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({profileToken:token,busy:mode==='local'&&moves.length>0&&!ended(),...body})});let data=await r.json();if(!r.ok)throw Error(data.error||'Servidor indisponível.');fetching=false;applyData(data);if(op==='invite')msg('Convite enviado. Aguarde a resposta.');if(op==='respond'&&body.accept){$('friends-dialog').close();msg('Partida iniciada.')}if(op==='journey-start'&&data.match?.journey){$('journey-dialog').close();window.scrollTo(0,0)}if(op!=='state')setTimeout(poll,80)}catch(e){msg(e.message);if(op==='journey-start')$('journey-error').textContent=e.message;$('chess-social-status').textContent='Não foi possível conectar ao clube. Local continua disponível.';fetching=false;updateControls()}finally{fetching=false;fetchOp='';const action=pendingAction;pendingAction=null;if(action)request(action.op,action.body,true);settle()}}
function poll(){if(!leaving&&!fetching&&!document.hidden)request('state')}
window.addEventListener('focus',poll);document.addEventListener('visibilitychange',()=>{if(!document.hidden)poll();else if(mode==='local'){tickLocal();save()}});setInterval(poll,1800);
$('white-icon').append(pieceArt('K'));$('black-icon').append(pieceArt('k'));
$('chess-focus').onclick=()=>{let on=document.body.classList.toggle('chess-focus');$('chess-focus').textContent=on?'Mostrar painéis':'Modo concentração';$('chess-focus').setAttribute('aria-pressed',String(on));if(on)window.scrollTo(0,0);if(motionRun)render()};
window.addEventListener('resize',()=>{if(motionRun)render()});
// Campaign metadata and unlocks come only from the authenticated server.
let profilePaintSignature='';function paintChessProfile(){const signature=JSON.stringify([profile,rankData,journeyData?.won]);if(signature===profilePaintSignature)return;profilePaintSignature=signature;if(profile){const glyph={crown:'♛',knight:'♞',shield:'⛨',oak:'♣',rook:'♜',star:'★'};$('chess-profile-avatar').textContent=glyph[profile.avatar]||'♞';$('chess-profile-avatar').className='profile-avatar frame-'+(profile.frame||'wood');$('chess-profile-account').textContent=profile.account?'Conta: @'+profile.account+' · Perfil compartilhado.':'Você está como visitante. Vincule uma conta para acessar seu perfil em outros dispositivos.'}if(!rankData)return;const p=rankData,total=p.wins+p.losses+p.draws,tiles=$('chess-profile-tiles');tiles.replaceChildren();for(const [label,v] of [['Vitórias',p.wins],['Derrotas',p.losses],['Empates',p.draws],['Taxa de vitória',total?Math.round(100*p.wins/total)+'%':'—'],['Partidas competitivas',total],['Coroas',journeyData?.won.length||0]]){const box=element('div');box.append(element('strong','',String(v)),element('small','',label));tiles.append(box)}const defs=[['⚔','Primeira vitória','Vença uma partida competitiva.',p.wins>=1],['♜','Guardião do Tabuleiro','Vença dez partidas competitivas.',p.wins>=10],['✦','Veterano','Conclua vinte partidas competitivas.',total>=20],...(journeyData?.stages||[]).map(s=>['♛',s.title,'Vença '+s.name+'.',journeyData.won.includes(s.id)])];const grid=$('chess-achievements');grid.replaceChildren();$('chess-achievement-count').textContent=defs.filter(d=>d[3]).length+' / '+defs.length;for(const [icon,title,desc,won] of defs){const tile=element('div','achievement-tile '+(won?'unlocked':'locked'));tile.append(element('span','achievement-icon',won?icon:'◇'),element('strong','',title),element('small','',desc));grid.append(tile)}}
$('chess-profile-edit').onclick=$('chess-profile-manage').onclick=()=>{$('profile-dialog').close();returnDamas(false,true)};
$('chess-profile-history').onclick=()=>{open('history-dialog');$('replay-panel').hidden=true;loadHistory()};
function openJourney(){open('journey-dialog');$('journey-error').textContent='';drawJourney();poll()}
function updateJourney(data){const sig=JSON.stringify(data);if(sig===journeySignature)return;journeyData=data;journeySignature=sig;applyPrefs();$('journey-profile-title').textContent='Jornada · '+data.title;drawJourney()}
let journeyCardSignature='';
function drawJourney(){const list=$('journey-cards');if(!journeyData){$('journey-progress').textContent='Entre na sua conta para acessar a jornada.';return}const d=journeyData;const sig=journeySignature+':'+(remote?.journey||0)+':'+activeRemote()+':'+queued;if(sig===journeyCardSignature&&list.children.length)return;journeyCardSignature=sig;list.replaceChildren();$('journey-progress').textContent=d.won.length+' / '+d.stages.length+' coroas conquistadas · '+d.title;$('journey-reward-status').textContent=d.complete?'Conquistado! Equipe em Efeitos visuais.':'Recompensa final · conquiste os cinco mestres.';
 for(const stage of d.stages){const won=d.won.includes(stage.id),locked=stage.id>d.unlocked,active=remote?.journey===stage.id&&activeRemote(),row=element('article','journey-card stage-'+stage.id+(won?' won':'')),crest=element('span','journey-crest',['Ⅰ','Ⅱ','Ⅲ','Ⅳ','Ⅴ'][stage.id-1]),body=element('div','journey-card-copy');body.append(element('small','',stage.hall+' · '+(won?'CONQUISTADO':locked?'BLOQUEADO':'DISPONÍVEL')),element('h3','',stage.name),element('p','',stage.description),element('small','','Título: '+stage.title));const go=button(active?'Continuar partida':locked?'Bloqueado':won?'Jogar novamente':'Desafiar mestre',()=>{if(active){$('journey-dialog').close();return}if(activeRemote()||queued){$('journey-error').textContent='Conclua a partida atual antes de iniciar outra.';return}if(fetching){$('journey-error').textContent='Sincronizando. Tente novamente.';return}if(mode==='local'&&moves.length&&!ended()&&!confirm('Sua partida local será salva. Entrar na jornada?'))return;$('journey-error').textContent='Preparando o salão…';request('journey-start',{stage:stage.id,nonce:crypto.randomUUID()})},locked?'':'gold');go.disabled=locked;row.append(crest,body,go);list.append(row)}
}
function drawJourneyMatch(){const id=remote?.journey,stage=journeyData?.stages.find(s=>s.id===id);$('journey-banner').hidden=!stage;$('journey-side').hidden=!stage;if(!stage){delete document.body.dataset.journeyStage;if($('journey-dialog').open)drawJourney();return}document.body.dataset.journeyStage=String(id);$('journey-stage-label').textContent='JORNADA DO MESTRE · COROA '+id+' / 5';$('journey-hall').textContent=stage.hall;$('journey-match-detail').textContent='Contra '+stage.name+' · Partida clássica completa';$('journey-side-title').textContent=stage.name;$('journey-side-text').textContent=stage.description;const result=remote.result;$('journey-side-result').textContent=result?(result.winner===remote.side?'Coroa conquistada · '+stage.title:'O mestre aguarda sua revanche. Nenhum progresso perdido.'):'Vença para conquistar esta coroa e avançar.';$('journey-continue').textContent=result?'Ver próxima coroa':'Ver jornada';if($('journey-dialog').open)drawJourney()}
$('menu-journey').onclick=$('journey-map-open').onclick=$('journey-continue').onclick=openJourney;
// School and replay have their own positions; neither can modify the live game.
const lessons=[
 ['centro','Controle do centro',C.START,'Avance o peão do rei duas casas para disputar o centro.','e2e4','O peão de e2 pode avançar para e4.','O centro fica controlado e você libera a dama e o bispo.'],
 ['cavalo','Desenvolva o cavalo',C.START,'Desenvolva o cavalo de g1 para a casa central f3.','g1f3','O cavalo salta em L.','Boa! Você desenvolveu uma peça e controla e5 e d4.'],
 ['roque','Proteja seu rei','r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4','Faça o roque curto com as brancas.','e1g1','O rei caminha duas casas para a direita.','Rei seguro e torre desenvolvida.'],
 ['enpassant','Captura en passant','rnbqkbnr/1pp1pppp/p7/3pP3/8/8/PPPP1PPP/RNBQKBNR w KQkq d6 0 3','O peão preto acabou de jogar d7–d5. Capture-o de passagem.','e5d6','O peão branco captura para d6, atrás do peão preto.','Correto! A captura de passagem só vale no lance imediatamente seguinte.'],
 ['promocao','A coroação do peão','7k/P7/8/8/8/8/8/7K w - - 0 1','Promova o peão a uma dama na oitava fileira.','a7a8q','Avance a7 para a8 e escolha Dama.','A promoção transforma o peão em uma nova peça.'],
 ['mate','Mate em um','7k/8/5KQ1/8/8/8/8/8 w - - 0 1','Dê xeque-mate em um lance com a dama.','g6g7','A dama pode ir a g7, protegida pelo rei.','Xeque-mate! O rei preto não pode capturar a dama nem escapar.']
];
let completed=new Set();try{completed=new Set(JSON.parse(localStorage.getItem('chess-school-v1')||'[]').filter(id=>lessons.some(l=>l[0]===id)))}catch{}
let lessonIndex=0,study=null,studySelected=-1,studyDone=false,replayPositions=[],replayLabels=[],replayIndex=0,historyLoad=0;
function studyBoard(id,g,sel=-1,targets=[],onClick=null){const board=$(id);board.replaceChildren();for(let n=0;n<64;n++){const i=(n>>3)*16+(n&7),p=g.b[i],cell=button('',()=>onClick?.(i),'chess-square '+(((i>>4)+(i&7))%2?'dark':'light'));cell.dataset.square=C.sq(i);cell.setAttribute('aria-label',C.sq(i)+(p!=='.'?' '+pieceNames[p.toLowerCase()]:' vazia'));if(!onClick)cell.tabIndex=-1;if(p!=='.'){cell.classList.add('occupied');cell.append(pieceArt(p))}if(i===sel)cell.classList.add('selected');if(targets.includes(i))cell.classList.add('target');if(n%8===0)cell.append(element('span','chess-coordinate rank',C.sq(i)[1]));if(n>=56)cell.append(element('span','chess-coordinate file',C.sq(i)[0]));board.append(cell)}}
function schoolList(){$('school-progress').textContent=completed.size+' de '+lessons.length+' desafios concluídos';const list=$('school-lessons');list.replaceChildren();lessons.forEach((l,i)=>{const b=button((completed.has(l[0])?'✓ ':'')+(i+1)+'. '+l[1],()=>loadLesson(i),i===lessonIndex?'active':'');b.setAttribute('aria-pressed',String(i===lessonIndex));list.append(b)})}
function loadLesson(i){lessonIndex=i;const l=lessons[i];study=C.parseFen(l[2]);studySelected=-1;studyDone=false;$('school-title').textContent=l[1];$('school-task').textContent=l[3];$('school-feedback').textContent='Selecione a peça e faça o lance.';$('school-promotion-wrap').hidden=l[0]!=='promocao';$('school-promotion').value='q';schoolList();drawSchool()}
function drawSchool(){studyBoard('school-board',study,studySelected,studyDone?[]:C.legal(study).filter(m=>m[0]===studySelected).map(m=>m[1]),schoolClick)}
function schoolClick(i){if(studyDone)return;const l=lessons[lessonIndex];if(C.side(study.b[i])===study.t){studySelected=studySelected===i?-1:i;drawSchool();return}let legal=C.legal(study).filter(m=>m[0]===studySelected&&m[1]===i),m=legal.find(m=>!m[2]||m[2]===$('school-promotion').value);if(!m)return;if(C.key(m)!==l[4]){$('school-feedback').textContent='Lance legal, mas não resolve este desafio. Tente novamente.';return}study=C.apply(study,m);studySelected=-1;studyDone=true;completed.add(l[0]);try{localStorage.setItem('chess-school-v1',JSON.stringify([...completed]))}catch{};$('school-feedback').textContent=l[6];schoolList();drawSchool()}
$('menu-school').onclick=()=>{open('school-dialog');loadLesson(lessonIndex)};$('school-hint').onclick=()=>{$('school-feedback').textContent=lessons[lessonIndex][5]};$('school-retry').onclick=()=>loadLesson(lessonIndex);$('school-next').onclick=()=>loadLesson((lessonIndex+1)%lessons.length);
function startReplay(keys,title){let h=[start()],labels=['Posição inicial'];for(const u of keys){const g=h.at(-1),m=C.legal(g).find(x=>C.key(x)===u);if(!m){$('history-status').textContent='Não foi possível reconstruir este replay.';return}labels.push(g.full+(g.t===1?'. ':'... ')+C.san(g,m));h.push(C.apply(g,m))}replayPositions=h;replayLabels=labels;replayIndex=0;$('replay-title').textContent=title;$('replay-panel').hidden=false;$('replay-range').max=h.length-1;drawReplay()}
function drawReplay(){studyBoard('replay-board',replayPositions[replayIndex]);$('replay-info').textContent=replayIndex+' / '+(replayPositions.length-1)+' · '+replayLabels[replayIndex];$('replay-range').value=replayIndex;$('replay-prev').disabled=replayIndex===0;$('replay-next').disabled=replayIndex===replayPositions.length-1}
$('replay-prev').onclick=()=>{if(replayIndex>0){replayIndex--;drawReplay()}};$('replay-next').onclick=()=>{if(replayIndex<replayPositions.length-1){replayIndex++;drawReplay()}};$('replay-range').oninput=()=>{replayIndex=Number($('replay-range').value);drawReplay()};
$('history-current').onclick=()=>startReplay(remote?.result?remote.moves:mode==='local'&&!moves.length&&lastLocalReplay.length?lastLocalReplay:moves.map(m=>m.key),'Partida atual / última concluída · '+(mode==='local'?'Local':mode==='ai'?'Computador':'Online'));
async function loadHistory(){const epoch=++historyLoad,token=localStorage.getItem('damas-profile-token'),list=$('history-list');list.replaceChildren();$('history-status').textContent='Carregando histórico…';if(!token){$('history-status').textContent='Entre na sua conta para acessar o histórico online.';return}try{const res=await fetch('/api/social/chess/history',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({profileToken:token,busy:activeRemote()||mode==='local'&&moves.length>0&&!ended()})}),data=await res.json();if(epoch!==historyLoad)return;if(!res.ok)throw Error(data.error||'Histórico indisponível');$('history-status').textContent=data.history.length?'Partidas concluídas':'Nenhuma partida registrada.';for(const item of data.history){const row=element('div','chess-history-entry'),info=element('div');const result={win:'Vitória',loss:'Derrota',resign:'Desistência',draw:'Empate'}[item.outcome]||item.outcome;info.append(element('b','',item.opponent+' · '+result),element('small','',(item.journey?'Jornada · Coroa '+item.journey:item.ranked?'Ranqueada':'Casual')+' · '+(item.delta>0?'+':'')+item.delta+' PH · '+new Date(item.played_at*1000).toLocaleDateString('pt-BR')));row.append(info,button('Rever',()=>startReplay(item.moves,'Contra '+item.opponent)));list.append(row)}}catch(e){if(epoch===historyLoad)$('history-status').textContent=e.message}}
$('menu-replay').onclick=()=>{open('history-dialog');$('replay-panel').hidden=true;loadHistory()};
$('menu-visual').onclick=()=>{applyPrefs();open('visual-dialog')};$('menu-sound').onclick=()=>{applyPrefs();open('sound-dialog')};
document.querySelectorAll('[data-chess-theme]').forEach(b=>b.onclick=()=>{if(b.dataset.chessTheme==='crowns'&&!journeyData?.complete)return;prefs.theme=b.dataset.chessTheme;applyPrefs()});$('visual-motion').onchange=()=>{prefs.motion=$('visual-motion').checked;if(motionRun)render();applyPrefs()};$('sound-enabled').onchange=()=>{prefs.sound=$('sound-enabled').checked;applyPrefs();unlockSound()};$('sound-volume').oninput=()=>{prefs.volume=Number($('sound-volume').value);applyPrefs()};$('sound-preview').onclick=()=>{prefs.sound=true;applyPrefs();unlockSound();if(soundCtx?.state==='suspended')soundCtx.resume().then(()=>playSound()).catch(()=>{});else playSound()};
applyPrefs();
restore();render();if(sessionStorage.getItem('chess-open-friends')==='1'){sessionStorage.removeItem('chess-open-friends');open('friends-dialog')}poll();
})();
