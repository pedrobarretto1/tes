from pathlib import Path
from tempfile import TemporaryDirectory
from io import BytesIO
from unittest.mock import patch
import json

def run(s):
    old=(s.BASE,s.DATABASE_URL,s.ROOMS,s.PRESENCE,s.INVITES,s.MATCH_QUEUE,s.LOGIN_LIMITS,s.SPECTATORS,s.TOURNAMENTS,s.LOCAL_LIVE)
    with TemporaryDirectory() as tmp:
        try:
            s.BASE=Path(tmp);s.DATABASE_URL='';s.ROOMS={};s.PRESENCE={};s.INVITES={};s.MATCH_QUEUE={};s.LOGIN_LIMITS={};s.SPECTATORS={};s.TOURNAMENTS={};s.LOCAL_LIVE={}
            s.setup()
            a={'name':'Teste A','profileToken':'a'*64};b={'name':'Teste B','profileToken':'b'*64}
            def call(route,who,**kw):
                status,d=s.social_action('/api/social/'+route,dict(who,**kw),1000)
                assert status==200,(route,status,d)
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
            d=call('challenge',a,target=bid,ranked=False,rule='free')
            invite=d['challenges'][0]['id']
            assert s.social_action('/api/social/challenge/respond',dict(a,invite=invite,accept=True,rule='official'),1000)[0]==409
            assert s.social_action('/api/social/challenge/respond',dict(b,invite=invite,accept=True,rule='bogus'),1000)[0]==400
            d=call('challenge/respond',b,invite=invite,accept=True,rule='official')
            room=s.ROOMS[d['session']['code']]
            assert room['rule']=='official' and not room['ranked'] and len(room['board'])==64
            assert call('state',a)['session']['rule']=='official'
            assert s.social_action('/api/social/challenge/respond',dict(b,invite=invite,accept=True,rule='english'),1000)[0]==409
            s.process(room,1,{'type':'resign'})
            assert call('state',a)['me']['points']==1050 and call('state',b)['me']['points']==960
            room['closed']=True
            # Receiver can choose a larger board; casual-only rules cannot award PH.
            d=call('challenge',a,target=bid,ranked=True,rule='free')
            invite=d['challenges'][0]['id']
            d=call('challenge/respond',b,invite=invite,accept=True,rule='international')
            room=s.ROOMS[d['session']['code']]
            assert room['rule']=='international' and not room['ranked'] and len(room['board'])==100
            assert call('state',a)['session']['rule']=='international'
            room['closed']=True
            # A ranked eligible choice preserves the sender's ranked preference.
            d=call('challenge',a,target=bid,ranked=True,rule='canadian')
            d=call('challenge/respond',b,invite=d['challenges'][0]['id'],accept=True,rule='english')
            room=s.ROOMS[d['session']['code']]
            assert room['rule']=='english' and room['ranked'] and len(room['board'])==64
            room['closed']=True
            def http(path,body):
                handler=object.__new__(s.Handler); payload=json.dumps(body).encode()
                handler.path=path;handler.headers={'Content-Length':str(len(payload))};handler.rfile=BytesIO(payload)
                out=[];handler.reply=lambda status,data,*args:out.extend([status,data])
                with patch.object(s.time,'monotonic',return_value=1000.0):handler.do_POST()
                assert out[0]==200,out
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
            # Keep HTTP and social tests on the same deterministic clock.
            room['last']=1000.0;room['seen']={1:room['last'],-1:room['last']};room['clock_at']=room['last'];room['started']=room['last']
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
            # Explicit opt-in spectator streams from local, AI and campaign matches.
            broadcaster={'name':'Mestre Ao Vivo','profileToken':'e'*64};viewer={'name':'Observador','profileToken':'f'*64}
            call('register',broadcaster);call('register',viewer)
            broadcaster_id=s.identity(broadcaster)
            payload=dict(public=True,match='local-1',mode='ai',rule='official',board=s.initial_for('official'),side=1,turn=1,sequence=0,last=[],result=None)
            status,_=s.social_action('/api/social/live/publish',dict(broadcaster,**{**payload,'public':False}),1000);assert status==403
            status,_=s.social_action('/api/social/live/publish',dict(broadcaster,**{**payload,'board':[0]*63}),1000);assert status==400
            live=call('live/publish',broadcaster,**payload);code=live['code']
            assert any(p['id']==broadcaster_id and p['live']['code']==code for p in call('state',viewer)['players'])
            assert call('player',viewer,target=broadcaster_id)['player']['live']['mode']=='ai'
            watched=call('live/watch',viewer,target=broadcaster_id);assert watched['code']==code and watched['board']==payload['board'] and 'token' not in watched
            move=s.legal(payload['board'],1,'official')[0];payload.update(board=s.journey_apply(payload['board'],move),sequence=1,turn=-1,last=[move['from'],*move['path']])
            assert call('live/publish',broadcaster,**payload)['code']==code
            assert call('live/watch',viewer,code=code)['sequence']==1
            published=dict(move,sequence=1,side=1,promotion=False,private='never expose')
            payload['moves']=[published]
            assert call('live/publish',broadcaster,**payload)['code']==code
            watched=call('live/watch',viewer,code=code)
            assert watched['moves']==[dict(move,sequence=1,side=1,promotion=False)] and watched['matchId']==code
            status,_=s.social_action('/api/social/live/publish',dict(broadcaster,**{**payload,'moves':[dict(published,sequence=2)]}),1000);assert status==400
            assert s.live_moves([dict(published,**{'from':64})],8,1) is None
            assert s.live_moves([dict(published,sequence=1),dict(published,sequence=3)],8,3) is None
            payload['result']=1;call('live/publish',broadcaster,**payload)
            assert call('live/watch',viewer,code=code)['result']==1
            assert not any(r['code']==code for r in call('live/list',viewer)['rooms'])
            for mode in ('local','journey'):
                payload.update(mode=mode,match=mode,board=s.initial_for('official'),sequence=0,turn=1,last=[],moves=[],result=None)
                code=call('live/publish',broadcaster,**payload)['code']
                assert call('live/watch',viewer,code=code)['mode']==mode
            call('live/stop',broadcaster)
            status,_=s.social_action('/api/social/live/watch',dict(viewer,code=code),1000);assert status==404
            code=call('live/publish',broadcaster,**payload)['code']
            status,_=s.social_action('/api/social/live/watch',dict(viewer,code=code),1016);assert status==404
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
            # Independent cosmetic categories, safe ownership and persistent selection.
            with s.database() as db:
                s.wallet_add(db,s.identity(a),500)
            before=call('school/state',a)
            assert before['skin']=='skin-classic' and 'skin-classic' in before['owned']
            status,_=s.social_action('/api/social/school/equip',dict(a,item='skin-gilded'),1000)
            assert status==403
            bought=call('school/buy',a,item='skin-gilded')
            assert bought['skin']=='skin-gilded' and bought['theme']==before['theme'] and bought['coins']==before['coins']-100
            assert 'skin-gilded' in bought['owned'] and 'imperial' in bought['owned']
            chosen=call('school/buy',a,item='midnight')
            assert chosen['theme']=='midnight' and chosen['skin']=='skin-gilded'
            repeated=call('school/buy',a,item='skin-gilded')
            assert repeated['coins']==chosen['coins']
            restored=call('school/equip',a,item='skin-classic')
            assert restored['theme']=='midnight' and restored['skin']=='skin-classic'
            assert call('school/state',a)['theme']=='midnight'
            assert call('school/state',b)['skin']=='skin-classic'
            assert len(s.THEMES)==12 and len(s.SKINS)==10
            # Thematic collections: seasons, separate pieces/boards, full bundles and profile frames.
            assert s.seasonal_open(s.THEMATIC_COLLECTIONS['halloween'],'2026-11-13')
            assert s.seasonal_open(s.THEMATIC_COLLECTIONS['halloween'],'2027-10-01')
            assert not s.seasonal_open(s.THEMATIC_COLLECTIONS['halloween'],'2027-12-01')
            assert s.seasonal_open(s.THEMATIC_COLLECTIONS['christmas'],'2027-12-01')
            assert s.seasonal_open(s.THEMATIC_COLLECTIONS['romance'],'2027-06-12')
            assert s.seasonal_open(s.THEMATIC_COLLECTIONS['horror'],'2027-01-01')
            with s.database() as db:s.wallet_add(db,s.identity(a),1000)
            w=call('school/state',a)
            assert len(w['thematic'])==4
            with patch.object(s,'seasonal_open',return_value=True):
                board=call('school/buy',a,item='haunted-night')
                assert board['theme']=='haunted-night' and board['skin']==w['skin'] and board['coins']==w['coins']-140
                bundle=call('school/bundle',a,collection='halloween')
                assert bundle['skin']=='skin-pumpkin' and bundle['coins']==board['coins']-100
                assert call('school/bundle',a,collection='halloween')['coins']==bundle['coins']
            assert 'halloween' in call('state',a)['me']['thematicFrames']
            assert call('customize',a,name='Teste A',frame='halloween')['me']['frame']=='halloween'
            with patch.object(s,'seasonal_open',return_value=False):
                assert call('school/equip',a,item='skin-pumpkin')['skin']=='skin-pumpkin'
                assert call('school/bundle',a,collection='halloween')['coins']==bundle['coins']
                status,_=s.social_action('/api/social/school/bundle',dict(a,collection='christmas'),1000)
                assert status==403
            status,_=s.social_action('/api/social/customize',dict(b,name='Teste B',frame='halloween'),1000)
            assert status==403
            # Deterministic correctness tests: runtime still has its real 25 ms deadline.
            with patch.object(s.time,'monotonic',return_value=1000.0):
                # Endgame proof: no guess based on material or evaluation.
                def endboard(pieces,n=64):
                    board=[0]*n
                    for at,piece in pieces.items():board[at]=piece
                    return board
                forced=endboard({19:1,1:-1,3:-1})
                k=s.position_key(forced,1,'official')
                assert len(s.legal(forced,1,'official'))==2
                assert s.inevitable_result(forced,1,'official',0,{k:1},12)=={'winner':-1,'plies':2}
                assert s.inevitable_result(forced,1,'giveaway',0,{},12)=={'winner':1,'plies':2}
                assert s.inevitable_result(forced,1,'official',0,{k:1},11) is None
                assert s.inevitable_result(forced,1,'official',0,{k:1},12,{1:15,-1:100}) is None
                assert s.inevitable_result(forced,1,'official',0,{k:3},12) is None
                assert s.inevitable_result(forced,1,'free',0,{},12) is None
                assert s.inevitable_result(endboard({3:1,10:-1,12:-1}),1,'official',0,{},12) is None
                assert s.inevitable_result(endboard({1:2,62:-2}),1,'official',0,{},20) is None
                # Repetition on even one branch blocks the proof.
                alternative=forced.copy();alternative[19]=0;alternative[12]=1
                branch=s.position_key(alternative,-1,'official')
                assert s.inevitable_result(forced,1,'official',0,{k:1,branch:2},12) is None
                # The actual authoritative move ends a late game, with normal loss and proof metadata.
                room=dict(rule='official',ranked=False,profiles={1:None,-1:None},minutes=0,tokens={1:'a',-1:'b'})
                s.reset_match(room)
                room.update(board=endboard({19:1,1:-1,14:-1}),turn=-1,sequence=11)
                room['repeats']={s.boardkey(room):1}
                m={'from':14,'path':[21],'cap':[]}
                assert m in s.legal(room['board'],-1,'official')
                assert s.process(room,-1,dict(type='move',sequence=12,before=s.boardkey(room),move=m))
                assert room['winner']==-1 and room['result']['reason']=='inevitable'
                assert room['result']['proof']=={'winner':-1,'plies':2}
                assert len(room['result']['moves'])==1 and room['result']['sequence']==12
                # A normal terminal capture still has priority over proof adjudication.
                room.update(winner=None,result=None,proof=None,board=endboard({42:1,35:-1}),turn=1,sequence=12,quiet=0)
                room['repeats']={s.boardkey(room):1}
                m=s.legal(room['board'],1,'official')[0]
                assert s.process(room,1,dict(type='move',sequence=13,before=s.boardkey(room),move=m))
                assert room['winner']==1 and room['result']['reason']=='normal'
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
            # Champion cosmetics are earned, never bought; historic titles count.
            champ=e['champion']
            winner_profile=next(who for who in competitors if s.identity(who)==champ)
            loser_profile=next(who for who in competitors if s.identity(who)!=champ)
            w=call('school/state',winner_profile)
            assert w['cups']==1 and 'champion-hall' in w['owned'] and 'skin-champion' in w['owned']
            assert 'champion-legacy' not in w['owned']
            assert 'cup_champion' in call('state',winner_profile)['me']['achievements']
            for who,item in ((loser_profile,'champion-hall'),(winner_profile,'skin-legend')):
                for action in ('buy','equip'):
                    status,_=s.social_action('/api/social/school/'+action,dict(who,item=item),now)
                    assert status==403
            equipped=call('school/equip',winner_profile,item='skin-champion')
            assert equipped['skin']=='skin-champion' and equipped['coins']==w['coins']
            equipped=call('school/equip',winner_profile,item='champion-hall')
            assert equipped['theme']=='champion-hall' and equipped['skin']=='skin-champion'
            with s.database() as db:
                for number in range(2,6):
                    s.sql(db,'INSERT INTO event_champions(event_id,player_id,name,played_at) VALUES(?,?,?,?)',('test-cup-'+str(number),champ,'Champion','2026-01-01'))
            w=call('school/state',winner_profile)
            assert w['cups']==5 and all(item in w['owned'] for item in s.CHAMPION_ITEMS)
            assert call('school/equip',winner_profile,item='skin-eternal')['skin']=='skin-eternal'
            assert call('school/state',loser_profile)['cups']==0
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
            # Campaign: real legal moves, server AI, sequential progression and one-time relic.
            hero={'name':'Herói da Jornada','profileToken':'journey-test-'+'x'*48}
            call('register',hero);hero_id=s.identity(hero)
            assert call('journey/state',hero)['completed']==0
            status,_=s.social_action('/api/social/journey/start',dict(hero,chapter=4),1000);assert status==403
            status,_=s.social_action('/api/social/journey/equip',hero,1000);assert status==403
            status,_=s.social_action('/api/social/school/buy',dict(hero,item='relic-throne'),1000);assert status==403
            start=call('journey/start',hero,chapter=0)['run']
            assert start['sequence']==0 and len(start['legal'])>0
            assert start['board']==s.initial_for('official') and start['board'].count(1)==12 and start['board'].count(-1)==12
            for chapter in range(5):assert s.journey_board(chapter)==s.initial_for('official')
            first=call('journey/move',hero,id=start['id'],sequence=0,move=start['legal'][0])['run']
            assert first['sequence']==2 and len(first['moves'])==2 and first['outcome'] is None
            assert call('journey/start',hero,chapter=0)['run']['board']==first['board']
            # Stronger engine: legal replies, tactical horizon and tier budgets.
            assert [x['depth'] for x in s.JOURNEY]==[3,5,7,9,11]
            assert all(s.JOURNEY_BUDGETS[i][0]<s.JOURNEY_BUDGETS[i+1][0] for i in range(4))
            trap=[0]*64
            for i,p in ((24,1),(40,1),(42,-1),(51,-1)):trap[i]=p
            original=trap[:];stats={}
            with patch.object(s.time,'monotonic',return_value=1000.0):
                choice=s.journey_ai(trap,2,stats=stats)
            assert choice in s.legal(trap,-1,'official') and trap==original and stats['depth']>=1
            assert not any(m['cap'] for m in s.legal(s.journey_apply(trap,choice),1,'official'))
            for level,path in ((0,None),(1,None),(2,None),(3,None),(4,None),(4,'shadow'),(4,'divine'),(4,'infinite')):
                stats={};board=s.initial_for('official');m=s.journey_ai(board,level,path,stats=stats)
                assert m in s.legal(board,-1,'official') and stats['depth']>=1
                assert stats['maxDepth']==(12 if path else s.JOURNEY[level]['depth'])
                print('JOURNEY AI BENCH',level+1,path or 'normal',stats,flush=True)
            print('JOURNEY AI OK: legal moves, tactical trap, five budgets and three legendary paths',flush=True)
            # Test fixture only: complete a near-terminal traditional game.
            board=[0]*64;board[42]=1;board[35]=-1
            start=dict(id='test-first',version=2,chapter=0,board=board,sequence=0,quiet=0,repeats={s.position_key(board,1,'official'):1},outcome=None,last=[],moves=[],reward=0)
            with s.database() as db:s.sql(db,'UPDATE journey SET payload=? WHERE player_id=?',(json.dumps(start),hero_id))
            start=call('journey/state',hero)['run']
            status,_=s.social_action('/api/social/journey/move',dict(hero,id=start['id'],sequence=0,move={'from':0,'path':[1],'cap':[]}),1000);assert status==400
            result=call('journey/move',hero,id=start['id'],sequence=0,move=start['legal'][0])
            assert result['completed']==1 and result['run']['outcome']=='win' and result['run']['reward']==25
            status,_=s.social_action('/api/social/journey/move',dict(hero,id=start['id'],sequence=0,move=start['legal'][0]),1000);assert status==409
            assert call('school/state',hero)['coins']==25
            second=call('journey/start',hero,chapter=1)['run']
            reply=call('journey/move',hero,id=second['id'],sequence=0,move=second['legal'][0])['run']
            assert reply['sequence']==2 and call('journey/state',hero)['run']['board']==reply['board']
            assert call('journey/start',hero,chapter=1)['run']['id']==reply['id']
            # Official campaign endgames: start at the position, count full moves.
            lead=[0]*64;lead[40]=2;lead[42]=2;lead[7]=-2
            assert s.journey_endgame(lead)['limit']==5
            equal=[0]*64;equal[40]=2;equal[7]=-2
            assert s.journey_endgame(equal)['limit']==2
            for board,limit in ((lead,5),(equal,2),([-p for p in lead],5)):
                trial=dict(board=board,sequence=30,quiet=0,repeats={})
                assert s.journey_draw_clock(trial)['remaining']==limit*2
                trial['sequence']+=limit*2-1
                assert s.journey_draw_reason(trial,'x') is None
                trial['sequence']+=1
                assert s.journey_draw_reason(trial,'x')=='endgame'
            trial=dict(board=lead[:],sequence=30,quiet=0,repeats={})
            s.journey_draw_clock(trial);trial['board']=equal;trial['sequence']=31
            assert s.journey_draw_clock(trial)['remaining']==4
            trial['repeats']={'x':3};assert s.journey_draw_reason(trial,'x')=='repetition'
            trial['repeats']={};trial['quiet']=40;assert s.journey_draw_reason(trial,'x')=='quiet'
            # Old drawn games remain drawn; no retroactive unlock or extra coins.
            old_draw=dict(id='old-draw',version=2,chapter=3,board=lead,sequence=40,quiet=40,repeats={},outcome='draw',last=[],moves=[],reward=0)
            with s.database() as db:s.sql(db,'UPDATE journey SET completed=3,payload=? WHERE player_id=?',(json.dumps(old_draw),hero_id))
            before=call('school/state',hero)['coins']
            unchanged=call('journey/state',hero);assert unchanged['completed']==3 and unchanged['run']['outcome']=='draw'
            assert call('school/state',hero)['coins']==before
            # A real final quiet move with two kings against one draws, not wins.
            drawn_run=dict(id='last-quiet',version=2,chapter=3,board=lead[:],sequence=39,quiet=0,repeats={},outcome=None,last=[],moves=[],reward=0)
            drawn_run['endgame']=dict(**s.journey_endgame(lead),start=30,remaining=1)
            with s.database() as db:s.sql(db,'UPDATE journey SET payload=? WHERE player_id=?',(json.dumps(drawn_run),hero_id))
            quiet_move=next(m for m in s.legal(lead,1,'official') if not m['cap'])
            drawn=call('journey/move',hero,id='last-quiet',sequence=39,move=quiet_move)
            assert drawn['run']['outcome']=='draw' and drawn['run']['reason']=='endgame' and drawn['completed']==3
            assert call('school/state',hero)['coins']==before
            # Real server move at the last half-move: a capture wins before the draw.
            win_board=[0]*64;win_board[42]=2;win_board[35]=-2
            last_run=dict(id='last-capture',version=2,chapter=3,board=win_board,sequence=33,quiet=0,repeats={},outcome=None,last=[],moves=[],reward=0)
            last_run['endgame']=dict(**s.journey_endgame(win_board),start=30,remaining=1)
            with s.database() as db:s.sql(db,'UPDATE journey SET payload=? WHERE player_id=?',(json.dumps(last_run),hero_id))
            won=call('journey/move',hero,id='last-capture',sequence=33,move=s.legal(win_board,1,'official')[0])
            assert won['run']['outcome']=='win' and won['completed']==4 and call('school/state',hero)['coins']==before+100
            # Bot proposals are consensual and persisted, not automatic wins.
            offer_board=[0]*64;offer_board[40]=2;offer_board[7]=-2
            offer_run=dict(id='bot-offer',version=2,chapter=3,board=offer_board,sequence=20,quiet=2,repeats={},outcome=None,last=[],moves=[],reward=0)
            s.journey_draw_clock(offer_run);s.journey_bot_offer(offer_run)
            assert offer_run['botOffer']['sequence']==20
            with s.database() as db:s.sql(db,'UPDATE journey SET payload=? WHERE player_id=?',(json.dumps(offer_run),hero_id))
            declined=call('journey/draw/respond',hero,id='bot-offer',sequence=20,accept=False)
            assert declined['run']['outcome'] is None and not declined['run'].get('botOffer')
            assert call('journey/state',hero)['run']['outcome'] is None
            s.journey_bot_offer(declined['run']);assert not declined['run'].get('botOffer')
            with s.database() as db:s.sql(db,'UPDATE journey SET payload=? WHERE player_id=?',(json.dumps(offer_run),hero_id))
            accepted=call('journey/draw/respond',hero,id='bot-offer',sequence=20,accept=True)
            assert accepted['run']['outcome']=='draw' and accepted['run']['reason']=='agreement' and accepted['completed']==4
            status,_=s.social_action('/api/social/journey/draw/respond',dict(hero,id='bot-offer',sequence=20,accept=True),1000);assert status==409
            # Dark has a legal move, but every reply permits immediate capture.
            forced=[0]*64;forced[1]=2;forced[39]=-1
            forced_run=dict(board=forced,sequence=20,quiet=0,repeats={})
            with patch.object(s.time,'monotonic',return_value=1000.0):
                assert s.legal(forced,-1,'official') and s.journey_bot_lost(forced_run)
            # Material advantage alone is not a proof.
            lead_test=dict(board=lead[:],sequence=20,quiet=0,repeats={})
            s.journey_draw_clock(lead_test);assert not s.journey_bot_lost(lead_test)
            # Test fixture only: simulate a late-game position in the final chapter.
            final_board=[0]*64;final_board[42]=1;final_board[35]=-1
            final_run=dict(id='test-final',chapter=4,board=final_board,sequence=20,quiet=0,repeats={s.position_key(final_board,1,'official'):1},outcome=None,last=[],reward=0)
            with s.database() as db:s.sql(db,'UPDATE journey SET completed=4,payload=? WHERE player_id=?',(json.dumps(final_run),hero_id))
            final=call('journey/move',hero,id='test-final',sequence=20,move=s.legal(final_board,1,'official')[0])
            assert final['completed']==5 and final['run']['relicUnlocked'] and final['unlocked']
            wallet=call('school/state',hero);assert {'relic-throne','skin-relic-throne'}<=set(wallet['owned'])
            equipped=call('journey/equip',hero);assert equipped['theme']=='relic-throne' and equipped['skin']=='skin-relic-throne'
            public=call('player',a,target=hero_id)['player'];assert public['title']=='last_king' and public['frame']=='last-king' and public['relics'][0]['id']=='last-king'
            assert call('school/equip',hero,item='classic')['skin']=='skin-relic-throne'
            assert call('school/equip',hero,item='relic-throne')['theme']=='relic-throne'
            assert call('school/state',hero)['coins']==wallet['coins']
            # Three paths: first choice, locked collection, loss without reward, then verified victory.
            assert final['paths']==[]
            status,_=s.social_action('/api/social/journey/claim',dict(a,path='shadow'),1000);assert status==403
            status,_=s.social_action('/api/social/journey/equip',dict(hero,path='divine'),1000);assert status==403
            chosen=call('journey/claim',hero,path='shadow');assert chosen['paths']==['shadow']
            assert 'king_shadow' in call('state',hero)['me']['achievements']
            assert call('customize',hero,name=hero['name'],title='king_shadow')['me']['title']=='king_shadow'
            status,_=s.social_action('/api/social/customize',dict(hero,title='king_divine'),1000);assert status==403
            status,_=s.social_action('/api/social/journey/claim',dict(hero,path='divine'),1000);assert status==403
            equipped=call('journey/equip',hero,path='shadow');assert equipped['theme']=='relic-shadow' and equipped['skin']=='skin-relic-shadow'
            status,_=s.social_action('/api/social/school/buy',dict(hero,item='relic-divine'),1000);assert status==403
            trial=call('journey/start',hero,chapter=4,path='divine')['run'];assert trial['path']=='divine'
            assert call('journey/start',hero,chapter=4,path='divine')['run']['id']==trial['id']
            lost=call('journey/resign',hero,id=trial['id']);assert lost['paths']==['shadow']
            assert 'king_divine' not in call('state',hero)['me']['achievements']
            for path in ('divine','infinite'):
                trial=call('journey/start',hero,chapter=4,path=path,restart=True)['run']
                trial.update(board=final_board[:],sequence=20,quiet=0,repeats={s.position_key(final_board,1,'official'):1},last=[],moves=[])
                with s.database() as db:s.sql(db,'UPDATE journey SET payload=? WHERE player_id=?',(json.dumps(trial),hero_id))
                earned=call('journey/move',hero,id=trial['id'],sequence=20,move=s.legal(final_board,1,'official')[0])
                assert earned['run']['pathUnlocked']==path and path in earned['paths']
                equipped=call('journey/equip',hero,path=path);assert equipped['theme']=='relic-'+path and equipped['skin']=='skin-relic-'+path
            assert set(call('journey/state',hero)['paths'])=={'shadow','divine','infinite'}
            me=call('state',hero)['me'];assert {'king_shadow','king_divine','king_cosmos'}<=set(me['achievements']) and me['title']=='king_shadow'
            assert call('customize',hero,name=hero['name'],title='king_cosmos')['me']['title']=='king_cosmos'
            assert call('player',a,target=hero_id)['player']['title']=='king_cosmos'
            saved=call('save/state',hero);assert saved['version']==1 and saved['me']['title']=='king_cosmos' and set(saved['journey']['paths'])=={'shadow','divine','infinite'}
            assert saved['wallet']['coins']==wallet['coins'] and 'relic-infinite' in saved['wallet']['owned'] and saved['journey']['completed']==5
            assert 'profileToken' not in saved and 'password' not in saved['me']
            other_save=call('save/state',a);assert other_save['me']['name']!=saved['me']['name'] and other_save['journey']['completed']==0
            status,_=s.social_action('/api/social/save/write',dict(hero,coins=999999),1000);assert status==404
            assert call('school/state',hero)['coins']==wallet['coins']
            assert call('state',hero)['me']['points']==1000
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
            assert call('save/state',other_device)['me']['account']=='teste_a'
            assert call('save/state',auth)['me']['points']==call('save/state',other_device)['me']['points']
            assert call('save/state',auth)['wallet']['owned']==call('save/state',other_device)['wallet']['owned']
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
            print('SELFTEST OK: presence, friendship, removal, accent-insensitive offline search, public profile, invitations, four moves, ranked resignation, duplicate result, casual mode, both random colors, rematch color swap and correct points, friendship notices, unread counts, presence offline/online, resignation then exit, repeated result, direct leave, casual result, matchmaking, reconnect snapshot, draw agreement, replay, timeout, queue cancellation, five variants, reverse victory, larger boards, custom rooms, chat, spectators, puzzles, coins, themes, independent skins, champion rewards, thematic bundles, seasonal access, profile frames, tournament, king table, campaign and relic, account linking/login, identity preservation, password hash, profile cosmetics, achievements, logout',flush=True)
        finally:
            s.BASE,s.DATABASE_URL,s.ROOMS,s.PRESENCE,s.INVITES,s.MATCH_QUEUE,s.LOGIN_LIMITS,s.SPECTATORS,s.TOURNAMENTS,s.LOCAL_LIVE=old
