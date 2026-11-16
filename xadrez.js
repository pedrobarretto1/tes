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
let history=[start()],moves=[],selected=-1,promotion=null,flipped=false,claimed='',auto=true,online=false,profile=null,fetching=false;
try{let x=JSON.parse(sessionStorage.getItem(savedKey)||'null');if(x&&Array.isArray(x.moves)&&x.moves.length<=1000){let h=[start()],ms=[];for(let u of x.moves){let g=h.at(-1),m=C.legal(g).find(m=>C.key(m)===u);if(!m||C.status(h).done)throw Error('invalid save');ms.push({key:u,label:C.san(g,m),side:g.t,full:g.full,from:m[0],to:m[1]});h.push(C.apply(g,m))}history=h;moves=ms;auto=x.auto!==false;flipped=auto?history.at(-1).t===-1:!!x.flipped;claimed=typeof x.claimed==='string'?x.claimed.slice(0,100):''}}catch{}
function save(){try{sessionStorage.setItem(savedKey,JSON.stringify({moves:moves.map(m=>m.key),auto,flipped,claimed}))}catch{}}
function element(tag,cls,text){let e=document.createElement(tag);if(cls)e.className=cls;if(text!==undefined)e.textContent=text;return e}
function button(label,fn,cls){let b=element('button',cls,label);b.type='button';b.onclick=fn;return b}
function open(id){for(let d of document.querySelectorAll('dialog[open]'))d.close();$(id).showModal();if(id==='friends-dialog')poll()}
function game(){return history.at(-1)}
function ended(){return !!claimed||C.status(history).done}
function render(){
 const g=game(),st=C.status(history),done=!!claimed||st.done,legal=done?[]:C.legal(g),targets=new Set(legal.filter(m=>m[0]===selected).map(m=>m[1])),last=moves.at(-1),board=$('chess-board');
 const check= C.checked(g)?g.b.indexOf(g.t===1?'K':'k'):-1;
 board.replaceChildren();
 for(let n=0;n<64;n++){let j=flipped?63-n:n,i=(j>>3)*16+(j&7),p=g.b[i],coord=C.sq(i);
 let cell=button('',()=>click(i),'chess-square '+(((i>>4)+(i&7))%2?'dark':'light'));
 cell.dataset.square=coord;cell.setAttribute('aria-label',coord+(p!=='.'?' '+pieceNames[p.toLowerCase()]+' '+(C.side(p)===1?'branco':'preto'):' vazia'));
 if(p!=='.'){cell.classList.add('occupied');cell.append(pieceArt(p))}
 if(last&&(last.from===i||last.to===i))cell.classList.add('last');if(i===selected)cell.classList.add('selected');if(legal.some(m=>m[0]===i))cell.classList.add('playable');if(targets.has(i))cell.classList.add('target');if(check===i)cell.classList.add('check');
 if(n%8===0)cell.append(element('span','chess-coordinate rank',coord[1]));if(n>=56)cell.append(element('span','chess-coordinate file',coord[0]));board.append(cell)}
 $('chess-status').textContent=claimed||st.text;$('white-player').classList.toggle('active',!done&&g.t===1);$('black-player').classList.toggle('active',!done&&g.t===-1);
 $('chess-hint').textContent=done?'Partida encerrada. Comece uma nova ou reveja os lances.':promotion?'Escolha a peça da promoção.':selected!==-1?'Escolha uma casa destacada.':'Selecione uma peça e escolha um destino disponível.';
 $('chess-back').disabled=!moves.length&&!claimed;$('chess-resign').disabled=done;$('chess-auto').checked=auto;
 $('chess-claim').hidden=done||!st.claim;$('chess-claim').textContent=st.claim?'Reivindicar empate · '+st.claim:'Reivindicar empate';
 $('chess-promote').hidden=!promotion;$('promotion-choices').replaceChildren();
 if(promotion){for(let m of promotion){let choice=button('',()=>play(m),'chess-promotion-choice');choice.append(pieceArt(g.t===1?m[2].toUpperCase():m[2]),element('span','',pieceNames[m[2]]));$('promotion-choices').append(choice)}$('promotion-choices').append(button('Cancelar',()=>{promotion=null;render()}))}
 const log=$('chess-history');log.replaceChildren();if(!moves.length)log.append(element('li','','Nenhum lance registrado.'));
 for(let m of moves.slice(-60))log.append(element('li','',m.full+(m.side===1?'. ':'... ')+m.label));log.scrollTop=log.scrollHeight;
 save();
}
function click(i){if(ended()||promotion)return;let g=game(),legal=C.legal(g);if(C.side(g.b[i])===g.t){selected=selected===i?-1:i;render();return}let choices=legal.filter(m=>m[0]===selected&&m[1]===i);if(choices.length>1){promotion=choices;render()}else if(choices.length)play(choices[0])}
function play(m){let g=game(),found=C.legal(g).find(x=>C.key(x)===C.key(m));if(!found||ended())return;moves.push({key:C.key(found),label:C.san(g,found),side:g.t,full:g.full,from:found[0],to:found[1]});history.push(C.apply(g,found));selected=-1;promotion=null;if(auto&&!ended())flipped=game().t===-1;render();poll()}
function reset(){if(moves.length&&!ended()&&!confirm('Começar uma nova partida?'))return;history=[start()];moves=[];claimed='';selected=-1;promotion=null;flipped=false;render();poll()}
$('chess-new').onclick=reset;$('menu-local').onclick=()=>{$('menu-dialog').close();reset()};
$('chess-back').onclick=()=>{if(claimed)claimed='';else if(moves.length){history.pop();moves.pop()}selected=-1;promotion=null;if(auto)flipped=game().t===-1;render();poll()};
$('chess-resign').onclick=()=>{if(!ended()&&confirm('Confirmar desistência das '+(game().t===1?'brancas':'pretas')+'?')){claimed=(game().t===1?'Pretas':'Brancas')+' venceram por desistência.';selected=-1;promotion=null;render();poll()}};
$('chess-claim').onclick=()=>{let st=C.status(history);if(!ended()&&st.claim){claimed='Empate por '+st.claim+'.';selected=-1;promotion=null;render();poll()}};
$('chess-flip').onclick=()=>{flipped=!flipped;render()};$('chess-auto').onchange=()=>{auto=$('chess-auto').checked;if(auto)flipped=game().t===-1;render()};
$('chess-menu').onclick=()=>open('menu-dialog');$('chess-friends').onclick=$('menu-friends').onclick=()=>open('friends-dialog');$('chess-profile').onclick=$('menu-profile').onclick=()=>open('profile-dialog');$('menu-rules').onclick=$('sidebar-rules').onclick=()=>open('rules-dialog');
document.querySelectorAll('[data-close]').forEach(e=>e.onclick=()=>$(e.dataset.close).close());
function label(p){return !p.online?'Offline':(p.game==='chess'?'Xadrez':'Damas')+' · '+(p.busy?'Em partida':'Disponível')}
function drawSocial(data){profile=data.me;online=true;$('chess-profile').textContent=profile.name;$('chess-profile-name').textContent=profile.name;$('white-name').textContent=profile.name;
 const list=$('chess-friend-list');list.replaceChildren();let accepted=data.friends.filter(p=>p.relation==='friend');$('friend-count').textContent=accepted.filter(p=>p.online).length?'('+accepted.filter(p=>p.online).length+' online)':'';
 for(let p of data.friends){let row=element('div','chess-friend-row'),info=element('div');info.append(element('b','',p.name),element('small','',label(p)+(p.relation==='incoming'?' · Pedido de amizade':p.relation==='outgoing'?' · Pedido enviado':'')));row.append(element('span','chess-dot '+(p.online?(p.busy?'busy':'online'):'')),info);list.append(row)}
 if(!data.friends.length)list.append(element('p','','Nenhum amigo adicionado. Use o Clube de Honra para encontrar jogadores.'));
 const invites=$('chess-invites');invites.replaceChildren();for(let x of data.invites){let card=element('div','chess-invite');card.append(element('b','','Convite de Damas · '+x.name),element('p','','Abra o universo Damas para escolher a modalidade e aceitar.'),button('Ver convite em Damas',()=>{if(moves.length&&!ended()&&!confirm('Sua partida Local ficará salva nesta aba. Ir para Damas?'))return;sessionStorage.setItem('damas-open-friends','1');location.href='/'}));invites.append(card)}
 $('chess-social-status').textContent='Conectado · lista compartilhada';
}
async function poll(){if(fetching||document.hidden)return;const token=localStorage.getItem('damas-profile-token');if(!token){$('chess-social-status').textContent='Entre no Clube de Honra das Damas para conectar sua conta.';return}fetching=true;try{let r=await fetch('/api/social/chess/state',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({profileToken:token,busy:moves.length>0&&!ended()})});if(!r.ok)throw Error('Perfil indisponível');drawSocial(await r.json())}catch{online=false;$('chess-social-status').textContent='Não foi possível conectar ao clube. Sua partida Local continua funcionando.'}finally{fetching=false}}
window.addEventListener('focus',poll);document.addEventListener('visibilitychange',()=>{if(!document.hidden)poll()});setInterval(poll,3000);
$('white-icon').append(pieceArt('K'));$('black-icon').append(pieceArt('k'));
$('chess-focus').onclick=()=>{let on=document.body.classList.toggle('chess-focus');$('chess-focus').textContent=on?'Mostrar painéis':'Modo concentração';$('chess-focus').setAttribute('aria-pressed',String(on));if(on)window.scrollTo(0,0)};
render();poll();
})();
