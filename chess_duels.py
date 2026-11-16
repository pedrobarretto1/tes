"""Independent, authoritative chess games. Existing account/identity is shared."""
import json,secrets,time,random
import chess

LEVELS=('easy','medium','hard')
MINUTES=(0,1,3,5,10,15,30)
JOURNEY=(
    dict(id=1,name='O Escudeiro',hall='Pátio de Carvalho',title='Escudeiro da Coroa',level='easy',description='O primeiro guardião testa os fundamentos. Desenvolva suas peças e proteja o rei.'),
    dict(id=2,name='O Guardião',hall='Fortaleza de Pedra',title='Guardião do Salão',level='medium',description='Um defensor atento ao material. Evite deixar peças desprotegidas.'),
    dict(id=3,name='O Estrategista',hall='Biblioteca Real',title='Estrategista Real',level='medium',description='Calcula respostas e contra-ataques. Pense antes de comprometer suas peças.'),
    dict(id=4,name='O Rei de Ferro',hall='Salão de Ferro',title='Vencedor de Ferro',level='hard',description='Uma busca mais profunda favorece combinações e ameaças táticas.'),
    dict(id=5,name='O Mestre das Coroas',hall='Trono das Cinco Coroas',title='Mestre das Cinco Coroas',level='hard',description='O adversário final usa o maior orçamento de busca da campanha.'),
)
def journey_progress(db,sql,pid):
    wins={r[0] for r in sql(db,'SELECT stage FROM chess_journey WHERE player_id=?',(pid,)).fetchall()}
    unlocked=1
    while unlocked<=len(JOURNEY) and unlocked in wins:unlocked+=1
    return dict(stages=JOURNEY,won=sorted(wins),unlocked=min(unlocked,len(JOURNEY)),complete=unlocked>len(JOURNEY),title=JOURNEY[unlocked-2]['title'] if unlocked>1 else 'Aspirante às Coroas')

def setup(db,sql):
    for q in (
        "CREATE TABLE IF NOT EXISTS chess_guard (id INTEGER PRIMARY KEY)",
        "CREATE TABLE IF NOT EXISTS chess_journey (player_id TEXT NOT NULL, stage INTEGER NOT NULL, won_at DOUBLE PRECISION NOT NULL, PRIMARY KEY(player_id,stage))",
        "CREATE TABLE IF NOT EXISTS chess_profiles (player_id TEXT PRIMARY KEY, points INTEGER NOT NULL DEFAULT 1000, coins INTEGER NOT NULL DEFAULT 0, wins INTEGER NOT NULL DEFAULT 0, losses INTEGER NOT NULL DEFAULT 0, draws INTEGER NOT NULL DEFAULT 0)",
        "CREATE TABLE IF NOT EXISTS chess_matches (id TEXT PRIMARY KEY, payload TEXT NOT NULL, finished INTEGER NOT NULL DEFAULT 0)",
        "CREATE TABLE IF NOT EXISTS chess_seats (player_id TEXT PRIMARY KEY, match_id TEXT NOT NULL REFERENCES chess_matches(id))",
        "CREATE TABLE IF NOT EXISTS chess_invites (id TEXT PRIMARY KEY, sender TEXT NOT NULL, receiver TEXT NOT NULL, minutes INTEGER NOT NULL, ranked INTEGER NOT NULL, expires DOUBLE PRECISION NOT NULL, status TEXT NOT NULL)",
        "CREATE TABLE IF NOT EXISTS chess_queue (player_id TEXT PRIMARY KEY, minutes INTEGER NOT NULL, ranked INTEGER NOT NULL, seen DOUBLE PRECISION NOT NULL)",
        "CREATE TABLE IF NOT EXISTS chess_history (match_id TEXT NOT NULL, player_id TEXT NOT NULL, opponent TEXT NOT NULL, outcome TEXT NOT NULL, delta INTEGER NOT NULL, coins INTEGER NOT NULL, played_at DOUBLE PRECISION NOT NULL, PRIMARY KEY(match_id,player_id))",
    ):sql(db,q)
    sql(db,"INSERT INTO chess_guard(id) VALUES(1) ON CONFLICT(id) DO NOTHING")
def ensure(db,sql,pid):
    sql(db,"INSERT INTO chess_profiles(player_id) VALUES(?) ON CONFLICT(player_id) DO NOTHING",(pid,))
def active(db,sql,pid,include_paused=True):
    r=sql(db,"SELECT m.payload FROM chess_seats s JOIN chess_matches m ON m.id=s.match_id WHERE s.player_id=? AND m.finished=0",(pid,)).fetchone()
    if not r:return False
    return include_paused or not json.loads(r[0]).get('paused',False)
def current(db,sql,pid):
    r=sql(db,"SELECT m.payload FROM chess_seats s JOIN chess_matches m ON m.id=s.match_id WHERE s.player_id=?",(pid,)).fetchone()
    return json.loads(r[0]) if r else None
def save(db,sql,g):
    sql(db,"UPDATE chess_matches SET payload=?,finished=? WHERE id=?",(json.dumps(g),int(g['result'] is not None),g['id']))
def board(g):
    b=chess.Board()
    for u in g['moves']:b.push_uci(u)
    return b
def color(g,pid):return 'w' if g['players']['w']==pid else 'b'
def opposite(c):return 'b' if c=='w' else 'w'
def amount(v,level):return (1 if v>=0 else -1)*((abs(v)+1)//2) if level=='medium' else v
def finish(s,db,g,winner,reason):
    if g['result'] is not None:return
    result=dict(winner=winner,reason=reason,rewards={})
    for c,pid in g['players'].items():
        if not pid:continue
        outcome='draw' if winner is None else 'win' if winner==c else 'resign' if reason=='resign' else 'loss'
        delta=amount({'win':25,'loss':-15,'resign':-20,'draw':5}[outcome],g['level']) if g['ranked'] else 0
        coins=amount(15 if outcome=='win' else 8,g['level']) if g['ranked'] and outcome!='resign' and reason!='resign' and len(g['moves'])>=8 else 0
        if g['ranked']:
            ensure(db,s.sql,pid)
            old=s.sql(db,'SELECT points FROM chess_profiles WHERE player_id=?',(pid,)).fetchone()[0]
            delta=max(0,old+delta)-old
            inserted=s.sql(db,'INSERT INTO chess_history VALUES(?,?,?,?,?,?,?) ON CONFLICT(match_id,player_id) DO NOTHING',(g['id'],pid,g['names'][opposite(c)],outcome,delta,coins,time.time())).rowcount
            if inserted:s.sql(db,'UPDATE chess_profiles SET points=points+?,coins=coins+?,wins=wins+?,losses=losses+?,draws=draws+? WHERE player_id=?',(delta,coins,int(outcome=='win'),int(outcome in ('loss','resign')),int(outcome=='draw'),pid))
            else:delta=coins=0
        else:
            s.sql(db,'INSERT INTO chess_history VALUES(?,?,?,?,?,?,?) ON CONFLICT(match_id,player_id) DO NOTHING',(g['id'],pid,g['names'][opposite(c)],outcome,0,0,time.time()))
        result['rewards'][c]=dict(delta=delta,coins=coins,outcome=outcome)
        if g.get('journey') and winner==c:
            stage=g['journey']
            first=s.sql(db,'INSERT INTO chess_journey VALUES(?,?,?) ON CONFLICT(player_id,stage) DO NOTHING',(pid,stage,time.time())).rowcount
            result['journey']=dict(stage=stage,first=bool(first),title=JOURNEY[stage-1]['title'])
    g['result']=result;save(db,s.sql,g)
def tick(s,db,g,b):
    if g['result'] or g.get('paused') or not g['minutes']:return
    now=time.time();c='w' if b.turn else 'b'
    # CPU search is charged explicitly; waiting for a bot poll does not cost its clock.
    if g['mode']=='ai' and g['players'][c] is None:return
    g['remaining'][c]=max(0,g['remaining'][c]-max(0,now-g['clock_at']));g['clock_at']=now
    if g['remaining'][c]<=0:
        other=opposite(c)
        finish(s,db,g,None if b.has_insufficient_material(other=='w') else other,'timeout')
def after_move(s,db,g,b,m):
    g['moves'].append(m.uci());b.push(m);g['clock_at']=time.time();g['offer']=None
    o=b.outcome(claim_draw=False)
    if o:finish(s,db,g,None if o.winner is None else 'w' if o.winner else 'b',o.termination.name.lower())
    else:save(db,s.sql,g)
def bot_move(b,level,stage=None):
    ms=list(b.legal_moves)
    if not ms:return None
    if level=='easy':return random.choice(ms)
    budget,limit,depth_cap={2:(.08,1000,1),3:(.18,4000,2),4:(.35,10000,3),5:(.65,22000,4)}.get(stage,(.15,3000,2) if level=='medium' else (.45,14000,4))
    deadline=time.monotonic()+budget;nodes=0
    values={chess.PAWN:100,chess.KNIGHT:320,chess.BISHOP:330,chess.ROOK:500,chess.QUEEN:900,chess.KING:0}
    class Budget(Exception):pass
    def evaluate():
        score=0
        for square,p in b.piece_map().items():
            r,f=chess.square_rank(square),chess.square_file(square)
            center= min(r,7-r)+min(f,7-f)
            score+=(1 if p.color==b.turn else -1)*(values[p.piece_type]+center*(5 if p.piece_type in (chess.KNIGHT,chess.BISHOP) else 2))
        return score
    def ordered(ms):
        return sorted(ms,key=lambda m:(bool(m.promotion),b.is_capture(m),values.get(b.piece_type_at(m.to_square),0)),reverse=True)
    def search(depth,a,z,ply):
        nonlocal nodes
        nodes+=1
        if nodes>limit or time.monotonic()>deadline:raise Budget
        if b.is_checkmate():return -100000+ply
        if b.is_stalemate() or b.is_insufficient_material() or b.is_seventyfive_moves():return 0
        if depth==0:return evaluate()
        v=-200000
        for m in ordered(b.legal_moves):
            b.push(m)
            try:x=-search(depth-1,-z,-a,ply+1)
            finally:b.pop()
            v=max(v,x);a=max(a,v)
            if a>=z:break
        return v
    ms=ordered(ms);best=ms[0]
    for depth in range(1,depth_cap+1):
        candidate=best;v=-200000
        try:
            for m in ms:
                b.push(m)
                try:x=-search(depth-1,-200000,-v,1)
                finally:b.pop()
                if x>v:candidate=m;v=x
        except Budget:break
        best=candidate;ms=[best]+[m for m in ms if m!=best]
    return best
def create(s,db,pid,other,mode,level,minutes,ranked,nonce,journey=None):
    side='w' if journey else secrets.choice(('w','b'));players={side:pid,opposite(side):other}
    names={c:s.sql(db,'SELECT name FROM players WHERE id=?',(p,)).fetchone()[0] if p else 'Computador' for c,p in players.items()}
    g=dict(id=secrets.token_hex(16),players=players,names=names,mode=mode,level=level,ranked=ranked,minutes=minutes,remaining={'w':minutes*60,'b':minutes*60},clock_at=time.time(),moves=[],result=None,offer=None,nonce=nonce)
    if journey:
        g['journey']=journey;g['names']['b']=JOURNEY[journey-1]['name']
    s.sql(db,'INSERT INTO chess_matches(id,payload,finished) VALUES(?,?,0)',(g['id'],json.dumps(g)))
    for p in players.values():
        if p:
            ensure(db,s.sql,p);s.sql(db,'INSERT INTO chess_seats VALUES(?,?) ON CONFLICT(player_id) DO UPDATE SET match_id=excluded.match_id',(p,g['id']))
            s.sql(db,'DELETE FROM chess_queue WHERE player_id=?',(p,))
    return g
def view(g,pid):
    if not g:return None
    c=color(g,pid)
    return dict(id=g['id'],side=c,names=g['names'],mode=g['mode'],level=g['level'],ranked=g['ranked'],minutes=g['minutes'],remaining=g['remaining'],moves=g['moves'],result=g['result'],offer=g['offer'],journey=g.get('journey'),paused=bool(g.get('paused')))
def incoming(db,sql,pid):
    rows=sql(db,"SELECT i.id,p.name,i.minutes,i.ranked FROM chess_invites i JOIN players p ON p.id=i.sender WHERE i.receiver=? AND i.status='pending' AND i.expires>? ORDER BY i.expires",(pid,time.time())).fetchall()
    return [dict(id=r[0],name=r[1],game='chess',minutes=r[2],ranked=bool(r[3])) for r in rows]
def snapshot(s,db,pid,g):
    ensure(db,s.sql,pid)
    r=s.sql(db,'SELECT points,coins,wins,losses,draws FROM chess_profiles WHERE player_id=?',(pid,)).fetchone()
    me=dict(zip(('points','coins','wins','losses','draws'),r))
    rank=s.sql(db,'SELECT COUNT(*) FROM chess_profiles WHERE points>? OR (points=? AND (wins>? OR (wins=? AND player_id<?)))',(r[0],r[0],r[2],r[2],pid)).fetchone()[0]+1
    me['rank']=rank
    rows=s.sql(db,'SELECT p.name,c.points,c.wins,c.losses,c.draws,c.player_id FROM chess_profiles c JOIN players p ON p.id=c.player_id ORDER BY c.points DESC,c.wins DESC,c.player_id LIMIT 100').fetchall()
    ranking=[dict(name=x[0],points=x[1],wins=x[2],losses=x[3],draws=x[4],own=x[5]==pid) for x in rows]
    return dict(profile=me,ranking=ranking,match=view(g,pid),journey=journey_progress(db,s.sql,pid),queued=bool(s.sql(db,'SELECT 1 FROM chess_queue WHERE player_id=?',(pid,)).fetchone()),invites=incoming(db,s.sql,pid))
def action(s,path,d,pid,now):
    op=path.rsplit('/',1)[-1]
    def err(msg,code=409):return code,{'error':msg}
    with s.database() as db:
        sql=s.sql
        if op=='history':
            rows=sql(db,'SELECT h.opponent,h.outcome,h.delta,h.coins,h.played_at,m.payload FROM chess_history h JOIN chess_matches m ON m.id=h.match_id WHERE h.player_id=? AND m.finished=1 ORDER BY h.played_at DESC LIMIT 20',(pid,)).fetchall()
            result=[]
            for r in rows:
                g=json.loads(r[5])
                result.append(dict(opponent=r[0],outcome=r[1],delta=r[2],coins=r[3],played_at=r[4],ranked=g['ranked'],moves=g['moves'],mode=g['mode'],journey=g.get('journey')))
            return 200,dict(history=result)
        sql(db,'UPDATE chess_guard SET id=id WHERE id=1')
        g=current(db,sql,pid)
        if g and not g['result']:
            b=board(g);tick(s,db,g,b);save(db,sql,g)
        def result():return 200,snapshot(s,db,pid,g)
        def blocked(p):
            return active(db,sql,p) or s.active_room(p,now) or (p!=pid and s.PRESENCE_GAME.get(p)==('chess',True) and now-s.PRESENCE.get(p,-1000)<=25)
        if op=='leave':
            if g and not g['result'] and g['mode']=='online' and d.get('allowOnline') is not True:return err('Existe um duelo online em andamento.',409)
            sql(db,'DELETE FROM chess_queue WHERE player_id=?',(pid,))
            if g and not g['result'] and g['mode']=='ai':
                g['paused']=True;save(db,sql,g)
            return 200,{'left':True}
        if op in ('state','poll'):
            if g and not g['result'] and g.get('paused') and not s.active_room(pid,now):
                g['paused']=False;g['clock_at']=time.time();save(db,sql,g)
            sql(db,'DELETE FROM chess_queue WHERE seen<?',(time.time()-25,))
            q=sql(db,'SELECT minutes,ranked FROM chess_queue WHERE player_id=?',(pid,)).fetchone()
            if q and not blocked(pid):
                sql(db,'UPDATE chess_queue SET seen=? WHERE player_id=?',(time.time(),pid))
                for row in sql(db,'SELECT player_id FROM chess_queue WHERE player_id<>? AND minutes=? AND ranked=? ORDER BY seen',(pid,q[0],q[1])).fetchall():
                    p=row[0]
                    if not blocked(p) and now-s.PRESENCE.get(p,-1000)<=25:
                        g=create(s,db,pid,p,'online','',q[0],bool(q[1]),'queue');break
            return result()
        if op=='journey-start':
            stage=d.get('stage');nonce=d.get('nonce')
            if type(stage) is not int or not 1<=stage<=len(JOURNEY) or not isinstance(nonce,str) or not 16<=len(nonce)<=80:return err('Etapa inválida.',400)
            if g and g['nonce']==nonce and g.get('journey')==stage:return result()
            if blocked(pid):return err('Conclua ou desista da partida atual.')
            if stage>journey_progress(db,sql,pid)['unlocked']:return err('Vença a etapa anterior para desbloquear esta coroa.')
            g=create(s,db,pid,None,'ai',JOURNEY[stage-1]['level'],0,False,nonce,journey=stage);return result()
        if op=='cancel':
            sql(db,'DELETE FROM chess_queue WHERE player_id=?',(pid,));return result()
        if op in ('start','queue','invite'):
            minutes=d.get('minutes',0)
            if type(minutes) is not int or minutes not in MINUTES:return err('Relógio inválido.',400)
            ranked=d.get('ranked') is not False
            if op=='start':
                level=d.get('level');nonce=d.get('nonce')
                if level not in LEVELS or not isinstance(nonce,str) or not 16<=len(nonce)<=80:return err('Configuração inválida.',400)
                if g and g['nonce']==nonce:return result()
                if blocked(pid):return err('Conclua ou desista da partida atual.')
                g=create(s,db,pid,None,'ai',level,minutes,level!='easy',nonce);return result()
            if blocked(pid):return err('Conclua a partida atual.')
            if op=='queue':
                sql(db,'INSERT INTO chess_queue VALUES(?,?,?,?) ON CONFLICT(player_id) DO UPDATE SET minutes=excluded.minutes,ranked=excluded.ranked,seen=excluded.seen',(pid,minutes,int(ranked),time.time()));return result()
            p=d.get('target')
            if not isinstance(p,str) or p==pid or not sql(db,'SELECT 1 FROM players WHERE id=?',(p,)).fetchone():return err('Jogador inválido.',400)
            if now-s.PRESENCE.get(p,-1000)>25 or blocked(p):return err('Jogador indisponível.')
            if sql(db,"SELECT 1 FROM chess_invites WHERE sender=? AND receiver=? AND status='pending' AND expires>?",(pid,p,time.time())).fetchone():return err('Convite já enviado.')
            if sql(db,"SELECT COUNT(*) FROM chess_invites WHERE sender=? AND status='pending' AND expires>?",(pid,time.time())).fetchone()[0]>=10:return err('Limite de convites.')
            sql(db,'INSERT INTO chess_invites VALUES(?,?,?,?,?,?,?)',(secrets.token_hex(16),pid,p,minutes,int(ranked),time.time()+60,'pending'));return result()
        if op=='respond':
            r=sql(db,"SELECT sender,minutes,ranked FROM chess_invites WHERE id=? AND receiver=? AND status='pending' AND expires>?",(str(d.get('invite','')),pid,time.time())).fetchone()
            if not r:return err('Convite expirado.')
            if d.get('accept') is not True:
                sql(db,"UPDATE chess_invites SET status='declined' WHERE id=?",(d['invite'],));return result()
            if blocked(pid) or blocked(r[0]) or now-s.PRESENCE.get(r[0],-1000)>25:return err('Jogador indisponível.')
            g=create(s,db,pid,r[0],'online','',r[1],bool(r[2]),'invite:'+d['invite'])
            sql(db,"UPDATE chess_invites SET status='accepted' WHERE id=?",(d['invite'],));return result()
        if not g or d.get('match')!=g['id']:return err('Partida indisponível.')
        if g['result']:return result()
        if g.get('paused'):return err('Retome a partida antes de jogar.')
        c=color(g,pid);b=board(g);turn='w' if b.turn else 'b'
        if op=='resign':finish(s,db,g,opposite(c),'resign');return result()
        if op=='draw':
            if g['mode']!='online':return err('Oferta indisponível.')
            if g['offer']==opposite(c):
                if d.get('accept') is True:finish(s,db,g,None,'agreement')
                else:g['offer']=None;save(db,sql,g)
            elif d.get('accept') is True:g['offer']=c;save(db,sql,g)
            return result()
        if d.get('sequence')!=len(g['moves']):return result()
        if op=='claim':
            if turn!=c or not (b.is_repetition(3) or b.is_fifty_moves()):return err('Empate não disponível.')
            finish(s,db,g,None,'claimed_draw');return result()
        if op=='move':
            if turn!=c:return err('Não é sua vez.')
            try:m=chess.Move.from_uci(d.get('move',''))
            except (ValueError,TypeError):return err('Lance inválido.',400)
            if m not in b.legal_moves:return err('Lance ilegal.')
        elif op=='bot':
            if g['mode']!='ai' or turn==c:return err('Não é a vez do computador.')
            t=time.monotonic();m=bot_move(b,g['level'],g.get('journey')) if g.get('journey') else bot_move(b,g['level'])
            if g['minutes']:
                g['remaining'][turn]=max(0,g['remaining'][turn]-(time.monotonic()-t))
                if g['remaining'][turn]<=0:finish(s,db,g,None if b.has_insufficient_material(c=='w') else c,'timeout');return result()
            if not m:return err('Sem lances legais.')
        else:return err('Ação inexistente.',404)
        after_move(s,db,g,b,m);return result()
