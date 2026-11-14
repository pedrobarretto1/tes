import json,tempfile,unittest,time
from pathlib import Path
import servidor as s
import bot_duels as bot

class BotTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.old=s.BASE,s.DATABASE_URL;s.BASE=Path(self.temp.name);s.DATABASE_URL=''
        s.setup()
        self.pid='bot-test'
        with s.database() as db:
            for pid in (self.pid,'other'):s.sql(db,'INSERT INTO players(id,name) VALUES(?,?)',(pid,pid))
    def tearDown(self):
        s.BASE,s.DATABASE_URL=self.old;self.temp.cleanup()
    def api(self,op,pid=None,**d):return bot.action(s,'/api/social/bot/'+op,d,pid or self.pid)
    def start(self,level='medium',**d):
        code,g=self.api('start',level=level,rule='official',nonce='a'*16,**d)
        self.assertEqual(code,200,g);return g
    def store(self,g):
        with s.database() as db:s.sql(db,'UPDATE bot_duels SET payload=? WHERE player_id=?',(json.dumps(g),self.pid))
    def score(self):
        with s.database() as db:
            p=s.sql(db,'SELECT points,wins,losses,draws FROM players WHERE id=?',(self.pid,)).fetchone()
            return tuple(p)+(s.wallet_state(db,self.pid)['coins'],)
    def test_authoritative_moves_retry_and_identity(self):
        g=self.start();mid=g['match']
        self.assertEqual(self.api('start',level='hard',rule='official',nonce='a'*16)[1]['level'],'medium')
        self.assertEqual(self.api('state',pid='other',match=mid)[0],409)
        self.assertEqual(self.api('finish',match=mid,sequence=0,winner=g['side'])[0],404)
        if g['turn']!=g['side']:g=self.api('bot',match=mid,sequence=0)[1]
        seq=g['sequence']
        self.assertEqual(self.api('move',match=mid,sequence=seq,move={'from':0,'path':[1],'cap':[]})[0],409)
        self.assertEqual(self.api('bot',match=mid,sequence=seq)[0],409)
        m=s.legal(g['board'],g['side'],'official')[0]
        code,new=self.api('move',match=mid,sequence=seq,move=m,winner=g['side'],level='hard')
        self.assertEqual(code,200);self.assertEqual(new['board'],bot.apply(g['board'],m));self.assertEqual(new['sequence'],seq+1)
        self.assertEqual(self.api('move',match=mid,sequence=seq,move=m)[1]['sequence'],seq+1)
        self.assertEqual(self.score(),(1000,0,0,0,0))
        code,new=self.api('resign',match=mid);self.assertEqual(code,200);self.assertEqual(new['result']['deltas'][str(g['side'])],-10)
        self.assertEqual(self.api('resign',match=mid)[1]['result'],new['result'])
        self.assertEqual(self.score(),(990,0,1,0,0))
    def terminal(self,level,kind):
        g=self.start(level);g['side']=1;g['turn']=1;g['sequence']=8;g['board']=[0]*64
        # A legal winning capture from d4 to f6; one black piece.
        g['board'][35]=1;g['board'][28]=-1
        g['repeats']={s.boardkey(g):1}
        if kind=='draw':
            g['board']=[0]*64;g['board'][35]=2;g['board'][0]=-2
            g['offer']=True;g['repeats']={s.boardkey(g):1}
        self.store(g)
        if kind=='win':return self.api('move',match=g['match'],sequence=8,move=s.legal(g['board'],1,'official')[0])[1]
        if kind=='draw':return self.api('draw',match=g['match'],sequence=8,accept=True)[1]
        g['minutes']=1;g['remaining']={'1':0,'-1':60};self.store(g)
        return self.api('state',match=g['match'])[1]
    def test_medium_win(self):
        g=self.terminal('medium','win');self.assertEqual(g['result']['winner'],1);self.assertEqual(self.score(),(1013,1,0,0,8))
        self.assertEqual(self.api('state',match=g['match'])[1]['result'],g['result'])
        with s.database() as db:
            self.assertEqual(s.sql(db,'SELECT COUNT(*) FROM results').fetchone()[0],1)
            self.assertEqual(s.sql(db,'SELECT COUNT(*) FROM replays').fetchone()[0],1)
            self.assertEqual(s.sql(db,'SELECT completed FROM cosmetics WHERE player_id=?',(self.pid,)).fetchone()[0],1)
    def test_hard_win(self):
        self.terminal('hard','win');self.assertEqual(self.score(),(1025,1,0,0,15))
    def test_medium_draw(self):
        self.terminal('medium','draw');self.assertEqual(self.score(),(1003,0,0,1,4))
    def test_hard_loss(self):
        self.terminal('hard','loss');self.assertEqual(self.score(),(985,0,1,0,8))
    def test_practice_and_reset(self):
        for level,rule in [('easy','official'),('hard','kings'),('hard','custom-1111')]:
            self.assertEqual(self.api('start',level=level,rule=rule,nonce='a'*16)[0],400)
        self.assertEqual(self.score(),(1000,0,0,0,0))
        g=self.start();new=self.api('start',level='hard',rule='official',nonce='b'*16)[1]
        self.assertNotEqual(g['match'],new['match'])
        self.assertEqual(self.score(),(990,0,1,0,0))
        self.assertEqual(self.api('resign',match=g['match'])[0],409)
        self.assertEqual(self.api('resign',match=new['match'])[1]['result']['coins'],0)
        self.assertEqual(self.score(),(970,0,2,0,0))
if __name__=='__main__':unittest.main()
