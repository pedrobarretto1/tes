(()=>{'use strict';
const E=id=>document.getElementById(id),check=E('livepermission'),focus=E('focuslive');
let enabled=localStorage.getItem('damas-live-optin')==='yes',match=crypto.randomUUID(),sent='',lastSent=0,inflight=false,revision=0,dirty=false,stopPending=false,finalAt=0,ownerToken='';
window.liveEnabled=()=>enabled;
async function request(action,data={},token=profileToken()){if(!token)return;let ctl=new AbortController(),timer=setTimeout(()=>ctl.abort(),8000);try{let res=await fetch('/api/social/live/'+action,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...data,profileToken:token}),signal:ctl.signal});if(!res.ok)throw Error('Transmissão indisponível');return await res.json()}finally{clearTimeout(timer)}}
function paint(){check.checked=enabled;focus.setAttribute('aria-pressed',String(enabled));focus.textContent=enabled?'◉ Transmitindo':'◉ Transmitir';focus.hidden=mode==='online';}
function eligible(){return enabled&&mode!=='online'&&offlineStarted}
function stop(){revision++;sent='';lastSent=0;finalAt=0;stopPending=true;dirty=true;flush()}
function change(v){enabled=v;localStorage.setItem('damas-live-optin',v?'yes':'no');paint();if(!v)stop();else{dirty=true;flush()}}
check.onchange=()=>change(check.checked);focus.onclick=()=>change(!enabled);
window.liveReset=()=>{match=crypto.randomUUID();if(enabled||sent||inflight)stop()};
function snapshot(){let result=winner==='draw'?0:winner||null;return {public:true,match,mode:window.journeyActive?.()?'journey':mode,rule:ruleMode,board:b.slice(),side:mySide,turn,sequence:Math.max(0,sequence||0),last:last.slice(),result,opponent:name(-mySide)}}
function flush(){if(inflight)return;let token=profileToken();if(ownerToken&&ownerToken!==token){let old=ownerToken;ownerToken='';sent='';lastSent=0;revision++;inflight=true;request('stop',{},old).catch(()=>{}).finally(()=>{inflight=false;flush()});return}
if(stopPending){stopPending=false;inflight=true;request('stop',{},ownerToken||token).catch(()=>{}).finally(()=>{inflight=false;ownerToken='';if(dirty||stopPending)flush()});return}
if(!eligible()){dirty=false;if(sent){stop()}return}
if(!token)return;let data=snapshot(),signature=JSON.stringify(data),now=Date.now();if(data.result!==null){if(!finalAt)finalAt=now;if(now-finalAt>12000){dirty=false;return}}else finalAt=0;
if(signature===sent&&now-lastSent<3500){dirty=false;return}
let ticket=revision;dirty=false;inflight=true;ownerToken=token;request('publish',data,token).then(()=>{if(ticket===revision){sent=signature;lastSent=Date.now()}}).catch(()=>{}).finally(()=>{inflight=false;if(dirty||stopPending)flush()})}
window.liveRender=()=>{paint();dirty=true;flush()};paint();setInterval(()=>{dirty=true;flush()},3500);
window.addEventListener('pagehide',()=>{if(ownerToken)fetch('/api/social/live/stop',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({profileToken:ownerToken}),keepalive:true}).catch(()=>{})});
})();