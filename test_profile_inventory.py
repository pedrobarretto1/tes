"""Inventario do perfil: itens reais, isolamento, equipar relíquias parcialmente adquiridas."""
import tempfile,time,unittest
from pathlib import Path
import servidor as s

class ProfileInventoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.old=s.BASE,s.DATABASE_URL
        s.BASE=Path(self.tmp.name);s.DATABASE_URL='';s.setup()
        self.tokens=('a'*64,'b'*64)
        self.pids=[s.profile(dict(name=n,profileToken=t)) for n,t in zip(('Inventario A','Inventario B'),self.tokens)]
    def tearDown(self):
        for pid in self.pids:
            s.PRESENCE.pop(pid,None);s.PRESENCE_GAME.pop(pid,None)
        s.BASE,s.DATABASE_URL=self.old;self.tmp.cleanup()
    def call(self,i,op,**d):
        return s.social_action('/api/social/profile/inventory/'+op,dict(profileToken=self.tokens[i],**d),time.monotonic())
    def test_reis_sem_tabuleiros_e_sem_recompensa_extra(self):
        with s.database() as db:
            for item in ('skin-relic-shadow','skin-relic-divine','skin-relic-infinite'):
                s.sql(db,'INSERT INTO purchases(player_id,item) VALUES(?,?)',(self.pids[0],item))
        code,a=self.call(0,'state');self.assertEqual(code,200)
        for item in ('skin-relic-shadow','skin-relic-divine','skin-relic-infinite'):
            self.assertIn(item,a['damas']['owned'])
        self.assertNotIn('relic-shadow',a['damas']['owned'])
        self.assertNotIn('skin-relic-shadow',self.call(1,'state')[1]['damas']['owned'])
        code,b=self.call(0,'equip',game='damas',item='skin-relic-shadow')
        self.assertEqual(code,200,b);self.assertEqual(b['damas']['skin'],'skin-relic-shadow')
        self.assertEqual(b['damas']['theme'],'classic')
        self.assertEqual(self.call(0,'equip',game='damas',item='relic-shadow')[0],403)
        self.assertEqual(self.call(1,'equip',game='damas',item='skin-relic-shadow')[0],403)
        self.assertEqual(self.call(0,'equip',game='damas',item='skin-relic-divine')[1]['damas']['skin'],'skin-relic-divine')
        self.assertEqual(self.call(0,'equip',game='damas',item='skin-relic-infinite')[1]['damas']['skin'],'skin-relic-infinite')
        with s.database() as db:
            self.assertEqual(s.sql(db,'SELECT COUNT(*) FROM journey WHERE player_id=?',(self.pids[0],)).fetchone()[0],0)
            self.assertEqual(s.sql(db,'SELECT COUNT(*) FROM purchases WHERE player_id=?',(self.pids[0],)).fetchone()[0],3)
            self.assertEqual(s.sql(db,'SELECT coins FROM wallets WHERE player_id=?',(self.pids[0],)).fetchone()[0],0)
    def test_completos_tres_reis_sem_conquista_de_jornada(self):
        with s.database() as db:
            for path in ('shadow','divine','infinite'):
                for item in ('relic-'+path,'skin-relic-'+path):
                    s.sql(db,'INSERT INTO purchases(player_id,item) VALUES(?,?)',(self.pids[0],item))
        code,inventory=self.call(0,'state')
        self.assertEqual(code,200)
        for path in ('shadow','divine','infinite'):
            self.assertIn('relic-'+path,inventory['damas']['owned'])
            self.assertIn('skin-relic-'+path,inventory['damas']['owned'])
            code,eq=self.call(0,'equip',game='damas',item='king-set-'+path)
            self.assertEqual(code,200,eq)
            self.assertEqual(eq['damas']['theme'],'relic-'+path)
            self.assertEqual(eq['damas']['skin'],'skin-relic-'+path)
        self.assertEqual(self.call(1,'equip',game='damas',item='king-set-shadow')[0],403)
        self.assertEqual(self.call(0,'equip',game='damas',item='king-set-invalid')[0],400)
        with s.database() as db:
            self.assertEqual(s.sql(db,'SELECT COUNT(*) FROM journey WHERE player_id=?',(self.pids[0],)).fetchone()[0],0)
            self.assertEqual(s.sql(db,'SELECT COUNT(*) FROM purchases WHERE player_id=?',(self.pids[0],)).fetchone()[0],6)
            self.assertEqual(s.sql(db,'SELECT coins FROM wallets WHERE player_id=?',(self.pids[0],)).fetchone()[0],0)

    def test_xadrez_independente_e_presenca_inalterada(self):
        import chess_shop
        with s.database() as db:
            s.sql(db,'INSERT INTO chess_shop_owned VALUES(?,?,?)',(self.pids[0],'pieces-imperial',time.time()))
        s.PRESENCE_GAME[self.pids[0]]=('damas',True)
        code,state=self.call(0,'state');self.assertEqual(code,200)
        self.assertEqual(s.PRESENCE_GAME[self.pids[0]],('damas',True))
        self.assertIn('pieces-imperial',state['chess']['shop']['owned'])
        self.assertNotIn('pieces-imperial',self.call(1,'state')[1]['chess']['shop']['owned'])
        code,out=self.call(0,'equip',game='chess',item='pieces-imperial')
        self.assertEqual(code,200,out)
        self.assertEqual(out['chess']['shop']['equipped']['pieces'],'pieces-imperial')
        self.assertEqual(out['damas']['skin'],'skin-classic')
        self.assertEqual(s.PRESENCE_GAME[self.pids[0]],('damas',True))
        self.assertEqual(self.call(1,'equip',game='chess',item='pieces-imperial')[0],403)
        self.assertEqual(self.call(0,'equip',game='chess',item='board-obsidian')[0],403)
        self.assertEqual(self.call(0,'equip',game='bad',item='pieces-imperial')[0],400)

if __name__=='__main__':unittest.main()
