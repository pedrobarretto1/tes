"""Authoritative computer duels. One persisted match per player; no client result claims."""
import json, secrets, time

LEVELS=('medium','hard')
RANKED_RULES=('free','official','english','mandatory','giveaway')
def setup(db,sql):
    sql(db,"CREATE TABLE IF NOT EXISTS bot_duels (player_id TEXT PRIMARY KEY, payload TEXT NOT NULL)")

def apply(board,m):
    b=board[:];p=b[m['from']];to=m['path'][-1];n=int(len(b)**.5)
    b[m['from']]=0
    for i in m['cap']:b[i]=0
    b[to]=p*2 if abs(p)==1 and to//n==(0 if p>0 else n-1) else p
    return b

def choose(s,b,side,rule,level):
    moves=s.legal(b,side,rule)
    if not moves:return None
    deadline=time.monotonic()+(.65 if level=='hard' else .24)
    nodes=0;limit=18000 if level=='hard' else 3500;best=moves[0];n=int(len(b)**.5)
    class Budget(Exception):pass
    def evaluate(x,t):
        value=0
        for i,p in enumerate(x):
            if not p:continue
            z=1 if p>0 else -1;r,c=divmod(i,n)
            v=(320 if abs(p)==2 else 100+(n-1-r if z==1 else r)*5)+min(r,n-1-r,c,n-1-c)*3
            if abs(p)==1 and r==(n-1 if z==1 else 0):v+=5
            value+=z*t*v
        return -value if rule=='giveaway' else value
    def search(x,t,d,a,z,ply):
        nonlocal nodes
        nodes+=1
        if nodes>limit or time.monotonic()>deadline:raise Budget()
        ms=s.legal(x,t,rule)
        if not ms:return (100000-ply) if rule=='giveaway' else (-100000+ply)
        if not d:return evaluate(x,t)
        v=-200000
        for m in ms:
            v=max(v,-search(apply(x,m),-t,d-1,-z,-a,ply+1));a=max(a,v)
            if a>=z:break
        return v
    for d in range(1,7 if level=='hard' else 4):
        val=-200000;candidate=best
        try:
            for m in moves:
                score=-search(apply(b,m),-side,d-1,-200000,-val,1)
                if score>val:val=score;candidate=m
        except Budget:break
        best=candidate;moves=[best]+[m for m in moves if m!=best]
    return best

def amount(value,level):
    return value if level=='hard' else (1 if value>=0 else -1)*((abs(value)+1)//2)

def finish(s,db,pid,g,w,reason):
    if g['result'] is not None:return
    side=g['side'];outcome='draw' if w==0 else 'win' if w==side else 'resign' if reason=='resign' else 'loss'
    delta=amount({'win':25,'draw':5,'loss':-15,'resign':-20}[outcome],g['level'])
    coins=amount(15 if outcome=='win' else 8,g['level']) if outcome!='resign' and g['sequence']>=8 else 0
    old=s.sql(db,'SELECT points,name FROM players WHERE id=?',(pid,)).fetchone()
    inserted=s.sql(db,'INSERT INTO results(id) VALUES(?) ON CONFLICT(id) DO NOTHING',(g['match'],)).rowcount
    actual=max(0,old[0]+delta)-old[0]
    if inserted:
        s.sql(db,'UPDATE players SET points=CASE WHEN points+? < 0 THEN 0 ELSE points+? END,wins=wins+?,losses=losses+?,draws=draws+? WHERE id=?',(delta,delta,int(outcome=='win'),int(outcome in ('loss','resign')),int(outcome=='draw'),pid))
        s.sql(db,'INSERT INTO match_history(match_id,player_id,opponent,outcome,delta,played_at) VALUES(?,?,?,?,?,?)',(g['match'],pid,'Computador · '+('Difícil' if g['level']=='hard' else 'Médio'),outcome,actual,time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())))
        s.award_progress(db,pid,outcome,s.match_stats(g)[str(side)]['promotions'])
        if coins:s.wallet_add(db,pid,coins)
    else:
        actual=0;coins=0
    g['result']=dict(match=g['match'],winner=w,reason=reason,ranked=True,side=side,rule=g['rule'],level=g['level'],bot=True,deltas={str(side):actual},coins=coins,points={str(side):old[0]+actual},board=g['board'][:],turn=g['turn'],sequence=g['sequence'],moves=g['moves'][:],stats=s.match_stats(g),duration=max(0,int(time.time()-g['started'])),names={str(side):old[1],str(-side):'Computador'})
    if inserted:s.sql(db,'INSERT INTO replays(match_id,player_a,player_b,payload) VALUES(?,?,?,?) ON CONFLICT(match_id) DO NOTHING',(g['match'],pid,'bot:'+g['level'],json.dumps(g['result'])))

def tick(s,db,pid,g):
    if g['result'] is not None or not g['minutes']:return
    # The bot's clock starts when its search is requested, not while animations/network wait.
    if g['turn']!=g['side']:return
    now=time.time();key=str(g['turn'])
    g['remaining'][key]=max(0,g['remaining'][key]-max(0,now-g['clock_at']));g['clock_at']=now
    if g['remaining'][key]<=0:finish(s,db,pid,g,-g['turn'],'timeout')

def play(s,db,pid,g,m):
    side=g['turn'];p=g['board'][m['from']];g['board']=apply(g['board'],m);g['turn']=-side;g['sequence']+=1
    g['moves'].append(dict(m,side=side,promotion=abs(p)==1 and abs(g['board'][m['path'][-1]])==2))
    g['quiet']=g['quiet']+1 if not m['cap'] and abs(p)==2 else 0
    k=s.boardkey(g);g['repeats'][k]=g['repeats'].get(k,0)+1;g['clock_at']=time.time();g['offer']=False
    if not s.legal(g['board'],g['turn'],g['rule']):finish(s,db,pid,g,g['turn'] if g['rule']=='giveaway' else side,'giveaway' if g['rule']=='giveaway' else 'normal')
    elif g['quiet']>=40 or g['repeats'][k]>=3:finish(s,db,pid,g,0,'normal')
    elif g['turn']==g['side'] and g['rule']!='giveaway' and g['sequence']-g['offer_at']>=10 and 0<sum(bool(p) for p in g['board'])<=4 and all(abs(p)!=1 for p in g['board']) and all(not any(m['cap'] for m in s.legal(g['board'],t,g['rule'])) for t in (1,-1)) and (g['quiet']>=8 or g['repeats'][k]>=2):
        g['offer']=True;g['offer_at']=g['sequence']

def action(s,path,d,pid):
    op=path.rsplit('/',1)[-1];sql=s.sql
    def err(msg,status=400):return status,{'error':msg}
    with s.database() as db:
        # A per-player row lock serializes moves/rewards across processes.
        sql(db,"INSERT INTO bot_duels(player_id,payload) VALUES(?,?) ON CONFLICT(player_id) DO NOTHING",(pid,''))
        sql(db,'UPDATE bot_duels SET payload=payload WHERE player_id=?',(pid,))
        raw=sql(db,'SELECT payload FROM bot_duels WHERE player_id=?',(pid,)).fetchone()[0];g=json.loads(raw) if raw else None
        def response():
            sql(db,'UPDATE bot_duels SET payload=? WHERE player_id=?',(json.dumps(g),pid))
            return 200,g
        if op=='start':
            level=d.get('level');rule=d.get('rule');minutes=d.get('minutes',0)
            if level not in LEVELS or rule not in RANKED_RULES or type(minutes) is not int or minutes not in (0,1,3,5,10):return err('Dificuldade, regra ou relógio inválido.')
            # Idempotent start on network retry; new start closes an unfinished duel as resignation.
            nonce=d.get('nonce')
            if not isinstance(nonce,str) or not 16<=len(nonce)<=80:return err('Pedido inválido.')
            if g and g.get('nonce')==nonce:return response()
            if g and g['result'] is None:finish(s,db,pid,g,-g['side'],'resign')
            now=time.time();side=secrets.choice((1,-1));g=dict(match=secrets.token_hex(16),nonce=nonce,level=level,rule=rule,side=side,board=s.initial_for(rule),turn=1,sequence=0,moves=[],quiet=0,repeats={},result=None,minutes=minutes,remaining={'1':minutes*60,'-1':minutes*60},clock_at=now,started=now,offer=False,offer_at=-100)
            g['repeats'][s.boardkey(g)]=1
            return response()
        if not g or d.get('match')!=g['match']:return err('Partida indisponível. Inicie uma nova.',409)
        if g['result'] is not None:return response()
        tick(s,db,pid,g)
        if g['result'] is not None:return response()
        if op=='state':return response()
        if op=='resign':finish(s,db,pid,g,-g['side'],'resign');return response()
        if d.get('sequence')!=g['sequence']:return response()
        if op=='move':
            if g['turn']!=g['side']:return err('Não é sua vez.',409)
            m=d.get('move')
            if m not in s.legal(g['board'],g['turn'],g['rule']):return err('Lance ilegal.',409)
            play(s,db,pid,g,m)
        elif op=='bot':
            if g['turn']==g['side']:return err('Não é a vez do computador.',409)
            start=time.monotonic();m=choose(s,g['board'],g['turn'],g['rule'],g['level'])
            if g['minutes']:
                key=str(g['turn']);g['remaining'][key]=max(0,g['remaining'][key]-(time.monotonic()-start))
                if g['remaining'][key]<=0:finish(s,db,pid,g,g['side'],'timeout');return response()
            if not m:return err('Não há lance disponível.',409)
            play(s,db,pid,g,m)
        elif op=='draw':
            if not g['offer'] or g['turn']!=g['side'] or type(d.get('accept')) is not bool:return err('Oferta de empate indisponível.',409)
            g['offer']=False
            if d['accept']:finish(s,db,pid,g,0,'agreement')
        else:return err('Ação inválida.',404)
        return response()
