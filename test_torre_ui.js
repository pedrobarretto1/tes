'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const html=fs.readFileSync('torre.html','utf8');
const source=[...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].at(-1)[1];
const ids=[...html.matchAll(/\bid="([^"]+)"/g)].map(m=>m[1]);
class Element {
    constructor(){this.children=[];this.dataset={};this.style={};this.checked=false;this.textContent='';this.className='';this.classes=new Set();this.classList={toggle:(n,v)=>v?this.classes.add(n):this.classes.delete(n),add:n=>this.classes.add(n),remove:n=>this.classes.delete(n)}}
    append(...nodes){this.children.push(...nodes)}
    replaceChildren(...nodes){this.children=nodes}
    setAttribute(k,v){this[k]=v}
    querySelector(){return null}
}
const initial=Array.from({length:64},(_,i)=>(Math.floor(i/8)+i%8)%2?(i<24?-1:i>=40?1:0):0);
const settle=()=>new Promise(resolve=>setImmediate(resolve));
function fixture(mode,status='playing',outcome=null,reason=null,floor=1,lives=3){
    const meta={floor,name:'Guardião',kind:'normal',stage:1,chapter:'Portões',style:'Defesa',difficulty:1};
    const board=Array(64).fill(0);board[40]=1;board[19]=-2;
    return {progress:{mode,status,floor,highest:floor-1,checkpoint:1,lives,version:2,domain:{id:'castle',name:'Castelo Esquecido',first:1,last:25},encounter:meta,realm_map:[],total_floors:100},balance:{label:'Muito fácil'},game:{id:'old',floor:1,outcome,reason,encounter:meta,board,chapter:0,sequence:4,legal:outcome?[]:[{from:40,path:[33],cap:[]}],last:[40,33],moves:[{from:40,path:[33],cap:[],side:1}],botOffer:{sequence:4}}};
}
function boot(response){
    const els=Object.fromEntries(ids.map(id=>[id,new Element()]));
    const doc={getElementById:id=>els[id],createElement:()=>new Element(),documentElement:new Element(),hidden:false,addEventListener(){}};
    const storage={getItem:k=>k==='damas-profile-token'?'token':'Tester'};
    let current=response,requests=[];
    const fetch=async(url,opts)=>{let action=url.split('/').at(-1),body=JSON.parse(opts.body);requests.push({action,body});return {ok:true,json:async()=>current}};
    new Function('document','localStorage','fetch','confirm','matchMedia',source)(doc,storage,fetch,()=>true,()=>({matches:true}));
    return {els,requests,set:x=>current=x};
}
function assertReset(els){
    assert.equal(els.board.children.length,64);
    for(let square of els.board.children){
        const i=Number(square.dataset.square),piece=square.children.find(c=>c.className.startsWith('piece '));
        assert.equal(piece?.className||null,initial[i]?(initial[i]>0?'piece white':'piece black'):null,'initial square '+i);
        assert(!/\b(last|target|selected|playable)\b/.test(square.className),'old board marks');
    }
    assert.equal(els.count1.textContent,12);
    assert.equal(els.count2.textContent,12);
    assert.equal(els.resign.hidden,true);
    assert.equal(els.accept.hidden,true);
    assert(!els.arena.classes.has('tower-focus'));
    assert(els.choices.children.length>0);
}
(async()=>{
    for(const mode of ['ascensao','expedicao']){
        for(const [outcome,reason,action,status,floor,lives] of [
            ['win',null,'move','choose',2,3],
            ['loss',null,'move','choose',1,2],
            ['draw','agreement','draw','choose',1,3],
            ['loss','resign','resign','choose',1,2],
            ['loss','resign','resign',mode==='expedicao'?'ended':'choose',1,mode==='expedicao'?0:3],
            ['win',null,'move','completed',30,3]
        ]){
            const active=fixture(mode),terminal=fixture(mode,status,outcome,reason,floor,lives);
            const app=boot(active);await settle();
            if(mode==='expedicao'){app.els.exp.onclick();await settle()}
            assert.equal(app.els.count1.textContent,1);
            assert.equal(app.els.count2.textContent,1);
            app.els.focustoggle.onclick();assert(app.els.arena.classes.has('tower-focus'));
            app.set(terminal);
            if(action==='resign')app.els.resign.onclick();
            else if(action==='draw')app.els.accept.onclick();
            else {app.els.board.children[40].onclick();app.els.board.children[33].onclick()}
            await settle();
            assert.equal(app.requests.at(-1).action,action);
            assert.equal(app.requests.at(-1).body.mode,mode);
            assertReset(app.els);
            assert.equal(app.els.statfloor.textContent,floor+' / 100');
            assert.equal(app.els.statlives.textContent,lives+' / 3');
            assert.match(app.els.historylabel.textContent,/Última partida/);
            // Refresh and mode changes must not resurrect the previous board.
            await app.els.refresh.onclick();assertReset(app.els);
            const reloaded=boot(terminal);await settle();assertReset(reloaded.els);
        }
    }
    console.log('TOWER UI RESET OK: 12 terminal scenarios, both modes, reload, focus, history and 24 pieces');
})().catch(e=>{console.error(e);process.exitCode=1});
