/* Motor de xadrez local: 0x88, sem dependências. */
(function(root){
'use strict';
const START='rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1';
const dirs={n:[-33,-31,-18,-14,14,18,31,33],b:[-17,-15,15,17],r:[-16,-1,1,16],k:[-17,-16,-15,-1,1,15,16,17],q:[-17,-16,-15,-1,1,15,16,17]};
const on=i=>i>=0&&i<128&&!(i&0x88);
const side=p=>!p||p==='.'?0:p===p.toUpperCase()?1:-1;
const sq=i=>'abcdefgh'[i&7]+(8-(i>>4));
const idx=s=>(8-Number(s[1]))*16+'abcdefgh'.indexOf(s[0]);
const key=m=>sq(m[0])+sq(m[1])+m[2];
function parseFen(fen){
 const f=fen.trim().split(/\s+/),rows=f[0].split('/'),b=Array(128).fill('.');
 if(rows.length!==8||! /^[wb]$/.test(f[1])||! /^(?:-|K?Q?k?q?)$/.test(f[2])||! /^(?:-|[a-h][36])$/.test(f[3]))throw Error('FEN inválida');
 rows.forEach((row,r)=>{let c=0;for(const p of row){if(/^[1-8]$/.test(p))c+=Number(p);else{if(!/^[prnbqkPRNBQK]$/.test(p)||c>=8)throw Error('FEN inválida');b[r*16+c++]=p}}if(c!==8)throw Error('FEN inválida')});
 if(b.filter(p=>p==='K').length!==1||b.filter(p=>p==='k').length!==1)throw Error('Reis inválidos');
 return {b,t:f[1]==='w'?1:-1,c:(f[2].includes('K')?1:0)|(f[2].includes('Q')?2:0)|(f[2].includes('k')?4:0)|(f[2].includes('q')?8:0),ep:f[3]==='-'?-1:idx(f[3]),half:Number(f[4]||0),full:Number(f[5]||1)};
}
function attacked(s,target,by){
 for(let f=0;f<128;f++){if(!on(f)||side(s.b[f])!==by)continue;const p=s.b[f].toLowerCase();
 if(p==='p'){if(target===f-16*by-1||target===f-16*by+1)return true;continue}
 for(const d of dirs[p])for(let t=f+d;on(t);t+=d){if(t===target)return true;if(s.b[t]!=='.'||p==='n'||p==='k')break}}
 return false;
}
const checked=(s,color=s.t)=>attacked(s,s.b.indexOf(color===1?'K':'k'),-color);
function apply(s,m){
 const [f,t,promo,flag]=m,b=s.b.slice(),p=b[f],captured=b[t];let c=s.c;
 b[f]='.';b[t]=promo?(s.t===1?promo.toUpperCase():promo):p;
 if(flag==='ep')b[t+16*s.t]='.';
 if(flag==='castle'){const rf=t>f?f+3:f-4,rt=t>f?f+1:f-1;b[rt]=b[rf];b[rf]='.'}
 if(p==='K')c&=~3;if(p==='k')c&=~12;
 const bits={119:1,112:2,7:4,0:8};
 if(p.toLowerCase()==='r')c&=~(bits[f]||0);if(captured.toLowerCase()==='r')c&=~(bits[t]||0);
 return {b,t:-s.t,c,ep:p.toLowerCase()==='p'&&Math.abs(t-f)===32?(t+f)/2:-1,half:p.toLowerCase()==='p'||captured!=='.'||flag==='ep'?0:s.half+1,full:s.full+(s.t===-1?1:0)};
}
function pseudo(s){
 const out=[];
 for(let f=0;f<128;f++){if(!on(f)||side(s.b[f])!==s.t)continue;const p=s.b[f].toLowerCase();
 const add=(t,flag='')=>{if(s.b[t].toLowerCase()==='k')return;if(p==='p'&&((t>>4)===0||(t>>4)===7))for(const q of ['q','r','b','n'])out.push([f,t,q,flag]);else out.push([f,t,'',flag])};
 if(p==='p'){const t=f-16*s.t;if(on(t)&&s.b[t]==='.'){add(t);const u=t-16*s.t;if((f>>4)===(s.t===1?6:1)&&s.b[u]==='.')add(u)}
 for(const d of [-1,1]){const u=t+d;if(!on(u))continue;if(side(s.b[u])===-s.t)add(u);else if(u===s.ep&&s.b[u]==='.'&&s.b[u+16*s.t]===(s.t===1?'p':'P'))add(u,'ep')}}
 else{for(const d of dirs[p])for(let t=f+d;on(t);t+=d){if(side(s.b[t])===s.t)break;add(t);if(s.b[t]!=='.'||p==='n'||p==='k')break}
 const home=s.t===1?116:4,rook=s.t===1?'R':'r',bits=s.t===1?[1,2]:[4,8];
 if(p==='k'&&f===home&&!checked(s)){
 if((s.c&bits[0])&&s.b[f+3]===rook&&s.b[f+1]==='.'&&s.b[f+2]==='.'&&!attacked(s,f+1,-s.t)&&!attacked(s,f+2,-s.t))add(f+2,'castle');
 if((s.c&bits[1])&&s.b[f-4]===rook&&s.b[f-1]==='.'&&s.b[f-2]==='.'&&s.b[f-3]==='.'&&!attacked(s,f-1,-s.t)&&!attacked(s,f-2,-s.t))add(f-2,'castle');
 }}}
 return out;
}
const legal=s=>pseudo(s).filter(m=>!checked(apply(s,m),s.t));
function san(s,m){
 const [f,t,promo,flag]=m,p=s.b[f].toUpperCase(),capture=s.b[t]!=='.'||flag==='ep';let text='';
 if(flag==='castle')text=t>f?'O-O':'O-O-O';else{
 if(p!=='P'){text=p;const other=legal(s).filter(x=>x[0]!==f&&x[1]===t&&s.b[x[0]]===s.b[f]);if(other.length)text+=!other.some(x=>(x[0]&7)===(f&7))?sq(f)[0]:!other.some(x=>(x[0]>>4)===(f>>4))?sq(f)[1]:sq(f)}
 else if(capture)text=sq(f)[0];
 text+=(capture?'x':'')+sq(t)+(promo?'='+promo.toUpperCase():'')}
 const next=apply(s,m);return text+(checked(next)?legal(next).length?'+':'#':'');
}
const positionKey=s=>s.b.join('')+':'+s.t+':'+s.c+':'+(s.ep>=0&&legal(s).some(m=>m[3]==='ep')?s.ep:-1);
function insufficient(s){const pieces=[];for(let i=0;i<128;i++)if(on(i)&&s.b[i]!=='.'&&s.b[i].toLowerCase()!=='k')pieces.push([s.b[i].toLowerCase(),((i>>4)+(i&7))%2]);return pieces.length===0||(pieces.length===1&&['b','n'].includes(pieces[0][0]))||(pieces.every(p=>p[0]==='b')&&new Set(pieces.map(p=>p[1])).size===1)}
function status(history){
 const s=history.at(-1),moves=legal(s),check=checked(s),k=positionKey(s),repeats=history.filter(p=>positionKey(p)===k).length;
 if(!moves.length)return {done:true,winner:check?-s.t:0,text:check?'Xeque-mate — '+(s.t===1?'pretas':'brancas')+' venceram.':'Empate por afogamento.'};
 if(insufficient(s))return {done:true,winner:0,text:'Empate por material insuficiente.'};
 if(s.half>=150||repeats>=5)return {done:true,winner:0,text:'Empate — '+(s.half>=150?'regra dos 75 lances.':'repetição quíntupla.')};
 return {done:false,text:(s.t===1?'Brancas':'Pretas')+' jogam'+(check?' · Xeque':''),claim:repeats>=3?'repetição tripla':s.half>=100?'regra dos 50 lances':''};
}
const api={START,parseFen,legal,apply,checked,side,sq,idx,key,san,status};
if(typeof module!=='undefined')module.exports=api;else root.ChessEngine=api;
})(typeof globalThis!=='undefined'?globalThis:this);
