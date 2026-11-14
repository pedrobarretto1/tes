"""Clan social foundation. All membership and chat authority lives here."""
import json, math, secrets, time, re

LIMIT=30
TTL=7*86400
FIELDS={'points':1000000,'wins':1000000,'losses':1000000,'rate':100,'level':10000,'max_losses':1000000,'games':1000000}
LABELS={'points':'PH mínimo','wins':'Vitórias mínimas','losses':'Derrotas mínimas','rate':'Taxa de vitória (%)','level':'Nível mínimo','max_losses':'Derrotas máximas','games':'Partidas mínimas'}
EMBLEMS=('crown','shield','knight','rook','star','moon','jerusalem')
CREST_COLORS=('gold','silver','bronze','crimson','sapphire','emerald','ivory','obsidian','violet','copper','wine','steel')
CREST_STYLES=('royal','fortress','dark','sacred','ancient','ornate')
def default_crest(emblem='shield'):
    return dict(symbol=emblem,symbol_color='gold',frame_style='royal',frame_color='gold',background_color={'crown':'bronze','knight':'wine','star':'sapphire','moon':'sapphire'}.get(emblem,'steel'))
def validate_crest(raw):
    if not isinstance(raw,dict) or set(raw)!=set(default_crest()):raise ValueError('Configuração do brasão inválida.')
    for k,allowed in (('symbol',EMBLEMS),('symbol_color',CREST_COLORS),('frame_style',CREST_STYLES),('frame_color',CREST_COLORS),('background_color',CREST_COLORS)):
        if raw[k] not in allowed:raise ValueError('Opção de brasão inválida: '+k)
    return dict(raw)
def saved_crest(db,sql,cid,emblem):
    row=sql(db,'SELECT design FROM clan_crests WHERE clan_id=?',(cid,)).fetchone()
    if row:
        try:return validate_crest(json.loads(row[0]))
        except (ValueError,TypeError):pass
    return default_crest(emblem)
def save_crest(db,sql,cid,design):
    sql(db,'INSERT INTO clan_crests(clan_id,design) VALUES(?,?) ON CONFLICT(clan_id) DO UPDATE SET design=excluded.design',(cid,json.dumps(design)))
    sql(db,'UPDATE clans SET emblem=? WHERE id=?',(design['symbol'],cid))
ACHIEVEMENTS=('first_win','ten_wins','streak5','honor20','friends5','triple_king','cup_champion')
def setup(db,sql):
    for q in (
        "CREATE TABLE IF NOT EXISTS clan_guard (id INTEGER PRIMARY KEY)",
        "CREATE TABLE IF NOT EXISTS clans (id TEXT PRIMARY KEY, name TEXT NOT NULL, name_key TEXT NOT NULL UNIQUE, tag TEXT NOT NULL, tag_key TEXT NOT NULL UNIQUE, description TEXT NOT NULL, emblem TEXT NOT NULL, owner TEXT NOT NULL, requirements TEXT NOT NULL, created_at DOUBLE PRECISION NOT NULL)",
        "CREATE TABLE IF NOT EXISTS clan_crests (clan_id TEXT PRIMARY KEY REFERENCES clans(id) ON DELETE CASCADE, design TEXT NOT NULL)",
        "CREATE TABLE IF NOT EXISTS clan_members (player_id TEXT PRIMARY KEY, clan_id TEXT NOT NULL REFERENCES clans(id), joined_at DOUBLE PRECISION NOT NULL)",
        "CREATE TABLE IF NOT EXISTS clan_roles (player_id TEXT PRIMARY KEY REFERENCES clan_members(player_id) ON DELETE CASCADE, role TEXT NOT NULL CHECK(role IN ('captain','vice')))",
        "CREATE TABLE IF NOT EXISTS clan_reports (id TEXT PRIMARY KEY, clan_id TEXT NOT NULL REFERENCES clans(id) ON DELETE CASCADE, author TEXT NOT NULL, target TEXT NOT NULL, status TEXT NOT NULL, history TEXT NOT NULL, decision TEXT, note TEXT NOT NULL, created_at DOUBLE PRECISION NOT NULL, updated_at DOUBLE PRECISION NOT NULL)",
        "CREATE TABLE IF NOT EXISTS clan_penalties (clan_id TEXT NOT NULL REFERENCES clans(id) ON DELETE CASCADE, player_id TEXT NOT NULL, until_at DOUBLE PRECISION NOT NULL, reason TEXT NOT NULL, PRIMARY KEY(clan_id,player_id))",
        "CREATE INDEX IF NOT EXISTS clan_reports_clan_idx ON clan_reports(clan_id,status,updated_at)",
        "CREATE INDEX IF NOT EXISTS clan_reports_target_idx ON clan_reports(target,updated_at)",
        "CREATE TABLE IF NOT EXISTS clan_requests (id TEXT PRIMARY KEY, clan_id TEXT NOT NULL REFERENCES clans(id), player_id TEXT NOT NULL, kind TEXT NOT NULL, status TEXT NOT NULL, created_at DOUBLE PRECISION NOT NULL, updated_at DOUBLE PRECISION NOT NULL)",
        "CREATE TABLE IF NOT EXISTS clan_messages (id TEXT PRIMARY KEY, clan_id TEXT NOT NULL REFERENCES clans(id), author TEXT NOT NULL, body TEXT NOT NULL, created_at DOUBLE PRECISION NOT NULL)",
        "CREATE INDEX IF NOT EXISTS clan_members_clan_idx ON clan_members(clan_id)",
        "CREATE INDEX IF NOT EXISTS clan_requests_clan_idx ON clan_requests(clan_id,status)",
        "CREATE INDEX IF NOT EXISTS clan_requests_player_idx ON clan_requests(player_id,status)",
        "CREATE INDEX IF NOT EXISTS clan_messages_clan_idx ON clan_messages(clan_id,created_at,id)",
        "CREATE UNIQUE INDEX IF NOT EXISTS clan_pending_unique ON clan_requests(clan_id,player_id) WHERE status='pending'",
    ):sql(db,q)
    sql(db,'INSERT INTO clan_guard(id) VALUES(1) ON CONFLICT(id) DO NOTHING')
STATS_SQL="""SELECT p.id,p.name,p.points,p.wins,p.losses,p.draws,
 COALESCE(c.completed,0),COALESCE(j.completed,0),
 (SELECT COUNT(*) FROM achievements a WHERE a.player_id=p.id AND a.code IN ('first_win','ten_wins','streak5','honor20','friends5','triple_king','cup_champion'))
 FROM players p LEFT JOIN cosmetics c ON c.player_id=p.id LEFT JOIN journey j ON j.player_id=p.id"""
def stat_row(r):
    pid,name,points,wins,losses,draws,completed,chapters,earned=r
    xp=10*wins+3*draws+2*completed+25*earned+50*chapters
    return dict(id=pid,name=name,points=points,wins=wins,losses=losses,draws=draws,games=wins+losses+draws,rate=100*wins/(wins+losses+draws) if wins+losses+draws else None,level=1+math.isqrt(xp//50),xp=xp)
def stats(db,sql,pid):
    r=sql(db,STATS_SQL+' WHERE p.id=?',(pid,)).fetchone()
    return stat_row(r) if r else None
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
    d['requirements']=json.loads(d['requirements']);d['crest']=saved_crest(db,sql,cid,d['emblem']);return d
def members(db,sql,cid):
    return [stat_row(r) for r in sql(db,STATS_SQL+' JOIN clan_members m ON m.player_id=p.id WHERE m.clan_id=? ORDER BY m.joined_at,p.id',(cid,)).fetchall()]
# The owner column is the single source of truth for the King.
ROLE_RANK={'member':0,'captain':1,'vice':2,'king':3}
def role(db,sql,c,pid):
    if not c or member(db,sql,pid)!=c['id']:return None
    if c['owner']==pid:return 'king'
    r=sql(db,'SELECT role FROM clan_roles WHERE player_id=?',(pid,)).fetchone()
    return r[0] if r else 'member'
def public_identity(db,sql,pid):
    r=sql(db,"SELECT c.id,c.name,c.tag,CASE WHEN c.owner=m.player_id THEN 'king' ELSE COALESCE(r.role,'member') END FROM clan_members m JOIN clans c ON c.id=m.clan_id LEFT JOIN clan_roles r ON r.player_id=m.player_id WHERE m.player_id=?",(pid,)).fetchone()
    return dict(zip(('id','name','tag','role'),r)) if r else None
def tournament_block(db,sql,cid,pid,now=None):
    """Mandatory guard for future internal tournament create/join/play APIs."""
    now=time.time() if now is None else now
    r=sql(db,'SELECT until_at,reason FROM clan_penalties WHERE clan_id=? AND player_id=? AND until_at>?',(cid,pid,now)).fetchone()
    return dict(until=r[0],reason=r[1]) if r else None
def vice_ids(db,sql,cid):
    return [r[0] for r in sql(db,"SELECT m.player_id FROM clan_members m JOIN clan_roles r ON r.player_id=m.player_id WHERE m.clan_id=? AND r.role='vice' ORDER BY m.joined_at,m.player_id",(cid,)).fetchall()]
def report_views(db,sql,c,pid):
    rank=ROLE_RANK.get(role(db,sql,c,pid),-1)
    if rank<1:return []
    rows=sql(db,'SELECT id,author,target,status,history,decision,note,created_at,updated_at FROM clan_reports WHERE clan_id=? ORDER BY updated_at DESC LIMIT 100',(c['id'],)).fetchall()
    out=[]
    for rid,author,target,status,history,decision,note,created,updated in rows:
        if target==pid or (rank==1 and author!=pid):continue
        a=stats(db,sql,author);t=stats(db,sql,target)
        can_reply=status=='returned' and rank!=3 and (rank==2 or (author==pid and not [v for v in vice_ids(db,sql,c['id']) if v!=target]))
        out.append(dict(id=rid,author=author,author_name=a['name'] if a else 'Ex-membro',target=target,target_name=t['name'] if t else 'Ex-membro',status=status,history=json.loads(history),decision=decision,note=note,created_at=created,updated_at=updated,can_reply=can_reply,can_decide=rank==3 and status=='open',can_reopen=rank==3 and status=='returned'))
    return out
def own_decisions(db,sql,pid):
    return [dict(id=r[0],clan_name=r[1],decision=r[2],note=r[3],updated_at=r[4],until=json.loads(r[5])[-1].get('until')) for r in sql(db,"SELECT r.id,c.name,r.decision,r.note,r.updated_at,r.history FROM clan_reports r JOIN clans c ON c.id=r.clan_id WHERE r.target=? AND r.status='resolved' ORDER BY r.updated_at DESC LIMIT 30",(pid,)).fetchall()]
def remove_member(db,sql,cid,pid):
    sql(db,'DELETE FROM clan_roles WHERE player_id=?',(pid,))
    sql(db,'DELETE FROM clan_members WHERE player_id=? AND clan_id=?',(pid,cid))
def report_text(value,required=True):
    if not isinstance(value,str) or len(value.strip())>1000 or (required and not value.strip()):raise ValueError('Escreva uma mensagem de 1 a 1000 caracteres.')
    return value.strip()
def summary(db,sql,c,pid,full=False):
    m=members(db,sql,c['id']);p=stats(db,sql,pid)
    d=dict(c,count=len(m),level=round(sum(x['level'] for x in m)/len(m),1) if m else 0,checks=check(p,c['requirements']),capacity=LIMIT)
    d['eligible']=all(x['ok'] for x in d['checks'])
    d['pending']=bool(sql(db,"SELECT 1 FROM clan_requests WHERE clan_id=? AND player_id=? AND status='pending' AND created_at>?",(c['id'],pid,time.time()-TTL)).fetchone())
    if full:
        roles=dict(sql(db,'SELECT r.player_id,r.role FROM clan_roles r JOIN clan_members m ON m.player_id=r.player_id WHERE m.clan_id=?',(c['id'],)).fetchall())
        for p in m:
            p['role']='king' if p['id']==c['owner'] else roles.get(p['id'],'member')
        d['members']=m
        d['role']=role(db,sql,c,pid)
        d['penalty']=tournament_block(db,sql,c['id'],pid)
        if ROLE_RANK[d['role']]>=1:
            d['reports']=report_views(db,sql,c,pid)
    return d
def notices(db,sql,pid):
    # Only the owner receives applications; only the invited player receives invitations.
    rows=sql(db,"SELECT r.id,r.kind,r.player_id,r.clan_id,r.created_at,c.name,c.owner FROM clan_requests r JOIN clans c ON c.id=r.clan_id WHERE r.status='pending' AND r.created_at>? AND ((r.kind='apply' AND c.owner=?) OR (r.kind='invite' AND r.player_id=?)) ORDER BY r.created_at DESC LIMIT 100",(time.time()-TTL,pid,pid)).fetchall()
    result=[]
    for rid,kind,target,cid,created,name,owner in rows:
        p=stats(db,sql,target);c=clan(db,sql,cid)
        if p and c:result.append(dict(id=rid,kind=kind,clan_id=cid,clan_name=name,crest=c['crest'],royal=kind=='invite',profile=p,checks=check(p,c['requirements']),created_at=created))
    return result
def account(db,sql,pid):
    return bool(sql(db,'SELECT 1 FROM accounts WHERE player_id=?',(pid,)).fetchone())
def state(db,sql,pid,q='',offset=0):
    cid=member(db,sql,pid);mine=clan(db,sql,cid) if cid else None
    query='%'+q.casefold().replace('%','').replace('_','')+'%'
    rows=sql(db,'SELECT id FROM clans WHERE name_key LIKE ? OR tag_key LIKE ? ORDER BY created_at DESC,id LIMIT 21 OFFSET ?',(query,query,offset)).fetchall()
    return dict(me=stats(db,sql,pid),account=account(db,sql,pid),mine=summary(db,sql,mine,pid,True) if mine else None,clans=[summary(db,sql,clan(db,sql,r[0]),pid) for r in rows[:20]],more=len(rows)>20,requests=notices(db,sql,pid),decisions=own_decisions(db,sql,pid))
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
            try:
                req=requirements(d.get('requirements',{}))
                design=validate_crest(d['crest']) if 'crest' in d else default_crest(emblem)
            except ValueError as e:return err(str(e))
            if sql(db,'SELECT 1 FROM clans WHERE name_key=? OR tag_key=?',(name.casefold(),tag.casefold())).fetchone():return err('Nome ou sigla já utilizados.',409)
            cid=secrets.token_hex(12)
            sql(db,'INSERT INTO clans VALUES(?,?,?,?,?,?,?,?,?,?)',(cid,name,name.casefold(),tag,tag.casefold(),desc,emblem,pid,json.dumps(req),now))
            save_crest(db,sql,cid,design)
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
            if op=='apply' and not all(x['ok'] for x in check(p,c['requirements'])):return err('O jogador não cumpre os requisitos.',409)
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
                if not p or not account(db,sql,target) or member(db,sql,target) or len(members(db,sql,c['id']))>=LIMIT or (r[2]=='apply' and not all(x['ok'] for x in check(p,c['requirements']))):return err('O candidato não atende mais aos requisitos ou não há vaga.',409)
                sql(db,'INSERT INTO clan_members VALUES(?,?,?)',(target,c['id'],now))
                sql(db,"UPDATE clan_requests SET status='closed',updated_at=? WHERE player_id=? AND status='pending' AND id<>?",(now,target,d['id']))
            sql(db,'UPDATE clan_requests SET status=?,updated_at=? WHERE id=?',('accepted' if d['accept'] else 'declined',now,d['id']))
            # Inform the other party; the actionable request itself is separate.
            s.notify(db,target if r[2]=='apply' else c['owner'],pid,'clan_accepted' if d['accept'] else 'clan_declined')
        elif op in ('report','report-return','report-reply','report-decide','report-reopen','promote'):
            if not mine:return err('Você não pertence a um clã.',409)
            rank=ROLE_RANK[role(db,sql,mine,pid)]
            if rank<1:return err('Somente oficiais podem administrar denúncias.',403)
            if op=='promote':
                if rank!=3:return err('Somente o Rei pode alterar cargos.',403)
                target=str(d.get('target',''));new=d.get('role')
                if target==pid or member(db,sql,target)!=cid or new not in ('member','captain','vice'):return err('Cargo ou membro inválido.')
                if new=='member':sql(db,'DELETE FROM clan_roles WHERE player_id=?',(target,))
                else:sql(db,'INSERT INTO clan_roles(player_id,role) VALUES(?,?) ON CONFLICT(player_id) DO UPDATE SET role=excluded.role',(target,new))
                s.notify(db,target,pid,'clan_role')
            elif op=='report':
                target=str(d.get('target',''))
                if target==pid or member(db,sql,target)!=cid or ROLE_RANK[role(db,sql,mine,target)]>=rank:return err('Denuncie apenas membros de cargo inferior.',403)
                try:reason=report_text(d.get('reason'))
                except ValueError as e:return err(str(e))
                if sql(db,"SELECT 1 FROM clan_reports WHERE clan_id=? AND author=? AND target=? AND status IN ('open','returned')",(cid,pid,target)).fetchone():return err('Já existe uma denúncia em andamento.',409)
                if sql(db,'SELECT COUNT(*) FROM clan_reports WHERE author=? AND created_at>?',(pid,now-86400)).fetchone()[0]>=10:return err('Limite diário de denúncias.',429)
                history=[dict(actor=pid,name=stats(db,sql,pid)['name'],kind='report',text=reason,at=now)]
                sql(db,'INSERT INTO clan_reports VALUES(?,?,?,?,?,?,?,?,?,?)',(secrets.token_hex(12),cid,pid,target,'open',json.dumps(history),None,'',now,now))
                if pid!=mine['owner']:s.notify(db,mine['owner'],pid,'clan_report')
            else:
                r=sql(db,'SELECT id,author,target,status,history FROM clan_reports WHERE id=? AND clan_id=?',(str(d.get('id','')),cid)).fetchone()
                if not r:return err('Denúncia indisponível.',404)
                rid,author,target,status,raw=r;history=json.loads(raw)
                if target==pid:return err('Você não pode analisar sua própria denúncia.',403)
                if op=='report-reply':
                    if status!='returned' or not (rank==2 or (rank==1 and author==pid and not [v for v in vice_ids(db,sql,cid) if v!=target])):return err('Somente o Vice-capitão responsável pode responder uma devolução.',403)
                    try:message=report_text(d.get('message'))
                    except ValueError as e:return err(str(e))
                    history.append(dict(actor=pid,name=stats(db,sql,pid)['name'],kind='reply',text=message,at=now))
                    sql(db,"UPDATE clan_reports SET status='open',history=?,updated_at=? WHERE id=?",(json.dumps(history),now,rid))
                    s.notify(db,mine['owner'],pid,'clan_report_reply')
                else:
                    if rank!=3:return err('Somente o Rei decide denúncias.',403)
                    if op=='report-reopen':
                        if status!='returned':return err('Denúncia não está devolvida.',409)
                        try:message=report_text(d.get('message'))
                        except ValueError as e:return err(str(e))
                        history.append(dict(actor=pid,name=stats(db,sql,pid)['name'],kind='reopen',text=message,at=now))
                        sql(db,"UPDATE clan_reports SET status='open',history=?,updated_at=? WHERE id=?",(json.dumps(history),now,rid))
                        return 200,state(db,sql,pid)
                    if status!='open':return err('Denúncia não está aguardando decisão.',409)
                    if op=='report-return':
                        try:message=report_text(d.get('message'))
                        except ValueError as e:return err(str(e))
                        recipients=[v for v in vice_ids(db,sql,cid) if v!=target]
                        if not recipients and member(db,sql,author)==cid and author!=pid and ROLE_RANK[role(db,sql,mine,author)]>=1:recipients=[author]
                        if not recipients:return err('Não há oficial disponível para responder. O Rei pode decidir diretamente.',409)
                        history.append(dict(actor=pid,name=stats(db,sql,pid)['name'],kind='return',text=message,at=now))
                        sql(db,"UPDATE clan_reports SET status='returned',history=?,updated_at=? WHERE id=?",(json.dumps(history),now,rid))
                        for v in recipients:s.notify(db,v,pid,'clan_report_return')
                    else:
                        decision=d.get('decision')
                        if decision not in ('keep','expel','suspend'):return err('Decisão inválida.')
                        try:note=report_text(d.get('message',''),False)
                        except ValueError as e:return err(str(e))
                        if decision!='keep' and (member(db,sql,target)!=cid or target==mine['owner']):return err('O jogador não é um membro elegível para punição.',409)
                        if decision=='suspend':
                            amount=d.get('duration');unit=d.get('unit')
                            if type(amount) is not int or amount<1 or unit not in ('hours','days') or amount*(24 if unit=='days' else 1)>8760:return err('Escolha de 1 hora a 365 dias.')
                            until=now+amount*(86400 if unit=='days' else 3600)
                            sql(db,'INSERT INTO clan_penalties(clan_id,player_id,until_at,reason) VALUES(?,?,?,?) ON CONFLICT(clan_id,player_id) DO UPDATE SET until_at=excluded.until_at,reason=excluded.reason',(cid,target,until,note))
                        if decision=='expel':remove_member(db,sql,cid,target)
                        history.append(dict(actor=pid,name=stats(db,sql,pid)['name'],kind=decision,text=note,at=now,until=until if decision=='suspend' else None))
                        sql(db,"UPDATE clan_reports SET status='resolved',history=?,decision=?,note=?,updated_at=? WHERE id=?",(json.dumps(history),decision,note,now,rid))
                        s.notify(db,target,pid,'clan_report_decision')
        elif op in ('edit','crest','kick','transfer','dissolve','leave'):
            if not mine:return err('Você não pertence a um clã.',409)
            owner=mine['owner']==pid
            if op in ('edit','crest') and ROLE_RANK[role(db,sql,mine,pid)]<2:return err('Somente Rei e Vice-capitão podem personalizar.',403)
            if op not in ('leave','edit','crest') and not owner:return err('Somente o Rei pode administrar.',403)
            if op=='crest':
                try:design=validate_crest(d.get('crest'))
                except ValueError as e:return err(str(e))
                save_crest(db,sql,cid,design)
            elif op=='edit':
                try:req=requirements(d.get('requirements',{}))
                except ValueError as e:return err(str(e))
                desc=str(d.get('description',mine['description'])).strip()
                if len(desc)>300:return err('Descrição muito longa.')
                sql(db,'UPDATE clans SET requirements=?,description=? WHERE id=?',(json.dumps(req),desc,cid))
            elif op in ('kick','transfer'):
                target=str(d.get('target',''))
                if target==pid or member(db,sql,target)!=cid:return err('Membro inválido.')
                if op=='kick':remove_member(db,sql,cid,target)
                else:
                    sql(db,'DELETE FROM clan_roles WHERE player_id IN (?,?)',(pid,target))
                    sql(db,'UPDATE clans SET owner=? WHERE id=?',(target,cid))
            elif op=='leave':
                if owner:return err('Transfira a liderança ou dissolva o clã.',409)
                remove_member(db,sql,cid,pid)
            else:
                # Explicit owner action; only an empty (owner-only) clan can dissolve.
                if len(members(db,sql,cid))!=1:return err('Transfira a liderança ou remova os membros primeiro.',409)
                for table in ('clan_messages','clan_requests','clan_reports','clan_penalties','clan_members','clan_crests'):sql(db,'DELETE FROM '+table+' WHERE clan_id=?',(cid,))
                sql(db,'DELETE FROM clans WHERE id=?',(cid,))
        elif op in ('chat','send'):
            if not mine:return err('Somente membros podem acessar o chat.',403)
            if op=='send':
                body=str(d.get('body','')).strip()
                if not 1<=len(body)<=500:return err('Mensagem deve ter de 1 a 500 caracteres.')
                if sql(db,'SELECT COUNT(*) FROM clan_messages WHERE author=? AND created_at>?',(pid,now-10)).fetchone()[0]>=5:return err('Envie mensagens mais devagar.',429)
                sql(db,'INSERT INTO clan_messages VALUES(?,?,?,?,?)',(secrets.token_hex(12),cid,pid,body,now))
            rows=sql(db,'SELECT m.id,m.author,p.name,m.body,m.created_at,CASE WHEN cm.player_id IS NULL THEN NULL WHEN c.owner=m.author THEN 'king' ELSE COALESCE(cr.role,'member') END FROM clan_messages m JOIN players p ON p.id=m.author JOIN clans c ON c.id=m.clan_id LEFT JOIN clan_members cm ON cm.player_id=m.author AND cm.clan_id=m.clan_id LEFT JOIN clan_roles cr ON cr.player_id=cm.player_id WHERE m.clan_id=? ORDER BY m.created_at DESC,m.id DESC LIMIT 50',(cid,)).fetchall()
            return 200,{'clan':cid,'messages':[dict(zip(('id','author','name','body','created_at','role'),r)) for r in reversed(rows)]}
        else:return err('Ação desconhecida.',404)
        return 200,state(db,sql,pid)
