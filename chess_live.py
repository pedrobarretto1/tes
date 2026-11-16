"""Read-only spectator views of authoritative chess matches. Consent belongs to a match."""
import json,time
import chess_duels as c
import chess_shop
def permitted(g):
    people=[p for p in g['players'].values() if p]
    return bool(people) and all(g.get('live',{}).get(p) is True for p in people)
def visible(s,g,now):
    if not permitted(g) or g.get('paused'):return False
    if g.get('result'):return time.time()-g.get('finished_at',0)<45
    return any(s.PRESENCE_GAME.get(p,('damas',False))[0]=='chess' and now-s.PRESENCE.get(p,-1000)<30 for p in g['players'].values() if p)
def friends(db,sql,pid):
    return {r[0] for r in sql(db,"SELECT CASE WHEN sender=? THEN receiver ELSE sender END FROM friendships WHERE state='accepted' AND (sender=? OR receiver=?)",(pid,pid,pid)).fetchall()}
def summary(g,fr):
    return dict(id=g['id'],names=g['names'],mode=g['mode'],level=g['level'],ranked=g['ranked'],minutes=g['minutes'],journey=g.get('journey'),sequence=len(g['moves']),friend=any(p in fr for p in g['players'].values() if p))
def action(s,path,d,pid,now):
    op=path.rsplit('/',1)[-1]
    with s.database() as db:
        sql=s.sql
        if op=='list':
            fr=friends(db,sql,pid);out=[]
            # Seats exclude historical games; bounded response and no board work for the directory.
            for (payload,) in sql(db,"SELECT m.payload FROM chess_matches m WHERE m.finished=0 AND EXISTS (SELECT 1 FROM chess_seats cs WHERE cs.match_id=m.id) ORDER BY m.id LIMIT 300").fetchall():
                g=json.loads(payload)
                if pid not in g['players'].values() and visible(s,g,now):out.append(summary(g,fr))
            out.sort(key=lambda g:(not g['friend'],-g['sequence'],g['id']))
            return 200,dict(matches=out[:50])
        if op!='watch':return 404,dict(error='Ação inválida.')
        mid=d.get('match')
        if not isinstance(mid,str) or len(mid)!=32:return 400,dict(error='Partida inválida.')
        row=sql(db,'SELECT payload FROM chess_matches WHERE id=?',(mid,)).fetchone()
        if not row:return 404,dict(error='Transmissão indisponível.')
        g=json.loads(row[0])
        if not visible(s,g,now):return 404,dict(error='Transmissão encerrada ou privada.')
        b=c.board(g);turn='w' if b.turn else 'b';remaining=dict(g['remaining'])
        if not g['result'] and g['minutes'] and not(g['mode']=='ai' and not g['players'][turn]):
            remaining[turn]=max(0,remaining[turn]-max(0,time.time()-g['clock_at']))
        equipment={side:chess_shop.state(db,sql,p)['equipped'] if p else dict(chess_shop.DEFAULTS) for side,p in g['players'].items()}
        host='w' if g['players']['w'] else 'b'
        result=g['result']
        return 200,dict(match=dict(summary(g,set()),moves=g['moves'],turn=turn,remaining=remaining,clock_running=bool(g['minutes'] and not result and not(g['mode']=='ai' and not g['players'][turn])),result=None if not result else dict(winner=result['winner'],reason=result['reason']),equipment=equipment,board=equipment[host]['board'],scene=equipment[host]['scene']))
