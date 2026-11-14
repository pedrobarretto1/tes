"""Tower progression core (not exposed by the live HTTP server).
The authoritative checkers engine supplies outcomes; this module does not decide
legal moves, accept client victories or award account cosmetics.
"""
from dataclasses import dataclass, replace
from uuid import uuid4

DOMAINS = (
    (1, 10, "castle", "Castelo Esquecido", "O Cavaleiro Sem Nome"),
    (11, 20, "crypt", "Catacumbas dos Reis", "O Rei Esquecido"),
    (21, 30, "gold", "Império Dourado", "O Imperador de Ouro"),
    (91, 100, "cosmos", "Trono do Fim", "O Rei Primordial"),
)
# Only the first domain is intended for the first playable release.
# The intervening domains 31–90 have not been designed yet.
RELEASE_MAX_FLOOR = 10
MODES = ("ascensao", "expedicao")
ROUTES = ("guardian", "executioner", "unknown")

def domain(floor):
    for lo, hi, key, title, boss in DOMAINS:
        if lo <= floor <= hi:
            return {"id": key, "name": title, "boss": boss if floor == hi else None,
                    "first": lo, "last": hi}
    return None

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
    if run.status != "choose" or route not in ROUTES:
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
            if run.mode == "ascensao" and run.floor % 10 == 0:
                changes["checkpoint"] = run.floor + 1
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
    return {**asdict(run), "domain": domain(run.floor),
            "release_max_floor": RELEASE_MAX_FLOOR}
