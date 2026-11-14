(()=>{'use strict';
const E=id=>document.getElementById(id),check=E('livepermission'),focus=E('focuslive');
let enabled=localStorage.getItem('damas-live-optin')==='yes',match=crypto.randomUUID(),sent='',lastSent=0,pending=false,rev=0,queued=false;
window.liveEnabled=()=>enabled;
async function request(action,data={}){let token=profileToken();if(!token)return;let res=await fetch('/api/social/live/'+action,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...data,profileToken:token})});if(!res.ok)throw Error('Transmissão indisponível');return res.json()}
function paint(){check.checked=enabled;focus.setAttribute('aria-pressed',String(enabled));focus.textContent=enabled?'◉ Transmitindo':'◉ Transmitir';focus.hidden=mode==='online';}
function stop(){rev++;sent='';lastSent=0;queued=false;request('stop').catch(()=>{})}
function change(v){enabled=v;localStorage.setItem('damas-live-optin',v?'yes':'no');paint();if(!enabled)stop();else publish(true)}
check.onchange=()=>change(check.checked);focus.onclick=()=>change(!enabled);
window.liveReset=()=>{match=crypto.randomUUID();sent='';lastSent=0;rev++;if(enabled)stop()};
function publish(force=false){paint();if(!enabled||mode==='online'||!offlineStarted){if(sent)stop();return}if(pending){queued=true;return}
let result=winner==='draw'?0:winner||null,kind=window.journeyActive?.()?'journey':mode;
let data={public:true,match,mode:kind,rule:ruleMode,board:b.slice(),side:mySide,turn,sequence:Math.max(0,sequence||0),last:last.slice(),result,opponent:name(-mySide)};
let signature=JSON.stringify(data),now=Date.now();if(!force&&signature===sent&&now-lastSent<3500)return;if(!force&&result!==null&&signature===sent&&now-lastSent>12000)return;
let ticket=rev;pending=true;request('publish',data).then(()=>{if(ticket===rev){sent=signature;lastSent=Date.now()}}).catch(()=>{}).finally(()=>{pending=false;if(queued){queued=false;publish(true)}});
}
window.liveRender=()=>publish();paint();setInterval(()=>publish(),3500);
window.addEventListener('pagehide',()=>{if(enabled&&sent){let token=profileToken();if(token)fetch('/api/social/live/stop',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({profileToken:token}),keepalive:true}).catch(()=>{})}});
})();