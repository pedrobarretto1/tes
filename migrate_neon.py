"""One-time, read-only source migration. No credentials or player rows are logged."""
import ast, hashlib, json, os, threading, time
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import psycopg
from psycopg import sql

STATUS={"phase":"starting"}
HOLD_SECONDS=240
SCHEMA="public"

def state(phase, **extra):
    STATUS.clear(); STATUS.update(phase=phase, **extra)
    print("MIGRATION "+json.dumps(STATUS),flush=True)

def tables(conn):
    return [r[0] for r in conn.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename").fetchall()]

def columns(conn, table):
    return conn.execute("SELECT column_name,data_type,udt_name,is_nullable FROM information_schema.columns WHERE table_schema='public' AND table_name=%s ORDER BY ordinal_position",(table,)).fetchall()

def ident(table):
    return sql.Identifier(SCHEMA,table)

def count(conn, table):
    return conn.execute(sql.SQL("SELECT count(*) FROM {}").format(ident(table))).fetchone()[0]

def copy_query(table, cols):
    order=sql.SQL(",").join(sql.SQL("{}::text COLLATE \"C\"").format(sql.Identifier(c[0])) for c in cols)
    return sql.SQL("COPY (SELECT * FROM {} ORDER BY {}) TO STDOUT").format(ident(table),order)

def checksum(conn, table, cols):
    digest=hashlib.sha256()
    with conn.cursor().copy(copy_query(table,cols)) as cp:
        for chunk in cp:digest.update(chunk)
    return digest.hexdigest()

def install_schema(conn):
    node=next(n for n in ast.parse(Path("servidor.py").read_text(encoding="utf-8")).body if isinstance(n,ast.FunctionDef) and n.name=="setup")
    for call in ast.walk(node):
        if isinstance(call,ast.Call) and isinstance(call.func,ast.Name) and call.func.id=="sql" and len(call.args)>1 and isinstance(call.args[1],ast.Constant):
            conn.execute(call.args[1].value)

def migrate():
    stage="connect"
    missing=[k for k in ("SOURCE_DATABASE_URL","NEON_DATABASE_URL") if not os.environ.get(k,"").strip()]
    if missing:
        state("blocked",missing=missing)
        return
    try:
        with psycopg.connect(os.environ["SOURCE_DATABASE_URL"],connect_timeout=15) as src, psycopg.connect(os.environ["NEON_DATABASE_URL"],connect_timeout=15) as dst:
            stage="destination safety"
            if tables(dst):
                state("blocked",reason="Destination is not empty; no changes made.")
                return
            stage="schema"
            install_schema(dst)
            names=tables(src)
            if not names or names!=tables(dst):raise RuntimeError("schema table mismatch")
            for table in names:
                if columns(src,table)!=columns(dst,table):raise RuntimeError("schema column mismatch")
            stage="source lock"
            src.execute("SET LOCAL lock_timeout='12s'")
            src.execute(sql.SQL("LOCK TABLE {} IN SHARE MODE").format(sql.SQL(",").join(ident(t) for t in names)))
            state("copying",tables=len(names))
            stage="copy"
            total=0;counts={}
            for table in names:
                cols=columns(src,table);digest=hashlib.sha256()
                with src.cursor().copy(copy_query(table,cols)) as reader, dst.cursor().copy(sql.SQL("COPY {} FROM STDIN").format(ident(table))) as writer:
                    for chunk in reader:
                        digest.update(chunk);writer.write(chunk)
                n=count(src,table)
                if n!=count(dst,table) or digest.hexdigest()!=checksum(dst,table,cols):raise RuntimeError("verification mismatch")
                counts[table]=n;total+=n
            dst.commit()
            stage="verified"
            state("verified_locked",tables=len(names),rows=total,counts=counts,lockExpiresIn=HOLD_SECONDS,verifiedAt=int(time.time()))
            # Keep the source stable during the connection switch. Never write to it.
            time.sleep(HOLD_SECONDS)
            src.rollback()
            state("verified_released",tables=len(names),rows=total,counts=counts)
    except Exception as exc:
        state("failed",stage=stage,error=type(exc).__name__,sqlstate=getattr(exc,"sqlstate",None))

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body=json.dumps(STATUS).encode()
        self.send_response(200);self.send_header("Content-Type","application/json");self.send_header("Cache-Control","no-store");self.send_header("Content-Length",str(len(body)));self.end_headers();self.wfile.write(body)
    def log_message(self,*args):pass

if __name__=="__main__":
    threading.Thread(target=migrate,daemon=True).start()
    ThreadingHTTPServer(("0.0.0.0",int(os.environ.get("PORT","10000"))),Handler).serve_forever()
