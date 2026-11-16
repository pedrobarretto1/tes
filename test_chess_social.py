import tempfile,unittest,time
from pathlib import Path
import servidor as s

class ChessSocialTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.old=s.BASE,s.DATABASE_URL
        s.BASE=Path(self.tmp.name);s.DATABASE_URL='';s.setup()
        self.a='a'*64;self.b='b'*64;self.now=time.monotonic()
        self.pa=s.profile(dict(name='Alice',profileToken=self.a));self.pb=s.profile(dict(name='Bob',profileToken=self.b))
        with s.database() as db:
            s.sql(db,"INSERT INTO friendships VALUES(?,?,'accepted')",(self.pa,self.pb))
            s.sql(db,'UPDATE players SET points=2345,wins=13 WHERE id=?',(self.pa,))
    def tearDown(self):
        for p in (self.pa,self.pb):
            s.PRESENCE.pop(p,None);s.PRESENCE_GAME.pop(p,None)
        s.BASE,s.DATABASE_URL=self.old;self.tmp.cleanup()
    def call(self,token,path,**d):
        return s.social_action('/api/social/'+path,dict(profileToken=token,**d),self.now)
    def test_shared_friends_and_separate_context(self):
        self.call(self.b,'state')
        code,data=self.call(self.a,'chess/state',busy=True)
        self.assertEqual(code,200);self.assertEqual(data['me'],{'name':'Alice','avatar':'crown','frame':'wood','account':None,'clan':None})
        self.assertEqual(data['friends'][0]['game'],'damas')
        self.assertEqual(data['friends'][0]['relation'],'friend')
        self.assertNotIn('points',data['me']);self.assertNotIn('clan',data)
        d=self.call(self.b,'state')[1]
        p=next(p for p in d['players'] if p['id']==self.pa)
        self.assertEqual(p['game'],'chess');self.assertTrue(p['busy'])
        self.assertEqual(self.call(self.b,'challenge',target=self.pa,rule='official')[0],409)
        self.call(self.a,'chess/state',busy=False)
        d=self.call(self.b,'state')[1];p=next(p for p in d['players'] if p['id']==self.pa)
        self.assertFalse(p['busy'])
        self.assertEqual(self.call(self.b,'challenge',target=self.pa,rule='official')[0],200)
        d=self.call(self.a,'chess/state')[1]
        self.assertEqual(d['invites'][0]['game'],'damas')
        d=self.call(self.a,'state')[1];self.assertEqual(d['me']['points'],2345);self.assertEqual(d['me']['wins'],13)
        self.assertEqual(s.PRESENCE_GAME[self.pa][0],'damas')
    def test_profile_details_and_shared_edit(self):
        code,d=self.call(self.a,'chess/profile-details');self.assertEqual(code,200)
        self.assertEqual(d['completed'],0);self.assertEqual(d['bestStreak'],0)
        self.assertEqual(d['level'],1)
        self.assertFalse(next(f for f in d['frames'] if f['id']=='gold')['locked'])
        self.assertTrue(next(f for f in d['frames'] if f['id']=='halloween')['locked'])
        self.assertEqual(self.call(self.a,'customize',name='Alice Real',avatar='knight',frame='gold')[0],200)
        d=self.call(self.a,'chess/state')[1];self.assertEqual(d['me']['name'],'Alice Real');self.assertEqual(d['me']['avatar'],'knight');self.assertEqual(d['me']['frame'],'gold');self.assertEqual(d['profile']['points'],1000)
        self.assertEqual(self.call(self.a,'state')[1]['me']['points'],2345)
        self.assertEqual(self.call('x'*64,'chess/profile-details')[0],403)
    def test_unauthenticated(self):
        self.assertEqual(self.call('x'*64,'chess/state')[0],403)
if __name__=='__main__':unittest.main()
