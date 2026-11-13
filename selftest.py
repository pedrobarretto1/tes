from pathlib import Path
from tempfile import TemporaryDirectory

def run(s):
    old=(s.BASE,s.DATABASE_URL,s.ROOMS,s.PRESENCE,s.INVITES)
    with TemporaryDirectory() as tmp:
        try:
            s.BASE=Path(tmp);s.DATABASE_URL='';s.ROOMS={};s.PRESENCE={};s.INVITES={}
            s.setup()
            a={'name':'Teste A','profileToken':'a'*64};b={'name':'Teste B','profileToken':'b'*64}
            def call(path,who,**kw):
                status,d=s.social_action('/api/social/'+path,dict(who,**kw),1000)
                assert status==200,(path,status,d)
                return d
            call('register',a);call('register',b)
            aid=s.identity(a);bid=s.identity(b)
            d=call('state',a);assert d['players'][0]['id']==bid and d['players'][0]['online']
            call('friend/request',a,target=bid)
            assert call('state',b)['players'][0]['relation']=='incoming'
            call('friend/accept',b,target=aid)
            assert call('state',a)['players'][0]['relation']=='friend'
            call('friend/remove',a,target=bid)
            assert call('state',b)['players'][0]['relation']=='none'
            d=call('challenge',a,target=bid,ranked=True,rule='free')
            invite=d['challenges'][0]['id']
            d=call('challenge/respond',b,invite=invite,accept=True)
            other=call('state',a)['session']
            assert d['session']['code']==other['code'] and d['session']['side']==-1 and other['side']==1
            room=s.ROOMS[other['code']]
            for _ in range(4):
                side=room['turn'];move=s.legal(room['board'],side,room['rule'])[0]
                assert s.process(room,side,{'type':'move','sequence':room['sequence']+1,'before':s.boardkey(room),'move':move})
            assert s.process(room,-1,{'type':'resign'})
            assert call('state',a)['me']['points']==1025
            assert call('state',b)['me']['points']==980
            assert call('state',b)['history'][0]['outcome']=='resign'
            assert not s.process(room,-1,{'type':'resign'})
            room['closed']=True
            d=call('challenge',a,target=bid,ranked=False,rule='official')
            d=call('challenge/respond',b,invite=d['challenges'][0]['id'],accept=True)
            room=s.ROOMS[d['session']['code']]
            assert room['rule']=='official' and not room['ranked']
            s.process(room,1,{'type':'resign'})
            assert call('state',a)['me']['points']==1025 and call('state',b)['me']['points']==980
            print('SELFTEST OK: presence, friendship, removal, invitations, four moves, ranked resignation, duplicate result, casual mode',flush=True)
        finally:
            s.BASE,s.DATABASE_URL,s.ROOMS,s.PRESENCE,s.INVITES=old
