# Torre dos Reis — estado atual e continuidade

Atualizado em 14/11/2026. Ver [plano dos 100 andares](TORRE_PLANO_100.md)
para a expansão e [histórico](CHANGELOG.md) para as correções.
O catálogo v2 está implementado na branch torre-castelo-25; consultar o changelog para confirmação da publicação.

## Produção confirmada
- Site: https://casa-de-damas.onrender.com/torre.html
- Última revisão funcional confirmada: af974ab8498538e9151c8b15fc32d2db421d4037
  (Render dep-dbs8ap3bc2fs73as9log, live). O criador aprovou cenário em
  tela cheia, mesa grande e layout tradicional.
- Beta 1–30: Castelo 1–10 / Catacumbas 11–20 / Império 21–30.
  Chefes: Cavaleiro Sem Nome, Rei Esquecido, Imperador de Ouro.
  Trono do Fim (cosmos) está no SVG, mas não é jogável.
- Revisão v2: Castelo 1–25, Catacumbas 26–50, Império 51–75, Trono do Fim 76–100. Limite jogável 30; Castelo completo e entrada das Catacumbas 26–30. Andares 31–100 visíveis no catálogo, não liberados.

## Arquivos e contratos
| Arquivo | Função |
|---|---|
| index.html | Menu Clube → Torre (menutower), impede saída de sala online |
| torre.html | Interface independente da Jornada, SVG original, mesa tradicional, HUD |
| torre.py | Run imutável, DOMAINS, RELEASE_MAX_FLOOR, choose/start_match/finish_match |
| servidor.py | tower_action, /api/social/tower/*, motor oficial, persistência |
| test_torre.py | Progressão, coroas, checkpoint, término, idempotência |
| test_torre_api.py | Partida real, lance inválido, recarga, reenvio, resign e isolamento |
| selftest.py | Regressão geral do jogo |
| docs/TORRE_PLANO_100.md | Proposta de evolução até 100 andares |
| docs/CHANGELOG.md | Registro obrigatório das mudanças |

## Regras atuais
- Ascensão: 3 coroas; vitória avança; derrota/desistência perde uma coroa;
  empate não avança nem perde; ao zerar, volta ao checkpoint (1/11/21/26)
  e restaura três, preservando recorde. Santuário restaura coroas.
- Expedição: 3 coroas, sem retorno; fim ao zerar. Tentativas independentes.
- Catálogo v2: encounter, realm_map, total_floors e catalog_version no payload. Rotas guardião/carrasco/desconhecido nos andares normais; elites, pré-boss e boss fixos. Perfil da IA derivado da meta D, Carrasco sobe um perfil, Desconhecido varia um perfil. Cinco perfis de busca (3/5/7/9/11 máximos). Estilos ainda são metas, não IA especializada. Finais/caminhos narrativos
  e recompensas cosméticas não implementados.
- Partida completa, brasileira (lei da maioria), 8×8, claras humanas,
  sem limite de tempo geral, com contagem oficial de finais.
- API autenticada por perfil: state, start, move, resign, draw, restart.
  Não aceitar resultado do cliente; validar jogada, partida e sequência.
  tower_runs guarda JSON com progress/game por player_id e mode; transação,
  versão e resultado idempotente. Não há concessão de PH, moedas ou ranking.
- Ambiente independente da skin/tema. .tower-world fixo ocupa viewport;
  .shell e .arena possuem layout tradicional, cartas, 64 casas, lateral
  com mapa 5×5 do reino atual, capítulos, ícones, inimigo e histórico. Cinco estágios SVG aditivos do Castelo. Sincronizar data-realm/data-stage/data-fx;
  efeitos pausados em aba oculta e respeitam redução de movimento.
  Variáveis de material da mesa vêm também de escola.css.
- A mesa não deve ser miniaturizada dentro do SVG; não reintroduzir
  caixas opacas que escondem a arquitetura.

## Validação
python -m py_compile servidor.py torre.py
python -m unittest test_torre.py test_torre_api.py -v
python -c "import servidor,selftest; selftest.run(servidor)"

Os oito testes Torre e o SELFTEST geral passaram na publicação da beta e
reformulação. O startup executa a suíte Torre em SQLite temporário antes
de setup Neon. A camada full-screen teve simulação JS de troca de reino,
64 casas e pausa de animação; o criador aprovou visualmente. Testes reais
de FPS e de todos os 100 andares ainda não existem.

## Próximo passo
Validar visualmente os cinco estágios do Castelo e a nova grade; calibrar IA em partidas reais. Detalhar Catacumbas 31–50 antes de ampliar o limite. Conservar runs legadas (inclusive 26–30 e completed), sem reset. Recompensas e cerimônias ainda pendentes. Recompensa do 100 diferente do tabuleiro do Rei Cósmico.
