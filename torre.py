"""Tower progression core used by the authoritative HTTP server.
The authoritative checkers engine supplies outcomes; this module does not decide
legal moves, accept client victories or award account cosmetics.
"""
from dataclasses import dataclass, replace
from uuid import uuid4

DOMAINS = (
    (1, 25, "castle", "Castelo Esquecido", "O Cavaleiro Sem Nome"),
    (26, 50, "crypt", "Catacumbas dos Reis", "O Rei Esquecido"),
    (51, 75, "gold", "Império Dourado", "O Imperador de Ouro"),
    (76, 100, "cosmos", "Trono do Fim", "O Rei Primordial"),
)
# Keep existing beta players at 26–30 playable; later chapters not released.
RELEASE_MAX_FLOOR = 30
TOTAL_FLOORS = 100
CATALOG_VERSION = 2
MODES = ("ascensao", "expedicao")
ROUTES = ("guardian", "executioner", "unknown")
CHAPTERS = {
    "castle": ("Portões", "Muralhas", "Salão das Armas", "Salão da Guarda", "Trono Abandonado"),
    "crypt": ("Entrada da Cripta", "Galeria dos Nomes", "Sepulcros", "Câmara dos Reis", "Tumba Real"),
    "gold": ("Portão Imperial", "Galeria das Vitórias", "Conselho Imperial", "Salão do Sol", "Trono Imperial"),
    "cosmos": ("Limiar Astral", "Órbita Celestial", "Véu do Vazio", "Horizonte do Eclipse", "Trono do Fim"),
}
CASTLE = (
    ("O Escudeiro Perdido", 1.0, "Posicionamento simples"),
    ("O Vigia da Ponte", 1.1, "Proteção de peças"),
    ("O Soldado de Ferro", 1.2, "Capturas imediatas"),
    ("O Guardião do Portão", 1.3, "Defesa e espaço"),
    ("O Sentinela", 1.7, "Defesa e ataque"),
    ("O Arqueiro da Muralha", 1.5, "Controle das diagonais"),
    ("O Lanceiro", 1.6, "Avanço agressivo"),
    ("O Protetor da Fortaleza", 1.8, "Defesa em grupos"),
    ("O Tenente da Guarda", 1.9, "Capturas múltiplas"),
    ("O Capitão", 2.3, "Centro e contra-ataques"),
    ("O Ferreiro Real", 2.1, "Estrutura defensiva"),
    ("O Espadachim", 2.2, "Ataques rápidos"),
    ("O Mestre dos Escudos", 2.3, "Proteção de ameaçadas"),
    ("O Duelista da Coroa", 2.5, "Sacrifícios e combinações"),
    ("O Carrasco", 2.9, "Armadilhas de captura"),
    ("O Cavaleiro de Bronze", 2.7, "Rotas de promoção"),
    ("O Vigia Real", 2.8, "Antecipação de ameaças"),
    ("O Comandante de Ferro", 3.0, "Pressão coordenada"),
    ("O Conselheiro da Coroa", 3.2, "Trocas favoráveis e finais"),
    ("O Estrategista", 3.6, "Planejamento e promoção"),
    ("O Último Sentinela", 3.3, "Defesa e paciência"),
    ("O Arauto do Trono", 3.5, "Diagonais e damas"),
    ("O Guardião da Coroa", 3.7, "Pressão e contra-ataque"),
    ("O Portador do Selo", 4.0, "Defesa avançada e finais"),
    ("O Cavaleiro Sem Nome", 4.5, "Defesa e contra-ataque"),
)
# The first five crypt floors stay accessible for existing beta players.
CRYPT_BETA = (
    ("O Vigia da Cripta", 3.8, "Segurança e contra-ataque"),
    ("O Guardião dos Ossos", 3.9, "Controle das diagonais"),
    ("A Sombra da Tumba", 4.0, "Armadilhas"),
    ("O Zelador dos Túmulos", 4.1, "Defesa"),
    ("O Guardião das Tumbas", 4.3, "Contra-ataque"),
)

def domain(floor):
    for lo, hi, key, title, boss in DOMAINS:
        if lo <= floor <= hi:
            return {"id": key, "name": title, "boss": boss if floor == hi else None,
                    "first": lo, "last": hi, "final_boss": boss}
    return None

def encounter(floor):
    d = domain(floor)
    if not d:
        return None
    local = floor - d["first"] + 1
    stage = (local - 1) // 5 + 1
    kind = "boss" if local == 25 else "preboss" if local == 24 else "elite" if local % 5 == 0 else "normal"
    detail = CASTLE[local - 1] if d["id"] == "castle" else CRYPT_BETA[local - 1] if d["id"] == "crypt" and local <= 5 else (d["final_boss"] if kind == "boss" else "Guardião do andar " + str(floor), None, "Em desenvolvimento")
    name, difficulty, style = detail
    tier = 0 if difficulty is None or difficulty < 2 else 1 if difficulty < 3 else 2 if difficulty < 4 else 3
    if kind == "elite": tier = min(3, tier + 1)
    return {"floor": floor, "id": f'{d["id"]}-{local:02d}', "name": name, "kind": kind,
            "difficulty": difficulty, "style": style, "stage": stage,
            "chapter": CHAPTERS[d["id"]][stage-1], "tier": tier,
            "released": floor <= RELEASE_MAX_FLOOR, "fixed": kind != "normal",
            "checkpoint_after": local in (10, 20, 25)}

@dataclass(frozen=True)
class Run:
    id: str
    mode: str
    floor: int = 1
    highest: int = 0
    checkpoint: int = 1
    lives: int = 3
    status: str = "choose"
    route: str | None = None
    match: str | None = None
    last_result_match: str | None = None
    version: int = 0

def new_run(mode="ascensao"):
    if mode not in MODES:
        raise ValueError("Modo inválido")
    return Run(id=uuid4().hex, mode=mode)

def choose(run, route):
    if run.status != "choose" or route not in ROUTES or (encounter(run.floor)["fixed"] and route != "guardian"):
        raise ValueError("Escolha indisponível")
    return replace(run, status="ready", route=route, version=run.version + 1)

def start_match(run, match_id):
    if run.status != "ready" or not isinstance(match_id, str) or not match_id:
        raise ValueError("Partida indisponível")
    if match_id == run.last_result_match:
        raise ValueError("Partida já concluída")
    return replace(run, match=match_id, status="playing", version=run.version + 1)

def finish_match(run, match_id, outcome):
    """Only call with the server engine's terminal result in a DB transaction."""
    if match_id and match_id == run.last_result_match:
        return run
    if run.status != "playing" or not match_id or match_id != run.match:
        raise ValueError("Partida não pertence a esta expedição")
    if outcome not in ("win", "loss", "draw"):
        raise ValueError("Resultado inválido")
    changes = dict(match=None, last_result_match=match_id, route=None,
                   version=run.version + 1, status="choose")
    if outcome == "win":
        best = max(run.highest, run.floor)
        changes["highest"] = best
        if run.floor >= RELEASE_MAX_FLOOR:
            changes["status"] = "completed"
        else:
            changes["floor"] = run.floor + 1
            if run.mode == "ascensao" and encounter(run.floor)["checkpoint_after"]:
                changes["checkpoint"] = run.floor + 1
                changes["lives"] = 3
    elif outcome == "loss":
        changes["lives"] = run.lives - 1
        if changes["lives"] <= 0:
            if run.mode == "ascensao":
                changes.update(floor=run.checkpoint, lives=3, status="choose")
            else:
                changes["status"] = "ended"
    # A draw leaves floor and lives unchanged; choose a new route.
    return replace(run, **changes)

def public_state(run):
    from dataclasses import asdict
    d = domain(run.floor)
    return {**asdict(run), "domain": d, "encounter": encounter(run.floor),
            "realm_map": [encounter(n) for n in range(d["first"], d["last"] + 1)],
            "release_max_floor": RELEASE_MAX_FLOOR, "total_floors": TOTAL_FLOORS,
            "catalog_version": CATALOG_VERSION}
