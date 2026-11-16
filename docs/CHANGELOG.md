# Histórico de alterações — Casa de Damas

Registro acumulativo para próximas sessões. Entradas anteriores foram
reconstruídas a partir de commits, testes e conversas já registradas; não
representam verificação visual retroativa. Acrescentar uma entrada para toda
correção/alteração futura, mesmo pequena. Mais recente primeiro.

## 15/11/2026 — Menu expandido, Escola, replay e preferências do Xadrez
- Pedido: adaptar as demais áreas do menu de Damas ao Xadrez. Primeira etapa: quatro seções, atalhos funcionais de busca, desafios, ranking, Escola, replay, amigos, perfil e configurações. Campanha, clãs, loja, Copa, Salão ao Vivo, sala privada e música ainda não disponíveis; nenhuma opção falsa.
- xadrez.html/css/js: seis exercícios legais com dicas, validação e progresso local; tabuleiros isolados da mesa; replay do jogo atual e últimos 20 registros online, navegação por lance; três acabamentos gratuitos, animações opcionais e efeitos sonoros sintetizados opcionais com volume. Preferências locais do navegador, sem PH/recompensas. Sem alterações no motor ou Damas.
- chess_duels.py: histórico autenticado por jogador, retorna somente seus jogos concluídos, sem tokens/IDs de outros jogadores. Registra também novos jogos casuais, sem pontuação; históricos casuais anteriores não são migrados. Mantém transações e registros competitivos existentes.
- Testes: test_chess_ui.js e test_chess_duels.py ampliados; CI pendente. Rollback: reverter alteração, preservar registros; sem migração destrutiva.

## 15/11/2026 — Animações das peças do Xadrez
- Pedido: movimentos suaves das peças, captura, cavalo, roque e promoção, preservando o visual rústico e desempenho.
- xadrez.js/css/html: camada transitória de SVG sobre o tabuleiro, animações Web Animations com transform/opacity, destino oculto até pouso; captura normal/en passant, salto do cavalo, roque simultâneo e promoção. Giro automático ocorre após pouso; estado e salvamento continuam imediatos. Local, IA e online animam um lance confirmado; histórico recuperado ou múltiplos lances perdidos entram diretamente no estado atual. Redimensionamento, desfazer e troca de modo limpam a camada; movimento reduzido respeitado. Nenhum filtro ou animação contínua; sem alteração de regras/banco.
- Testes: test_chess_ui.js verifica camada transitória, giro após movimento, roque, en passant, promoção e reduced-motion; CI pendente, publicação não confirmada. Rollback: reverter este commit.

## 15/11/2026 — Menu fechado ao iniciar e trocar de reino
- Pedido: impedir abertura automática do menu ao carregar Damas ou retornar do Xadrez.
- clube.js: cadastro silencioso para nome salvo; primeiro acesso ou sessão inválida ainda mostra identificação. Após cadastro/login, fecha identificação sem abrir menu; abertura manual durante conexão é atendida após sucesso. Atalhos explícitos de amigos continuam abrindo o painel correto e o parâmetro é consumido. Navegação manual existente preservada.
- index.html: versão do clube.js atualizada para 79, evitando cache antigo. Nenhuma alteração de motor, partidas ou banco.
- test_chess_ui.js/test_bot_ui.js: esperam registro pelo perfil, verificam menu fechado, abertura manual, retorno do Xadrez, reload e link de amigos. Testes de navegador pendentes de CI; publicação não confirmada.
- Rollback: reverter este commit; nenhuma migração necessária.

## 15/11/2026 — Xadrez: mesa competitiva e painel lateral
- Pedido: replicar funcionalidade dos quatro painéis de Damas adaptados ao Xadrez (configuração, andamento, ranking e como jogar).
- xadrez.html/css/js: controles de modo Local/Computador/Online, regras clássicas, sorteio de cores, relógios 0/1/3/5/10/15/30, três dificuldades, ranqueada/casual, busca/cancelamento, desafios, nova partida/desistência, empate, histórico, ranking top3/completo, perfil com PH/moedas, regras expansíveis. Nome da mesma conta, edição via Damas. Preserva peças SVG e giro Local; relógio Local salvo na aba; partidas online e IA restauradas pelo servidor.
- chess_duels.py: motor python-chess (chess==1.11.2), partidas/assentos/convites/fila/perfil/histórico persistidos, relógio autoridade servidor, IA com limites de busca, validação de turnos/lances, fim por regras e tempo, resultado idempotente e transação com guard. Sorteio de cores. Ranking PH inicial 1000; +25/-15/+5/-20, Médio metade arredondada em magnitude, moedas 15/8 após 8 plies sem desistência, Fácil/casual/Local sem progresso competitivo. Recompensas, ranking e históricos independentes de Damas.
- servidor.py/clube.js/index.html: rotas chess/* e schema aditivo, amigos e jogadores online compartilhados, convites Xadrez visíveis nas Damas (abrem Xadrez para aceite explícito), bloqueio de salas Damas enquanto duelo Xadrez ativo. Não migra nem remove dados. Motor Local original mantido.
- Limites: IA própria leve, não Stockfish; ranking por PH (não Elo FIDE); fila por tempo/tipo, sem seleção de variante; sem clãs/loja/campanha Xadrez, sem chat/espectadores/replay visual online. Recompensa sem transferências entre jogos. Nome compartilhado gerenciado em Damas.
- Testes: CI 43779044887 aprovado: 38 testes Python, SELFTEST, motor Xadrez, regressões Torre/Clãs/IA/Local, Chromium em desktop/celular e partida online entre duas contas. Primeiro CI detectou ausência do id black-name, corrigida antes da integração. PR #16 integrada: 422452b9f2ff1557afede23f7f266dbc257a682c. Render dep-dbt4lr49v7es73c6oku0 live; Neon confirmou sete tabelas chess_* e inicialização OK. Validação manual em produção pendente. Rollback: reverter rotas/interface preservando tabelas e resultados existentes; não apagar dados.

## 15/11/2026 — Xadrez: mesa rústica e peças entalhadas
- Pedido: aproximar layout da Casa de Xadrez ao visual rústico aprovado das Damas e refinar peças.
- xadrez.html/css: cabeçalho, navegação, mesa, cartas, moldura de madeira com cantos de latão, painéis e menu com a paleta e dimensões das Damas. Retira banner de apresentação para priorizar tabuleiro; painel de regras útil, expansões futuras informativas no menu. Modo concentração reversível, sem mudar estado da partida. Breakpoints 850/520 px, coordenadas separadas e contraste por casa. Portal compartilhado preservado.
- xadrez.js: 12 símbolos SVG originais (6 tipos x marfim/madeira escura), definições únicas reutilizadas via use, gradientes estáticos, sombras vetoriais sem filtros; desenhos distintos com bases/entalhes. Cartas e promoção usam mesmas peças. Mantém aria-label das casas, seleção, destinos, último lance, xeque, giro e salvamento. Sem alterar motor, identidade, servidor, banco ou Damas.
- Testes: test_chess_ui.js verifica 32 peças, 12 símbolos, referências e dimensões, concentração, regras, lances/giro/salvamento e responsividade; CI 43776502551 aprovado: 33 testes Python, SELFTEST, motor Xadrez, regressões Torre/Clãs/IA/Local e Chromium Xadrez desktop/celular. PR #15 integrada: 96051b6ebd166ed2388542f52b912d16726323b8. Render dep-dbt4f33bc2fs73d3cqkg live, confirmado. Validação estética manual pendente. Rollback: reverter arquivos Xadrez/teste, sem mudança de dados.

## 15/11/2026 — Portal dos Dois Reinos, Xadrez v1
- Pedido: universo Xadrez acessível fora do menu, menus independentes, mesma conta e amigos, indicador Damas/Xadrez; não incluir Torre dos Reis no Xadrez.
- index.html: seletor no cabeçalho (visível também com menu inicial aberto), protege troca durante duelo online/IA remunerado/Jornada, confirma abandono Local. xadrez.html, xadrez.css e xadrez.js: mesa Local independente com 32 peças, giro por turno, histórico SAN, desfazer, desistência, promoção e salvamento em sessionStorage. Menu próprio Local/Amigos/Perfil/Regras; nenhuma Torre/Jornada ou link que simule sistema não implementado. Visual original em CSS/glyphs, sem imagens geradas.
- chess-engine.js: motor local 0x88, lances legais, xeque, roque, en passant, promoção, mate, afogamento, material insuficiente, repetição, 50/75 lances. Sem resultado competitivo ou confiança do servidor no cliente.
- servidor.py: PRESENCE_GAME efêmero, chess/state com identidade e amizades compartilhadas, sem PH/estatísticas de Damas; status online/busy/game em Damas, bloqueio de desafio durante partida Xadrez Local. Convites Damas recebidos no Xadrez encaminham ao Clube de Honra para escolha/aceite; sem convite Xadrez nesta versão. clube.js: presença abaixo do nome, polling visível, abertura Amigos ao retorno. Conta gerenciada no portal Damas; sem nova tabela ou migração. Amigos offline não exibem universo atual. Última aba visível com heartbeat define presença.
- Escopo v1: apenas Local; IA, online Xadrez, ranking, PH/moedas, loja, clãs, escola e torneios ainda pendentes. Torre dos Reis exclusiva das Damas. Salva partida Local nesta aba, sem sincronização cloud. Mesma conta sem duplicar perfil. Nenhuma economia alterada.
- Testes: perft 20/400/8902, regras especiais, isolamento social, Chromium 1280/375 e troca de reino; CI 43775641747 aprovado: 33 testes Python, SELFTEST, motor Xadrez perft 20/400/8902 e regras especiais, regressão Torre/Clãs/IA/Local, Chromium Portal Xadrez desktop/celular. PR #14 integrada: 65da633ee7f5829575f4a950771b56347bbf4ccc. Render dep-dbt4466i0phs73ekpqkg live; inicialização e Neon OK. Teste manual em produção pendente. Rollback: reverter portal e rotas/arquivos, sem mudança de dados.

## 15/11/2026 — Giro automático no modo Local
- Pedido: alternar a perspectiva do tabuleiro para facilitar partidas no mesmo dispositivo.
- index.html: runMoveFX atualiza flipped somente após finalizar a animação,
  se modo Local, partida em andamento e sem captura intermediária. Claras
  embaixo na vez das claras, escuras embaixo na vez das escuras. Usa o renderer
  e coordenadas existentes; não adiciona transformação CSS sobre as peças.
  Nova partida volta à orientação inicial. Giro manual continua disponível
  e a próxima troca de vez restabelece a perspectiva automática.
- Sem alterações em regras, IA, online, Torre, Jornada, servidor ou economia.
- test_bot_ui.js: teste real Chromium em 1280/375 px, duas trocas de vez,
  animação retida, captura múltipla e reinício. CI 43745259870 aprovado:
  31 testes Python, SELFTEST, regressão Torre, Clãs e IA, giro Local em
  1280 e 375 px. PR #13 integrada: 7d270f351ec60c105a47079ea39e57165082c516.
  Render dep-dbsvbrm1egvs73evvdj0 live; teste manual em produção pendente.
  Rollback: reverter alteração de interface.

## 14/11/2026 — Recompensas nas partidas contra computador
- Pedido: Fácil sem recompensa, Médio 50%, Difícil 100% dos benefícios de partidas ranqueadas contra pessoas.
- bot_duels.py: partidas autoritativas persistidas (bot_duels, uma por jogador), sorteio de cores, motor oficial, busca minimax com limites de profundidade/nós/tempo, relógio servidor, lances legais, empate automático/oferta e final inevitável. Nenhum resultado declarado pelo navegador. Idempotência por match/sequence/nonce e results; recompensa, histórico, replay, estatísticas e conquistas na mesma transação.
- Médio: +13/-8/+3/-10 PH (vitória/derrota/empate/desistência), moedas +8 vitória/+4 derrota ou empate; Difícil +25/-15/+5/-20 PH, +15/+8 moedas. Metades arredondadas em magnitude para cima; moedas só a partir de oito lances e sem desistência. Estatísticas discretas contam uma partida inteira. PH nunca abaixo de zero. Recomeçar partida remunerada não concluída = desistência; Fácil e modalidades casuais permanecem locais e sem recompensa.
- Regras remuneradas iguais às ranqueadas online: Livre, Brasileira, Inglesa, Captura Obrigatória, Antidamas. Duelo de Damas, Internacional, Canadense e personalizadas continuam casuais. Jornada/Torre intactas. Recompensas de sobrevivência seguem a dificuldade da partida normal.
- servidor.py: setup aditivo, rotas /api/social/bot/*. index.html: fluxo de partida servidor, animações por lance, relógio, resultado com PH/moedas, reconexão/retry e aviso da dificuldade. Sem alteração da economia PvP.
- Testes: test_bot_duels.py economia/identidade/duplicidade/validação; test_bot_ui.js Chromium com servidor local real; CI 43639589748 aprovado: 31 testes Python, SELFTEST, regressão Torre, Clãs em três larguras e duelo IA ponta a ponta (lances, desistência Médio/Difícil, Fácil sem progresso, perfil persistido). PR #12 integrada: 8d9650d2e80baf59a0dc574328a53fb1ab24b199. Render dep-dbscjiei0phs73coeeog live; tabela bot_duels confirmada no Neon. Validação manual em produção pendente; rollback reverte código preservando tabela e histórico. Não apagar dados.

## 14/11/2026 — Recrutamento por recomendação
- Pedido adicional: demais cargos recomendam jogador; apenas Capitão e Rei
  recebem, com estatísticas públicas e requisitos.
- clas.py: tabela aditiva clan_recommendations, estados, unicidade, validade,
  limite de 5/dia por autor e 30 pendentes/clã. recommend, recommend-review,
  recommend-decide. Capitão registra parecer, sem autoavaliação; Rei encerra
  ou cria Convite Real em transação. Recomendado precisa aceitar. Nenhum
  requisito bloqueia recomendação; vaga/conta/único clã continuam obrigatórios.
- clube.js: botão no perfil e membros, aba Recomendações exclusiva Rei/Capitão,
  aviso com acesso ao painel e cartões com stats e comparação dos requisitos.
  Vice pode recomendar mas não vê fila. Sem alterações na economia.
- Testes test_clas.py e test_clas_ui.js para privacidade, duplicidade,
  parecer, aceite e acesso por cargo. Refinamento solicitado: parecer favorável
  nunca cria convite ou autoriza ingresso; Capitão não avalia indicação própria,
  não pode chamar API de convite/decisão nem após parecer favorável. UI usa
  'Parecer favorável', sem botão de aprovação. CI 43637988986 aprovado: 25 testes Python, SELFTEST, regressão Torre e Chromium 375/758/1280 px. PR #11 integrada: dfdf874592b647a2925b35a804397090169ef4f3. Render dep-dbscblbrjlhs73dq038g live; tabela clan_recommendations confirmada no Neon.
- Rollback preserva a nova tabela. Nenhuma exclusão de dados existentes.

## 14/11/2026 — Insígnias de cargo e Convite Real
- Pedido: cargo abaixo do nome de todos os membros; Rei pode convidar
  independentemente dos requisitos.
- clas.py: apply continua validando requisitos; invite autorizado somente
  pelo Rei dispensa requisitos no envio e no aceite. Mantidos conta registrada,
  vaga, unicidade, consentimento, expiração e limites. notices sinaliza royal.
  public_identity retorna identidade pública do clã; chat inclui cargo atual
  por associação, sem cargo para ex-membro. servidor.py expõe clã nos perfis.
- clube.js/clube.css/index.html: insígnia vertical em Membros, Administração,
  chat e perfis público/próprio, cores por cargo e sigla no perfil; chat
  re-renderiza quando o cargo muda. Convite Real identificado nos pedidos,
  avisos, perfil e lista. Cache v76/v71.
- Decisões: convite não força ingresso; convite já emitido permanece válido
  durante troca de Rei até expiração. Títulos cosméticos preservados. Sem
  mudança de schema, saldo, penalidade ou torneios.
- test_clas.py: exceção real, bloqueio de aplicação, aceite autorizado,
  recusa, capacidade, cargos no chat/perfil e ex-membro; test_clas_ui.js:
  quatro insígnias abaixo do nome e controle exclusivo do Rei.
  CI 43637988986 aprovado, PR #11 integrada (dfdf874592b647a2925b35a804397090169ef4f3); Render dep-dbscblbrjlhs73dq038g live; tabela clan_recommendations confirmada no Neon. Primeiro CI falhou por delimitadores SQL na consulta do chat; corrigido antes da integração.
- Rollback: reverter código; sem alteração de dados ou migração.

## 14/11/2026 — Conselho Real: hierarquia, administração e denúncias
- Pedido: Rei com controle integral, Vice-capitão personaliza, Capitão
  acompanha membros/denuncia, Membro sem opções administrativas.
- clas.py: três tabelas aditivas (roles/reports/penalties), role/ROLE_RANK,
  promote, report/return/reply/reopen/decide, histórico persistente e
  tournament_block; controle de permissão por operação, revalidação sob
  clan_guard, proteção contra autopromoção/denúncia de superior/dupla decisão.
- Decisões: Rei é owner existente; membros legados começam Membro. Rei
  único que promove/rebaixa/expulsa; transferência mantém um Rei. Vice
  pode editar brasão/requisitos/descrição, nunca cargo/expulsão. Denúncia
  retorna a Vice elegível ou Capitão autor se não houver Vice; Rei pode
  retomar justificando. Histórico privado (Capitão próprio, Vice/Rei do clã
  exceto alvo); afetado recebe apenas decisão, mensagem/prazo. Limite 10
  denúncias/autor/dia, uma ativa por autor/alvo. Suspensão 1h–365d por clã,
  persiste se sair/reentrar; expiração por horário de servidor.
- servidor.py: clan_role no estado social; avisos de denúncia/devolução/
  resposta/decisão/cargo usam notifications. clube.js: abas Administração,
  Personalização, Denúncias, Minhas decisões; controles por cargo, link
  dos avisos e insignias. clube.css estilo Conselho Real, cache v75/v70.
- Torneios internos ainda pendentes; penalidade salva e helper testável,
  a futura API deve obrigatoriamente aplicá-lo em criar/inscrever/jogar.
  Não bloquear partidas oficiais, ranking ou campanhas. Nenhum saldo alterado.
- test_clas.py: hierarquia, legado, autorização, histórico, retorno/resposta,
  suspensão/expiração, expulsão, transferência; test_clas_ui.js: abas e
  ações por cargo. CI 43637006196 aprovado: 22 testes Python, SELFTEST, regressão Torre e Chromium 375/758/1280 px. PR #10 integrada: e8e2f8f77667bacd5190ccc247d47b15949b7238. Render dep-dbsc5m56e07s739efrl0 live.
- Rollback: reverter código preservando novas tabelas (não apagar histórico).
  Validação manual entre contas reais ainda pendente.

## 14/11/2026 — Molduras heráldicas refinadas
- Pedido: refinar as seis molduras dos brasões, antes recortes geométricos planos.
- clube.js: heraldicFrames, paintCrestFrame, crestShade e crestSvg criam seis
  desenhos SVG originais com campo interno, contornos metálicos duplos,
  ornamentos, rebites e sombreamento derivado da cor escolhida. IDs antigos
  royal/fortress/dark/sacred/ancient/ornate preservados. Símbolos e cores
  independentes, inclusive Cruz de Jerusalém, sem contraste obrigatório.
- clube.css: substitui clip-path por SVG em camadas, sem filtros/animacoes,
  adapta cartões, notificações e preview maior de fundação. Cache v74/v69.
- test_clas_ui.js: verifica seis paths distintos, camadas, cor de fundo,
  troca da Cruz de Jerusalém, preview e editor administrativo.
- Correção adicional (print): cabeçalho do Salão escapava da moldura durante
  rolagem. index.html separa #clanscroll; CSS limita shell ao grid do viewport,
  cabeçalho fixo dentro da borda e corpo rolável, preview com margem interna;
  renderClan/openClan reiniciam rolagem ao trocar aba. Teste Chromium confere
  limites do topo/rodapé durante rolagem e viewport baixo de 540 px.
- Sem alteração de servidor, schema, economia ou dados. CI 43634927016 aprovado:
  20 testes Python, SELFTEST, regressão Torre, Chromium 375/758/1280 px e altura
  540 px. PR #9 integrada: 42502eaf096e53baf2773577056f4d200f1eda63.
  Render dep-dbsbr23m8hqs73camacg live; SELFTEST, 14 testes Torre e Neon OK.
  Rollback: reverter renderer, HTML e CSS; designs salvos continuam compatíveis.

## 14/11/2026 — Cruz de Jerusalém nos brasões
- Pedido: incluir o símbolo da imagem enviada, com cruz central e quatro menores.
- clas.py: novo ID jerusalem no catálogo EMBLEMS, compatível com create/crest.
- clube.js: opção Cruz de Jerusalém, paintCrestSymbol desenha cinco paths SVG
  conforme a referência, usando currentColor e sem depender de fonte; todos os
  usos do brasão compartilham o renderer. clube.css dimensiona o SVG em 1em.
  Cache JS v73/CSS v68. Todas as cores e molduras continuam livres.
- Testes: test_clas.py cria/edita/recarrega o design; test_clas_ui.js confere
  cinco paths, cor, troca para símbolo anterior e editor administrativo.
  CI 43634566062 aprovado: 20 testes Python e Chromium 375/758/1280 px.
- Sem alteração de schema, dados existentes, economia ou requisitos.
  PR #8 integrada: 8d8c245e94fe79390e10d46a8ead64c1a2eb79f9. Render dep-dbsbp5ec6qcc738o7o2g live (confirmado). Rollback: reverter UI e manter ID no catálogo
  para não invalidar brasões já salvos.

## 14/11/2026 — Brasões personalizados dos Clãs
- Pedido: símbolo, cor do símbolo, seis molduras, cor da moldura e fundo,
  prévia ao vivo e edição pelo dono, sem contraste mínimo.
- clas.py: tabela aditiva clan_crests, validação por IDs de catálogo, leitura
  compatível com clãs legados e gravação transacional. Nova ação clans/crest
  exclusiva do dono; não altera requisitos. Criação aceita design ou padrão.
- clube.js: editor reutilizável com paletas de 12 cores, seis símbolos, seis
  estilos, restauração de padrão, preview ao vivo; brasão aplicado a cartões,
  Meu clã, cabeçalho do chat e pedidos/convites. clube.css: geometria distinta
  por moldura e variáveis de cor independentes. Cache JS v72/CSS v67.
- Decisões: gratuito, sem contraste obrigatório ou aviso, inclusive três cores
  iguais; catálogo fechado de valores seguros. Sem alterações na economia,
  requisitos, membros, chat persistido, Torre ou Jornada. Clãs antigos usam
  padrão derivado do símbolo; sem reset. Torneios internos ainda pendentes.
- Testes: test_clas.py cobre criação, persistência, reedição, legado, permissões,
  cores iguais, dados preservados e dissolução. test_clas_ui.js cobre seis
  geometrias, paletas e administração em 375/758/1280 px. CI 43634204285 aprovado: 19 testes Python, Chromium nas três larguras, SELFTEST e regressão Torre.
- PR #7 integrada: 2f5719b0ab84a75abd0b75e865ab9b0cfb6378cb. Render live dep-dbsbn8ek1f9s738rakc0. Rollback: reverter
  código mantendo tabela e design salvo; não excluir dados.

## 14/11/2026 — Clãs: identidade de honra, busca e fundação ao vivo
- Pedido: corrigir letras espremidas na busca (print), dar mais identidade
  às telas de busca/criação, atualizar prévia durante digitação e harmonizar menu.
- Causa: largura global 100% dos botões consumia o flex da busca e fazia
  as abas ocuparem linhas inteiras; inputs sem estilo específico.
- clube.css: escopo #clanoverlay; busca em grid minmax(0,1fr)/auto, campos
  escuros legíveis, abas compactas, brasões em CSS, salão de ferro/dourado,
  cartas e estado vazio temático, formulário e prévia responsivos.
- clube.js: renderClanCreation, clanCrest, labels explícitos; prévia atualiza
  nome/sigla/descrição/brasão em input/change, sem salvar/recriar formulário;
  sigla em maiúsculas, aviso de 2–6 letras/números (sem pontos), botão
  bloqueado até nome/sigla válidos. Requisitos opcionais preservados.
- index.html: menu Clãs secondary como os três vizinhos; novo banner,
  cache clube.js v71/clube.css v66.
- Testes: sintaxe JS e simulação da busca, prévia, sigla C.T inválida/CE
  válida, envio com 7 requisitos null aprovadas. test_clas_ui.js verifica
  layout real 375/758/1280 px no Chromium: todos aprovados no CI 43633284488.
  Primeiro CI falhou na instalação do Playwright em Ubuntu 26.04; runner
  fixado em Ubuntu 24.04 (d147dc12), sem falha na interface. Testes gerais,
  18 testes Python e regressão da Torre aprovados.
- Sem alteração no servidor, banco, torneios, Torre ou regras de entrada.
  PR #6 integrada: e522bf09430b3a6eb7ec94dcb4df6f27dd5cb588.
  Render live dep-dbsbidu1egvs73dculog; rollback reverte UI/teste.

## 14/11/2026 — Clãs: primeira versão social
- Pedido: aplicar clãs após aprovação do plano. Entrega inicial sem torneios
  financiados: criação, busca, requisitos opcionais, solicitações e convites,
  dono exclusivo, membros, nível individual/médio, chat privado.
- clas.py: schema aditivo clans/clan_members/clan_requests/clan_messages/guard,
  constraints e transação de admissão; validação de conta, vaga, requisitos
  e permissões. Chat texto puro, rate limit e últimas 50 mensagens.
- servidor.py: setup e rotas social/clans; nível no perfil e avisos privados.
  clube.js/index.html/clube.css: salão medieval, abas e cartões acionáveis;
  convite direto no perfil e administração. Cache v70/v65.
- Decisões: 30 membros, 1 clã por conta registrada, pedido válido 7 dias,
  cooldown 5 min após recusa; sem timer visual. Torneios apenas aba informativa,
  sem débito, sem PH transferível. Moderação/paginação antiga pendentes.
- test_clas.py: 4 testes com SQLite, CI inicial 43632242305 aprovado,
  incluindo 14 testes Torre, regressão UI e SELFTEST. CI final 43632355617 aprovado (18 testes); simulação JS verificou requisitos, campos opcionais e controles do dono. Sem teste visual real.
- PR #5 integrada: 8d7cb4de18a59d4507af4e7e8e5cbf7c77bf8d04. Render live dep-dbsbddlg1s2s73enea1g; Neon conectado e cinco tabelas de clãs confirmadas. Startup SELFTEST e 14 testes Torre OK. Não alterar dados existentes; schema aditivo.
  Rollback: reverter código mantendo tabelas e dados de clãs; não apagar banco.

## 14/11/2026 — Proposta de desempate nos torneios de clãs
- Pedido: definir empate inicial/final e consequência para quem propõe/aceita.
- docs/CLAS_PLANO.md: empate não elimina; revanche com cores invertidas;
  par de rápidas, placar 1/0,5/0 e sessão final com prazo. Proposta de
  co-campeões e divisão da reserva na final; skin convertida em moedas
  pelo preço reservado; impasse anterior à final sem vencedor implica
  cancelamento objetivo e devolução, nunca sorteio. PH segue pendente.
- Verificação: event_tick atual cria nova sala a cada empate, sem limite
  explícito; não alterar torneios oficiais nesta etapa. Novo fluxo deverá
  persistir estado e liquidar reserva uma única vez.
- Decisões propostas, ainda sem aprovação final. Apenas documentação;
  sem código, banco, deploy ou testes de execução.
- Commit plano 2139a8099752562062f44a65e0c17ffa792c421a. Próximo: confirmar política e
  implementar torneios persistidos com testes de empate e reserva.

## 14/11/2026 — Planejamento dos Clãs e torneios financiados
- Pedido: clãs com requisitos opcionais, pedidos exclusivos ao dono, convites,
  chat, nível médio e torneios de membros com PH/moedas/skins de prêmio.
- docs/CLAS_PLANO.md: especificação, fluxos, autorização, nível por feitos,
  requisitos AND, revalidação, cofre, catálogo, cancelamento, idempotência,
  persistência e testes. AGENTS.md aponta para o plano.
- Fragilidades verificadas: players.points é ranking e saldo (visitantes
  iniciam com 1000 PH); TOURNAMENTS está em memória; não há nível numérico
  canônico. Proposta: nível derivado; moedas/skins com reserva transacional;
  PH direto somente após decisão de separar economia e ranking.
- Limites, fórmula XP e regras de torneio são propostas, não aprovados.
  Nenhuma alteração em código jogável, banco ou deploy; testes não aplicáveis.
- Próximo: implementar núcleo social em branch, testar; persistir torneios
  e partidas antes de reservar valores. Registrar cada correção e publicação.

## 14/11/2026 — Reinício visual do tabuleiro após resultado da Torre
- Pedido: reiniciar a mesa após vitória, derrota, empate e desistência em ambos
  os modos. Causa: render() exibia game.board do duelo encerrado, ainda mantido
  pelo servidor para histórico/resultado, mesmo quando progress.status não era playing.
- torre.html: render usa posição inicial de 24 peças sempre que não existe partida
  ativa; limpa seleção, alvos e marcações de último lance, sai do modo concentração,
  mantém o resultado e histórico identificado como última partida. Rótulo distingue
  próximo andar, nova partida e retorno ao santuário; nova tentativa disponível
  após fim da Expedição ou beta. A partida ativa continua a partir do estado salvo.
- Regras, persistência, coroas, IA, animação dos lances e skins não alteradas.
  A mesa reiniciada aguarda escolha de rota, sem iniciar automaticamente ou
  gastar coroas adicionais. Demais modalidades fora da Torre não modificadas.
- test_torre_ui.js: regressão com DOM simulado para 12 cenários terminais,
  ambos modos, atualização/reabertura, foco, contadores e 64 casas; workflow
  torre-beta.yml executa o teste. CI 43628856830 aprovado, incluindo 12 cenários UI, 14 testes Torre e SELFTEST geral.
- Commits f6dd5585, 4f3e40ce, 03c549eb. PR #4 integrada: 278736309a751ad6f58a7701172aafe1b87ffcc6. Render live dep-dbsar9qfngtc73c7deo0. Rollback: reverter alterações de UI/testes,
  sem migração ou alteração de banco.

## 14/11/2026 — Rebalanceamento da Torre e pedidos sem timer
- Pedido: andar 1 muito difícil; suavizar cada nível, retirar fechamento automático de 30 s.
- torre.py: ai_balance e TOWER_SEARCH_CHANCE, curva exclusiva 1–30, chance de busca
  zero no andar 1 em todas as rotas, aumento gradual com picos leves nos elites,
  perfis de busca limitados no início. Metas, não Elo nem taxas de vitória.
- servidor.py: tower_ai escolhe lances legais com erros posicionais deliberados
  no início, oferece oportunidades de captura, reduz preferência por promoção,
  respeita captura obrigatória e lei da maioria. A chance de usar busca cresce.
  Partidas salvas adotam nova política no próximo lance da IA, mantendo tabuleiro,
  sequência, coroas e recorde. Jornada e online usam motor original.
- torre.html: dificuldade real em texto, sem confundir profundidade com força;
  rotas do andar 1 explicitamente muito fáceis.
- clube.js: pedidos de amizade/desafio sem timer local, permanecem até resposta,
  X ou pedido deixar de estar válido; avisos informativos mantêm 7/10 s.
  index.html cache v69. Convites ainda expiram no servidor em 60 s.
- Testes: sintaxe JS; testes de curva, partida legada, 12 simulações com
  jogador heurístico e legalidade. CI e Render: 14 testes da Torre OK, 12/12 vitórias do jogador heurístico, SELFTEST geral OK. Simulação JS: pedidos sem timer, X sem recusa, deduplicação e timers informativos preservados.
- Commits bcf0198f, 1c3c40e2, 2f2b1306, 5c8f3b76, 23387e38, 59cd69af.
  PR #3 integrada: 5966dd654e39e1738e2a66cfa258aa25282382b5. Render live dep-dbsaf7t6e07s739a6l60; Neon conectado. Sem reset de dados, sem alterar recompensas ou regras. Não excluir Pedro 2
  sem a confirmação solicitada.
- Próximo: validar com jogador real, ajustar chance de busca por feedback.
  Rollback: reverter commits de balanceamento/UI; dados permanecem compatíveis.

## 14/11/2026 — Notificações interativas de desafio e amizade
- Pedido: aceitar/recusar direto no aviso, X e duração conforme o tipo.
- clube.js: pendingRequests, requestActions, snack, syncRequestSnacks e
  renderNotices unificam convites e amizade; desafios aceitos abrem seleção
  de modalidade existente, sem criar sala até confirmar. Recusar chama API
  existente. Central de avisos permite responder a pedidos pendentes.
- X e expiração apenas ocultam o cartão, não recusam nem marcam como lido;
  30 s para pedidos, 10 s para respostas informativas, 7 s presença.
  Deduplicação durante polling, limpeza ao trocar perfil e ao resolver,
  proteção contra ações simultâneas; convite ainda expira em 60 s no servidor.
- index.html remove toast antigo; cache clube.js v68, clube.css v64;
  CSS de ações, status, responsividade e redução de movimento.
- Testes: sintaxe JS e simulação de dois cartões, timers 30/10/7 s,
  deduplicação, aceite de desafio sem API, recusa de amizade, X e timeout
  sem recusa; todos aprovados. Sem teste visual em navegadores reais.
- Commits 7116bc50, 90ade956, 4e834a98, e8d524b8. Render live: dep-dbsad7jbc2fs73b1p2n0, commit df5d523f0707d37c858ea173b66d7cf2d8f86a6b. SELFTEST geral e 12 testes da Torre aprovados; Neon conectado.
- Banco não modificado: exclusão do perfil visitante solicitado depende de
  confirmação explícita após identificar o registro. Não registrar dados pessoais.
- Rollback: reverter commits da UI; sem alteração no protocolo ou na Torre.

## 14/11/2026 — Castelo 1–25: catálogo e mapa da campanha
- Pedido: continuar a Torre e corrigir mapa antigo de 10 níveis.
- torre.py: catálogo v2, 4 reinos de 25, 25 inimigos do Castelo, classes,
  capítulos, estágios, metas D e checkpoints; mantém release 30 para preservar
  jogadores da beta. Catacumbas 26–30 jogáveis; 31–100 não liberados.
- servidor.py: metadados autoritativos por encontro, rota fixa nos especiais,
  perfil de busca persistido na partida; sem alteração de schema ou reset.
- torre.html: mapa 5×5 por reino, símbolos e estados, nomes, capítulo, HUD
  medieval, cinco estágios SVG aditivos; Catacumbas usa nichos e pedra
  espectral. Mantém mesa tradicional e skins. index.html: texto do menu.
- Decisões: números de andares/recorde/coroas/checkpoint e partida ativa
  preservados; reinos antigos remapeados pelo número atual. Conclusão da
  beta permanece no 30 até a próxima expansão. Metas D não são Elo;
  IA ainda usa cinco perfis existentes, estilos são descrições planejadas.
- Testes: catálogo/fronteira 25→26, elites, rota fixa, estado legado, API
  e sintaxe JS: 12 testes da Torre aprovados, simulação 25 casas e troca 25→26 aprovada, CI geral e Node OK. Corrigido relógio simulado de selftest.py (501728c).
- Commits 482f7a95, f27d13cd, be7dea8f, c452e75f, 1ae97a96.
  PR #2 integrada: bc68ac387a5992c6e806e03e5a87b01d969ddf6f. Render live dep-dbsa9pjm8hqs73c6ukb0; SELFTEST geral e 12 testes da Torre aprovados, Neon pronto. Validação visual real pendente.
- Pendências: validação visual, calibragem real de IA, Catacumbas 31–50,
  demais reinos, cerimônias/recompensas e migração futura do completed.
- Rollback: manter main anterior até validar; sem migração destrutiva.

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
- Commit cf0a2e3b; Render live: dep-dbsa7367bikc73f1r410, commit 4426887220cbc05e420b6c27eec26436bf1f1116. SELFTEST geral e 8 testes da Torre aprovados; Neon conectado. Sem alteração de servidor ou banco.
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
