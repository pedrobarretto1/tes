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
        self.assertEqual(a['game']['chapter'],3)
        self.assertEqual(self.api('state')[1]['game']['id'],a['game']['id'])
if __name__=='__main__':unittest.main()
