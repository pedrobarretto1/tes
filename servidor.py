from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import json, secrets, threading, time, os

ROOMS = {}
LOCK = threading.Lock()
TTL = 60 * 60 * 4
BASE = Path(__file__).resolve().parent

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
        elif self.path == '/api/health': self.reply(200, {'ok':True})
        else: self.reply(404, {'error':'Página inexistente.'})
    def do_POST(self):
        try:
            n=int(self.headers.get('Content-Length','0'))
            if not 0<n<=32768: raise ValueError()
            d=json.loads(self.rfile.read(n)); assert isinstance(d,dict)
        except Exception: return self.reply(400, {'error':'Pedido inválido.'})
        path=self.path.split('?')[0]; now=time.monotonic()
        with LOCK:
            for k,r in list(ROOMS.items()):
                if now-r['last']>TTL: del ROOMS[k]
            if path=='/api/create':
                if len(ROOMS)>=1000: return self.reply(503, {'error':'Servidor cheio.'})
                code=''.join(secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') for _ in range(8))
                while code in ROOMS: code=''.join(secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') for _ in range(8))
                token=secrets.token_urlsafe(24); side=d.get('side')
                if side not in (1,-1): return self.reply(400,{'error':'Player inválido.'})
                ROOMS[code]={'last':now,'host':side,'tokens':{side:token},'queues':{1:[],-1:[]},'seen':{side:now},'closed':False}
                return self.reply(200,{'code':code,'token':token,'connected':False})
            code=str(d.get('code','')).upper(); r=ROOMS.get(code)
            if not r or r['closed']: return self.reply(404,{'error':'Sala inexistente ou encerrada.'})
            side=d.get('side'); r['last']=now
            if path=='/api/join':
                if side!=-r['host']: return self.reply(409,{'error':'Escolha o Player oposto ao criador.'})
                if len(r['tokens'])==2: return self.reply(409,{'error':'Sala cheia.'})
                token=secrets.token_urlsafe(24); r['tokens'][side]=token; r['seen'][side]=now
                return self.reply(200,{'code':code,'token':token,'connected':True})
            if side not in (1,-1) or not secrets.compare_digest(r['tokens'].get(side,'!'),str(d.get('token',''))): return self.reply(403,{'error':'Sessão inválida.'})
            r['seen'][side]=now
            if path=='/api/leave':
                r['closed']=True; return self.reply(200,{'ok':True})
            if path=='/api/poll':
                if -side in r['seen'] and now-r['seen'][-side]>90:
                    r['closed']=True; return self.reply(410,{'error':'Adversário desconectado.'})
                messages=r['queues'][side][:]; r['queues'][side].clear()
                return self.reply(200,{'connected':len(r['tokens'])==2,'messages':messages})
            if path=='/api/send':
                if len(r['tokens'])!=2: return self.reply(409,{'error':'Aguarde o adversário.'})
                m=d.get('message')
                if not isinstance(m,str) or len(m)>12000: return self.reply(400,{'error':'Mensagem inválida.'})
                if len(r['queues'][-side])>=200: return self.reply(429,{'error':'Fila cheia.'})
                r['queues'][-side].append(m); return self.reply(200,{'ok':True})
            return self.reply(404,{'error':'Rota inexistente.'})
    def log_message(self, fmt, *args): pass

if __name__=='__main__':
    port=int(os.environ.get('PORT','8765'))
    print(f'Casa de Damas: http://localhost:{port} (Ctrl+C para encerrar)',flush=True)
    ThreadingHTTPServer(('0.0.0.0',port),Handler).serve_forever()
