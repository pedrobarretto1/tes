from pathlib import Path
from tempfile import TemporaryDirectory
from io import BytesIO
from unittest.mock import patch
import json

def run(s):
    old=(s.BASE,s.DATABASE_URL,s.ROOMS,s.PRESENCE,s.INVITES,s.MATCH_QUEUE,s.LOGIN_LIMITS,s.SPECTATORS,s.TOURNAMENTS)
    with TemporaryDirectory() as tmp:
        try:
            s.BASE=Path(tmp);s.DATABASE_URL='';s.ROOMS={};s.PRESENCE={};s.INVITES={};s.MATCH_QUEUE={};s.LOGIN_LIMITS={};s.SPECTATORS={};s.TOURNAMENTS={}
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
            # Real HTTP handler regression: resignation then immediate exit,
            # winner can still fetch authoritative result, with points awarded once.
            for expected in (1,-1):
                orig=s.secrets.choice
                with patch.object(s.secrets,'choice',side_effect=lambda seq:expected if isinstance(seq,tuple) else orig(seq)):
                    host=http('/api/create',dict(a,rule='free'))
                guest=http('/api/join',dict(b,code=host['code']))
                ha={k:host[k] for k in ('code','side','token')}
                gb={k:guest[k] for k in ('code','side','token')}
                before_a=call('state',a)['me']['points'];before_b=call('state',b)['me']['points']
                result=http('/api/resign',gb)['result']
                assert result['winner']==expected and result['side']==-expected and result['ranked']
                assert result['deltas'][str(expected)]==25 and result['deltas'][str(-expected)]==-20
                http('/api/leave',gb)
                data=http('/api/poll',ha)
                assert data['closed'] and data['result']['winner']==expected and data['result']['side']==expected
                assert data['result']['points'][str(expected)]==before_a+25
                assert http('/api/poll',ha)['result']['match']==result['match']
                assert http('/api/resign',gb)['result']['match']==result['match']
                assert call('state',a)['me']['points']==before_a+25 and call('state',b)['me']['points']==before_b-20
            # Leaving directly must also produce the victory screen payload.
            host=http('/api/create',dict(a,rule='free'))
            guest=http('/api/join',dict(b,code=host['code']))
            ha={k:host[k] for k in ('code','side','token')};gb={k:guest[k] for k in ('code','side','token')}
            before_a=call('state',a)['me']['points'];before_b=call('state',b)['me']['points']
            http('/api/leave',gb)
            result=http('/api/poll',ha)['result']
            assert result['winner']==ha['side'] and result['reason']=='resign'
            assert call('state',a)['me']['points']==before_a+25 and call('state',b)['me']['points']==before_b-20
            # Casual results use the same reliable delivery without affecting PH.
            host=http('/api/create',dict(a,rule='free',ranked=False))
            guest=http('/api/join',dict(b,code=host['code']))
            ha={k:host[k] for k in ('code','side','token')};gb={k:guest[k] for k in ('code','side','token')}
            before_a=call('state',a)['me']['points'];before_b=call('state',b)['me']['points']
            http('/api/resign',ha);http('/api/leave',ha)
            result=http('/api/poll',gb)['result']
            assert result['winner']==gb['side'] and not result['ranked']
            assert call('state',a)['me']['points']==before_a and call('state',b)['me']['points']==before_b
            # Matchmaking: two compatible players, opposite colors, same room.
            s.ROOMS[host['code']]['closed']=True
            s.MATCH_QUEUE.clear()
            queued=call('matchmaking/start',a,rule='free',ranked=True,minutes=5)
            assert queued['matchmaking'] and not queued['session']
            status,found=s.social_action('/api/social/matchmaking/start',dict(b,rule='free',ranked=True,minutes=5),1011)
            assert status==200
            other=call('state',a)['session'];match=found['session']
            assert other['code']==match['code'] and other['side']==-match['side']
            room=s.ROOMS[match['code']]
            # Switch from the synthetic matchmaking clock to the real HTTP clock.
            room['last']=s.time.monotonic();room['seen']={1:room['last'],-1:room['last']}
            assert room['minutes']==5 and not s.MATCH_QUEUE
            aa={k:other[k] for k in ('code','side','token')}
            bb={k:match[k] for k in ('code','side','token')}
            # Snapshot recovery on refresh includes board, side, moves and clocks.
            data=http('/api/poll',aa);assert data['snapshot']['minutes']==5
            seat=aa if aa['side']==1 else bb
            move=s.legal(room['board'],1,room['rule'])[0]
            http('/api/send',dict(seat,message=json.dumps({'type':'move','sequence':1,'before':s.boardkey(room),'move':move})))
            resumed=call('state',a)['session'];assert resumed['token']==aa['token']
            snap=http('/api/poll',aa)['snapshot'];assert snap['sequence']==1 and snap['board']==room['board'] and len(snap['moves'])==1
            before_a=call('state',a)['me']['points'];before_b=call('state',b)['me']['points']
            http('/api/send',dict(aa,message=json.dumps({'type':'draw-offer'})))
            assert http('/api/poll',bb)['snapshot']['drawOffer']==aa['side']
            http('/api/send',dict(bb,message=json.dumps({'type':'draw-accept'})))
            result=http('/api/poll',aa)['result']
            assert result['winner']==0 and result['reason']=='agreement' and len(result['moves'])==1
            assert call('state',a)['me']['points']==before_a+5 and call('state',b)['me']['points']==before_b+5
            assert call('replay',a,match=result['match'])['replay']['moves']==result['moves']
            room['closed']=True
            # Timeout uses server time, awards a normal loss, no resignation penalty.
            host=http('/api/create',dict(a,rule='free',minutes=3))
            guest=http('/api/join',dict(b,code=host['code']))
            room=s.ROOMS[host['code']]
            s.tick_clock(room,1000);s.tick_clock(room,1181)
            assert room['winner']==-1 and room['result']['reason']=='timeout'
            assert room['result']['deltas']['1']==-15 and room['result']['deltas']['-1']==25
            room['closed']=True
            call('matchmaking/start',a,rule='official',minutes=0)
            assert not call('matchmaking/cancel',a)['matchmaking']
            # Variant-specific movement and results.
            board=[0]*64;board[42]=1;board[49]=-1
            assert any(m['cap']==[49] for m in s.legal(board,1,'free'))
            assert all(not m['cap'] for m in s.legal(board,1,'english'))
            board=[0]*64;board[35]=2
            assert max(abs(m['path'][0]//8-4) for m in s.legal(board,1,'english'))==1
            assert max(abs(m['path'][0]//8-4) for m in s.legal(board,1,'official'))>1
            board=[0]*64;board[42]=1;board[33]=board[35]=board[19]=-1
            assert {len(m['cap']) for m in s.legal(board,1,'mandatory')}=={1,2}
            assert {len(m['cap']) for m in s.legal(board,1,'official')}=={2}
            assert {len(m['cap']) for m in s.legal(board,1,'english')}=={1,2}
            board=[0]*64;board[17]=1;board[10]=board[12]=-1
            assert s.legal(board,1,'english')==[{'from':17,'path':[3],'cap':[10]}]
            for variant in ('english','mandatory','giveaway'):
                host=http('/api/create',dict(a,rule=variant,ranked=False))
                guest=http('/api/join',dict(b,code=host['code']))
                room=s.ROOMS[host['code']];assert room['rule']==variant
                if variant=='giveaway':
                    room['board']=[0]*64;room['board'][42]=1;room['board'][35]=-1
                    m=s.legal(room['board'],1,variant)[0]
                    assert s.process(room,1,{'type':'move','sequence':1,'before':s.boardkey(room),'move':m})
                    assert room['winner']==-1 and room['result']['reason']=='giveaway'
                room['closed']=True
            # School, rewards, custom and larger boards.
            for rule,n,count in [('international',10,20),('canadian',12,30),('kings',8,12),('custom-1010',8,12)]:
                board=s.initial_for(rule)
                assert len(board)==n*n and sum(p>0 for p in board)==count
                assert s.legal(board,1,rule)
                host=http('/api/create',dict(a,rule=rule,ranked=True,minutes=1,public=True))
                guest=http('/api/join',dict(b,code=host['code']))
                room=s.ROOMS[host['code']]
                assert not room['ranked'] and room['minutes']==1 and len(room['board'])==n*n
                aa={k:host[k] for k in ('code','side','token')};bb={k:guest[k] for k in ('code','side','token')}
                seat=aa if aa['side']==1 else bb
                m=s.legal(room['board'],1,rule)[0]
                http('/api/send',dict(seat,message=json.dumps({'type':'move','sequence':1,'before':s.boardkey(room),'move':m})))
                assert len(http('/api/poll',aa)['snapshot']['board'])==n*n
                http('/api/send',dict(aa,message=json.dumps({'type':'chat','text':'Boa partida!'})))
                assert http('/api/poll',bb)['snapshot']['chat'][0]['text']=='Boa partida!'
                watch=call('live/watch',c,code=host['code'])
                assert len(watch['board'])==n*n and 'token' not in watch and 'chat' not in watch
                room['closed']=True
            assert not s.valid_rule('custom-0111')
            for p in s.PUZZLES:
                moves=s.legal(s.puzzle_board(p),1,'official')
                assert moves and all(m['cap'] for m in moves)
                reward=call('school/solve',a,puzzle=p['id'],move=moves[0])
                assert reward['reward']>=p['reward']
                assert call('school/solve',a,puzzle=p['id'],move=moves[0])['reward']==0
            wallet=call('school/state',a)
            assert len(wallet['solved'])==5 and wallet['coins']>=100
            bought=call('school/buy',a,item='imperial')
            assert bought['theme']=='imperial' and 'imperial' in bought['owned'] and bought['coins']==wallet['coins']-100
            assert call('school/equip',a,item='classic')['theme']=='classic'
            # 8-player cup: simulate seven confirmed wins, verify champion once.
            now=s.time.monotonic()
            competitors=[{'name':'Copa '+str(i),'profileToken':('cup'+str(i))*16} for i in range(8)]
            def event(route,who,**kw):
                status,d=s.social_action('/api/social/'+route,dict(who,**kw),now)
                assert status==200,(route,status,d)
                return d
            for who in competitors:event('register',who)
            created=event('events/create',competitors[0],kind='cup')
            eid=created['events'][-1]['id']
            for who in competitors[1:]:event('events/join',who,event=eid)
            e=s.TOURNAMENTS[eid];assert e['status']=='playing' and len(e['pairs'])==4
            for expected in (4,2,1):
                assert len(e['pairs'])==expected
                for pair in e['pairs']:
                    room=s.ROOMS[pair['code']]
                    s.finish(room,1)
                s.event_tick(e,now)
            assert e['status']=='finished' and e['champion'] in e['players']
            with s.database() as db:
                assert s.sql(db,'SELECT COUNT(*) FROM event_champions WHERE event_id=?',(eid,)).fetchone()[0]==1
                assert s.wallet_state(db,e['champion'])['coins']==100
            # King of the table: winner remains, loser joins the end of queue.
            created=event('events/create',competitors[0],kind='king')
            kid=created['events'][-1]['id']
            event('events/join',competitors[1],event=kid);event('events/join',competitors[2],event=kid)
            event('events/start',competitors[0],event=kid)
            e=s.TOURNAMENTS[kid];room=s.ROOMS[e['pairs'][0]['code']]
            s.finish(room,1);s.event_tick(e,now)
            assert e['round']==2 and e['king']==e['pairs'][0]['a'] and len(e['queue'])==1
            event('events/stop',competitors[0],event=kid)
            assert e['status']=='cancelled'
            # A guest keeps their identifier, points, history and friends after linking.
            call('friend/request',a,target=bid);call('friend/accept',b,target=aid)
            previous=call('state',a)
            linked=call('account/link',a,username='teste_a',password='teste-senha-123')
            auth=dict(name='Teste A',profileToken=linked['token'])
            assert s.identity(auth)==aid and s.identity(a) is None
            assert linked['state']['me']['points']==previous['me']['points']
            assert linked['state']['history']==previous['history']
            assert any(p['id']==bid and p['relation']=='friend' for p in linked['state']['players'])
            assert 'first_win' in linked['state']['me']['achievements']
            bad,_=s.social_action('/api/social/account/login',{'username':'teste_a','password':'senha-errada'},1000)
            assert bad==401
            login=call('account/login',b,username='teste_a',password='teste-senha-123')
            other_device=dict(name='Teste A',profileToken=login['token'])
            assert s.identity(other_device)==aid and other_device['profileToken']!=auth['profileToken']
            assert call('state',other_device)['me']['points']==previous['me']['points']
            saved=call('customize',other_device,name='Guardiao A',avatar='knight',title='first_win',frame='bronze')
            assert saved['me']['avatar']=='knight' and saved['me']['title']=='first_win'
            public=call('player',b,target=aid)['player']
            assert public['name']=='Guardiao A' and public['avatar']=='knight' and 'account' not in public
            status,_=s.social_action('/api/social/customize',dict(other_device,name='Guardiao A',title='triple_king'),1000)
            assert status==403
            assert http('/api/profile',other_device)['points']==previous['me']['points']
            with s.database() as db:
                secret=s.sql(db,'SELECT salt,password_hash FROM accounts WHERE player_id=?',(aid,)).fetchone()
                assert secret[1]!='teste-senha-123' and len(secret[0])==32 and len(secret[1])==64
                for _ in range(5):s.award_progress(db,aid,'win',3)
            progress=call('state',other_device)['me']
            assert progress['bestStreak']>=5 and 'streak5' in progress['achievements'] and 'triple_king' in progress['achievements']
            call('account/logout',other_device)
            assert s.identity(other_device) is None and s.identity(auth)==aid
            print('SELFTEST OK: presence, friendship, removal, accent-insensitive offline search, public profile, invitations, four moves, ranked resignation, duplicate result, casual mode, both random colors, rematch color swap and correct points, friendship notices, unread counts, presence offline/online, resignation then exit, repeated result, direct leave, casual result, matchmaking, reconnect snapshot, draw agreement, replay, timeout, queue cancellation, five variants, reverse victory, larger boards, custom rooms, chat, spectators, puzzles, coins, themes, tournament, king table, account linking/login, identity preservation, password hash, profile cosmetics, achievements, logout',flush=True)
        finally:
            s.BASE,s.DATABASE_URL,s.ROOMS,s.PRESENCE,s.INVITES,s.MATCH_QUEUE,s.LOGIN_LIMITS,s.SPECTATORS,s.TOURNAMENTS=old
