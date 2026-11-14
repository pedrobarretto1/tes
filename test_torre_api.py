import tempfile, unittest, time
from pathlib import Path
import servidor as s

class TowerAPI(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.old=(s.BASE,s.DATABASE_URL)
        s.BASE=Path(self.temp.name);s.DATABASE_URL=''
        s.setup()
        self.pid='tower-test'
        with s.database() as db:s.sql(db,'INSERT INTO players(id,name) VALUES(?,?)',(self.pid,'Tower test'))
    def tearDown(self):
        s.BASE,s.DATABASE_URL=self.old;self.temp.cleanup()
    def api(self,action,mode='ascensao',**data):
        return s.tower_action('/api/social/tower/'+action,dict(mode=mode,**data),self.pid,time.monotonic())
    def test_play_resume_and_isolation(self):
        code,a=self.api('state');self.assertEqual(code,200)
        self.assertEqual(a['progress']['id'],self.api('state')[1]['progress']['id'])
        code,a=self.api('start',route='guardian',version=a['progress']['version']);self.assertEqual(code,200)
        g=a['game'];self.assertEqual(len(g['board']),64)
        self.assertEqual(self.api('move',id=g['id'],sequence=0,move={'from':0,'path':[1],'cap':[]})[0],400)
        code,a=self.api('move',id=g['id'],sequence=0,move=g['legal'][0]);self.assertEqual(code,200)
        self.assertGreater(a['game']['sequence'],0)
        self.assertEqual(a['game']['board'],self.api('state')[1]['game']['board'])
        self.assertEqual(self.api('move',id=g['id'],sequence=0,move=g['legal'][0])[0],409)
        code,a=self.api('resign',id=g['id'],sequence=a['game']['sequence']);self.assertEqual(code,200)
        self.assertEqual(a['progress']['lives'],2)
        self.assertEqual(self.api('state',mode='expedicao')[1]['progress']['lives'],3)
        with s.database() as db:
            self.assertEqual(s.sql(db,'SELECT points FROM players WHERE id=?',(self.pid,)).fetchone()[0],1000)
            self.assertEqual(s.sql(db,'SELECT COUNT(*) FROM journey WHERE player_id=?',(self.pid,)).fetchone()[0],0)
    def test_no_client_result(self):
        self.assertEqual(self.api('finish',outcome='win')[0],404)
        self.assertEqual(self.api('state')[1]['progress']['floor'],1)
    def test_fixed_encounter_and_legacy_resume(self):
        import json
        from dataclasses import asdict
        from torre import Run
        run=Run(id='legacy',mode='ascensao',floor=25,highest=24,checkpoint=21,lives=2)
        with s.database() as db:
            s.sql(db,'INSERT INTO tower_runs(player_id,mode,payload) VALUES(?,?,?)',(self.pid,'ascensao',json.dumps({'progress':asdict(run),'game':None})))
        code,a=self.api('state')
        self.assertEqual((a['progress']['id'],a['progress']['lives']),('legacy',2))
        self.assertEqual(a['progress']['encounter']['kind'],'boss')
        self.assertEqual(self.api('start',route='unknown',version=0)[0],409)
        code,a=self.api('start',route='guardian',version=0)
        self.assertEqual(code,200)
        self.assertEqual(a['game']['encounter']['name'],'O Cavaleiro Sem Nome')
        self.assertEqual(a['game']['chapter'],2)
        self.assertEqual(self.api('state')[1]['game']['id'],a['game']['id'])
    def test_beginner_balance_and_legacy_game(self):
        from unittest.mock import patch
        from torre import ai_balance
        for route in ('guardian','executioner','unknown'):
            self.assertEqual(ai_balance(1,route)['chance'],0)
        self.assertGreater(ai_balance(25)['chance'],ai_balance(10)['chance'])
        a=self.api('state')[1]
        a=self.api('start',route='executioner',version=a['progress']['version'])[1]
        g=a['game']
        self.assertEqual(a['balance']['label'],'Muito fácil')
        self.assertEqual(g['balance']['chance'],0)
        # A legacy active game must also use the new beginner policy.
        with s.database() as db:
            import json
            raw=s.sql(db,'SELECT payload FROM tower_runs WHERE player_id=? AND mode=?',(self.pid,'ascensao')).fetchone()[0]
            data=json.loads(raw);data['game'].pop('balance',None);data['game']['chapter']=4
            s.sql(db,'UPDATE tower_runs SET payload=? WHERE player_id=? AND mode=?',(json.dumps(data),self.pid,'ascensao'))
        with patch.object(s,'journey_ai',side_effect=AssertionError('beginner must not search')):
            code,a=self.api('move',id=g['id'],sequence=0,move=g['legal'][0])
        self.assertEqual(code,200)
        self.assertEqual(a['game']['id'],g['id'])
        self.assertEqual(a['game']['chapter'],0)
        self.assertEqual(a['game']['balance']['chance'],0)
        self.assertEqual(a['progress']['lives'],3)
    def test_beginner_playtest(self):
        import random
        from collections import Counter
        results=Counter()
        for seed in range(12):
            rng=random.Random(seed);b=s.initial_for('official');repeats={};side=1
            for ply in range(200):
                legal=s.legal(b,side,'official')
                if not legal:
                    results['win' if side==-1 else 'loss']+=1;break
                if side==1:
                    def score(m):
                        x=s.journey_apply(b,m)
                        danger=max((len(r['cap']) for r in s.legal(x,-1,'official')),default=0)
                        promote=abs(b[m['from']])==1 and abs(x[m['path'][-1]])==2
                        return 3*len(m['cap'])-3*danger+2*promote+.15*(m['from']//8-m['path'][-1]//8)-2*repeats.get(s.position_key(x,-1,'official'),0)+rng.random()*.3
                    m=max(legal,key=score)
                else:
                    m=s.tower_ai(dict(board=b,floor=1,route='guardian',id=str(seed),sequence=ply,repeats=repeats),rng)
                    self.assertIn(m,legal)
                b=s.journey_apply(b,m);side=-side;k=s.position_key(b,side,'official');repeats[k]=repeats.get(k,0)+1
                if repeats[k]>=3:results['draw']+=1;break
            else:results['draw']+=1
        print('TOWER BEGINNER PLAYTEST',dict(results),flush=True)
        self.assertGreaterEqual(results['win'],9)
if __name__=='__main__':unittest.main()
