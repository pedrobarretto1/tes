from pathlib import Path
from tempfile import TemporaryDirectory
from io import BytesIO
from unittest.mock import patch
import json

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
            c={'name':'João da Silva','profileToken':'c'*64};call('register',c)
            cid=s.identity(c);s.PRESENCE.pop(cid)
            found=call('search',a,query='JOAO');assert found['total']==1 and found['players'][0]['id']==cid and not found['players'][0]['online']
            assert call('player',a,target=cid)['player']['points']==1000
            call('friend/request',a,target=cid);assert call('player',a,target=cid)['player']['relation']=='outgoing'
            call('friend/remove',a,target=cid)
            assert call('search',a,query='inexistente')['players']==[]
            aid=s.identity(a);bid=s.identity(b)
            d=call('state',a);assert d['players'][0]['id']==bid and d['players'][0]['online']
            call('friend/request',a,target=bid)
            assert call('state',b)['players'][0]['relation']=='incoming'
            assert call('state',b)['notifications'][0]['kind']=='friend_request'
            call('friend/accept',b,target=aid)
            assert call('state',a)['players'][0]['relation']=='friend'
            assert call('state',a)['notifications'][0]['kind']=='friend_accepted'
            call('friend/remove',a,target=bid)
            assert call('state',b)['players'][0]['relation']=='none'
            call('friend/request',a,target=bid)
            call('friend/decline',b,target=aid)
            a_notices=call('state',a)
            assert any(n['kind']=='friend_declined' for n in a_notices['notifications'])
            assert a_notices['unread']>=2
            assert call('notifications/read',a,all=True)['unread']==0
            assert call('state',b)['unread']>0
            call('friend/request',a,target=bid)
            call('friend/accept',b,target=aid)
            s.PRESENCE[bid]=960
            assert next(p for p in call('state',a)['players'] if p['id']==bid)['online']==False
            call('state',b)
            assert next(p for p in call('state',a)['players'] if p['id']==bid)['online']==True
            call('friend/remove',a,target=bid)
            d=call('challenge',a,target=bid,ranked=True,rule='free')
            invite=d['challenges'][0]['id']
            with patch.object(s.secrets,'choice',side_effect=lambda seq: seq[-1]):
                d=call('challenge/respond',b,invite=invite,accept=True)
            other=call('state',a)['session']; a_side=other['side']; b_side=d['session']['side']
            assert d['session']['code']==other['code'] and a_side==-1 and b_side==1
            assert other['host'] and not d['session']['host']
            room=s.ROOMS[other['code']]
            for _ in range(4):
                side=room['turn'];move=s.legal(room['board'],side,room['rule'])[0]
                assert s.process(room,side,{'type':'move','sequence':room['sequence']+1,'before':s.boardkey(room),'move':move})
            assert s.process(room,b_side,{'type':'resign'})
            assert call('state',a)['me']['points']==1025
            assert call('state',b)['me']['points']==980
            assert call('state',b)['history'][0]['outcome']=='resign'
            assert not s.process(room,b_side,{'type':'resign'})
            assert s.process(room,a_side,{'type':'rematch'})
            with patch.object(s.secrets,'choice',return_value=True):
                assert s.process(room,b_side,{'type':'rematch-ok'})
            assert json.loads(room['rematch_event'])=={'type':'rematch-start','swap':True}
            assert s.game_side(room,a_side)==1 and s.game_side(room,b_side)==-1
            assert room['winner'] is None and room['turn']==1
            move=s.legal(room['board'],1,room['rule'])[0]
            msg={'type':'move','sequence':1,'before':s.boardkey(room),'move':move}
            assert not s.process(room,b_side,msg)
            assert s.process(room,a_side,msg)
            assert s.process(room,b_side,{'type':'resign'})
            assert call('state',a)['me']['points']==1050 and call('state',b)['me']['points']==960
            room['closed']=True
            d=call('challenge',a,target=bid,ranked=False,rule='official')
            d=call('challenge/respond',b,invite=d['challenges'][0]['id'],accept=True)
            room=s.ROOMS[d['session']['code']]
            assert room['rule']=='official' and not room['ranked']
            s.process(room,1,{'type':'resign'})
            assert call('state',a)['me']['points']==1050 and call('state',b)['me']['points']==960
            room['closed']=True
            def http(path,body):
                handler=object.__new__(s.Handler); payload=json.dumps(body).encode()
                handler.path=path;handler.headers={'Content-Length':str(len(payload))};handler.rfile=BytesIO(payload)
                out=[];handler.reply=lambda status,data,*args:out.extend([status,data])
                handler.do_POST();assert out[0]==200,out
                return out[1]
            for expected in (1,-1):
                orig=s.secrets.choice
                with patch.object(s.secrets,'choice',side_effect=lambda seq:expected if isinstance(seq,tuple) else orig(seq)):
                    host=http('/api/create',dict(a,rule='free'))
                guest=http('/api/join',dict(b,code=host['code']))
                assert host['side']==expected and guest['side']==-expected
                assert s.ROOMS[host['code']]['host']==expected
                s.ROOMS[host['code']]['closed']=True
            print('SELFTEST OK: presence, friendship, removal, accent-insensitive offline search, public profile, invitations, four moves, ranked resignation, duplicate result, casual mode, both random colors, rematch color swap and correct points, friendship notices, unread counts, presence offline/online',flush=True)
        finally:
            s.BASE,s.DATABASE_URL,s.ROOMS,s.PRESENCE,s.INVITES=old
