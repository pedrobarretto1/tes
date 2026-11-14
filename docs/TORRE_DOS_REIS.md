# Torre dos Reis — beta jogável

A Torre é um modo solo de partidas completas de damas brasileiras. A beta habilita
30 andares nos três reinos contíguos já desenhados: Castelo Esquecido (1–10, chefe
Cavaleiro Sem Nome), Catacumbas dos Reis (11–20, Rei Esquecido) e Império Dourado
(21–30, Imperador de Ouro). A arena original V3 fornecida pelo criador é preservada
em torre.html, com tabuleiro interativo independente e camada SVG decorativa.
Trono do Fim e Rei Primordial (91–100) permanecem reservados; 31–90 não definidos.

## Regras
- Ascensão: três coroas; derrota consome uma; após perder todas, volta ao último
  santuário (1, 11, 21), preservando o maior andar conquistado na tentativa.
  Santuários restauram as coroas. Empate não consome coroa nem avança.
- Expedição: três coroas, sem retorno ao santuário; tentativa termina ao esgotar.
- Rotas Guardião, Carrasco e Desconhecido ajustam a força da IA.
  A base sobe a cada seis andares; chefes e Carrasco elevam um nível; Desconhecido
  varia um nível para cima/baixo. Cinco perfis do motor existente (3–11 profundidade).
- Resultado, jogadas, IA, limites de empate e desistência validados pelo servidor.
  Estado salvo por jogador e modo em tower_runs, em transação; sem PH,
  moedas, cosméticos ou ranking durante beta. Recompensas após testes.
- A skin/tema do perfil permanecem independentes do ambiente; efeitos pausam
  quando a página fica oculta e respeitam redução de movimento.

## Validação
test_torre.py cobre a progressão, coroas, checkpoints, fim de expedição e
idempotência. test_torre_api.py testa movimento real, lance inválido, reabertura,
reenvio, desistência e isolamento de Jornada/PH em SQLite temporário.
O servidor executa esses testes antes de inicializar o Neon de produção.

## Futuro
- Ajustar dificuldade com feedback e testes de partidas.
- Projetar reinos 31–90, caminhos narrativos e finais.
- Cosméticos e ambientes conquistados por reino, sem benefícios competitivos.
- Andar 100 terá prêmio exclusivo distinto do tabuleiro do Rei Cósmico da Jornada;
  identidade final a definir.
