'use strict';
const assert=require('node:assert/strict'),C=require('./chess-engine.js');
const start=C.parseFen(C.START);
function perft(s,d){if(!d)return 1;return C.legal(s).reduce((n,m)=>n+perft(C.apply(s,m),d-1),0)}
assert.equal(perft(start,1),20);assert.equal(perft(start,2),400);assert.equal(perft(start,3),8902);
function line(fen,seq){let h=[C.parseFen(fen)];for(let u of seq){let s=h.at(-1),m=C.legal(s).find(x=>C.key(x)===u);assert(m,'illegal '+u);h.push(C.apply(s,m))}return h}
let h=line(C.START,['f2f3','e7e5','g2g4','d8h4']);assert.equal(C.status(h).winner,-1);
h=line(C.START,['e2e4','a7a6','e4e5','d7d5','e5d6']);assert.equal(h.at(-1).b[C.idx('d5')],'.');assert.equal(h.at(-1).b[C.idx('d6')],'P');
h=line(C.START,['e2e4','e7e5','g1f3','b8c6','f1c4','g8f6','e1g1']);assert.equal(h.at(-1).b[C.idx('f1')],'R');assert.equal(h.at(-1).b[C.idx('g1')],'K');
let p=C.parseFen('4k3/P7/8/8/8/8/8/4K3 w - - 0 1');assert.equal(C.legal(p).filter(m=>m[0]===C.idx('a7')).length,4);
assert.equal(C.status([C.parseFen('7k/5Q2/6K1/8/8/8/8/8 b - - 0 1')]).winner,0);
assert(C.status([C.parseFen('4k3/8/8/8/8/8/8/4K3 w - - 0 1')]).done);
h=line(C.START,['g1f3','g8f6','f3g1','f6g8','g1f3','g8f6','f3g1','f6g8']);assert.equal(C.status(h).claim,'repetição tripla');
assert(!C.legal(C.parseFen('4r1k1/8/8/8/8/8/4R3/4K3 w - - 0 1')).some(m=>C.key(m)==='e2d2'));
console.log('CHESS ENGINE OK: perft 20/400/8902, mate, en passant, castling, promotion, draw and pin');
