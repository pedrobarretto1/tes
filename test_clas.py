import tempfile, unittest, time
from pathlib import Path
import servidor as s
import clas

class ClanTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.old=s.BASE,s.DATABASE_URL
        s.BASE=Path(self.temp.name);s.DATABASE_URL=''
        s.setup()
        with s.database() as db:
            for p in ('owner','alice','bob','guest','other'):
                s.sql(db,'INSERT INTO players(id,name) VALUES(?,?)',(p,p.title()))
                if p!='guest':s.sql(db,'INSERT INTO accounts(player_id,username,salt,password_hash) VALUES(?,?,?,?)',(p,p,'salt','hash'))
    def tearDown(self):
        s.BASE,s.DATABASE_URL=self.old;self.temp.cleanup()
    def call(self,who,op,**d):
        return clas.action(s,'/api/social/clans/'+op,d,who)
    def create(self,who='owner',**req):
        code,d=self.call(who,'create',name='Ordem Real',tag='REAL',requirements=req)
        self.assertEqual(code,200,d);return d['mine']['id']
    def test_requirements_and_ownership(self):
        cid=self.create(points=1200,wins=10)
        self.assertEqual(self.call('guest','create',name='Guest',tag='GUE')[0],403)
        self.assertEqual(self.call('alice','apply',clan=cid)[0],409)
        with s.database() as db:s.sql(db,'UPDATE players SET points=1300,wins=12 WHERE id=?',('alice',))
        self.assertEqual(self.call('alice','apply',clan=cid)[0],200)
        self.assertEqual(self.call('alice','apply',clan=cid)[0],409)
        self.assertEqual(self.call('bob','state')[1]['requests'],[])
        r=self.call('owner','state')[1]['requests'][0]
        self.assertTrue(all(x['ok'] for x in r['checks']))
        self.assertEqual(self.call('bob','respond',id=r['id'],accept=True)[0],403)
        with s.database() as db:s.sql(db,'UPDATE players SET points=1100 WHERE id=?',('alice',))
        self.assertEqual(self.call('owner','respond',id=r['id'],accept=True)[0],409)
        self.assertEqual(self.call('owner','edit',requirements={})[0],200)
        self.assertEqual(self.call('owner','respond',id=r['id'],accept=True)[0],200)
        self.assertEqual(self.call('owner','respond',id=r['id'],accept=True)[0],409)
        self.assertEqual(self.call('alice','create',name='Another',tag='AAA')[0],409)
        self.assertEqual(self.call('alice','state')[1]['mine']['id'],cid)
        self.assertEqual(self.call('alice','edit',requirements={})[0],403)
    def test_invite_chat_transfer(self):
        cid=self.create()
        self.assertEqual(self.call('bob','chat')[0],403)
        self.assertEqual(self.call('owner','invite',target='alice')[0],200)
        self.assertEqual(self.call('owner','state')[1]['requests'],[])
        r=self.call('alice','state')[1]['requests'][0]
        self.assertEqual(r['kind'],'invite')
        self.assertEqual(self.call('bob','respond',id=r['id'],accept=True)[0],403)
        self.assertEqual(self.call('alice','respond',id=r['id'],accept=True)[0],200)
        self.assertEqual(self.call('owner','send',body='<script>alert(1)</script>')[0],200)
        self.assertEqual(self.call('alice','chat')[1]['messages'][0]['body'],'<script>alert(1)</script>')
        self.assertEqual(self.call('bob','chat')[0],403)
        self.assertEqual(self.call('owner','leave')[0],409)
        self.assertEqual(self.call('owner','transfer',target='alice')[0],200)
        self.assertEqual(self.call('owner','leave')[0],200)
        self.assertEqual(self.call('owner','chat')[0],403)
        self.assertEqual(self.call('alice','dissolve')[0],200)
        self.assertIsNone(self.call('alice','state')[1]['mine'])
    def test_rate_level_and_decline(self):
        cid=self.create(rate=50,level=1)
        self.assertEqual(self.call('alice','apply',clan=cid)[0],409)
        with s.database() as db:s.sql(db,'UPDATE players SET wins=3,losses=1,draws=2 WHERE id=?',('alice',))
        self.assertEqual(self.call('alice','apply',clan=cid)[0],200)
        r=self.call('owner','state')[1]['requests'][0]
        self.assertEqual(r['profile']['rate'],50)
        self.assertEqual(self.call('owner','respond',id=r['id'],accept=False)[0],200)
        self.assertEqual(self.call('alice','apply',clan=cid)[0],409)
        self.assertEqual(self.call('owner','edit',requirements={'rate':101})[0],400)
        self.assertEqual(self.call('owner','edit',requirements={'losses':10,'max_losses':2})[0],400)
    def test_social_endpoint_and_notices(self):
        # Valid account session token, no client-supplied identity.
        with s.database() as db:
            token=s.new_account_session(db,'owner')
        code,d=s.social_action('/api/social/clans/create',dict(profileToken=token,name='Ordem Real',tag='REAL'),time.monotonic())
        self.assertEqual(code,200,d)
        cid=d['mine']['id']
        self.assertEqual(self.call('alice','apply',clan=cid)[0],200)
        code,d=s.social_action('/api/social/state',dict(profileToken=token),time.monotonic())
        self.assertEqual(code,200)
        self.assertEqual(len(d['clan_requests']),1)
        self.assertEqual(d['me']['level'],1)
        self.assertEqual(s.social_action('/api/social/clans/state',dict(profileToken='invalid'),time.monotonic())[0],400)
if __name__=='__main__':unittest.main()
