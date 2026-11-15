(()=>{
'use strict';
const C=window.ChessEngine,$=id=>document.getElementById(id);
const glyph={K:'♔',Q:'♕',R:'♖',B:'♗',N:'♘',P:'♙',k:'♚',q:'♛',r:'♜',b:'♝',n:'♞',p:'\u265f\ufe0e'};
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
 if(p!=='.'){cell.classList.add('occupied');cell.append(element('span','chess-piece '+(C.side(p)===1?'white':'black'),glyph[p]))}
 if(last&&(last.from===i||last.to===i))cell.classList.add('last');if(i===selected)cell.classList.add('selected');if(targets.has(i))cell.classList.add('target');if(check===i)cell.classList.add('check');
 if(n%8===0)cell.append(element('span','chess-coordinate rank',coord[1]));if(n>=56)cell.append(element('span','chess-coordinate file',coord[0]));board.append(cell)}
 $('chess-status').textContent=claimed||st.text;$('white-player').classList.toggle('active',!done&&g.t===1);$('black-player').classList.toggle('active',!done&&g.t===-1);
 $('chess-hint').textContent=done?'Partida encerrada. Comece uma nova ou reveja os lances.':promotion?'Escolha a peça da promoção.':selected!==-1?'Escolha uma casa destacada.':'Selecione uma peça e escolha um destino disponível.';
 $('chess-back').disabled=!moves.length&&!claimed;$('chess-resign').disabled=done;$('chess-auto').checked=auto;
 $('chess-claim').hidden=done||!st.claim;$('chess-claim').textContent=st.claim?'Reivindicar empate · '+st.claim:'Reivindicar empate';
 $('chess-promote').hidden=!promotion;$('promotion-choices').replaceChildren();
 if(promotion){for(let m of promotion)$('promotion-choices').append(button(pieceNames[m[2]],()=>play(m),'gold'));$('promotion-choices').append(button('Cancelar',()=>{promotion=null;render()}))}
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
$('chess-menu').onclick=()=>open('menu-dialog');$('chess-friends').onclick=$('menu-friends').onclick=()=>open('friends-dialog');$('chess-profile').onclick=$('menu-profile').onclick=()=>open('profile-dialog');$('menu-rules').onclick=()=>open('rules-dialog');
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
render();poll();
})();
