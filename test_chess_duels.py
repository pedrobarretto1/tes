import tempfile, unittest, time
from pathlib import Path
import servidor as s
import chess_duels as c

class ChessDuelsTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.old=s.BASE,s.DATABASE_URL
        s.BASE=Path(self.tmp.name);s.DATABASE_URL='';s.setup()
        self.a='a'*64;self.b='b'*64;self.z='z'*64
        self.pa=s.profile(dict(name='Alice',profileToken=self.a));self.pb=s.profile(dict(name='Bob',profileToken=self.b));self.pz=s.profile(dict(name='Zed',profileToken=self.z))
        for t in (self.a,self.b,self.z):self.call(t,'state')
    def tearDown(self):
        for p in (self.pa,self.pb,self.pz):s.PRESENCE.pop(p,None);s.PRESENCE_GAME.pop(p,None);s.MATCH_QUEUE.pop(p,None)
        s.BASE,s.DATABASE_URL=self.old;self.tmp.cleanup()
    def call(self,t,op,**d):
        return s.social_action('/api/social/chess/'+op,dict(profileToken=t,**d),time.monotonic())
    def ok(self,t,op,**d):
        code,r=self.call(t,op,**d);self.assertEqual(code,200,r);return r
    def start(self,level='medium',minutes=0):
        return self.ok(self.a,'start',level=level,minutes=minutes,nonce='a'*16)['match']
    def duel(self,ranked=True,minutes=0):
        self.ok(self.a,'invite',target=self.pb,ranked=ranked,minutes=minutes)
        inv=self.ok(self.b,'state')['chess_invites'][0]
        self.assertEqual(self.call(self.z,'respond',invite=inv['id'],accept=True)[0],409)
        return self.ok(self.b,'respond',invite=inv['id'],accept=True)['match']
    def tokens(self,g):return (self.b,self.a) if g['side']=='w' else (self.a,self.b)
    def test_online_mate_idempotent_isolated(self):
        g=self.duel();w,b=self.tokens(g);mid=g['id']
        self.assertEqual(self.call(b,'move',match=mid,sequence=0,move='e7e5')[0],409)
        self.assertEqual(self.call(self.z,'move',match=mid,sequence=0,move='e2e4')[0],409)
        self.assertEqual(self.call(w,'move',match=mid,sequence=0,move='e2e5')[0],409)
        for i,(t,m) in enumerate([(w,'f2f3'),(b,'e7e5'),(w,'g2g4'),(b,'d8h4')]):g=self.ok(t,'move',match=mid,sequence=i,move=m)['match']
        self.assertEqual(g['result']['winner'],'b');self.assertEqual(g['result']['reason'],'checkmate')
        self.assertEqual(self.ok(b,'state')['profile']['points'],1025);self.assertEqual(self.ok(w,'state')['profile']['points'],985)
        self.ok(b,'move',match=mid,sequence=3,move='d8h4')
        self.assertEqual(self.ok(b,'state')['profile']['points'],1025)
        with s.database() as db:
            self.assertEqual(s.sql(db,'SELECT COUNT(*) FROM chess_history').fetchone()[0],2)
            self.assertEqual(s.sql(db,'SELECT points,wins FROM players WHERE id=?',(self.pa,)).fetchone(),(1000,0))
    def test_ai_levels_and_retries(self):
        g=self.start('medium');mid=g['id'];side=g['side']
        self.assertEqual(self.ok(self.a,'start',level='hard',minutes=0,nonce='a'*16)['match']['id'],mid)
        if side=='b':g=self.ok(self.a,'bot',match=mid,sequence=0)['match']
        seq=len(g['moves']);b=c.board(g);m=next(iter(b.legal_moves)).uci()
        g=self.ok(self.a,'move',match=mid,sequence=seq,move=m)['match']
        self.assertEqual(len(self.ok(self.a,'move',match=mid,sequence=seq,move=m)['match']['moves']),seq+1)
        self.ok(self.a,'bot',match=mid,sequence=seq+1)
        r=self.ok(self.a,'resign',match=mid);self.assertEqual(r['profile']['points'],990);self.assertEqual(r['profile']['losses'],1)
        self.assertEqual(self.ok(self.a,'resign',match=mid)['profile']['points'],990)
        g=self.ok(self.a,'start',level='easy',minutes=0,nonce='b'*16)['match'];self.assertFalse(g['ranked'])
        self.assertEqual(self.ok(self.a,'resign',match=g['id'])['profile']['points'],990)
    def test_ranked_coins_and_draw(self):
        g=self.duel();w,b=self.tokens(g);mid=g['id']
        for i,m in enumerate(['e2e4','e7e5','g1f3','b8c6','f1c4','g8f6','d2d3','f8c5']):self.ok(w if i%2==0 else b,'move',match=mid,sequence=i,move=m)
        self.ok(w,'draw',match=mid,accept=True)
        self.assertIsNone(self.ok(b,'draw',match=mid,accept=True)['match']['result']['winner'])
        for t in (w,b):
            p=self.ok(t,'state')['profile'];self.assertEqual((p['points'],p['coins'],p['draws']),(1005,8,1))
    def test_casual_and_queue(self):
        self.ok(self.a,'queue',minutes=3,ranked=False);self.ok(self.b,'queue',minutes=3,ranked=False)
        g=self.ok(self.a,'state')['match'];self.assertEqual(g['mode'],'online');self.assertFalse(g['ranked'])
        self.assertEqual(self.ok(self.b,'state')['match']['id'],g['id'])
        self.ok(self.a,'resign',match=g['id']);self.assertEqual(self.ok(self.b,'state')['profile']['points'],1000)
    def test_timeout(self):
        g=self.start('hard',minutes=1)
        with s.database() as db:
            raw=c.current(db,s.sql,self.pa);raw['remaining'][raw['players']['w'] is None and 'b' or 'w']=0
            if g['side']=='b':
                raw['moves']=['e2e4'];raw['remaining']['b']=0
            else:raw['remaining']['w']=0
            c.save(db,s.sql,raw)
        r=self.ok(self.a,'state');self.assertEqual(r['match']['result']['reason'],'timeout');self.assertEqual(r['profile']['points'],985)
if __name__=='__main__':unittest.main()
