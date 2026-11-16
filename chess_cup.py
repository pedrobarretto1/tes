"""Copa de Honra: persistent eight-player chess knockout with server-verified results."""
import json
import secrets
import time

SIZE = 8
MINUTES = 10
PRIZE = 100

def setup(db, sql):
    sql(db, "CREATE TABLE IF NOT EXISTS chess_cups (id TEXT PRIMARY KEY, payload TEXT NOT NULL, status TEXT NOT NULL, created_at DOUBLE PRECISION NOT NULL)")
    sql(db, "CREATE INDEX IF NOT EXISTS chess_cups_status_idx ON chess_cups(status,created_at)")
    sql(db, "CREATE TABLE IF NOT EXISTS chess_cup_champions (cup_id TEXT PRIMARY KEY, player_id TEXT NOT NULL, name TEXT NOT NULL, won_at DOUBLE PRECISION NOT NULL)")
    sql(db, "CREATE INDEX IF NOT EXISTS chess_cup_champions_player_idx ON chess_cup_champions(player_id)")

def _active(db, sql):
    return [json.loads(row[0]) for row in sql(db, "SELECT payload FROM chess_cups WHERE status IN ('waiting','playing')").fetchall()]

def _contenders(e):
    if e['status'] == 'waiting':
        return set(e['players'])
    if e['status'] == 'playing':
        return {p['winner'] for p in e['pairs'] if p['winner']} | {pid for p in e['pairs'] if not p['winner'] for pid in (p['a'],p['b'])}
    return set()

def occupied(db, sql, pid):
    return any(pid in _contenders(e) for e in _active(db, sql))

def _save(db, sql, e):
    sql(db, "UPDATE chess_cups SET payload=?,status=? WHERE id=?", (json.dumps(e),e['status'],e['id']))

def _available(s,db,pid,now):
    import chess_duels as chess_games
    return (not chess_games.active(db,s.sql,pid)
            and not s.active_room(pid,now)
            and not s.sql(db,"SELECT 1 FROM chess_queue WHERE player_id=?",(pid,)).fetchone())

def _pair(s,db,e,a,b,idx):
    import chess_duels as chess_games
    g=chess_games.create(s,db,a,b,'online','',MINUTES,False,
        'cup:'+e['id']+':'+str(e['round'])+':'+str(idx))
    g['cup']=e['id']
    g['cup_round']=e['round']
    chess_games.save(db,s.sql,g)
    return dict(a=a,b=b,match=g['id'],winner=None,draws=0)

def _begin(s,db,e):
    players=e['players'][:]
    secrets.SystemRandom().shuffle(players)
    e['status']='playing'
    e['round']=1
    e['pairs']=[_pair(s,db,e,players[i],players[i+1],i//2) for i in range(0,SIZE,2)]

def _award(s,db,e,pid):
    sql=s.sql
    r=sql(db,"SELECT name FROM players WHERE id=?",(pid,)).fetchone()
    name=r[0] if r else 'Campeão'
    inserted=sql(db,"INSERT INTO chess_cup_champions VALUES(?,?,?,?) ON CONFLICT(cup_id) DO NOTHING",
                 (e['id'],pid,name,time.time())).rowcount
    if inserted:
        sql(db,"UPDATE chess_profiles SET coins=coins+? WHERE player_id=?",(PRIZE,pid))
        for item in ('pieces-champion','board-champion'):
            sql(db,"INSERT INTO chess_shop_owned VALUES(?,?,?) ON CONFLICT(player_id,item_id) DO NOTHING",
                (pid,item,time.time()))

def tick(s,db):
    """Advance only from chess_matches persisted results, never client claims."""
    import chess_duels as chess_games
    sql=s.sql
    for e in _active(db,sql):
        changed=False
        if e['status']=='waiting':
            if time.time()-e['created_at']>86400:
                e['status']='cancelled'
                _save(db,sql,e)
            continue
        for pair in e['pairs']:
            if pair['winner']:
                continue
            r=sql(db,"SELECT payload FROM chess_matches WHERE id=?",(pair['match'],)).fetchone()
            if not r:
                # Never guess a winner when a match is missing.
                e['status']='cancelled';changed=True;break
            g=json.loads(r[0])
            if g['result'] is None:
                chess_games.tick(s,db,g,chess_games.board(g))
                chess_games.save(db,sql,g)
            result=g['result']
            if result is None:
                continue
            if result['winner'] is None:
                # A draw replays the same pairing, without awarding points.
                pair['draws']+=1
                new=_pair(s,db,e,pair['a'],pair['b'],pair['draws'])
                pair['match']=new['match']
                changed=True
            else:
                winner=g['players'].get(result['winner'])
                if winner not in (pair['a'],pair['b']):
                    e['status']='cancelled';changed=True;break
                pair['winner']=winner
                changed=True
        if e['status']=='cancelled':
            _save(db,sql,e)
            continue
        if all(p['winner'] for p in e['pairs']):
            winners=[p['winner'] for p in e['pairs']]
            e['history'].append(dict(round=e['round'],pairs=[p.copy() for p in e['pairs']]))
            if len(winners)==1:
                e['status']='finished'
                e['champion']=winners[0]
                _award(s,db,e,winners[0])
            else:
                e['round']+=1
                e['pairs']=[_pair(s,db,e,winners[i],winners[i+1],i//2) for i in range(0,len(winners),2)]
            changed=True
        if changed:
            _save(db,sql,e)

def snapshot(s,db,pid):
    sql=s.sql
    rows=sql(db,"SELECT payload FROM chess_cups ORDER BY created_at DESC LIMIT 30").fetchall()
    names=dict(sql(db,"SELECT id,name FROM players").fetchall())
    events=[]
    for (raw,) in rows:
        e=json.loads(raw)
        pairs=[dict(a=names.get(p['a'],'Jogador'),b=names.get(p['b'],'Jogador'),
                    winner=names.get(p['winner']) if p['winner'] else None,
                    draws=p['draws'],mine=pid in (p['a'],p['b']),
                    match=p['match'] if pid in (p['a'],p['b']) else None)
               for p in e['pairs']]
        events.append(dict(id=e['id'],status=e['status'],round=e['round'],
            count=len(e['players']),players=[names.get(p,'Jogador') for p in e['players']],
            joined=pid in e['players'],contender=pid in _contenders(e),host=e['host']==pid,
            pairs=pairs,champion=names.get(e.get('champion')),created=e['created_at']))
    champs=sql(db,"SELECT name,won_at FROM chess_cup_champions ORDER BY won_at DESC LIMIT 12").fetchall()
    total=sql(db,"SELECT COUNT(*) FROM chess_cup_champions WHERE player_id=?",(pid,)).fetchone()[0]
    return dict(events=events,champions=[dict(name=x[0],date=x[1]) for x in champs],wins=total)

def action(s,db,op,d,pid,now):
    """All operations run inside chess_guard and the database transaction."""
    sql=s.sql
    def err(message,code=409):return code,{'error':message}
    if op=='cup-list':
        return 200,{}
    if op=='cup-create':
        if occupied(db,sql,pid) or not _available(s,db,pid,now):
            return err('Você já está em uma partida ou Copa.')
        if len(_active(db,sql))>=32:
            return err('Limite de Copas abertas atingido.',503)
        key=secrets.token_hex(6)
        e=dict(id=key,host=pid,players=[pid],status='waiting',
               round=0,pairs=[],history=[],champion=None,created_at=time.time())
        sql(db,"INSERT INTO chess_cups VALUES(?,?,?,?)",(key,json.dumps(e),'waiting',e['created_at']))
        return 200,{}
    key=d.get('event')
    if not isinstance(key,str) or len(key)>40 or not key:
        return err('Copa inválida.',400)
    row=sql(db,"SELECT payload FROM chess_cups WHERE id=?",(key,)).fetchone()
    if not row:
        return err('Copa não encontrada.',404)
    e=json.loads(row[0])
    if op=='cup-join':
        if e['status']!='waiting' or len(e['players'])>=SIZE:
            return err('Inscrições encerradas.')
        if pid in e['players']:
            return 200,{}
        if occupied(db,sql,pid) or not _available(s,db,pid,now):
            return err('Você já está em uma partida ou Copa.')
        # Every entrant must be free when the eighth seat launches the bracket.
        if len(e['players'])==SIZE-1:
            for p in e['players']:
                if not _available(s,db,p,now):
                    return err('Um inscrito está ocupado em outro jogo. Tente quando estiver livre.')
        e['players'].append(pid)
        if len(e['players'])==SIZE:
            _begin(s,db,e)
    elif op=='cup-leave':
        if e['status']!='waiting' or pid not in e['players']:
            return err('Só é possível sair antes da primeira rodada.')
        e['players'].remove(pid)
        if not e['players']:
            sql(db,"DELETE FROM chess_cups WHERE id=?",(key,))
            return 200,{}
        if e['host']==pid:
            e['host']=e['players'][0]
    elif op=='cup-cancel':
        if e['host']!=pid or e['status']!='waiting':
            return err('Somente o organizador pode cancelar antes do início.',403)
        e['status']='cancelled'
    else:
        return err('Ação da Copa não reconhecida.',404)
    _save(db,sql,e)
    return 200,{}
