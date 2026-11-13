from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import json, secrets, threading, time, os, hashlib, sqlite3, subprocess, sys, unicodedata, re
from contextlib import contextmanager

ROOMS = {}
PRESENCE = {}
INVITES = {}
MATCH_QUEUE = {}
LOGIN_LIMITS = {}
SPECTATORS = {}
TOURNAMENTS = {}
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
        sql(db,'CREATE TABLE IF NOT EXISTS notifications (id TEXT PRIMARY KEY, recipient TEXT NOT NULL, actor TEXT NOT NULL, kind TEXT NOT NULL, created_at DOUBLE PRECISION NOT NULL, seen INTEGER NOT NULL DEFAULT 0)')
        sql(db,'CREATE INDEX IF NOT EXISTS notifications_recipient_idx ON notifications(recipient,created_at)')
        sql(db,'CREATE TABLE IF NOT EXISTS match_history (match_id TEXT NOT NULL, player_id TEXT NOT NULL, opponent TEXT NOT NULL, outcome TEXT NOT NULL, delta INTEGER NOT NULL, played_at TEXT NOT NULL, PRIMARY KEY(match_id,player_id))')
        sql(db,'CREATE TABLE IF NOT EXISTS replays (match_id TEXT PRIMARY KEY, player_a TEXT NOT NULL, player_b TEXT NOT NULL, payload TEXT NOT NULL)')
        sql(db,'CREATE TABLE IF NOT EXISTS accounts (player_id TEXT PRIMARY KEY, username TEXT UNIQUE NOT NULL, salt TEXT NOT NULL, password_hash TEXT NOT NULL)')
        sql(db,'CREATE TABLE IF NOT EXISTS account_sessions (token_hash TEXT PRIMARY KEY, player_id TEXT NOT NULL, expires DOUBLE PRECISION NOT NULL)')
        sql(db,'CREATE INDEX IF NOT EXISTS account_sessions_player_idx ON account_sessions(player_id)')
        sql(db,'CREATE TABLE IF NOT EXISTS cosmetics (player_id TEXT PRIMARY KEY, avatar TEXT NOT NULL DEFAULT \'crown\', title TEXT NOT NULL DEFAULT \'visitor\', frame TEXT NOT NULL DEFAULT \'wood\', streak INTEGER NOT NULL DEFAULT 0, best_streak INTEGER NOT NULL DEFAULT 0, completed INTEGER NOT NULL DEFAULT 0)')
        sql(db,'CREATE TABLE IF NOT EXISTS achievements (player_id TEXT NOT NULL, code TEXT NOT NULL, unlocked_at DOUBLE PRECISION NOT NULL, PRIMARY KEY(player_id,code))')
        sql(db,'CREATE TABLE IF NOT EXISTS wallets (player_id TEXT PRIMARY KEY, coins INTEGER NOT NULL DEFAULT 0, theme TEXT NOT NULL DEFAULT \'classic\')')
        sql(db,'CREATE TABLE IF NOT EXISTS purchases (player_id TEXT NOT NULL, item TEXT NOT NULL, PRIMARY KEY(player_id,item))')
        sql(db,'CREATE TABLE IF NOT EXISTS puzzle_solves (player_id TEXT NOT NULL, puzzle_id TEXT NOT NULL, day TEXT NOT NULL, PRIMARY KEY(player_id,puzzle_id))')
        sql(db,'CREATE TABLE IF NOT EXISTS event_champions (event_id TEXT PRIMARY KEY, player_id TEXT NOT NULL, name TEXT NOT NULL, played_at TEXT NOT NULL)')
def token_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()
def identity(d):
    token=str(d.get('profileToken',''))
    if not 32<=len(token)<=128:return None
    digest=token_hash(token)
    with database() as db:
        if token.startswith('acc_'):
            row=sql(db,'SELECT player_id FROM account_sessions WHERE token_hash=? AND expires>?',(digest,time.time())).fetchone()
            return row[0] if row else None
        if sql(db,'SELECT player_id FROM accounts WHERE player_id=?',(digest,)).fetchone():return None
    return digest
def profile(d):
    name=' '.join(str(d.get('name','')).split())[:24]
    token=str(d.get('profileToken',''))
    if not name or not 32<=len(token)<=128: return None
    pid=identity(d)
    if not pid:return None
    with database() as db:
        if token.startswith('acc_'):
            if not sql(db,'SELECT id FROM players WHERE id=?',(pid,)).fetchone():return None
        else:sql(db,'INSERT INTO players(id,name) VALUES(?,?) ON CONFLICT(id) DO UPDATE SET name=excluded.name',(pid,name))
    return pid
AVATARS={'crown','knight','shield','oak','rook','star'}
TITLES={'visitor','first_win','ten_wins','streak5','honor20','friends5','triple_king'}
FRAMES={'wood','bronze','silver','gold'}
ACHIEVEMENTS={
 'first_win':('Primeiro Duelo','Vença uma partida ranqueada.','first_win'),
 'ten_wins':('Guardião do Tabuleiro','Vença dez partidas ranqueadas.','ten_wins'),
 'streak5':('Invencível','Vença cinco partidas ranqueadas consecutivas.','streak5'),
 'honor20':('Até o Último Lance','Complete vinte partidas ranqueadas sem desistir.','honor20'),
 'friends5':('Companheiros de Honra','Tenha cinco amizades aceitas.','friends5'),
 'triple_king':('Rei do Tabuleiro','Promova três pedras em uma partida ranqueada.','triple_king')}
def ensure_cosmetics(db,pid):
    sql(db,'INSERT INTO cosmetics(player_id) VALUES(?) ON CONFLICT(player_id) DO NOTHING',(pid,))
def unlock(db,pid,code):
    sql(db,'INSERT INTO achievements(player_id,code,unlocked_at) VALUES(?,?,?) ON CONFLICT(player_id,code) DO NOTHING',(pid,code,time.time()))
def cosmetics_for(db,pid,refresh=False):
    ensure_cosmetics(db,pid)
    if refresh:
        p=sql(db,'SELECT wins,points FROM players WHERE id=?',(pid,)).fetchone()
        if p:
            if p[0]>=1:unlock(db,pid,'first_win')
            if p[0]>=10:unlock(db,pid,'ten_wins')
        friends=sql(db,"SELECT COUNT(*) FROM friendships WHERE state='accepted' AND (sender=? OR receiver=?)",(pid,pid)).fetchone()[0]
        if friends>=5:unlock(db,pid,'friends5')
    x=sql(db,'SELECT avatar,title,frame,streak,best_streak,completed FROM cosmetics WHERE player_id=?',(pid,)).fetchone()
    earned=[row[0] for row in sql(db,'SELECT code FROM achievements WHERE player_id=? ORDER BY code',(pid,)).fetchall()]
    return dict(avatar=x[0],title=x[1],frame=x[2],streak=x[3],bestStreak=x[4],completed=x[5],achievements=earned)
def award_progress(db,pid,outcome,promotions):
    ensure_cosmetics(db,pid)
    sql(db,'UPDATE cosmetics SET streak=CASE WHEN ?=1 THEN streak+1 ELSE 0 END,completed=completed+? WHERE player_id=?',(int(outcome=='win'),int(outcome!='resign'),pid))
    sql(db,'UPDATE cosmetics SET best_streak=CASE WHEN streak>best_streak THEN streak ELSE best_streak END WHERE player_id=?',(pid,))
    x=cosmetics_for(db,pid,True)
    if x['streak']>=5:unlock(db,pid,'streak5')
    if x['completed']>=20:unlock(db,pid,'honor20')
    if promotions>=3:unlock(db,pid,'triple_king')
def new_account_session(db,pid):
    token='acc_'+secrets.token_urlsafe(32)
    sql(db,'DELETE FROM account_sessions WHERE expires<=?',(time.time(),))
    sql(db,'INSERT INTO account_sessions(token_hash,player_id,expires) VALUES(?,?,?)',(token_hash(token),pid,time.time()+30*86400))
    return token
def password_digest(password,salt):
    return hashlib.scrypt(password.encode('utf-8'),salt=bytes.fromhex(salt),n=16384,r=8,p=1,dklen=32,maxmem=64*1024*1024).hex()
def login_limited(key,now):
    for k,v in list(LOGIN_LIMITS.items()):
        if now-v[0]>300:LOGIN_LIMITS.pop(k,None)
    if len(LOGIN_LIMITS)>=5000 and key not in LOGIN_LIMITS:return True
    start,count=LOGIN_LIMITS.get(key,(now,0))
    if count>=8:return True
    LOGIN_LIMITS[key]=(start,count+1);return False
def account_action(path,d,now):
    action=path.rsplit('/',1)[-1]
    if action=='logout':
        token=str(d.get('profileToken',''));pid=identity(d)
        if token.startswith('acc_') and pid:
            if active_room(pid,now):return 409,{'error':'Saia da sala antes de trocar de conta.'}
            with database() as db:sql(db,'DELETE FROM account_sessions WHERE token_hash=?',(token_hash(token),))
            PRESENCE.pop(pid,None);MATCH_QUEUE.pop(pid,None)
        return 200,{'ok':True}
    username=str(d.get('username','')).strip().lower()
    password=d.get('password','')
    if not re.fullmatch(r'[a-z0-9_.-]{3,24}',username) or not isinstance(password,str) or not 8<=len(password)<=128 or len(password.encode('utf-8'))>512:
        return 400,{'error':'Usuário: 3 a 24 letras/números (._-). Senha: 8 a 128 caracteres.'}
    if action not in ('link','login'):return 404,{'error':'Ação inválida.'}
    if login_limited(username,now):return 429,{'error':'Muitas tentativas. Tente novamente em alguns minutos.'}
    pid=identity(d)
    if pid and active_room(pid,now):return 409,{'error':'Saia da sala antes de trocar de conta.'}
    if action=='link':
        if not pid:return 403,{'error':'Entre com seu perfil primeiro.'}
        with database() as db:
            if not sql(db,'SELECT id FROM players WHERE id=?',(pid,)).fetchone():return 403,{'error':'Perfil não encontrado.'}
            if sql(db,'SELECT player_id FROM accounts WHERE player_id=?',(pid,)).fetchone():return 409,{'error':'Este perfil já tem uma conta.'}
            if sql(db,'SELECT player_id FROM accounts WHERE username=?',(username,)).fetchone():return 409,{'error':'Nome de usuário indisponível.'}
            salt=secrets.token_hex(16);digest=password_digest(password,salt)
            sql(db,'INSERT INTO accounts(player_id,username,salt,password_hash) VALUES(?,?,?,?)',(pid,username,salt,digest))
            token=new_account_session(db,pid)
    else:
        with database() as db:
            row=sql(db,'SELECT player_id,salt,password_hash FROM accounts WHERE username=?',(username,)).fetchone()
            digest=password_digest(password,row[1] if row else '0'*32)
            if not row or not secrets.compare_digest(digest,row[2]):return 401,{'error':'Usuário ou senha incorretos.'}
            pid=row[0]
            token=new_account_session(db,pid)
    LOGIN_LIMITS.pop(username,None)
    PRESENCE[pid]=now
    return 200,dict(token=token,state=social_state(pid,now))
def customize(pid,d,now):
    if active_room(pid,now):return 409,{'error':'Personalize seu perfil após sair da sala.'}
    with database() as db:
        me=sql(db,'SELECT points FROM players WHERE id=?',(pid,)).fetchone()
        if not me:return 404,{'error':'Perfil não encontrado.'}
        c=cosmetics_for(db,pid,True)
        avatar=d.get('avatar',c['avatar']);title=d.get('title',c['title']);frame=d.get('frame',c['frame'])
        if avatar not in AVATARS or title not in TITLES or frame not in FRAMES:return 400,{'error':'Personalização inválida.'}
        if title!='visitor' and title not in c['achievements']:return 403,{'error':'Título ainda bloqueado.'}
        minimum={'wood':0,'bronze':1000,'silver':1250,'gold':1500}[frame]
        if frame!=c['frame'] and me[0]<minimum:return 403,{'error':'Moldura ainda bloqueada.'}
        name=' '.join(str(d.get('name','')).split())[:24]
        if not name:return 400,{'error':'Informe seu nome.'}
        sql(db,'UPDATE players SET name=? WHERE id=?',(name,pid))
        sql(db,'UPDATE cosmetics SET avatar=?,title=?,frame=? WHERE player_id=?',(avatar,title,frame,pid))
    return 200,social_state(pid,now)

def game_side(r,seat):
    return r.get('colors',{}).get(seat,seat)
def finish(r,w,resigned=False,reason=None):
    if r.get('winner') is not None: return
    p=r['profiles']
    ranked=bool(r.get('ranked',True) and len(p)==2 and p[1] and p[-1] and p[1]!=p[-1])
    names={}; deltas={}; points={}
    if ranked:
        with database() as db:
            inserted=sql(db,'INSERT INTO results(id) VALUES(?) ON CONFLICT(id) DO NOTHING',(r['match'],)).rowcount
            if inserted:
                for seat in (1,-1):
                    side=game_side(r,seat)
                    delta=5 if w==0 else 25 if w==side else (-20 if resigned else -15)
                    old=sql(db,'SELECT name,points FROM players WHERE id=?',(p[seat],)).fetchone()
                    names[str(side)]=old[0]
                    deltas[str(side)]=max(0,old[1]+delta)-old[1]
                    points[str(side)]=max(0,old[1]+delta)
                    sql(db,'UPDATE players SET points=CASE WHEN points+? < 0 THEN 0 ELSE points+? END,wins=wins+?,losses=losses+?,draws=draws+? WHERE id=?',(delta,delta,int(w==side),int(w==-side),int(w==0),p[seat]))
                    opponent=sql(db,'SELECT name FROM players WHERE id=?',(p[-seat],)).fetchone()[0]
                    outcome='draw' if w==0 else 'win' if w==side else 'resign' if resigned else 'loss'
                    sql(db,'INSERT INTO match_history(match_id,player_id,opponent,outcome,delta,played_at) VALUES(?,?,?,?,?,?)',(r['match'],p[seat],opponent,outcome,delta,time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())))
                    award_progress(db,p[seat],outcome,match_stats(r)[str(side)]['promotions'])
                    if outcome!='resign' and r['sequence']>=8: wallet_add(db,p[seat],15 if outcome=='win' else 8)
    if not names:
        with database() as db:
            for seat,pid in p.items():
                row=sql(db,'SELECT name,points FROM players WHERE id=?',(pid,)).fetchone() if pid else None
                if row: names[str(game_side(r,seat))]=row[0]
    r['winner']=w
    reason=reason or ('resign' if resigned else 'normal')
    r['result']=dict(match=r['match'],winner=w,reason=reason,ranked=ranked,rule=r['rule'],names=names,deltas=deltas,points=points,board=r['board'][:],turn=r['turn'],sequence=r['sequence'],duration=max(0,int(time.monotonic()-r.get('started',time.monotonic()))),moves=r.get('moves',[])[:],stats=match_stats(r))
    if len(p)==2 and p.get(1) and p.get(-1):
        with database() as db:
            sql(db,'INSERT INTO replays(match_id,player_a,player_b,payload) VALUES(?,?,?,?) ON CONFLICT(match_id) DO NOTHING',(r['match'],p[1],p[-1],json.dumps(r['result'])))
def result_for(r,seat):
    return dict(r['result'],side=game_side(r,seat)) if r.get('result') else None
def initial():
    return [(-1 if i//8<3 else 1 if i//8>4 else 0) if (i//8+i%8)%2 else 0 for i in range(64)]
RULES=('free','official','english','mandatory','giveaway','kings','international','canadian')
def valid_rule(rule):
    return isinstance(rule,str) and (rule in RULES or (re.fullmatch(r'custom-[01]{4}',rule) and not (rule[7]=='0' and rule[8]=='1')))
def rule_flags(rule):
    if rule.startswith('custom-'):return tuple(x=='1' for x in rule[7:])
    return (rule!='free',rule in ('official','giveaway','international','canadian'),rule!='english',rule!='english')
def board_size(rule):return 10 if rule=='international' else 12 if rule=='canadian' else 8
def initial_for(rule):
    n=board_size(rule);rows=n//2-1
    return [(-1 if i//n<rows else 1 if i//n>=n-rows else 0)*(2 if rule=='kings' else 1) if (i//n+i%n)%2 else 0 for i in range(n*n)]
DIR=((1,1),(1,-1),(-1,1),(-1,-1))
def inside(r,c): return 0<=r<8 and 0<=c<8
def legal(b,s,rule):
    n=int(len(b)**.5); inside=lambda r,c:0<=r<n and 0<=c<n
    caps=[]; quiet=[]; mandatory,majority,long_king,backward=rule_flags(rule); short=not long_king
    for i,p in enumerate(b):
        if not p or p*s<=0: continue
        def walk(board,at,path,cap):
            steps=[]
            for dr,dc in DIR:
                r,c=at//n+dr,at%n+dc
                if not backward and abs(p)==1 and dr!=-s: continue
                if abs(p)==1 or short:
                    rr,cc=r+dr,c+dc
                    if inside(r,c) and inside(rr,cc):
                        v,t=r*n+c,rr*n+cc
                        if board[v]*p<0 and v not in cap and not board[t]: steps.append((t,v))
                else:
                    while inside(r,c) and not board[r*n+c]: r+=dr; c+=dc
                    if not inside(r,c): continue
                    v=r*n+c
                    if board[v]*p>=0 or v in cap: continue
                    r+=dr; c+=dc
                    while inside(r,c) and not board[r*n+c]:
                        steps.append((r*n+c,v)); r+=dr; c+=dc
            if not steps:
                if cap: caps.append({'from':i,'path':path,'cap':cap})
                return
            for t,v in steps:
                x=board.copy(); x[at]=0; x[t]=p
                if rule=='english': x[v]=0
                if rule=='english' and abs(p)==1 and t//n==(0 if s==1 else n-1): caps.append({'from':i,'path':path+[t],'cap':cap+[v]})
                else: walk(x,t,path+[t],cap+[v])
        walk(b,i,[],[])
        for dr,dc in DIR:
            if abs(p)==1 and dr!=-s: continue
            r,c=i//n+dr,i%n+dc
            while inside(r,c) and not b[r*n+c]:
                quiet.append({'from':i,'path':[r*n+c],'cap':[]})
                if abs(p)==1 or short: break
                r+=dr; c+=dc
    if not mandatory: return caps+quiet
    if not majority: return caps or quiet
    return [m for m in caps if len(m['cap'])==max(len(x['cap']) for x in caps)] if caps else quiet
def boardkey(r): return r['rule']+'/'+','.join(map(str,r['board']))+'/'+str(r['turn'])
def match_stats(r):
    stats={'1':{'captures':0,'promotions':0},'-1':{'captures':0,'promotions':0}}
    for m in r.get('moves',[]):
        a=stats[str(m['side'])];a['captures']+=len(m['cap']);a['promotions']+=int(m['promotion'])
    return stats
def clock_value(d):
    v=d.get('minutes',0)
    return v if type(v) is int and v in (0,1,3,5,10) else 0
def reset_match(r):
    now=time.monotonic()
    seconds=r.get('minutes',0)*60
    r.update(board=initial_for(r['rule']),turn=1,sequence=0,winner=None,result=None,quiet=0,match=secrets.token_hex(16),rematch=set(),moves=[],chat=[],chat_seen={},draw_offer=None,remaining={1:seconds,-1:seconds},clock_at=None,started=now)

    r['repeats']={boardkey(r):1}
def tick_clock(r,now):
    if r['winner'] is not None or not r.get('minutes') or len(r['tokens'])!=2: return
    if r.get('clock_at') is None:
        r['clock_at']=now;r['started']=now;return
    turn=r['turn'];r['remaining'][turn]=max(0,r['remaining'][turn]-max(0,now-r['clock_at']));r['clock_at']=now
    if r['remaining'][turn]<=0: finish(r,-turn,reason='timeout')
def room_snapshot(r,seat,now):
    cached=r.setdefault('name_by_seat',{})
    if any(pid and seat not in cached for seat,pid in r['profiles'].items()):
        with database() as db:
            for seat,pid in r['profiles'].items():
                if pid and seat not in cached:
                    row=sql(db,'SELECT name FROM players WHERE id=?',(pid,)).fetchone()
                    if row: cached[seat]=row[0]
    names={str(game_side(r,seat)):name for seat,name in cached.items()}
    return dict(match=r['match'],side=game_side(r,seat),board=r['board'],turn=r['turn'],sequence=r['sequence'],rule=r['rule'],names=names,moves=r.get('moves',[]),quiet=r['quiet'],repeats=r['repeats'],minutes=r.get('minutes',0),remaining=r['remaining'],drawOffer=r.get('draw_offer'),chat=r.get('chat',[]),stats=match_stats(r),opponentOffline=now-r['seen'].get(-seat,now)>10,grace=max(0,90-int(now-r['seen'].get(-seat,now))),connected=len(r['tokens'])==2)
def process(r,seat,msg):
    side=game_side(r,seat)
    t=msg.get('type')
    if t=='hello': return True
    if t=='chat' and r['winner'] is None:
        message=msg.get('text');now=time.monotonic()
        if not isinstance(message,str) or not 1<=len(message.strip())<=180 or now-r['chat_seen'].get(seat,-1000)<1:return False
        r['chat_seen'][seat]=now;r['chat'].append(dict(side=side,text=message.strip(),id=secrets.token_hex(8)));r['chat']=r['chat'][-50:];return True
    if t=='draw-offer' and r['winner'] is None and r.get('draw_offer') is None:
        r['draw_offer']=side;return True
    if t in ('draw-accept','draw-decline') and r['winner'] is None and r.get('draw_offer')==-side:
        r['draw_offer']=None
        if t=='draw-accept': finish(r,0,reason='agreement')
        return True
    if t=='resign':
        if r['winner'] is not None: return False
        finish(r,-side,True); return True
    if t=='move':
        if r['winner'] is not None or side!=r['turn'] or msg.get('sequence')!=r['sequence']+1 or msg.get('before')!=boardkey(r): return False
        m=msg.get('move')
        if m not in legal(r['board'],side,r['rule']): return False
        b=r['board']; p=b[m['from']]; to=m['path'][-1]; b[m['from']]=0
        for v in m['cap']: b[v]=0
        n=board_size(r['rule']);b[to]=p*2 if abs(p)==1 and to//n==(0 if side==1 else n-1) else p
        r['moves'].append(dict(side=side,**m,promotion=abs(p)==1 and abs(b[to])==2))
        r['draw_offer']=None
        r['quiet']=r['quiet']+1 if not m['cap'] and abs(p)==2 else 0
        r['turn']=-side; r['sequence']+=1
        k=boardkey(r); r['repeats'][k]=r['repeats'].get(k,0)+1
        if not legal(b,-side,r['rule']): finish(r,-side if r['rule']=='giveaway' else side,reason='giveaway' if r['rule']=='giveaway' else None)
        elif r['quiet']>=40 or r['repeats'][k]>=3: finish(r,0)
        return True
    if r.get('event') and t.startswith('rematch'):return False
    if t=='rematch' and r['winner'] is not None:
        r['rematch'].add(seat); return True
    if t=='rematch-ok' and r['winner'] is not None and -seat in r['rematch']:
        swap=secrets.choice((False,True))
        if swap: r['colors']={1:-game_side(r,1),-1:-game_side(r,-1)}
        reset_match(r)
        r['rematch_event']=json.dumps({'type':'rematch-start','swap':swap})
        return True
    if t=='rematch-no' and r['winner'] is not None:
        r['rematch'].clear(); return True
    # simultaneous rematch acknowledgements are harmless
    if t=='rematch-ok' and r['sequence']==0: return True
    return False

def active_room(pid,now):
    return any(not r['closed'] and pid in r['profiles'].values() and now-max(r['seen'].values())<100 for r in ROOMS.values())
def session_for(pid,now):
    for code,r in ROOMS.items():
        if r['closed'] or len(r['tokens'])!=2 or r['winner'] is not None: continue
        for seat,player in r['profiles'].items():
            if player==pid and now-r['seen'].get(seat,now)<90:
                return dict(code=code,side=game_side(r,seat),seat=seat,token=r['tokens'][seat],host=seat==r['host'],ranked=r['ranked'],rule=r['rule'],minutes=r.get('minutes',0),resume=True)
    return None
def matchmake(pid,now):
    q=MATCH_QUEUE.get(pid)
    if not q:return
    if active_room(pid,now): MATCH_QUEUE.pop(pid,None);return
    for other,o in list(MATCH_QUEUE.items()):
        if now-o['seen']>25 or active_room(other,now): MATCH_QUEUE.pop(other,None);continue
        if other==pid or (q['rule'],q['ranked'],q['minutes'])!=(o['rule'],o['ranked'],o['minutes']):continue
        window=200+int(max(now-q['start'],now-o['start'])//10)*100
        if abs(q['points']-o['points'])>window:continue
        if len(ROOMS)>=1000:return
        code=secrets.token_hex(4).upper().replace('0','A').replace('1','B')
        while code in ROOMS:code=secrets.token_hex(4).upper().replace('0','A').replace('1','B')
        side=secrets.choice((1,-1))
        r=dict(last=now,host=side,tokens={1:secrets.token_urlsafe(24),-1:secrets.token_urlsafe(24)},queues={1:[],-1:[]},seen={1:now,-1:now},closed=False,profiles={side:pid,-side:other},rule=q['rule'],ranked=q['ranked'],minutes=q['minutes'])
        reset_match(r);ROOMS[code]=r
        MATCH_QUEUE.pop(pid,None);MATCH_QUEUE.pop(other,None);return
def notify(db,recipient,actor,kind):
    sql(db,'INSERT INTO notifications(id,recipient,actor,kind,created_at,seen) VALUES(?,?,?,?,?,0)',(secrets.token_hex(16),recipient,actor,kind,time.time()))
def social_state(pid,now):
    for event in list(TOURNAMENTS.values()):event_tick(event,now)
    for k,v in list(PRESENCE.items()):
        if now-v>25: del PRESENCE[k]
    for k,v in list(INVITES.items()):
        if now-v['time']>120: del INVITES[k]
    if pid in MATCH_QUEUE:
        MATCH_QUEUE[pid]['seen']=now;matchmake(pid,now)
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
        challenges=[]; session=session_for(pid,now)
        for key,v in INVITES.items():
            if pid not in (v['sender'],v['receiver']): continue
            other=v['receiver'] if pid==v['sender'] else v['sender']
            if v['state']=='pending' and now-v['time']<60:
                p=sql(db,'SELECT name FROM players WHERE id=?',(other,)).fetchone()
                challenges.append(dict(id=key,name=p[0] if p else 'Jogador',incoming=pid==v['receiver'],ranked=v['ranked'],rule=v['rule'],minutes=v.get('minutes',0)))
            elif v['state']=='accepted' and now-v['time']<100:
                r=ROOMS.get(v['code'])
                if r and not r['closed'] and r['winner'] is None and not session:
                    side=r['host'] if pid==v['sender'] else -r['host']
                    session=dict(code=v['code'],side=game_side(r,side),seat=side,token=r['tokens'][side],host=side==r['host'],ranked=r['ranked'],rule=r['rule'],minutes=r.get('minutes',0),resume=True)
        hist=sql(db,'SELECT opponent,outcome,delta,played_at,match_id FROM match_history WHERE player_id=? ORDER BY played_at DESC,match_id DESC LIMIT 20',(pid,)).fetchall()
        notices=sql(db,'SELECT n.id,n.kind,n.actor,p.name,n.created_at,n.seen FROM notifications n JOIN players p ON p.id=n.actor WHERE n.recipient=? ORDER BY n.created_at DESC,n.id DESC LIMIT 50',(pid,)).fetchall()
        unread=sql(db,'SELECT COUNT(*) FROM notifications WHERE recipient=? AND seen=0',(pid,)).fetchone()[0]
        cosmetics=cosmetics_for(db,pid,True)
        account=sql(db,'SELECT username FROM accounts WHERE player_id=?',(pid,)).fetchone()
    people.sort(key=lambda p:(not p['online'],p['relation']!='friend',p['name'].casefold(),p['id']))
    return dict(me=dict(zip(('name','points','wins','losses','draws'),me),**cosmetics,account=account[0] if account else None),persistent=bool(DATABASE_URL),players=people[:200],challenges=challenges,session=session,history=[dict(zip(('opponent','outcome','delta','played_at','match_id'),x)) for x in hist],notifications=[dict(zip(('id','kind','actor','name','created_at','seen'),x)) for x in notices],unread=unread,matchmaking=pid in MATCH_QUEUE)
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
        p.update(cosmetics_for(db,target,True))
        return 200,{'player':p}

PUZZLES=[
 dict(id='capture1',name='Primeiro salto',level='Iniciante',pieces={42:1,35:-1},goal='Capture a pedra adversária.',reward=15),
 dict(id='double',name='Caminho duplo',level='Intermediário',pieces={42:1,35:-1,21:-1},goal='Capture duas pedras em um lance.',reward=25),
 dict(id='majority',name='A lei da maioria',level='Intermediário',pieces={42:1,33:-1,35:-1,19:-1},goal='Encontre a sequência que captura mais pedras.',reward=30),
 dict(id='crown',name='A coroação',level='Iniciante',pieces={17:1,10:-1},goal='Capture e transforme a pedra em dama.',reward=20),
 dict(id='triple',name='Três em linha',level='Avançado',pieces={56:1,49:-1,35:-1,21:-1},goal='Capture três pedras em um único lance.',reward=40)]
THEMES={'classic':0,'imperial':100,'marble':150,'emerald':120}
def puzzle_board(p):
    b=[0]*64
    for i,v in p['pieces'].items():b[i]=v
    return b
def wallet_add(db,pid,amount):
    sql(db,'INSERT INTO wallets(player_id,coins) VALUES(?,?) ON CONFLICT(player_id) DO UPDATE SET coins=wallets.coins+excluded.coins',(pid,amount))
def wallet_state(db,pid):
    sql(db,'INSERT INTO wallets(player_id) VALUES(?) ON CONFLICT(player_id) DO NOTHING',(pid,))
    coins,theme=sql(db,'SELECT coins,theme FROM wallets WHERE player_id=?',(pid,)).fetchone()
    return dict(coins=coins,theme=theme,owned=['classic']+[x[0] for x in sql(db,'SELECT item FROM purchases WHERE player_id=?',(pid,)).fetchall()])
def school_action(path,d,pid,now):
    day=time.strftime('%Y-%m-%d',time.gmtime());daily=PUZZLES[int(time.time()//86400)%len(PUZZLES)]['id']
    with database() as db:
        if path.endswith('/solve'):
            p=next((p for p in PUZZLES if p['id']==d.get('puzzle')),None)
            if not p:return 404,{'error':'Desafio inexistente.'}
            m=d.get('move')
            if m not in legal(puzzle_board(p),1,'official'):return 400,{'error':'Esse lance não resolve o desafio.'}
            inserted=sql(db,'INSERT INTO puzzle_solves(player_id,puzzle_id,day) VALUES(?,?,?) ON CONFLICT(player_id,puzzle_id) DO NOTHING',(pid,p['id'],day)).rowcount
            reward=p['reward']+(10 if p['id']==daily else 0) if inserted else 0
            if reward:wallet_add(db,pid,reward)
            return 200,dict(reward=reward,**wallet_state(db,pid))
        if path.endswith('/buy') or path.endswith('/equip'):
            item=d.get('item')
            if not isinstance(item,str) or item not in THEMES:return 400,{'error':'Tema inexistente.'}
            w=wallet_state(db,pid)
            if item not in w['owned']:
                if path.endswith('/equip'):return 403,{'error':'Tema ainda bloqueado.'}
                if w['coins']<THEMES[item]:return 400,{'error':'Moedas insuficientes.'}
                sql(db,'UPDATE wallets SET coins=coins-? WHERE player_id=?',(THEMES[item],pid))
                sql(db,'INSERT INTO purchases(player_id,item) VALUES(?,?)',(pid,item))
            sql(db,'UPDATE wallets SET theme=? WHERE player_id=?',(item,pid))
            return 200,wallet_state(db,pid)
        solved=[x[0] for x in sql(db,'SELECT puzzle_id FROM puzzle_solves WHERE player_id=?',(pid,)).fetchall()]
        return 200,dict(puzzles=[dict(id=p['id'],name=p['name'],level=p['level'],goal=p['goal'],reward=p['reward'],board=puzzle_board(p)) for p in PUZZLES],daily=daily,solved=solved,**wallet_state(db,pid))
def live_action(path,d,pid,now):
    for k,v in list(SPECTATORS.items()):
        if now-v[1]>15:SPECTATORS.pop(k,None)
    if path.endswith('/watch'):
        code=str(d.get('code',''));r=ROOMS.get(code)
        if not r or not r.get('public') or len(r['tokens'])!=2:return 404,{'error':'Partida pública indisponível.'}
        SPECTATORS[pid]=(code,now)
        snapshot=room_snapshot(r,1,now)
        return 200,dict(board=snapshot['board'],names=snapshot['names'],turn=snapshot['turn'],rule=r['rule'],sequence=r['sequence'],remaining=r['remaining'],minutes=r.get('minutes',0),result=r['winner'],closed=r['closed'],viewers=sum(v[0]==code for v in SPECTATORS.values()))
    if path.endswith('/leave'):
        SPECTATORS.pop(pid,None);return 200,{'ok':True}
    rooms=[]
    for code,r in ROOMS.items():
        if r.get('public') and not r['closed'] and r['winner'] is None and len(r['tokens'])==2:
            snap=room_snapshot(r,1,now);rooms.append(dict(code=code,names=snap['names'],rule=r['rule'],minutes=r.get('minutes',0),viewers=sum(v[0]==code for v in SPECTATORS.values())))
    return 200,{'rooms':rooms[:50]}
def event_room(event,a,b,now):
    code=''.join(secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') for _ in range(8))
    while code in ROOMS:code=''.join(secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') for _ in range(8))
    side=secrets.choice((1,-1))
    r=dict(last=now,host=side,tokens={1:secrets.token_urlsafe(24),-1:secrets.token_urlsafe(24)},queues={1:[],-1:[]},seen={1:now,-1:now},closed=False,profiles={side:a,-side:b},rule='official',ranked=False,minutes=5,public=True,event=event['id'])
    reset_match(r);ROOMS[code]=r;return code
def event_pair(event,a,b,now):
    return dict(a=a,b=b,code=event_room(event,a,b,now),winner=None)
def event_tick(e,now):
    if e['status']!='playing':return
    for pair in e['pairs']:
        if pair['winner']:continue
        r=ROOMS.get(pair['code'])
        if not r:return
        if r['winner'] is None:
            if now-max(r['seen'].values())>90:
                e['status']='cancelled'
                for pending in e['pairs']:
                    room=ROOMS.get(pending['code'])
                    if room and room['winner'] is None:finish(room,0,reason='agreement');room['closed']=True
                return
            else:continue
        if r['winner']==0:
            r['closed']=True;pair['code']=event_room(e,pair['a'],pair['b'],now);continue
        pair['winner']=next(pid for seat,pid in r['profiles'].items() if game_side(r,seat)==r['winner'])
        r['closed']=True
    if any(not p['winner'] for p in e['pairs']):return
    winners=[p['winner'] for p in e['pairs']]
    if e['type']=='king':
        p=e['pairs'][0];king=winners[0];loser=p['b'] if p['a']==king else p['a'];e['queue'].append(loser);e['king']=king;e['round']+=1;e['history'].append(dict(round=e['round']-1,pairs=e['pairs']));e['history']=e['history'][-10:]
        challenger=e['queue'].pop(0);e['pairs']=[event_pair(e,king,challenger,now)];return
    e['history'].append(dict(round=e['round'],pairs=e['pairs']))
    if len(winners)==1:
        e['status']='finished';e['champion']=winners[0]
        with database() as db:
            name=sql(db,'SELECT name FROM players WHERE id=?',(winners[0],)).fetchone()[0]
            inserted=sql(db,'INSERT INTO event_champions(event_id,player_id,name,played_at) VALUES(?,?,?,?) ON CONFLICT(event_id) DO NOTHING',(e['id'],winners[0],name,time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()))).rowcount
            if inserted:wallet_add(db,winners[0],100)
        return
    e['round']+=1;e['pairs']=[event_pair(e,winners[i],winners[i+1],now) for i in range(0,len(winners),2)]
def event_action(path,d,pid,now):
    action=path.rsplit('/',1)[-1]
    for e in list(TOURNAMENTS.values()):event_tick(e,now)
    if action=='create':
        kind=d.get('kind','cup')
        if kind not in ('cup','king'):return 400,{'error':'Evento inválido.'}
        if len(TOURNAMENTS)>=100:return 503,{'error':'Limite de eventos atingido.'}
        if active_room(pid,now) or any(pid in e['players'] and e['status'] not in ('finished','cancelled') for e in TOURNAMENTS.values()):return 409,{'error':'Você já está em uma sala ou evento.'}
        key=secrets.token_hex(5);TOURNAMENTS[key]=dict(id=key,type=kind,host=pid,players=[pid],status='waiting',round=1,pairs=[],history=[],queue=[],champion=None)
    elif action in ('join','leave','start','stop'):
        e=TOURNAMENTS.get(str(d.get('event','')))
        if not e:return 404,{'error':'Evento inexistente.'}
        if action=='join':
            if e['status']!='waiting' or len(e['players'])>=8:return 409,{'error':'Inscrições encerradas.'}
            if pid not in e['players']:
                if active_room(pid,now) or any(pid in x['players'] and x['status'] not in ('finished','cancelled') for x in TOURNAMENTS.values()):return 409,{'error':'Você já está em uma sala ou evento.'}
                e['players'].append(pid)
        elif action=='leave':
            if e['status']!='waiting':return 409,{'error':'O evento já começou.'}
            if pid in e['players']:e['players'].remove(pid)
            if not e['players']:TOURNAMENTS.pop(e['id'],None)
            elif e['host']==pid:e['host']=e['players'][0]
        elif action=='stop':
            if e['host']!=pid or e['status'] not in ('waiting','playing'):return 403,{'error':'Somente o organizador pode encerrar.'}
            e['status']='cancelled'
            for pair in e['pairs']:
                room=ROOMS.get(pair['code'])
                if room and room['winner'] is None:finish(room,0,reason='agreement');room['closed']=True
        elif action=='start':
            if e['host']!=pid or e['status']!='waiting' or e['type']!='king' or len(e['players'])<2:return 409,{'error':'São necessários pelo menos dois jogadores.'}
            e['status']='playing';e['queue']=e['players'][2:];e['pairs']=[event_pair(e,*e['players'][:2],now)]
        if e['type']=='cup' and e['status']=='waiting' and len(e['players'])==8:
            e['status']='playing';players=e['players'][:];secrets.SystemRandom().shuffle(players);e['pairs']=[event_pair(e,players[i],players[i+1],now) for i in range(0,8,2)]
    elif action!='list':return 404,{'error':'Ação inválida.'}
    with database() as db:
        names={p[0]:p[1] for p in sql(db,'SELECT id,name FROM players').fetchall()}
        champs=sql(db,'SELECT name,played_at FROM event_champions ORDER BY played_at DESC LIMIT 20').fetchall()
    result=[]
    for e in TOURNAMENTS.values():
        result.append(dict(id=e['id'],type=e['type'],status=e['status'],round=e['round'],host=e['host']==pid,joined=pid in e['players'],players=[names.get(x,'Jogador') for x in e['players']],pairs=[dict(a=names.get(p['a'],'Jogador'),b=names.get(p['b'],'Jogador'),winner=names.get(p['winner']) if p['winner'] else None) for p in e['pairs']],champion=names.get(e.get('champion')),king=names.get(e.get('king')),queue=[names.get(x,'Jogador') for x in e['queue']]))
    return 200,{'events':result[-30:],'champions':[dict(name=x[0],date=x[1]) for x in champs]}
def social_action(path,d,now):
    if path.startswith('/api/social/account/'):return account_action(path,d,now)
    if path=='/api/social/register':
        pid=profile(d)
    else: pid=identity(d)
    if not pid: return 400,{'error':'Informe seu nome e perfil.'}
    with database() as db:
        if not sql(db,'SELECT id FROM players WHERE id=?',(pid,)).fetchone(): return 403,{'error':'Perfil não encontrado. Abra o cadastro.'}
    PRESENCE[pid]=now
    if path.startswith('/api/social/school/'):return school_action(path,d,pid,now)
    if path.startswith('/api/social/live/'):return live_action(path,d,pid,now)
    if path.startswith('/api/social/events/'):return event_action(path,d,pid,now)
    if path=='/api/social/customize':return customize(pid,d,now)
    if path in ('/api/social/search','/api/social/player'):
        return social_lookup(path,d,pid,now)
    if path in ('/api/social/register','/api/social/state'):
        return 200,social_state(pid,now)
    if path=='/api/social/matchmaking/start':
        if active_room(pid,now):return 409,{'error':'Saia da sala atual antes de buscar partida.'}
        rule=d.get('rule','free')
        if not valid_rule(rule):return 400,{'error':'Regra inválida.'}
        with database() as db: points=sql(db,'SELECT points FROM players WHERE id=?',(pid,)).fetchone()[0]
        MATCH_QUEUE[pid]=dict(rule=rule,ranked=d.get('ranked') is not False and not rule.startswith('custom-') and rule not in ('kings','international','canadian'),minutes=clock_value(d),points=points,start=now,seen=now)
        matchmake(pid,now);return 200,social_state(pid,now)
    if path=='/api/social/matchmaking/cancel':
        MATCH_QUEUE.pop(pid,None);return 200,social_state(pid,now)
    if path=='/api/social/replay':
        with database() as db:
            row=sql(db,'SELECT payload FROM replays WHERE match_id=? AND (player_a=? OR player_b=?)',(str(d.get('match','')),pid,pid)).fetchone()
        return (200,{'replay':json.loads(row[0])}) if row else (404,{'error':'Replay não disponível para esta partida.'})
    if path=='/api/social/notifications/read':
        with database() as db:
            ids=d.get('ids',[])
            if d.get('all') is True:
                sql(db,'UPDATE notifications SET seen=1 WHERE recipient=?',(pid,))
                ids=[]
            if not isinstance(ids,list): return 400,{'error':'Notificações inválidas.'}
            for nid in ids[:50]:
                if isinstance(nid,str): sql(db,'UPDATE notifications SET seen=1 WHERE recipient=? AND id=?',(pid,nid))
        return 200,social_state(pid,now)
    target=str(d.get('target',''))
    if path.startswith('/api/social/friend/'):
        if target==pid: return 400,{'error':'Escolha outro jogador.'}
        with database() as db:
            if not sql(db,'SELECT id FROM players WHERE id=?',(target,)).fetchone(): return 404,{'error':'Jogador não encontrado.'}
            row=sql(db,'SELECT sender,receiver,state FROM friendships WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?)',(pid,target,target,pid)).fetchone()
            action=path.rsplit('/',1)[-1]
            if action=='request':
                if not row:
                    sql(db,'INSERT INTO friendships(sender,receiver,state) VALUES(?,?,?)',(pid,target,'pending'))
                    notify(db,target,pid,'friend_request')
                elif row[0]==target and row[2]=='pending':
                    sql(db,'UPDATE friendships SET state=? WHERE sender=? AND receiver=?',('accepted',target,pid))
                    notify(db,target,pid,'friend_accepted')
            elif action=='accept':
                if not row or row[0]!=target or row[2]!='pending': return 409,{'error':'Pedido indisponível.'}
                sql(db,'UPDATE friendships SET state=? WHERE sender=? AND receiver=?',('accepted',target,pid))
                notify(db,target,pid,'friend_accepted')
            elif action in ('remove','decline'):
                if action=='decline' and (not row or row[0]!=target or row[2]!='pending'): return 409,{'error':'Pedido indisponível.'}
                if row and row[2]=='pending' and row[0]==target: notify(db,target,pid,'friend_declined')
                elif row and row[2]=='accepted': notify(db,target,pid,'friend_removed')
                sql(db,'DELETE FROM friendships WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?)',(pid,target,target,pid))
            else: return 400,{'error':'Ação inválida.'}
        return 200,social_state(pid,now)
    if path=='/api/social/challenge':
        if target==pid or target not in PRESENCE or now-PRESENCE[target]>25: return 409,{'error':'Jogador não está online.'}
        if active_room(pid,now) or active_room(target,now): return 409,{'error':'Um jogador está em outra sala.'}
        if any(v['state']=='pending' and now-v['time']<60 and {v['sender'],v['receiver']}=={pid,target} for v in INVITES.values()): return 409,{'error':'Já existe um desafio pendente.'}
        key=secrets.token_urlsafe(16); rule=d.get('rule','free')
        if not valid_rule(rule): return 400,{'error':'Regra inválida.'}
        INVITES[key]=dict(sender=pid,receiver=target,state='pending',time=now,ranked=d.get('ranked') is not False and not rule.startswith('custom-') and rule not in ('kings','international','canadian'),rule=rule,minutes=clock_value(d))
        return 200,social_state(pid,now)
    if path=='/api/social/challenge/respond':
        v=INVITES.get(str(d.get('invite','')))
        if not v or v['receiver']!=pid or v['state']!='pending' or now-v['time']>=60: return 409,{'error':'Convite expirado.'}
        if d.get('accept') is not True:
            v['state']='declined'
            with database() as db: notify(db,v['sender'],pid,'challenge_declined')
            return 200,social_state(pid,now)
        if active_room(pid,now) or active_room(v['sender'],now): return 409,{'error':'Um jogador está em outra sala.'}
        if now-PRESENCE.get(v['sender'],-1000)>25: return 409,{'error':'Adversário desconectado.'}
        if len(ROOMS)>=1000: return 503,{'error':'Servidor cheio.'}
        code=''.join(secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') for _ in range(8))
        while code in ROOMS: code=''.join(secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') for _ in range(8))
        host_side=secrets.choice((1,-1))
        r=dict(last=now,host=host_side,tokens={1:secrets.token_urlsafe(24),-1:secrets.token_urlsafe(24)},queues={1:[],-1:[]},seen={1:now,-1:now},closed=False,profiles={host_side:v['sender'],-host_side:pid},rule=v['rule'],ranked=v['ranked'],minutes=v.get('minutes',0))
        reset_match(r);ROOMS[code]=r;MATCH_QUEUE.pop(pid,None);MATCH_QUEUE.pop(v['sender'],None);v.update(state='accepted',code=code,time=now)
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
        elif self.path.split('?')[0] in ('/clube.js','/clube.css','/escola.js','/escola.css'):
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
            pid=identity(d)
            if not pid:return self.reply(200,{'found':False})
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
                token=secrets.token_urlsafe(24); side=secrets.choice((1,-1))
                pid=profile(d)
                if d.get('ranked') is not False and not pid: return self.reply(400,{'error':'Informe um perfil válido para jogar valendo PH.'})
                rule=d.get('rule','free')
                if not valid_rule(rule): return self.reply(400,{'error':'Regra inválida.'})
                ROOMS[code]={'last':now,'host':side,'tokens':{side:token},'queues':{1:[],-1:[]},'seen':{side:now},'closed':False,'profiles':{side:pid},'rule':rule,'ranked':d.get('ranked') is not False and not rule.startswith('custom-') and rule not in ('kings','international','canadian'),'minutes':clock_value(d),'public':d.get('public') is True}
                reset_match(ROOMS[code]);MATCH_QUEUE.pop(pid,None)
                return self.reply(200,{'code':code,'token':token,'connected':False,'side':side,'ranked':ROOMS[code]['ranked'],'minutes':ROOMS[code]['minutes']})
            code=str(d.get('code','')).upper(); r=ROOMS.get(code)
            if not r: return self.reply(404,{'error':'Sala inexistente ou encerrada.'})
            side=d.get('side'); r['last']=now
            if path=='/api/join':
                if r['closed']: return self.reply(404,{'error':'Sala encerrada.'})
                side=-r['host']
                if len(r['tokens'])==2: return self.reply(409,{'error':'Sala cheia.'})
                pid=profile(d)
                if r.get('ranked',True) and not pid: return self.reply(400,{'error':'Informe um perfil válido para jogar valendo PH.'})
                if pid and pid==r['profiles'].get(r['host']): return self.reply(409,{'error':'Use outro perfil ou navegador para o adversário.'})
                r['profiles'][side]=pid
                token=secrets.token_urlsafe(24); r['tokens'][side]=token; r['seen'][side]=now;MATCH_QUEUE.pop(pid,None)
                return self.reply(200,{'code':code,'token':token,'connected':True,'side':side,'ranked':r.get('ranked',True),'minutes':r.get('minutes',0)})
            if side not in (1,-1) or not secrets.compare_digest(r['tokens'].get(side,'!'),str(d.get('token',''))): return self.reply(403,{'error':'Sessão inválida.'})
            r['seen'][side]=now
            if not r['closed']: tick_clock(r,now)
            if path=='/api/resign':
                if len(r['tokens'])!=2: return self.reply(409,{'error':'Aguarde o adversário.'})
                if r['winner'] is None:
                    if r['closed']: return self.reply(409,{'error':'Sala encerrada.'})
                    finish(r,-game_side(r,side),True)
                return self.reply(200,{'ok':True,'result':result_for(r,side),'closed':r['closed']})
            if path=='/api/leave':
                if len(r['tokens'])==2 and r['winner'] is None: finish(r,-game_side(r,side),True)
                r['closed']=True
                return self.reply(200,{'ok':True,'result':result_for(r,side),'closed':True})
            if path=='/api/poll':
                if not r['closed'] and -side in r['seen'] and now-r['seen'][-side]>90:
                    if r['winner'] is None: finish(r,game_side(r,side),True)
                    r['closed']=True
                messages=r['queues'][side][:]; r['queues'][side].clear()
                return self.reply(200,{'connected':len(r['tokens'])==2,'messages':messages,'result':result_for(r,side),'closed':r['closed'],'snapshot':room_snapshot(r,side,now)})
            if r['closed']: return self.reply(409,{'error':'Sala encerrada.'})
            if path=='/api/send':
                if len(r['tokens'])!=2: return self.reply(409,{'error':'Aguarde o adversário.'})
                m=d.get('message')
                if not isinstance(m,str) or len(m)>12000: return self.reply(400,{'error':'Mensagem inválida.'})
                if len(r['queues'][-side])>=200: return self.reply(429,{'error':'Fila cheia.'})
                try:
                    msg=json.loads(m)
                    if not isinstance(msg,dict) or not process(r,side,msg): return self.reply(409,{'error':'Jogada ou ação inválida.'})
                except (ValueError,TypeError,KeyError,IndexError): return self.reply(400,{'error':'Mensagem inválida.'})
                if msg.get('type')=='rematch-ok':
                    event=r.pop('rematch_event',None)
                    if event:
                        for q in r['queues'].values(): q.append(event)
                elif msg.get('type')!='chat': r['queues'][-side].append(m)
                return self.reply(200,{'ok':True})
            return self.reply(404,{'error':'Rota inexistente.'})
    def log_message(self, fmt, *args): pass

if __name__=='__main__':
    from selftest import run
    run(sys.modules[__name__])
    setup()
    port=int(os.environ.get('PORT','8765'))
    print(f'Casa de Damas: http://localhost:{port} (Ctrl+C para encerrar)',flush=True)
    ThreadingHTTPServer(('0.0.0.0',port),Handler).serve_forever()
