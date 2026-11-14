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
    def test_crest_persistence_permissions_and_legacy(self):
        design=dict(symbol='knight',symbol_color='violet',frame_style='ornate',frame_color='silver',background_color='wine')
        code,d=self.call('owner','create',name='Chama Eterna',tag='CE',crest=design,requirements={'points':1000})
        self.assertEqual(code,200,d)
        cid=d['mine']['id']
        self.assertEqual(d['mine']['crest'],design)
        self.assertEqual(d['mine']['emblem'],'knight')
        self.assertEqual(self.call('alice','state')[1]['clans'][0]['crest'],design)
        self.assertEqual(self.call('alice','apply',clan=cid)[0],200)
        self.assertEqual(self.call('owner','state')[1]['requests'][0]['crest'],design)
        same=dict(symbol='moon',symbol_color='gold',frame_style='dark',frame_color='gold',background_color='gold')
        self.assertEqual(self.call('alice','crest',crest=same)[0],409)
        r=self.call('owner','state')[1]['requests'][0]
        self.assertEqual(self.call('owner','respond',id=r['id'],accept=True)[0],200)
        self.assertEqual(self.call('alice','crest',crest=same)[0],403)
        self.assertEqual(self.call('owner','crest',crest={**same,'frame_style':'bad'})[0],400)
        self.assertEqual(self.call('owner','crest',crest=same)[0],200)
        self.assertEqual(self.call('owner','state')[1]['mine']['crest'],same)
        self.assertEqual(self.call('alice','state')[1]['mine']['crest'],same)
        self.assertEqual(self.call('owner','state')[1]['mine']['requirements']['points'],1000)
        with s.database() as db:
            s.sql(db,'DELETE FROM clan_crests WHERE clan_id=?',(cid,))
        self.assertEqual(self.call('owner','state')[1]['mine']['crest'],clas.default_crest('moon'))
        self.assertEqual(self.call('owner','crest',crest=design)[0],200)
        self.assertEqual(self.call('owner','kick',target='alice')[0],200)
        self.assertEqual(self.call('owner','dissolve')[0],200)
        with s.database() as db:
            self.assertIsNone(s.sql(db,'SELECT 1 FROM clan_crests WHERE clan_id=?',(cid,)).fetchone())
    def test_jerusalem_crest(self):
        design=dict(symbol='jerusalem',symbol_color='crimson',frame_style='sacred',frame_color='gold',background_color='ivory')
        code,d=self.call('owner','create',name='Ordem Real',tag='REAL',crest=design)
        self.assertEqual(code,200,d)
        self.assertEqual(d['mine']['crest'],design)
        self.assertEqual(d['mine']['emblem'],'jerusalem')
        self.assertEqual(self.call('alice','state')[1]['clans'][0]['crest'],design)
        changed={**design,'symbol_color':'obsidian','frame_style':'dark'}
        self.assertEqual(self.call('owner','crest',crest=changed)[0],200)
        self.assertEqual(self.call('owner','state')[1]['mine']['crest'],changed)
    def admit(self,cid,p):
        self.assertEqual(self.call(p,'apply',clan=cid)[0],200)
        r=next(r for r in self.call('owner','state')[1]['requests'] if r['profile']['id']==p)
        self.assertEqual(self.call('owner','respond',id=r['id'],accept=True)[0],200)
    def test_royal_hierarchy_and_reports(self):
        cid=self.create()
        for p in ('alice','bob','other'):self.admit(cid,p)
        self.assertEqual(self.call('owner','promote',target='alice',role='captain')[0],200)
        self.assertEqual(self.call('owner','promote',target='bob',role='vice')[0],200)
        self.assertEqual(self.call('alice','promote',target='other',role='vice')[0],403)
        self.assertEqual(self.call('alice','kick',target='other')[0],403)
        self.assertEqual(self.call('bob','kick',target='other')[0],403)
        self.assertEqual(self.call('alice','edit',requirements={})[0],403)
        self.assertEqual(self.call('bob','edit',requirements={'points':1000})[0],200)
        design=clas.default_crest('jerusalem')
        self.assertEqual(self.call('bob','crest',crest=design)[0],200)
        self.assertEqual(self.call('other','report',target='alice',reason='test')[0],403)
        self.assertEqual(self.call('alice','report',target='bob',reason='test')[0],403)
        self.assertEqual(self.call('alice','report',target='other',reason='Abuso no chat')[0],200)
        r=self.call('owner','state')[1]['mine']['reports'][0];rid=r['id']
        self.assertEqual(r['status'],'open')
        self.assertNotIn('reports',self.call('other','state')[1]['mine'])
        self.assertEqual(self.call('alice','report-decide',id=rid,decision='expel')[0],403)
        self.assertEqual(self.call('owner','report-return',id=rid,message='Explique melhor')[0],200)
        self.assertEqual(self.call('alice','report-reply',id=rid,message='Não autorizado')[0],403)
        self.assertEqual(self.call('bob','report-reply',id=rid,message='Mais detalhes')[0],200)
        r=self.call('owner','state')[1]['mine']['reports'][0]
        self.assertEqual([h['kind'] for h in r['history']],['report','return','reply'])
        self.assertEqual(self.call('owner','report-decide',id=rid,decision='suspend',duration=0,unit='days')[0],400)
        self.assertEqual(self.call('owner','report-decide',id=rid,decision='suspend',duration=2,unit='days',message='Penalidade')[0],200)
        d=self.call('other','state')[1]
        self.assertGreater(d['mine']['penalty']['until'],time.time()+170000)
        self.assertEqual(d['decisions'][0]['note'],'Penalidade')
        self.assertEqual(d['decisions'][0]['until'],d['mine']['penalty']['until'])
        self.assertEqual(self.call('owner','report-decide',id=rid,decision='expel')[0],409)
        with s.database() as db:
            self.assertIsNone(clas.tournament_block(db,s.sql,cid,'other',time.time()+173000))
            kinds=[x[0] for x in s.sql(db,'SELECT kind FROM notifications WHERE recipient=?',('owner',)).fetchall()]
            self.assertIn('clan_report',kinds);self.assertIn('clan_report_reply',kinds)
            self.assertIn('clan_report_return',[x[0] for x in s.sql(db,'SELECT kind FROM notifications WHERE recipient=?',('bob',)).fetchall()])
        self.assertEqual(self.call('owner','promote',target='bob',role='member')[0],200)
        self.assertEqual(self.call('bob','crest',crest=design)[0],403)
        self.assertEqual(self.call('owner','report',target='other',reason='Outro incidente')[0],200)
        rid=next(r['id'] for r in self.call('owner','state')[1]['mine']['reports'] if r['status']=='open')
        self.assertEqual(self.call('owner','report-decide',id=rid,decision='expel',message='Motivo da saída')[0],200)
        d=self.call('other','state')[1];self.assertIsNone(d['mine'])
        self.assertEqual(d['decisions'][0]['decision'],'expel')
        self.assertEqual(self.call('owner','transfer',target='alice')[0],200)
        self.assertEqual(self.call('owner','state')[1]['mine']['role'],'member')
        self.assertEqual(self.call('alice','state')[1]['mine']['role'],'king')
    def test_report_fallback_and_reopen(self):
        cid=self.create()
        for p in ('alice','bob'):self.admit(cid,p)
        self.call('owner','promote',target='alice',role='captain')
        self.call('alice','report',target='bob',reason='Motivo')
        rid=self.call('owner','state')[1]['mine']['reports'][0]['id']
        self.assertEqual(self.call('owner','report-return',id=rid,message='Detalhe')[0],200)
        self.assertEqual(self.call('alice','report-reply',id=rid,message='Detalhes')[0],200)
        self.assertEqual(self.call('owner','report-return',id=rid,message='Outra dúvida')[0],200)
        self.assertEqual(self.call('owner','promote',target='alice',role='member')[0],200)
        self.assertEqual(self.call('alice','report-reply',id=rid,message='Não pode')[0],403)
        self.assertEqual(self.call('owner','report-reopen',id=rid,message='Retomada')[0],200)
        self.assertEqual(self.call('owner','report-decide',id=rid,decision='keep')[0],200)
        self.assertEqual(self.call('bob','state')[1]['decisions'][0]['decision'],'keep')
    def test_royal_invite_bypasses_only_requirements(self):
        cid=self.create(points=2000,wins=50,rate=80,level=10)
        self.assertEqual(self.call('alice','apply',clan=cid)[0],409)
        self.assertEqual(self.call('owner','invite',target='guest')[0],400)
        self.assertEqual(self.call('owner','invite',target='alice')[0],200)
        r=self.call('alice','state')[1]['requests'][0]
        self.assertTrue(r['royal'])
        self.assertTrue(any(not c['ok'] for c in r['checks']))
        self.assertEqual(self.call('bob','respond',id=r['id'],accept=True)[0],403)
        self.assertEqual(self.call('alice','respond',id=r['id'],accept=True)[0],200)
        self.assertEqual(self.call('alice','state')[1]['mine']['role'],'member')
        self.assertEqual(self.call('owner','promote',target='alice',role='vice')[0],200)
        self.assertEqual(self.call('alice','invite',target='bob')[0],403)
        self.assertEqual(self.call('owner','invite',target='bob')[0],200)
        r=self.call('bob','state')[1]['requests'][0]
        self.assertEqual(self.call('bob','respond',id=r['id'],accept=False)[0],200)
        self.assertIsNone(self.call('bob','state')[1]['mine'])
        self.assertEqual(self.call('other','apply',clan=cid)[0],409)
        self.assertEqual(self.call('owner','invite',target='other')[0],200)
        r=self.call('other','state')[1]['requests'][0]
        from unittest.mock import patch
        with patch.object(clas,'LIMIT',2):
            self.assertEqual(self.call('other','respond',id=r['id'],accept=True)[0],409)
        self.assertEqual(self.call('other','respond',id=r['id'],accept=True)[0],200)
    def test_role_identity_and_chat_refresh(self):
        cid=self.create()
        self.admit(cid,'alice')
        self.call('alice','send',body='Olá')
        self.assertEqual(self.call('owner','chat')[1]['messages'][0]['role'],'member')
        self.call('owner','promote',target='alice',role='captain')
        self.assertEqual(self.call('owner','chat')[1]['messages'][0]['role'],'captain')
        with s.database() as db:
            self.assertEqual(clas.public_identity(db,s.sql,'alice')['role'],'captain')
            self.assertEqual(clas.public_identity(db,s.sql,'owner')['role'],'king')
            self.assertIsNone(clas.public_identity(db,s.sql,'bob'))
        code,data=s.social_lookup('/api/social/player',{'target':'alice'},'owner',time.monotonic())
        self.assertEqual(code,200)
        self.assertEqual(data['player']['clan']['role'],'captain')
        self.assertEqual(s.social_state('alice',time.monotonic())['me']['clan']['tag'],'REAL')
        self.call('owner','kick',target='alice')
        self.assertIsNone(self.call('owner','chat')[1]['messages'][0]['role'])
        with s.database() as db:self.assertIsNone(clas.public_identity(db,s.sql,'alice'))
    def test_recommendations_private_and_royal_decision(self):
        cid=self.create()
        for p in ('alice','bob'):self.admit(cid,p)
        self.call('owner','promote',target='alice',role='captain')
        self.call('owner','promote',target='bob',role='vice')
        self.call('owner','edit',requirements={'points':2000,'wins':30})
        self.assertEqual(self.call('bob','recommend',target='other')[0],200)
        self.assertEqual(self.call('alice','recommend',target='other')[0],409)
        self.assertNotIn('recommendations',self.call('bob','state')[1]['mine'])
        self.assertIsNone(self.call('other','state')[1]['mine'])
        self.assertEqual(self.call('other','state')[1]['requests'],[])
        r=self.call('alice','state')[1]['mine']['recommendations'][0]
        self.assertEqual(r['profile']['id'],'other')
        self.assertTrue(any(not c['ok'] for c in r['checks']))
        self.assertEqual(self.call('bob','recommend-review',id=r['id'],opinion='support')[0],403)
        self.assertEqual(self.call('alice','recommend-decide',id=r['id'],accept=True)[0],403)
        self.assertEqual(self.call('alice','invite',target='other')[0],403)
        self.assertEqual(self.call('alice','recommend-review',id=r['id'],opinion='support')[0],200)
        # A favorable opinion is not an invitation, admission, or approval.
        self.assertEqual(self.call('other','state')[1]['requests'],[])
        self.assertIsNone(self.call('other','state')[1]['mine'])
        self.assertEqual(self.call('alice','recommend-decide',id=r['id'],accept=True)[0],403)
        self.assertEqual(self.call('alice','invite',target='other')[0],403)
        rr=self.call('owner','state')[1]['mine']['recommendations'][0]
        self.assertEqual(rr['opinion'],'support')
        with s.database() as db:
            recipients=[x[0] for x in s.sql(db,"SELECT recipient FROM notifications WHERE kind='clan_recommend'").fetchall()]
            self.assertEqual(set(recipients),{'owner','alice'})
        self.assertEqual(self.call('owner','recommend-decide',id=r['id'],accept=True)[0],200)
        self.assertEqual(self.call('owner','recommend-decide',id=r['id'],accept=True)[0],409)
        request=self.call('other','state')[1]['requests'][0]
        self.assertTrue(request['royal'])
        self.assertEqual(self.call('other','respond',id=request['id'],accept=True)[0],200)
        self.assertEqual(self.call('other','state')[1]['mine']['role'],'member')
        self.assertEqual(self.call('other','recommend',target='guest')[0],400)
        self.call('owner','kick',target='other')
        self.assertEqual(self.call('alice','recommend',target='other')[0],200)
        rid=self.call('owner','state')[1]['mine']['recommendations'][0]['id']
        self.assertEqual(self.call('alice','recommend-review',id=rid,opinion='support')[0],403)
        self.assertEqual(self.call('owner','recommend-decide',id=rid,accept=False)[0],200)
        self.assertEqual(self.call('other','state')[1]['requests'],[])
if __name__=='__main__':unittest.main()
