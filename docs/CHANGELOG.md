# Histórico de alterações — Casa de Damas

Registro acumulativo para próximas sessões. Entradas anteriores foram
reconstruídas a partir de commits, testes e conversas já registradas; não
representam verificação visual retroativa. Acrescentar uma entrada para toda
correção/alteração futura, mesmo pequena. Mais recente primeiro.

## 14/11/2026 — Pedido de empate em janela do jogo
- Pedido: destacar a oferta de empate na tela do adversário, sem aviso genérico
  do navegador, com foco visual e decisões dentro do jogo.
- index.html: dialog drawdialog, card medieval em madeira/dourado, ícone SVG,
  nome do adversário, mensagem de PH, botões Aceitar empate/Continuar jogando.
  Backdrop escurece a mesa; foco acessível no botão de continuar, sem alert/confirm.
- syncDrawDialog integra clockSnapshot.drawOffer em updateDuelControls;
  respondDraw envia draw-accept/draw-decline pelo protocolo existente. Janela
  abre apenas para destinatário online, inclusive modo concentração, e fecha
  quando servidor limpa oferta, termina partida, reinicia ou desconecta.
  drawReplyPending evita duplicidade; reconexão/erro libera tentativa; ações
  bloqueadas sem conexão. Escape não aceita/recusa implicitamente. Relógio não
  pausa. Antigos avisos laterais ocultos; IA e Torre/Jornada preservadas.
- Testes: sintaxe dos scripts OK; simulação isolada aprovada para abertura
  única, resposta de recusa/aceite, proteção de duplicidade, atualização de
  PH/casual, fechamento por estado/resultado, reconexão e ausência de janela
  no remetente/offline. Sem teste visual em dois navegadores reais.
- Commit cf0a2e3b; publicação a confirmar. Sem alteração de servidor ou banco.
- Rollback: reverter commit funcional para restaurar aviso lateral.

## 14/11/2026 — Aceitar desafio abre escolha antes de criar a sala
- Pedido: ao aceitar um desafio recebido, abrir uma tela própria para escolher
  a modalidade antes de entrar na partida, em vez do seletor no cartão do convite.
- clube.js: renderClub exibe Aceitar desafio e Recusar; openChallengeChoice
  apenas abre modal, sem requisição. confirmChallengeChoice envia a modalidade
  selecionada a challenge/respond somente na confirmação. Botão Voltar mantém
  convite pendente; Escape volta; expiração bloqueia confirmação; envio duplicado
  bloqueado; joinInvitation fecha modal. Sugestão inicial, tempo e elegibilidade
  de PH exibidos. Contrato servidor e regras de ranking permanecem intactos.
- index.html: challengechoiceoverlay, cache clube.js v67 e clube.css v63.
  clube.css: modal com identidade do Clube e responsividade.
- Testes: sintaxe JS e simulação isolada do fluxo aprovadas: primeira aceitação
  sem API, Voltar sem requisição, restrição casual, confirmação única com regra
  escolhida, convite expirado bloqueado. Não houve teste em dois navegadores.
- Commits: 066e24de, b3c34c1b, aa04b8e8. Sem mudança em servidor, banco, Torre
  ou Jornada. Render live: dep-dbsa0iuc6qcc738jr8mg, commit 77c95e30c99e128155b830b39cd37acbef2b6ef0.
  SELFTEST geral e 8 testes da Torre aprovados; Neon conectado.
- Rollback: reverter os três commits funcionais e preservar o seletor anterior.

## 14/11/2026 — Desafiado escolhe a modalidade do convite
- Pedido: permitir que quem recebe um desafio escolha a regra da partida.
- servidor.py: social_action challenge/respond valida a regra escolhida
  pelo destinatário, preserva compatibilidade com clientes antigos (sugestão
  original quando ausente), usa a regra final para criar a sala e envia a
  mesma sessão a ambos. Guarda ranked_requested para recalcular elegibilidade.
- clube.js: renderClub inclui seletor das oito modalidades e indicação de
  sugestão, tempo e ranking; preserva escolha durante atualização do Clube.
  index.html explica que regra de envio é sugestão; cache clube.js v66.
- Decisão: convite casual permanece casual; ranqueado vira casual se a
  escolha for Duelo de Damas, Internacional, Canadense ou customizada.
  O tempo e a política de sala pública continuam conforme fluxo original.
  Não há segunda confirmação: o envio autoriza a escolha do destinatário.
- selftest.py: troca Livre→Brasileira, escolha inválida, usuário remetente
  não autorizado, resposta duplicada, sincronização, Internacional 100 casas
  sem PH e escolha Inglesa elegível preservando ranking. Teste JS de sintaxe
  aprovado; SELFTEST geral e 8 testes da Torre passaram no startup do Render.
- Commits a2575e28, 84a0e9d0, c4e29856, c9452fe4. Sem alteração de banco,
  Torre, Jornada ou matchmaking. Render live: dep-dbs9i6c9v7es73c3g0ag,
  commit 4e12bd13966e2d5f7671919871dad91e7a7ff156; Neon conectado.
  Não houve teste visual entre dois navegadores reais; validar no próximo teste do criador.
- Rollback: reverter commits desta mudança mantendo as outras funcionalidades.

## 14/11/2026 — Detalhamento do Castelo Esquecido (opção B)
- Pedido: planejar os 25 níveis individualmente; mapa 5×5 do reino atual,
  ícones de guardiões, elites, pré-boss e boss; HUD próprio por cenário.
- Arquivos: docs/TORRE_CASTELO_25.md (novo), docs/TORRE_PLANO_100.md e este
  histórico. Catálogo 1–25 com nomes, classes, estilos e D proposto, cinco
  estágios visuais, narrativa, santuários, rotas e prêmio proposto.
- Decisões de UI confirmadas; nomes, balanceamento, narrativa, chefes fixos
  sem rota e recompensas são propostas. Elites 5/10/15/20, pré-boss 24,
  Cavaleiro Sem Nome 25. Refinamento de meta D4,5 no boss, a calibrar.
- Sem alteração em código/Neon/produção; testes de execução não aplicáveis.
  Commit do catálogo: 41ce92d9f813bd6f85013f8089118c56f534d9d6.
- Próximo passo: implementação em branch de teste, catálogo versionado,
  migração preservando beta 1–30, HUD e estágios, testes antes de publicar.

## 14/11/2026 — Planejamento dos 100 andares e guia de continuidade
- Pedido: manter layout aprovado, 4 cenários × 25 andares, identidade de cada
  reino, registrar toda mudança/correção no Git.
- Arquivos: AGENTS.md, docs/TORRE_DOS_REIS.md, docs/TORRE_PLANO_100.md,
  docs/CHANGELOG.md.
- Decisão confirmada: 1–25 Castelo, 26–50 Catacumbas, 51–75 Império, 76–100
  Trono do Fim. Plano de dificuldade, estágios visuais, rotas, santuários,
  recompensas e migração são propostas (ainda não implementadas).
- Sem mudança em código, DB ou release de produção. Testes de execução:
  não necessários para docs; conferir arquivos no Git.
- Próximo passo: revisar plano, implementar catálogo versionado e migração
  preservando progresso; adaptar Castelo primeiro em branch de teste.

## 14/11/2026 — Cenário full-screen aprovado
- Pedido: cenário em tela cheia, com destaque visual aos reinos.
- torre.html: camada .tower-world fixa, SVG original único atrás de .shell,
  data-realm/data-fx sincronizados, fundo da .arena transparente, painéis
  tematizados, véu moderado; preservar estilo e tabuleiro tradicional.
- Commit af974ab8498538e9151c8b15fc32d2db421d4037.
- Teste: JS sintaticamente válido; simulação verificou 64 casas, mudança para
  Catacumbas, pausa/retomada de animações em aba oculta. Render live:
  dep-dbs8ap3bc2fs73as9log. O criador aprovou a interface nesta conversa.
  Não houve inspeção automatizada de screenshot real.
- Próxima etapa: evoluir identidade dos quatro reinos sem substituir layout.

## 14/11/2026 — Reformulação visual da Torre
- Problema: tela genérica de protótipo, tabuleiro pequeno e casas sem contraste.
- torre.html: layout tradicional com cartas de jogadores, contadores, mesa
  grande, skins originais, inclusão de escola.css (variáveis de material),
  painel lateral com mapa, dificuldade, coroas, recorde, santuário, histórico,
  girar tabuleiro e modo concentração. Cenário inicialmente atrás da arena.
- Commit aa1c5e40c2aa3eb7119e5b64ea28d9e77b7cbfc9.
- Validação: simulação JS de 64 casas, 3 rotas, 10 marcadores de andar,
  12 peças por lado, giro; testes gerais e 8 da Torre aprovados no Render.
  Deploy dep-dbs87t61egvs73d4lnog live.
- Sem alteração de dificuldade ou dados salvos. Criador aprovou o layout,
  pediu cenário em tela cheia (resolvido na entrada acima).

## 14/11/2026 — Publicação da beta e correção do autoteste de reconexão
- Problema: botão Torre não aparecia porque Render ainda servia commit antigo.
- PR #1 integrado a main: commit 2b65bd95e8617b87ac24b4b09e44b5374ba02fa0.
- Teste antigo misturava relógio sintético/monotônico; selftest.py ajustou
  clock_at e started na transição (commit 13f0e5ffaf7f692910b12776aa61e4ec31876b14).
- Deploy manual dep-dbs8496k1f9s738i6od0, confirmado live; SELFTEST OK,
  8 testes Torre OK, DATABASE READY: neon. O menu foi disponibilizado.
- Não houve reset do banco; mudança no teste, não nas regras da partida.

## 14/11/2026 — Integração da Torre jogável
- Branch torre-dos-reis-base: núcleo torre.py, docs e testes iniciais.
  Integrada via PR #1: https://github.com/pedrobarretto1/tes/pull/1.
- Beta 1–30: Castelo (1–10), Catacumbas (11–20), Império (21–30).
  Trono do Fim existe como SVG; ainda não é acessível na campanha.
- servidor.py: tower_action, tabela aditiva tower_runs, persistência separada
  por jogador e modo, validação de lances e resultados no motor existente,
  coroas, checkpoint, rotas, resign, draw, resume e isolamento de PH/Jornada.
- torre.html: cena SVG V3 original, tabuleiro jogável, seleção de rotas e
  animação de movimentos; index.html: botão do Clube.
- Testes test_torre.py + test_torre_api.py (8 aprovados); startup executa
  testes em SQLite temporário antes do Neon. Recompensas e ranking desligados.
- Limites: 5 perfis de IA, rotas simples; narrativa/finais, cosméticos e
  campanha até 100 ainda não implementados.

## 14/11/2026 — Base visual e desempenho antes da Torre
- Commit 903b9f087af224325d9b12cd6c42bd5ecfa9b968: conservar raio solar diagonal
  com textura em cache. Commit 48c7da97b0ef8eadb1ef35e81180aa25a5f616ad:
  ciclo de vida das prévias e animação de captura/promoção. Commit
  0ed6e7b5270ed24109162534dbff5c8dc26a55d7: peças por transform, tabuleiro
  estável, efeitos mobile mais leves.
- Referência: otimizações já existentes na mesa/loja/Jornada devem ser
  preservadas. Não se afirma aqui um teste novo de FPS ou desempenho.

## Modelo de próxima entrada

### AAAA-MM-DD — título
- Pedido / problema:
- Arquivos / funções / seletores:
- Solução e decisões:
- Testes reais e resultados:
- Commit / PR / deploy:
- Pendências / rollback:
