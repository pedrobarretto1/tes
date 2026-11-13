from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import json, secrets, threading, time, os, hashlib, sqlite3, subprocess, sys, unicodedata
from contextlib import contextmanager

ROOMS = {}
PRESENCE = {}
INVITES = {}
LOCK = threading.Lock()
TTL = 60 * 60 * 4
BASE = Path(__file__).resolve().parent

# Persistent PostgreSQL when DATABASE_URL is configured; temporary SQLite otherwise.
DATABASE_URL=os.environ.get('DATABASE_URL','')
if DATABASE_URL:
    try: import psycopg
    except ImportError:
        subprocess.check_call([sys.executable,'-m','pip','install','psycopg[binary]==3.2.13'])
        import psycopg
@contextmanager
def database():
    db=psycopg.connect(DATABASE_URL) if DATABASE_URL else sqlite3.connect(BASE/'ranking.sqlite3')
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally: db.close()
def sql(db,query,args=()):
    return db.execute(query.replace('?', '%s') if DATABASE_URL else query,args)
def setup():
    with database() as db:
        sql(db,'CREATE TABLE IF NOT EXISTS players (id TEXT PRIMARY KEY, name TEXT NOT NULL, points INTEGER NOT NULL DEFAULT 1000, wins INTEGER NOT NULL DEFAULT 0, losses INTEGER NOT NULL DEFAULT 0, draws INTEGER NOT NULL DEFAULT 0)')
        sql(db,'CREATE TABLE IF NOT EXISTS results (id TEXT PRIMARY KEY)')
        sql(db,'CREATE TABLE IF NOT EXISTS friendships (sender TEXT NOT NULL, receiver TEXT NOT NULL, state TEXT NOT NULL, PRIMARY KEY(sender,receiver))')
        sql(db,'CREATE TABLE IF NOT EXISTS match_history (match_id TEXT NOT NULL, player_id TEXT NOT NULL, opponent TEXT NOT NULL, outcome TEXT NOT NULL, delta INTEGER NOT NULL, played_at TEXT NOT NULL, PRIMARY KEY(match_id,player_id))')
def profile(d):
    name=' '.join(str(d.get('name','')).split())[:24]
    token=str(d.get('profileToken',''))
    if not name or not 32<=len(token)<=128: return None
    pid=hashlib.sha256(token.encode()).hexdigest()
    with database() as db:
        sql(db,'INSERT INTO players(id,name) VALUES(?,?) ON CONFLICT(id) DO UPDATE SET name=excluded.name',(pid,name))
    return pid
def finish(r,w,resigned=False):
    if r.get('winner') is not None: return
    p=r['profiles']
    if r.get('ranked',True) and len(p)==2 and p[1] and p[-1] and p[1]!=p[-1]:
        with database() as db:
            inserted=sql(db,'INSERT INTO results(id) VALUES(?) ON CONFLICT(id) DO NOTHING',(r['match'],)).rowcount
            if inserted:
                for side in (1,-1):
                    delta=5 if w==0 else 25 if w==side else (-20 if resigned else -15)
                    sql(db,'UPDATE players SET points=CASE WHEN points+? < 0 THEN 0 ELSE points+? END,wins=wins+?,losses=losses+?,draws=draws+? WHERE id=?',(delta,delta,int(w==side),int(w==-side),int(w==0),p[side]))
                    opponent=sql(db,'SELECT name FROM players WHERE id=?',(p[-side],)).fetchone()[0]
                    outcome='draw' if w==0 else 'win' if w==side else 'resign' if resigned else 'loss'
                    sql(db,'INSERT INTO match_history(match_id,player_id,opponent,outcome,delta,played_at) VALUES(?,?,?,?,?,?)',(r['match'],p[side],opponent,outcome,delta,time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())))
    r['winner']=w
def initial():
    return [(-1 if i//8<3 else 1 if i//8>4 else 0) if (i//8+i%8)%2 else 0 for i in range(64)]
DIR=((1,1),(1,-1),(-1,1),(-1,-1))
def inside(r,c): return 0<=r<8 and 0<=c<8
def legal(b,s,rule):
    caps=[]; quiet=[]
    for i,p in enumerate(b):
        if not p or p*s<=0: continue
        def walk(board,at,path,cap):
            steps=[]
            for dr,dc in DIR:
                r,c=at//8+dr,at%8+dc
                if abs(p)==1:
                    rr,cc=r+dr,c+dc
                    if inside(r,c) and inside(rr,cc):
                        v,t=r*8+c,rr*8+cc
                        if board[v]*p<0 and v not in cap and not board[t]: steps.append((t,v))
                else:
                    while inside(r,c) and not board[r*8+c]: r+=dr; c+=dc
                    if not inside(r,c): continue
                    v=r*8+c
                    if board[v]*p>=0 or v in cap: continue
                    r+=dr; c+=dc
                    while inside(r,c) and not board[r*8+c]:
                        steps.append((r*8+c,v)); r+=dr; c+=dc
            if not steps:
                if cap: caps.append({'from':i,'path':path,'cap':cap})
                return
            for t,v in steps:
                x=board.copy(); x[at]=0; x[t]=p
                walk(x,t,path+[t],cap+[v])
        walk(b,i,[],[])
        for dr,dc in DIR:
            if abs(p)==1 and dr!=-s: continue
            r,c=i//8+dr,i%8+dc
            while inside(r,c) and not b[r*8+c]:
                quiet.append({'from':i,'path':[r*8+c],'cap':[]})
                if abs(p)==1: break
                r+=dr; c+=dc
    if rule=='free': return caps+quiet
    return [m for m in caps if len(m['cap'])==max(len(x['cap']) for x in caps)] if caps else quiet
def boardkey(r): return r['rule']+'/'+','.join(map(str,r['board']))+'/'+str(r['turn'])
def reset_match(r):
    r.update(board=initial(),turn=1,sequence=0,winner=None,quiet=0,match=secrets.token_hex(16),rematch=set())
    r['repeats']={boardkey(r):1}
def process(r,side,msg):
    t=msg.get('type')
    if t=='hello': return True
    if t=='resign':
        if r['winner'] is not None: return False
        finish(r,-side,True); return True
    if t=='move':
        if r['winner'] is not None or side!=r['turn'] or msg.get('sequence')!=r['sequence']+1 or msg.get('before')!=boardkey(r): return False
        m=msg.get('move')
        if m not in legal(r['board'],side,r['rule']): return False
        b=r['board']; p=b[m['from']]; to=m['path'][-1]; b[m['from']]=0
        for v in m['cap']: b[v]=0
        b[to]=p*2 if abs(p)==1 and to//8==(0 if side==1 else 7) else p
        r['quiet']=r['quiet']+1 if not m['cap'] and abs(p)==2 else 0
        r['turn']=-side; r['sequence']+=1
        k=boardkey(r); r['repeats'][k]=r['repeats'].get(k,0)+1
        if not legal(b,-side,r['rule']): finish(r,side)
        elif r['quiet']>=40 or r['repeats'][k]>=3: finish(r,0)
        return True
    if t=='rematch' and r['winner'] is not None:
        r['rematch'].add(side); return True
    if t=='rematch-ok' and r['winner'] is not None and -side in r['rematch']:
        reset_match(r); return True
    if t=='rematch-no' and r['winner'] is not None:
        r['rematch'].clear(); return True
    # simultaneous rematch acknowledgements are harmless
    if t=='rematch-ok' and r['sequence']==0: return True
    return False

def identity(d):
    token=str(d.get('profileToken',''))
    return hashlib.sha256(token.encode()).hexdigest() if 32<=len(token)<=128 else None
def active_room(pid,now):
    return any(not r['closed'] and pid in r['profiles'].values() and now-max(r['seen'].values())<100 for r in ROOMS.values())
def social_state(pid,now):
    for k,v in list(PRESENCE.items()):
        if now-v>25: del PRESENCE[k]
    for k,v in list(INVITES.items()):
        if now-v['time']>120: del INVITES[k]
    with database() as db:
        me=sql(db,'SELECT name,points,wins,losses,draws FROM players WHERE id=?',(pid,)).fetchone()
        if not me: return None
        rows=sql(db,'SELECT sender,receiver,state FROM friendships WHERE sender=? OR receiver=?',(pid,pid)).fetchall()
        rel={b if a==pid else a:('friend' if st=='accepted' else 'outgoing' if a==pid else 'incoming') for a,b,st in rows}
        people=[]
        for other in sorted(set(PRESENCE)|set(rel)):
            if other==pid: continue
            p=sql(db,'SELECT name,points,wins,losses,draws FROM players WHERE id=?',(other,)).fetchone()
            if not p: continue
            people.append(dict(id=other,name=p[0],points=p[1],wins=p[2],losses=p[3],draws=p[4],online=other in PRESENCE,busy=active_room(other,now),relation=rel.get(other,'none')))
        challenges=[]; session=None
        for key,v in INVITES.items():
            if pid not in (v['sender'],v['receiver']): continue
            other=v['receiver'] if pid==v['sender'] else v['sender']
            if v['state']=='pending' and now-v['time']<60:
                p=sql(db,'SELECT name FROM players WHERE id=?',(other,)).fetchone()
                challenges.append(dict(id=key,name=p[0] if p else 'Jogador',incoming=pid==v['receiver'],ranked=v['ranked'],rule=v['rule']))
            elif v['state']=='accepted' and now-v['time']<100:
                r=ROOMS.get(v['code'])
                if r and not r['closed']:
                    side=1 if pid==v['sender'] else -1
                    session=dict(code=v['code'],side=side,token=r['tokens'][side],host=side==1,ranked=r['ranked'],rule=r['rule'])
        hist=sql(db,'SELECT opponent,outcome,delta,played_at FROM match_history WHERE player_id=? ORDER BY played_at DESC,match_id DESC LIMIT 20',(pid,)).fetchall()
    people.sort(key=lambda p:(not p['online'],p['relation']!='friend',p['name'].casefold(),p['id']))
    return dict(me=dict(zip(('name','points','wins','losses','draws'),me)),players=people[:200],challenges=challenges,session=session,history=[dict(zip(('opponent','outcome','delta','played_at'),x)) for x in hist])
def search_key(value):
    return ''.join(c for c in unicodedata.normalize('NFKD',str(value).casefold()) if not unicodedata.combining(c))
def public_player(db,pid,row,now):
    other,n,points,wins,losses,draws=row
    rel=sql(db,'SELECT sender,receiver,state FROM friendships WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?)',(pid,other,other,pid)).fetchone()
    relation='none' if not rel else 'friend' if rel[2]=='accepted' else 'outgoing' if rel[0]==pid else 'incoming'
    online=now-PRESENCE.get(other,-1000)<=25
    return dict(id=other,name=n,points=points,wins=wins,losses=losses,draws=draws,relation=relation,online=online,busy=online and active_room(other,now))
def social_lookup(path,d,pid,now):
    with database() as db:
        if path=='/api/social/search':
            q=search_key(' '.join(str(d.get('query','')).split())[:24])
            if not q: return 200,{'players':[]}
            # Unicode and accent-insensitive search on both SQLite and PostgreSQL.
            matches=[]
            for row in sql(db,'SELECT id,name,points,wins,losses,draws FROM players WHERE id<>?',(pid,)):
                key=search_key(row[1])
                if q in key: matches.append((not key.startswith(q),key,-row[2],row[0],row))
            matches.sort(key=lambda x:x[:4])
            return 200,{'players':[public_player(db,pid,x[4],now) for x in matches[:50]],'total':len(matches)}
        target=str(d.get('target',''))
        row=sql(db,'SELECT id,name,points,wins,losses,draws FROM players WHERE id=?',(target,)).fetchone()
        if not row: return 404,{'error':'Jogador não encontrado.'}
        player=public_player(db,pid,row,now)
        p=player
        p['rank']=sql(db,'SELECT COUNT(*) FROM players WHERE points>? OR (points=? AND (wins>? OR (wins=? AND (name<? OR (name=? AND id<?)))))',(p['points'],p['points'],p['wins'],p['wins'],p['name'],p['name'],p['id'])).fetchone()[0]+1
        return 200,{'player':p}

def social_action(path,d,now):
    if path=='/api/social/register':
        pid=profile(d)
    else: pid=identity(d)
    if not pid: return 400,{'error':'Informe seu nome e perfil.'}
    with database() as db:
        if not sql(db,'SELECT id FROM players WHERE id=?',(pid,)).fetchone(): return 403,{'error':'Perfil não encontrado. Abra o cadastro.'}
    PRESENCE[pid]=now
    if path in ('/api/social/search','/api/social/player'):
        return social_lookup(path,d,pid,now)
    if path in ('/api/social/register','/api/social/state'):
        return 200,social_state(pid,now)
    target=str(d.get('target',''))
    if path.startswith('/api/social/friend/'):
        if target==pid: return 400,{'error':'Escolha outro jogador.'}
        with database() as db:
            if not sql(db,'SELECT id FROM players WHERE id=?',(target,)).fetchone(): return 404,{'error':'Jogador não encontrado.'}
            row=sql(db,'SELECT sender,receiver,state FROM friendships WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?)',(pid,target,target,pid)).fetchone()
            action=path.rsplit('/',1)[-1]
            if action=='request':
                if not row: sql(db,'INSERT INTO friendships(sender,receiver,state) VALUES(?,?,?)',(pid,target,'pending'))
                elif row[0]==target and row[2]=='pending': sql(db,'UPDATE friendships SET state=? WHERE sender=? AND receiver=?',('accepted',target,pid))
            elif action=='accept':
                if not row or row[0]!=target or row[2]!='pending': return 409,{'error':'Pedido indisponível.'}
                sql(db,'UPDATE friendships SET state=? WHERE sender=? AND receiver=?',('accepted',target,pid))
            elif action=='remove':
                sql(db,'DELETE FROM friendships WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?)',(pid,target,target,pid))
            else: return 400,{'error':'Ação inválida.'}
        return 200,social_state(pid,now)
    if path=='/api/social/challenge':
        if target==pid or target not in PRESENCE or now-PRESENCE[target]>25: return 409,{'error':'Jogador não está online.'}
        if active_room(pid,now) or active_room(target,now): return 409,{'error':'Um jogador está em outra sala.'}
        if any(v['state']=='pending' and now-v['time']<60 and {v['sender'],v['receiver']}=={pid,target} for v in INVITES.values()): return 409,{'error':'Já existe um desafio pendente.'}
        key=secrets.token_urlsafe(16); rule=d.get('rule','free')
        if rule not in ('free','official'): return 400,{'error':'Regra inválida.'}
        INVITES[key]=dict(sender=pid,receiver=target,state='pending',time=now,ranked=d.get('ranked') is not False,rule=rule)
        return 200,social_state(pid,now)
    if path=='/api/social/challenge/respond':
        v=INVITES.get(str(d.get('invite','')))
        if not v or v['receiver']!=pid or v['state']!='pending' or now-v['time']>=60: return 409,{'error':'Convite expirado.'}
        if d.get('accept') is not True: v['state']='declined';return 200,social_state(pid,now)
        if active_room(pid,now) or active_room(v['sender'],now): return 409,{'error':'Um jogador está em outra sala.'}
        if now-PRESENCE.get(v['sender'],-1000)>25: return 409,{'error':'Adversário desconectado.'}
        if len(ROOMS)>=1000: return 503,{'error':'Servidor cheio.'}
        code=''.join(secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') for _ in range(8))
        while code in ROOMS: code=''.join(secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') for _ in range(8))
        r=dict(last=now,host=1,tokens={1:secrets.token_urlsafe(24),-1:secrets.token_urlsafe(24)},queues={1:[],-1:[]},seen={1:now,-1:now},closed=False,profiles={1:v['sender'],-1:pid},rule=v['rule'],ranked=v['ranked'])
        reset_match(r);ROOMS[code]=r;v.update(state='accepted',code=code,time=now)
        return 200,social_state(pid,now)
    return 404,{'error':'Ação inexistente.'}

class Handler(BaseHTTPRequestHandler):
    def reply(self, status, data, kind='application/json; charset=utf-8'):
        body = json.dumps(data, ensure_ascii=False).encode() if isinstance(data, dict) else data
        self.send_response(status)
        self.send_header('Content-Type', kind)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)
    def do_OPTIONS(self): self.reply(204, b'')
    def do_GET(self):
        if self.path.split('?')[0] in ('/', '/index.html'):
            self.reply(200, (BASE/'index.html').read_bytes(), 'text/html; charset=utf-8')
        elif self.path.split('?')[0] in ('/clube.js','/clube.css'):
            file=self.path.split('?')[0][1:]
            self.reply(200,(BASE/file).read_bytes(),'text/javascript; charset=utf-8' if file.endswith('.js') else 'text/css; charset=utf-8')
        elif self.path == '/api/health': self.reply(200, {'ok':True,'persistentRanking':bool(DATABASE_URL)})
        elif self.path == '/api/ranking':
            try:
                with database() as db:
                    rows=sql(db,'SELECT name,points,wins,losses,draws FROM players ORDER BY points DESC,wins DESC,name,id LIMIT 100').fetchall()
                self.reply(200,{'players':[dict(zip(('name','points','wins','losses','draws'),x)) for x in rows],'persistent':bool(DATABASE_URL)})
            except Exception: self.reply(503,{'error':'Banco de dados indisponível.'})
        else: self.reply(404, {'error':'Página inexistente.'})
    def do_POST(self):
        try:
            n=int(self.headers.get('Content-Length','0'))
            if not 0<n<=32768: raise ValueError()
            d=json.loads(self.rfile.read(n)); assert isinstance(d,dict)
        except Exception: return self.reply(400, {'error':'Pedido inválido.'})
        path=self.path.split('?')[0]; now=time.monotonic()
        if path=='/api/profile':
            token=str(d.get('profileToken',''))
            if not 32<=len(token)<=128: return self.reply(400,{'error':'Perfil inválido.'})
            pid=hashlib.sha256(token.encode()).hexdigest()
            with database() as db:
                p=sql(db,'SELECT name,points,wins,losses,draws FROM players WHERE id=?',(pid,)).fetchone()
                if not p: return self.reply(200,{'found':False})
                rank=sql(db,'SELECT COUNT(*) FROM players WHERE points>? OR (points=? AND (wins>? OR (wins=? AND (name<? OR (name=? AND id<?)))))',(p[1],p[1],p[2],p[2],p[0],p[0],pid)).fetchone()[0]+1
            return self.reply(200,dict(zip(('name','points','wins','losses','draws'),p),found=True,rank=rank))
        with LOCK:
            if path.startswith('/api/social/'):
                try: status,result=social_action(path,d,now);return self.reply(status,result)
                except Exception as exc:
                    print('Social error:',type(exc).__name__,str(exc),flush=True)
                    return self.reply(503,{'error':'Clube indisponível. Tente novamente.'})
            for k,r in list(ROOMS.items()):
                if now-r['last']>TTL: del ROOMS[k]
            if path=='/api/create':
                if len(ROOMS)>=1000: return self.reply(503, {'error':'Servidor cheio.'})
                code=''.join(secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') for _ in range(8))
                while code in ROOMS: code=''.join(secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') for _ in range(8))
                token=secrets.token_urlsafe(24); side=d.get('side')
                if side not in (1,-1): return self.reply(400,{'error':'Player inválido.'})
                pid=profile(d)
                rule=d.get('rule','free')
                if rule not in ('free','official'): return self.reply(400,{'error':'Regra inválida.'})
                ROOMS[code]={'last':now,'host':side,'tokens':{side:token},'queues':{1:[],-1:[]},'seen':{side:now},'closed':False,'profiles':{side:pid},'rule':rule,'ranked':d.get('ranked') is not False}
                reset_match(ROOMS[code])
                return self.reply(200,{'code':code,'token':token,'connected':False,'ranked':ROOMS[code]['ranked']})
            code=str(d.get('code','')).upper(); r=ROOMS.get(code)
            if not r or r['closed']: return self.reply(404,{'error':'Sala inexistente ou encerrada.'})
            side=d.get('side'); r['last']=now
            if path=='/api/join':
                if side!=-r['host']: return self.reply(409,{'error':'Escolha o Player oposto ao criador.'})
                if len(r['tokens'])==2: return self.reply(409,{'error':'Sala cheia.'})
                pid=profile(d)
                if pid and pid==r['profiles'].get(r['host']): return self.reply(409,{'error':'Use outro perfil ou navegador para o adversário.'})
                r['profiles'][side]=pid
                token=secrets.token_urlsafe(24); r['tokens'][side]=token; r['seen'][side]=now
                return self.reply(200,{'code':code,'token':token,'connected':True,'ranked':r.get('ranked',True)})
            if side not in (1,-1) or not secrets.compare_digest(r['tokens'].get(side,'!'),str(d.get('token',''))): return self.reply(403,{'error':'Sessão inválida.'})
            r['seen'][side]=now
            if path=='/api/leave':
                if len(r['tokens'])==2 and r['winner'] is None: finish(r,-side,True)
                r['closed']=True; return self.reply(200,{'ok':True})
            if path=='/api/poll':
                if -side in r['seen'] and now-r['seen'][-side]>90:
                    if r['winner'] is None: finish(r,side,True)
                    r['closed']=True; return self.reply(410,{'error':'Adversário desconectado.'})
                messages=r['queues'][side][:]; r['queues'][side].clear()
                return self.reply(200,{'connected':len(r['tokens'])==2,'messages':messages})
            if path=='/api/send':
                if len(r['tokens'])!=2: return self.reply(409,{'error':'Aguarde o adversário.'})
                m=d.get('message')
                if not isinstance(m,str) or len(m)>12000: return self.reply(400,{'error':'Mensagem inválida.'})
                if len(r['queues'][-side])>=200: return self.reply(429,{'error':'Fila cheia.'})
                try:
                    msg=json.loads(m)
                    if not isinstance(msg,dict) or not process(r,side,msg): return self.reply(409,{'error':'Jogada ou ação inválida.'})
                except (ValueError,TypeError,KeyError,IndexError): return self.reply(400,{'error':'Mensagem inválida.'})
                r['queues'][-side].append(m); return self.reply(200,{'ok':True})
            return self.reply(404,{'error':'Rota inexistente.'})
    def log_message(self, fmt, *args): pass

if __name__=='__main__':
    from selftest import run
    run(sys.modules[__name__])
    setup()
    port=int(os.environ.get('PORT','8765'))
    print(f'Casa de Damas: http://localhost:{port} (Ctrl+C para encerrar)',flush=True)
    ThreadingHTTPServer(('0.0.0.0',port),Handler).serve_forever()
