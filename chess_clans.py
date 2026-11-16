"""Chess realm adapter for the shared clan authority. Never writes Damas clan tables."""
import re, time
from fractions import Fraction
from types import SimpleNamespace
import clas

TABLES=('clan_guard','clans','clan_crests','clan_members','clan_roles','clan_reports','clan_penalties','clan_reports_clan_idx','clan_reports_target_idx','clan_recommendations','clan_recommendation_pending','clan_recommendation_clan_idx','clan_requests','clan_messages','clan_members_clan_idx','clan_requests_clan_idx','clan_requests_player_idx','clan_messages_clan_idx','clan_pending_unique')
NAMES=re.compile(r'\b(?:'+'|'.join(TABLES)+r')\b')
# Same level formula as Damas, with only ranked chess results and chess crowns.
STATS="""SELECT p.id,p.name,COALESCE(cp.points,1000),COALESCE(cp.wins,0),COALESCE(cp.losses,0),COALESCE(cp.draws,0),
 (SELECT COUNT(*) FROM chess_history h JOIN chess_matches cm ON cm.id=h.match_id WHERE h.player_id=p.id AND h.outcome<>'resign' AND h.delta<>0),
 (SELECT COUNT(*) FROM chess_journey cj WHERE cj.player_id=p.id),
 CASE WHEN COALESCE(cp.wins,0)>=1 THEN 1 ELSE 0 END+CASE WHEN COALESCE(cp.wins,0)>=10 THEN 1 ELSE 0 END+CASE WHEN COALESCE(cp.wins,0)+COALESCE(cp.losses,0)+COALESCE(cp.draws,0)>=20 THEN 1 ELSE 0 END
 FROM players p LEFT JOIN chess_profiles cp ON cp.player_id=p.id"""
def scoped(sql):
    def run(db,q,args=()):
        return sql(db,NAMES.sub(lambda m:'chess_'+m.group(),q.replace(clas.STATS_SQL,STATS)),args)
    return run

def setup(db,sql):
    clas.setup(db,scoped(sql))
    sql(db,"CREATE TABLE IF NOT EXISTS chess_clan_notifications (id TEXT PRIMARY KEY, recipient TEXT NOT NULL, actor TEXT NOT NULL, kind TEXT NOT NULL, created_at DOUBLE PRECISION NOT NULL, seen INTEGER NOT NULL DEFAULT 0)")
    sql(db,"CREATE INDEX IF NOT EXISTS chess_clan_notifications_recipient_idx ON chess_clan_notifications(recipient,seen,created_at)")

def identity(db,sql,pid):
    return clas.public_identity(db,scoped(sql),pid)

def pending(db,sql,pid):
    return sql(db,"SELECT COUNT(*) FROM chess_clan_requests r JOIN chess_clans c ON c.id=r.clan_id WHERE r.status='pending' AND r.created_at>? AND ((r.kind='apply' AND c.owner=?) OR (r.kind='invite' AND r.player_id=?))",(time.time()-clas.TTL,pid,pid)).fetchone()[0]+sql(db,"SELECT COUNT(*) FROM chess_clan_notifications WHERE recipient=? AND seen=0",(pid,)).fetchone()[0]

def candidates(db,sql,pid,q=''):
    # Registered accounts, including offline players; never expose login fields.
    pattern='%'+q.casefold().replace('%','').replace('_','')+'%'
    return [dict(id=r[0],name=r[1]) for r in sql(db,"SELECT p.id,p.name FROM players p JOIN accounts a ON a.player_id=p.id LEFT JOIN chess_clan_members m ON m.player_id=p.id WHERE p.id<>? AND m.player_id IS NULL AND LOWER(p.name) LIKE ? ORDER BY p.name,p.id LIMIT 50",(pid,pattern)).fetchall()]

def ranking(db,sql,pid):
    q=scoped(sql);now=time.time();out=[]
    for (cid,) in q(db,'SELECT id FROM clans').fetchall():
        c=clas.clan(db,q,cid);members=clas.members(db,q,cid)
        if not members:continue
        mean=Fraction(sum(p['level'] for p in members),len(members))
        official=len(members)>=5 and now-c['created_at']>=7*86400
        out.append((official,mean,dict(c,count=len(members),capacity=clas.LIMIT,level=round(float(mean),1),official=official)))
    out.sort(key=lambda x:(not x[0],-x[1],x[2]['name'].casefold(),x[2]['id']))
    return [x[2] for x in out[:100]]

def action(s,path,d,pid):
    import secrets
    op=path.rsplit('/',1)[-1]
    def notify(db,recipient,actor,kind):
        s.sql(db,'INSERT INTO chess_clan_notifications VALUES(?,?,?,?,?,0)',(secrets.token_hex(16),recipient,actor,kind,time.time()))
    q=scoped(s.sql)
    if op=='candidates':
        with s.database() as db:return 200,dict(candidates=candidates(db,s.sql,pid,str(d.get('q',''))[:60]))
    if op=='read-notices':
        with s.database() as db:s.sql(db,'UPDATE chess_clan_notifications SET seen=1 WHERE recipient=?',(pid,))
        op='state'
    code,data=clas.action(SimpleNamespace(sql=q,database=s.database,notify=notify),'/clans/'+op,d,pid)
    if code==200 and 'mine' in data:
        with s.database() as db:
            data['candidates']=candidates(db,s.sql,pid)
            data['notices']=[dict(kind=r[0],name=r[1]) for r in s.sql(db,"SELECT n.kind,p.name FROM chess_clan_notifications n JOIN players p ON p.id=n.actor WHERE n.recipient=? AND n.seen=0 ORDER BY n.created_at DESC LIMIT 50",(pid,)).fetchall()]
            if d.get('ranking') is True:data['ranking']=ranking(db,s.sql,pid)
    return code,data
