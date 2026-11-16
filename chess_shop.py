"""Account-owned chess cosmetics. All mutations run under chess_guard."""
import time
CATEGORIES=('pieces','board','scene','effect')
CATALOG=[]
def item(category,style,name,description,price,exclusive=False):
    CATALOG.append(dict(id=category+'-'+style,category=category,style=style,name=name,description=description,price=price,exclusive=exclusive,
        collection={'classic':'Clássico','imperial':'Império Dourado','obsidian':'Ordem da Obsidiana','champion':'Copa de Honra'}[style],
        rarity='Épico · Exclusivo' if exclusive else 'Clássico' if style=='classic' else 'Lendário'))
for category,name,description in (
    ('pieces','Peças Clássicas','Madeira entalhada original.'),
    ('board','Tabuleiro Clássico','Seu tema gratuito ou conquistado na Jornada.'),
    ('scene','Salão de Madeira','O ambiente tradicional da Casa de Xadrez.'),
    ('effect','Efeitos Clássicos','Animações originais de movimento e resultado.'),
):item(category,'classic',name,description,0)
for category,name,description,price in (
    ('pieces','Corte de Marfim','Seis peças entalhadas em marfim e ouro, contra bronze real.',90),
    ('board','Mesa Imperial','Mármore claro e nogueira dourada, com moldura de ouro.',60),
    ('scene','Salão Imperial','Vitrais, pilares e luz dourada do trono real.',45),
    ('effect','Aurora Imperial','Anel dourado de captura, promoção e brilho de vitória.',30),
):item(category,'imperial',name,description,price)
for category,name,description,price in (
    ('pieces','Ordem da Obsidiana','Marfim cinzento contra obsidiana com detalhes de rubi.',90),
    ('board','Tabuleiro de Ônix','Pedra clara e ônix escuro, com acabamento em rubi.',60),
    ('scene','Fortaleza de Rubi','Estandartes rubros, pilares e penumbra.',45),
    ('effect','Brasas da Ordem','Fragmentos rubros em capturas e promoções.',30),
):item(category,'obsidian',name,description,price)
item('pieces','champion','Guardas das Oito Coroas','Reis e peças em ouro claro contra aço verde-real. Exclusivas dos campeões.',0,True)
item('board','champion','Arena das Oito Coroas','Tabuleiro esmeralda e ouro conquistado na Copa de Honra.',0,True)
BY_ID={i['id']:i for i in CATALOG}
DEFAULTS={c:c+'-classic' for c in CATEGORIES}
def setup(db,sql):
    sql(db,"CREATE TABLE IF NOT EXISTS chess_shop_owned (player_id TEXT NOT NULL, item_id TEXT NOT NULL, bought_at DOUBLE PRECISION NOT NULL, PRIMARY KEY(player_id,item_id))")
    sql(db,"CREATE TABLE IF NOT EXISTS chess_shop_equipped (player_id TEXT NOT NULL, category TEXT NOT NULL, item_id TEXT NOT NULL, PRIMARY KEY(player_id,category))")
def state(db,sql,pid):
    owned=set(DEFAULTS.values())|{r[0] for r in sql(db,'SELECT item_id FROM chess_shop_owned WHERE player_id=?',(pid,)).fetchall() if r[0] in BY_ID}
    equipped=dict(DEFAULTS)
    for cat,i in sql(db,'SELECT category,item_id FROM chess_shop_equipped WHERE player_id=?',(pid,)).fetchall():
        if i in owned and BY_ID[i]['category']==cat:equipped[cat]=i
    return dict(owned=sorted(owned),equipped=equipped)
def action(db,sql,pid,op,d):
    if op=='shop-state':return 200,{}
    iid=d.get('item')
    if not isinstance(iid,str) or iid not in BY_ID:return 400,{'error':'Relíquia inválida.'}
    item=BY_ID[iid];current=state(db,sql,pid)
    if op=='shop-buy':
        if iid in current['owned']:return 200,{}
        if item.get('exclusive'):return 403,{'error':'Este item é conquistado ao vencer a Copa de Honra.'}
        # The guarded transaction atomically charges and grants ownership.
        row=sql(db,'UPDATE chess_profiles SET coins=coins-? WHERE player_id=? AND coins>=?',(item['price'],pid,item['price']))
        if not row.rowcount:return 409,{'error':'Moedas de Xadrez insuficientes.'}
        sql(db,'INSERT INTO chess_shop_owned VALUES(?,?,?)',(pid,iid,time.time()))
        return 200,{}
    if iid not in current['owned']:return 403,{'error':'Adquira esta relíquia antes de equipar.'}
    sql(db,'INSERT INTO chess_shop_equipped VALUES(?,?,?) ON CONFLICT(player_id,category) DO UPDATE SET item_id=excluded.item_id',(pid,item['category'],iid))
    return 200,{}
