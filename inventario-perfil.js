/* Inventario do perfil compartilhado: itens do servidor, nunca do localStorage. */
(()=>{'use strict';
 const $=id=>document.getElementById(id);
 const node=(tag,cls,text)=>{const e=document.createElement(tag);if(cls)e.className=cls;if(text!==undefined)e.textContent=text;return e};
 const token=()=>localStorage.getItem('damas-profile-token');
 const names=Object.fromEntries([
  ['classic','Madeira Clássica'],['skin-classic','Pedras Clássicas'],['imperial','Madeira Imperial'],['marble','Mármore Real'],['emerald','Esmeralda'],['midnight','Meia-Noite'],['sakura','Jardim Sakura'],['ocean','Atlântico'],['desert','Areias do Deserto'],['obsidian','Obsidiana'],['parchment','Pergaminho'],['cherry','Cerejeira'],['frost','Inverno Ártico'],
  ['skin-ivory','Marfim e Ébano'],['skin-gilded','Ouro e Obsidiana'],['skin-jade','Jade e Âmbar'],['skin-crystal','Cristal e Ametista'],['skin-metal','Aço e Bronze'],['skin-porcelain','Porcelana Azul'],['skin-ruby','Rubi e Pérola'],['skin-neon','Neon Cibernético'],['skin-royal','Coroa Real'],
  ['champion-hall','Salão dos Campeões'],['champion-legacy','Legado Imperial'],['champion-eternal','Trono Eterno'],['skin-champion','Coroa dos Campeões'],['skin-legend','Lenda Imperial'],['skin-eternal','Glória Eterna'],
  ['haunted-night','Noite das Bruxas'],['winter-feast','Noite de Natal'],['midnight-crypt','Cripta da Meia-Noite'],['rose-garden','Jardim de Rosas'],
  ['skin-pumpkin','Abóbora e Ossos'],['skin-holly','Neve e Enfeite'],['skin-haunted','Olho e Sombra'],['skin-rose','Rosa e Coração'],
  ['relic-shadow','Fortaleza do Rei Caído'],['relic-divine','Catedral do Sol Eterno'],['relic-infinite','Coração do Universo'],['relic-throne','Trono do Último Rei'],
  ['skin-relic-shadow','Guardas da Forja · Rei Caído'],['skin-relic-divine','Medalhões Solares · Rei Divino'],['skin-relic-infinite','Núcleos do Éter · Rei do Infinito'],['skin-relic-throne','Medalhões do Último Rei']
 ]);
 const kings=[['shadow','Rei Caído','Fortaleza das Sombras'],['divine','Rei Divino','Catedral do Sol Eterno'],['infinite','Rei do Infinito','Coração do Universo']];
 const categoryLabel={pieces:'Peças',board:'Tabuleiros',scene:'Cenários',effect:'Efeitos'};
 const title=id=>names[id]||String(id).replace(/^skin-/,'').replace(/-/g,' ');
 let serial=0,busy=false,view=null;
 async function api(path,data,t){
  const response=await fetch('/api/social/'+path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({profileToken:t,...data})});
  const payload=await response.json();if(t!==token())throw Error('Conta alterada. Abra o perfil novamente.');
  if(!response.ok)throw Error(payload.error||'Inventário indisponível.');return payload;
 }
 function checkersPreview(board,skin){
  const frame=node('div','shop-preview profile-skin-preview');frame.dataset.theme=board;frame.dataset.skin=skin;frame.setAttribute('aria-hidden','true');
  for(let i=0;i<16;i++){
   const r=Math.floor(i/4),c=i%4,dark=(r+c)%2===1,cell=node('span','shop-square '+(dark?'dark':'light'));
   if(dark&&(r===0||r===3)){const piece=node('span','piece '+(r===0?'white':'black')+(i===1||i===14?' king':''));cell.append(piece)}
   frame.append(cell);
  }
  const trim=node('div','forge-corners');for(let i=0;i<4;i++)trim.append(node('i'));frame.append(trim);return frame;
 }
 function chessPreview(item,state){
  const equip=state.shop?.equipped||{},board=item.category==='board'?item.id:equip.board||'board-classic',pieces=item.category==='pieces'?item.id:equip.pieces||'pieces-classic';
  if(typeof window.profileChessPreview==='function'){
   const frame=window.profileChessPreview(board,pieces);frame.classList.add('profile-skin-preview');return frame;
  }
  const frame=node('div','shop-preview profile-skin-preview profile-chess-fallback');
  const style=board.split('-')[1]||'classic';frame.dataset.theme=style==='champion'?'champion-hall':style;frame.setAttribute('aria-hidden','true');
  const figures={1:'♞',3:'♛',4:'♟',11:'♙',12:'♘',14:'♔'};
  for(let i=0;i<16;i++){const dark=(Math.floor(i/4)+i%4)%2,cell=node('span','shop-square '+(dark?'dark':'light'));if(figures[i])cell.append(node('span','profile-chess-glyph',figures[i]));frame.append(cell)}
  const trim=node('div','forge-corners');for(let i=0;i<4;i++)trim.append(node('i'));frame.append(trim);return frame;
 }
 function card(host,game,item,label,kind,selected,preview){
  const article=node('article','profile-inventory-card'+(selected?' equipped':''));article.dataset.game=game;article.dataset.item=item;
  article.append(preview);
  const content=node('div','profile-inventory-copy');content.append(node('strong','',label),node('small','',kind),node('span','profile-inventory-state',selected?'✓ Equipada':'Adquirida'));
  const button=node('button','secondary',selected?'Equipada':'Equipar');button.type='button';button.disabled=selected||busy;
  button.onclick=()=>equip(game,item);
  content.append(button);article.append(content);host.append(article);
 }
 function section(host,label,description){const block=node('section','profile-inventory-section');block.append(node('h4','',label),node('p','sub',description));const grid=node('div','profile-inventory-grid');block.append(grid);host.append(block);return grid;}
 function renderKings(host,d){
  if(!d)return;
  const owned=new Set(d.owned||[]),available=kings.filter(([key])=>owned.has('relic-'+key)||owned.has('skin-relic-'+key));
  if(!available.length)return;
  const section=node('section','profile-royal-gallery');section.append(node('h4','','♛ Os Três Reis · Suas Relíquias'),node('p','sub','Coleções reais presentes no seu inventário. Equipe as peças individualmente ou o conjunto completo.'));
  const grid=node('div','profile-royal-grid');
  for(const [key,king,place] of available){
   const board='relic-'+key,skin='skin-relic-'+key,ownsBoard=owned.has(board),ownsSkin=owned.has(skin),complete=ownsBoard&&ownsSkin,equipped=complete?d.theme===board&&d.skin===skin:ownsSkin?d.skin===skin:d.theme===board;
   const el=node('article','profile-royal-card'+(equipped?' equipped':''));el.dataset.king=key;
   const preview=checkersPreview(ownsBoard?board:d.theme,ownsSkin?skin:d.skin);
   const detail=node('div','profile-royal-copy');detail.append(node('strong','',king),node('small','',place),node('span','profile-royal-status',complete?'Tabuleiro + peças adquiridos':ownsSkin?'Peças adquiridas': 'Tabuleiro adquirido'));
   const btn=node('button','primary',equipped?'Equipado':complete?'Equipar coleção':ownsSkin?'Equipar peças':'Equipar tabuleiro');btn.type='button';btn.disabled=equipped||busy;btn.onclick=()=>equip('damas',complete?'king-set-'+key:ownsSkin?skin:board);
   detail.append(btn);el.append(preview,detail);grid.append(el);
  }
  section.append(grid);host.append(section);
 }
 function render(){
  const host=$(view?.id);if(!host||!view)return;host.replaceChildren();
  if(view.notice)host.append(node('p','profile-inventory-message',view.notice));
  const account=node('div','profile-inventory-account');
  account.append(node('strong','',view.account?'Inventário da conta @'+view.account:'Inventário de visitante'),node('small','',view.account?(view.playerName||'Perfil autenticado')+' · recompensas sincronizadas com o servidor':'Se você adquiriu skins em outra conta, entre nela para visualizá-las.'));
  host.append(account);
  renderKings(host,view.damas);
  const dgrid=section(host,'♛ Damas','Pedras e tabuleiros adquiridos. As relíquias dos reis aparecem separadamente; possuir as peças não desbloqueia o tabuleiro.');
  if(view.damas){
   const d=view.damas,owned=[...new Set((d.owned||[]).filter(id=>typeof id==='string'))];
   const sort=(a,b)=>Number(b.startsWith('skin-relic'))-Number(a.startsWith('skin-relic'))||a.localeCompare(b,'pt-BR');
   for(const id of owned.sort(sort)){const piece=id.startsWith('skin-');card(dgrid,'damas',id,title(id),piece?'Skin de peças':'Tabuleiro',piece?d.skin===id:d.theme===id,checkersPreview(piece?d.theme:id,piece?id:d.skin));}
   if(!owned.length)dgrid.append(node('p','sub','Nenhuma skin registrada.'));
  }else dgrid.append(node('p','sub',view.damasError||'Inventário de Damas não disponível.'));
  const cgrid=section(host,'♞ Xadrez','Peças, tabuleiros, cenários e efeitos adquiridos no Xadrez. O inventário e as moedas são independentes das Damas.');
  if(view.chess){
   const d=view.chess,owned=new Set(d.shop?.owned||[]),items=(d.catalog||[]).filter(i=>owned.has(i.id));
   for(const item of items)card(cgrid,'chess',item.id,item.name,categoryLabel[item.category]||item.category,d.shop.equipped[item.category]===item.id,chessPreview(item,d));
   if(!items.length)cgrid.append(node('p','sub','Nenhuma skin de Xadrez registrada.'));
  }else cgrid.append(node('p','sub',view.chessError||'Inventário de Xadrez não disponível.'));
 }
 async function equip(game,item){
  if(!view||busy)return;const t=view.token,before=view;busy=true;view.notice='Equipando item…';render();
  try{
   const response=await api('profile/inventory/equip',{game,item},t);
   if(view!==before)return;
   view.damas=response.damas;view.chess=response.chess;view.account=response.account;view.playerName=response.playerName;
   if(game==='damas')window.schoolRefreshStyle?.();
   view.notice='✓ Skin equipada! A alteração foi salva no servidor.';
   window.dispatchEvent(new CustomEvent('profile-inventory-equipped',{detail:{game,item}}));
  }catch(e){if(view===before)view.notice=e.message}
  finally{busy=false;if(view===before)render()}
 }
 async function open(game){
  const id=game==='damas'?'profile-skins':'chess-profile-skins',host=$(id),t=token();if(!host)return;
  const current=++serial;view={id,token:t,notice:'',damas:null,chess:null,damasError:'',chessError:'',account:null,playerName:''};busy=false;
  host.replaceChildren(node('p','sub',t?'Carregando skins do servidor…':'Entre na sua conta para consultar o inventário.'));
  if(!t)return;
  try{
   const result=await api('profile/inventory/state',{},t);
   if(serial!==current||t!==token()||view?.id!==id)return;
   view.damas=result.damas;view.chess=result.chess;view.account=result.account;view.playerName=result.playerName;render();
  }catch(e){if(serial===current&&t===token()&&view?.id===id){view.damasError=e.message;view.chessError=e.message;render()}}
 }
 window.perfilInventario={open};
})();