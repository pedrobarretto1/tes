"""Clan social foundation. All membership and chat authority lives here."""
import json, math, secrets, time, re

LIMIT=30
TTL=7*86400
FIELDS={'points':1000000,'wins':1000000,'losses':1000000,'rate':100,'level':10000,'max_losses':1000000,'games':1000000}
LABELS={'points':'PH mínimo','wins':'Vitórias mínimas','losses':'Derrotas mínimas','rate':'Taxa de vitória (%)','level':'Nível mínimo','max_losses':'Derrotas máximas','games':'Partidas mínimas'}
EMBLEMS=('crown','shield','knight','rook','star','moon')
ACHIEVEMENTS=('first_win','ten_wins','streak5','honor20','friends5','triple_king','cup_champion')
def setup(db,sql):
    for q in (
        "CREATE TABLE IF NOT EXISTS clan_guard (id INTEGER PRIMARY KEY)",
        "CREATE TABLE IF NOT EXISTS clans (id TEXT PRIMARY KEY, name TEXT NOT NULL, name_key TEXT NOT NULL UNIQUE, tag TEXT NOT NULL, tag_key TEXT NOT NULL UNIQUE, description TEXT NOT NULL, emblem TEXT NOT NULL, owner TEXT NOT NULL, requirements TEXT NOT NULL, created_at DOUBLE PRECISION NOT NULL)",
        "CREATE TABLE IF NOT EXISTS clan_members (player_id TEXT PRIMARY KEY, clan_id TEXT NOT NULL REFERENCES clans(id), joined_at DOUBLE PRECISION NOT NULL)",
        "CREATE TABLE IF NOT EXISTS clan_requests (id TEXT PRIMARY KEY, clan_id TEXT NOT NULL REFERENCES clans(id), player_id TEXT NOT NULL, kind TEXT NOT NULL, status TEXT NOT NULL, created_at DOUBLE PRECISION NOT NULL, updated_at DOUBLE PRECISION NOT NULL)",
        "CREATE TABLE IF NOT EXISTS clan_messages (id TEXT PRIMARY KEY, clan_id TEXT NOT NULL REFERENCES clans(id), author TEXT NOT NULL, body TEXT NOT NULL, created_at DOUBLE PRECISION NOT NULL)",
        "CREATE INDEX IF NOT EXISTS clan_members_clan_idx ON clan_members(clan_id)",
        "CREATE INDEX IF NOT EXISTS clan_requests_clan_idx ON clan_requests(clan_id,status)",
        "CREATE INDEX IF NOT EXISTS clan_requests_player_idx ON clan_requests(player_id,status)",
        "CREATE INDEX IF NOT EXISTS clan_messages_clan_idx ON clan_messages(clan_id,created_at,id)",
        "CREATE UNIQUE INDEX IF NOT EXISTS clan_pending_unique ON clan_requests(clan_id,player_id) WHERE status='pending'",
    ):sql(db,q)
    sql(db,'INSERT INTO clan_guard(id) VALUES(1) ON CONFLICT(id) DO NOTHING')
def stats(db,sql,pid):
    r=sql(db,'SELECT name,points,wins,losses,draws FROM players WHERE id=?',(pid,)).fetchone()
    if not r:return None
    name,points,wins,losses,draws=r
    c=sql(db,'SELECT completed FROM cosmetics WHERE player_id=?',(pid,)).fetchone()
    j=sql(db,'SELECT completed FROM journey WHERE player_id=?',(pid,)).fetchone()
    earned=sum(row[0] in ACHIEVEMENTS for row in sql(db,'SELECT code FROM achievements WHERE player_id=?',(pid,)).fetchall())
    completed=c[0] if c else 0
    xp=10*wins+3*draws+2*completed+25*earned+50*(j[0] if j else 0)
    return dict(id=pid,name=name,points=points,wins=wins,losses=losses,draws=draws,games=wins+losses+draws,rate=100*wins/(wins+losses+draws) if wins+losses+draws else None,level=1+math.isqrt(xp//50),xp=xp)
def requirements(raw):
    if not isinstance(raw,dict) or set(raw)-set(FIELDS):raise ValueError('Requisitos inválidos.')
    out={}
    for k,maximum in FIELDS.items():
        v=raw.get(k)
        if v is not None and (type(v) is not int or not 0<=v<=maximum):raise ValueError('Requisito inválido: '+LABELS[k])
        out[k]=v
    if out['losses'] is not None and out['max_losses'] is not None and out['losses']>out['max_losses']:raise ValueError('Mínimo de derrotas maior que o máximo.')
    return out
def check(p,req):
    return [dict(key=k,label=LABELS[k],required=v,actual=p['losses' if k=='max_losses' else k],ok=(p['losses']<=v if k=='max_losses' else p[k] is not None and p[k]>=v)) for k,v in req.items() if v is not None]
def member(db,sql,pid):
    row=sql(db,'SELECT clan_id FROM clan_members WHERE player_id=?',(pid,)).fetchone()
    return row[0] if row else None
def clan(db,sql,cid):
    r=sql(db,'SELECT id,name,tag,description,emblem,owner,requirements,created_at FROM clans WHERE id=?',(cid,)).fetchone()
    if not r:return None
    d=dict(zip(('id','name','tag','description','emblem','owner','requirements','created_at'),r))
    d['requirements']=json.loads(d['requirements']);return d
def members(db,sql,cid):
    return [p for r in sql(db,'SELECT player_id FROM clan_members WHERE clan_id=? ORDER BY joined_at,player_id',(cid,)).fetchall() if (p:=stats(db,sql,r[0]))]
def summary(db,sql,c,pid,full=False):
    m=members(db,sql,c['id']);p=stats(db,sql,pid)
    d=dict(c,count=len(m),level=round(sum(x['level'] for x in m)/len(m),1) if m else 0,checks=check(p,c['requirements']),capacity=LIMIT)
    d['eligible']=all(x['ok'] for x in d['checks'])
    d['pending']=bool(sql(db,"SELECT 1 FROM clan_requests WHERE clan_id=? AND player_id=? AND status='pending' AND created_at>?",(c['id'],pid,time.time()-TTL)).fetchone())
    if full:d['members']=m
    return d
def notices(db,sql,pid):
    # Only the owner receives applications; only the invited player receives invitations.
    rows=sql(db,"SELECT r.id,r.kind,r.player_id,r.clan_id,r.created_at,c.name,c.owner FROM clan_requests r JOIN clans c ON c.id=r.clan_id WHERE r.status='pending' AND r.created_at>? AND ((r.kind='apply' AND c.owner=?) OR (r.kind='invite' AND r.player_id=?)) ORDER BY r.created_at DESC LIMIT 100",(time.time()-TTL,pid,pid)).fetchall()
    result=[]
    for rid,kind,target,cid,created,name,owner in rows:
        p=stats(db,sql,target);c=clan(db,sql,cid)
        if p and c:result.append(dict(id=rid,kind=kind,clan_id=cid,clan_name=name,profile=p,checks=check(p,c['requirements']),created_at=created))
    return result
def account(db,sql,pid):
    return bool(sql(db,'SELECT 1 FROM accounts WHERE player_id=?',(pid,)).fetchone())
def state(db,sql,pid,q='',offset=0):
    cid=member(db,sql,pid);mine=clan(db,sql,cid) if cid else None
    query='%'+q.casefold().replace('%','').replace('_','')+'%'
    rows=sql(db,'SELECT id FROM clans WHERE name_key LIKE ? OR tag_key LIKE ? ORDER BY created_at DESC,id LIMIT 21 OFFSET ?',(query,query,offset)).fetchall()
    return dict(me=stats(db,sql,pid),account=account(db,sql,pid),mine=summary(db,sql,mine,pid,True) if mine else None,clans=[summary(db,sql,clan(db,sql,r[0]),pid) for r in rows[:20]],more=len(rows)>20,requests=notices(db,sql,pid))
def action(s,path,d,pid):
    sql=s.sql;op=path.rsplit('/',1)[-1];now=time.time()
    def err(msg,code=400):return code,{'error':msg}
    with s.database() as db:
        if op=='state':
            q=str(d.get('q',''))[:60];offset=d.get('offset',0)
            if type(offset) is not int or not 0<=offset<=10000:return err('Página inválida.')
            return 200,state(db,sql,pid,q,offset)
        if not account(db,sql,pid):return err('Entre em uma conta registrada para participar de clãs.',403)
        # Serialize membership/capacity/owner transitions across processes.
        sql(db,'UPDATE clan_guard SET id=id WHERE id=1')
        sql(db,"UPDATE clan_requests SET status='expired',updated_at=? WHERE status='pending' AND created_at<=?",(now,now-TTL))
        cid=member(db,sql,pid);mine=clan(db,sql,cid) if cid else None
        if op=='create':
            if cid:return err('Você já pertence a um clã.',409)
            name=' '.join(str(d.get('name','')).split());tag=str(d.get('tag','')).strip().upper()
            desc=str(d.get('description','')).strip();emblem=d.get('emblem','shield')
            if not 3<=len(name)<=40 or not re.fullmatch(r'[A-Z0-9]{2,6}',tag) or len(desc)>300 or emblem not in EMBLEMS:return err('Nome (3–40), sigla (2–6 letras/números), descrição ou brasão inválido.')
            try:req=requirements(d.get('requirements',{}))
            except ValueError as e:return err(str(e))
            if sql(db,'SELECT 1 FROM clans WHERE name_key=? OR tag_key=?',(name.casefold(),tag.casefold())).fetchone():return err('Nome ou sigla já utilizados.',409)
            cid=secrets.token_hex(12)
            sql(db,'INSERT INTO clans VALUES(?,?,?,?,?,?,?,?,?,?)',(cid,name,name.casefold(),tag,tag.casefold(),desc,emblem,pid,json.dumps(req),now))
            sql(db,'INSERT INTO clan_members VALUES(?,?,?)',(pid,cid,now))
            sql(db,"UPDATE clan_requests SET status='closed',updated_at=? WHERE player_id=? AND status='pending'",(now,pid))
        elif op in ('apply','invite'):
            c=clan(db,sql,str(d.get('clan',''))) if op=='apply' else mine
            target=pid if op=='apply' else str(d.get('target',''))
            if not c:return err('Clã inexistente.',404)
            if op=='invite' and c['owner']!=pid:return err('Somente o dono pode convidar.',403)
            p=stats(db,sql,target)
            if not p or not account(db,sql,target):return err('O jogador precisa de uma conta registrada.')
            if member(db,sql,target):return err('O jogador já pertence a um clã.',409)
            if len(members(db,sql,c['id']))>=LIMIT:return err('Clã lotado.',409)
            if not all(x['ok'] for x in check(p,c['requirements'])):return err('O jogador não cumpre os requisitos.',409)
            old=sql(db,"SELECT status,updated_at FROM clan_requests WHERE clan_id=? AND player_id=? ORDER BY updated_at DESC LIMIT 1",(c['id'],target)).fetchone()
            if old and old[0]=='pending':return err('Já existe um pedido pendente.',409)
            if old and old[0]=='declined' and now-old[1]<300:return err('Aguarde cinco minutos após uma recusa.',409)
            if sql(db,"SELECT COUNT(*) FROM clan_requests WHERE player_id=? AND status='pending'",(target,)).fetchone()[0]>=10:return err('Limite de pedidos pendentes.',409)
            sql(db,'INSERT INTO clan_requests VALUES(?,?,?,?,?,?,?)',(secrets.token_hex(12),c['id'],target,op,'pending',now,now))
        elif op=='respond':
            r=sql(db,"SELECT clan_id,player_id,kind FROM clan_requests WHERE id=? AND status='pending'",(str(d.get('id','')),)).fetchone()
            if not r:return err('Pedido indisponível.',409)
            c=clan(db,sql,r[0]);target=r[1]
            if (r[2]=='apply' and c['owner']!=pid) or (r[2]=='invite' and target!=pid):return err('Você não pode responder a este pedido.',403)
            if type(d.get('accept')) is not bool:return err('Resposta inválida.')
            if d['accept']:
                p=stats(db,sql,target)
                if not p or not account(db,sql,target) or member(db,sql,target) or len(members(db,sql,c['id']))>=LIMIT or not all(x['ok'] for x in check(p,c['requirements'])):return err('O candidato não atende mais aos requisitos ou não há vaga.',409)
                sql(db,'INSERT INTO clan_members VALUES(?,?,?)',(target,c['id'],now))
                sql(db,"UPDATE clan_requests SET status='closed',updated_at=? WHERE player_id=? AND status='pending' AND id<>?",(now,target,d['id']))
            sql(db,'UPDATE clan_requests SET status=?,updated_at=? WHERE id=?',('accepted' if d['accept'] else 'declined',now,d['id']))
            # Inform the other party; the actionable request itself is separate.
            s.notify(db,target if r[2]=='apply' else c['owner'],pid,'clan_accepted' if d['accept'] else 'clan_declined')
        elif op in ('edit','kick','transfer','dissolve','leave'):
            if not mine:return err('Você não pertence a um clã.',409)
            owner=mine['owner']==pid
            if op!='leave' and not owner:return err('Somente o dono pode administrar.',403)
            if op=='edit':
                try:req=requirements(d.get('requirements',{}))
                except ValueError as e:return err(str(e))
                desc=str(d.get('description',mine['description'])).strip()
                if len(desc)>300:return err('Descrição muito longa.')
                sql(db,'UPDATE clans SET requirements=?,description=? WHERE id=?',(json.dumps(req),desc,cid))
            elif op in ('kick','transfer'):
                target=str(d.get('target',''))
                if target==pid or member(db,sql,target)!=cid:return err('Membro inválido.')
                if op=='kick':sql(db,'DELETE FROM clan_members WHERE player_id=? AND clan_id=?',(target,cid))
                else:sql(db,'UPDATE clans SET owner=? WHERE id=?',(target,cid))
            elif op=='leave':
                if owner:return err('Transfira a liderança ou dissolva o clã.',409)
                sql(db,'DELETE FROM clan_members WHERE player_id=?',(pid,))
            else:
                # Explicit owner action; only an empty (owner-only) clan can dissolve.
                if len(members(db,sql,cid))!=1:return err('Transfira a liderança ou remova os membros primeiro.',409)
                for table in ('clan_messages','clan_requests','clan_members'):sql(db,'DELETE FROM '+table+' WHERE clan_id=?',(cid,))
                sql(db,'DELETE FROM clans WHERE id=?',(cid,))
        elif op in ('chat','send'):
            if not mine:return err('Somente membros podem acessar o chat.',403)
            if op=='send':
                body=str(d.get('body','')).strip()
                if not 1<=len(body)<=500:return err('Mensagem deve ter de 1 a 500 caracteres.')
                if sql(db,'SELECT COUNT(*) FROM clan_messages WHERE author=? AND created_at>?',(pid,now-10)).fetchone()[0]>=5:return err('Envie mensagens mais devagar.',429)
                sql(db,'INSERT INTO clan_messages VALUES(?,?,?,?,?)',(secrets.token_hex(12),cid,pid,body,now))
            rows=sql(db,'SELECT m.id,m.author,p.name,m.body,m.created_at FROM clan_messages m JOIN players p ON p.id=m.author WHERE m.clan_id=? ORDER BY m.created_at DESC,m.id DESC LIMIT 50',(cid,)).fetchall()
            return 200,{'clan':cid,'messages':[dict(zip(('id','author','name','body','created_at'),r)) for r in reversed(rows)]}
        else:return err('Ação desconhecida.',404)
        return 200,state(db,sql,pid)
