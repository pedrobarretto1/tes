(()=>{'use strict';
const E=id=>document.getElementById(id),root=document.documentElement,board=E('board'),result=E('victory'),status=E('demostatus'),reduce=matchMedia('(prefers-reduced-motion: reduce)'),titles={shadow:'A Fortaleza do Rei Caído',divine:'A Catedral do Sol Eterno',infinite:'O Coração do Universo'};
let key=new URLSearchParams(location.search).get('king');if(!Object.hasOwn(titles,key))key='shadow';
let b=[],motion=0,epoch=0,busy=false,lastFinal=null,endingType=null,skip=false;
const initial=()=>Array.from({length:64},(_,i)=>{let r=i>>3,c=i%8;return (r+c)%2?(r<3?-1:r>=5?1:0):0});
const pos=i=>({x:(i%8+.5)*12.5,y:((i>>3)+.5)*12.5});
function stone(p){let n=document.createElement('span');n.className='piece '+(p>0?'white':'black')+(Math.abs(p)===2?' king':'');return n}
function render(){board.replaceChildren();for(let i=0;i<64;i++){let sq=document.createElement('div');sq.className='sq '+(((i>>3)+i%8)%2?'dark':'light');sq.dataset.square=i;if(b[i])sq.append(stone(b[i]));board.append(sq)}}
function buttons(){document.querySelectorAll('[data-action]').forEach(e=>{let a=e.dataset.action;e.disabled=a==='skip'?!endingType:busy&&a!=='reset'});}
function hide(){result.classList.remove('shown');result.inert=true;result.setAttribute('aria-hidden','true')}
function reset(next=initial()){epoch++;cancelAnimationFrame(motion);motion=0;busy=false;endingType=null;skip=false;window.royalReset();hide();b=next.slice();render();buttons()}
function select(k){reset();key=k;root.dataset.theme='relic-'+k;root.dataset.skin='skin-relic-'+k;E('demotitle').textContent=titles[k];document.querySelectorAll('[data-king]').forEach(x=>x.setAttribute('aria-pressed',String(x.dataset.king===k)));status.textContent='Escolha uma animação. Você controla as peças claras.'}
function setup(entries){let out=Array(64).fill(0);for(let [i,p] of entries)out[i]=p;return out}
function move(from,to,cap=null,promote=false,onDone=null){
 let p=b[from];if(!p||b[to]||busy)return;busy=true;buttons();let ticket=epoch,ghost=stone(p),layer=document.createElement('div');layer.className='demo-flight';layer.append(ghost);board.append(layer);board.children[from].querySelector('.piece').style.visibility='hidden';let a=pos(from),z=pos(to),elapsed=0,last=0,duration=reduce.matches?1:cap===null?620:820;
 const step=t=>{if(ticket!==epoch)return;let dt=last?Math.min(34,t-last):0;last=t;if(document.hidden)dt=0;elapsed+=dt;let u=Math.min(1,elapsed/duration),q=u*u*(3-2*u),x=a.x+(z.x-a.x)*q,y=a.y+(z.y-a.y)*q;ghost.style.left=x+'%';ghost.style.top=y+'%';window.royalTrack(x,y,Math.sign(p));if(u<1){motion=requestAnimationFrame(step);return}
 motion=0;let victim=cap===null?0:b[cap];b[from]=0;b[to]=promote?Math.sign(p)*2:p;if(cap!==null){b[cap]=0;let v=pos(cap);window.royalCapture(victim,1,v.x,v.y)}if(promote)window.royalPromotion(Math.sign(p),z.x,z.y);render();busy=false;buttons();onDone?.()};
 ghost.style.left=a.x+'%';ghost.style.top=a.y+'%';motion=requestAnimationFrame(step);
}
function reveal(type){if(!endingType)return;E('resulttitle').textContent=({victory:'Vitória',defeat:'Derrota',resign:'Desistência'})[type];result.classList.add('shown');result.inert=false;result.setAttribute('aria-hidden','false');busy=false;endingType=null;buttons();status.textContent='Final concluído. Repita a animação ou explore outra relíquia.'}
function final(type){lastFinal=type;endingType=type;busy=true;buttons();status.textContent='A relíquia reage ao destino da partida…';if(!window.royalEnd(type,()=>reveal(type)))reveal(type)}
function run(a){if(a==='reset'){reset();status.textContent='Tabuleiro restaurado.';return}if(a==='skip'){if(endingType){let t=endingType;window.royalReset();reveal(t)}return}if(busy)return;
 if(a==='resign'){let saved=b.slice();reset(saved);final(a);return}
 if(a==='move'){reset();status.textContent='Observe o símbolo acompanhando o movimento.';move(40,33);return}
 if(a==='capture'||a==='victory'){reset(setup([[42,1],[35,-1],[17,2],[26,1],[49,1],...(a==='capture'?[[19,-1],[21,-1]]:[])]));status.textContent='Sua pedra captura a adversária.';move(42,28,35,false,()=>{if(a==='victory')final(a);else status.textContent='A relíquia celebra sua captura.'});return}
 if(a==='loss'||a==='defeat'){reset(setup([[21,-1],[28,1],[8,-1],[17,-2],[42,-1],...(a==='loss'?[[56,1],[58,1],[60,1]]:[])]));status.textContent='O adversário captura uma das suas pedras.';move(21,35,28,false,()=>{if(a==='defeat')final(a);else status.textContent='A relíquia sente sua perda.'});return}
 if(a==='crown'){reset(setup([[10,1],[19,-1],[21,-1],[26,1],[42,1]]));status.textContent='Sua pedra alcança a última linha.';move(10,1,null,true,()=>{status.textContent='Uma nova dama foi coroada.'})}
}
document.querySelectorAll('[data-king]').forEach(e=>e.onclick=()=>select(e.dataset.king));document.querySelectorAll('[data-action]').forEach(e=>e.onclick=()=>run(e.dataset.action));E('dismiss').onclick=hide;E('replay').onclick=()=>{hide();if(lastFinal)run(lastFinal)};document.addEventListener('keydown',e=>{if(e.key==='Escape')parent.postMessage({type:'royal-demo-close'},'*')});select(key);
})();