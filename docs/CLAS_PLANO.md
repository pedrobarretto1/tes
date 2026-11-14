# Clãs da Casa de Damas — especificação inicial

Status: planejamento, 14/11/2026. Pedido do criador: criar/entrar em clã, requisitos opcionais, convites e pedidos exclusivos ao dono, chat, nível médio e torneios internos com prêmios financiados pelo organizador. Núcleo social v1 publicado: PR #5, commit 8d7cb4de18a59d4507af4e7e8e5cbf7c77bf8d04, Render dep-dbsbddlg1s2s73enea1g live. Torneios, prêmios e PH ainda não implementados.

## Implementação social v1
Validação: CI final 43632355617, 18 testes aprovados, SELFTEST e regressão UI Torre aprovados. Simulação de interface Clãs passou; teste visual e ingresso entre duas contas reais pendentes. Neon confirmou cinco tabelas novas.

- clas.py: schema aditivo e autoridade de recrutamento, nível, chat e gestão; servidor.py integra setup, API /api/social/clans/* e estado social. Perfil público e próprio mostram nível. index.html/clube.js/clube.css: Salão dos Clãs, formulário, busca, membros, pedidos, administração, chat e aba de torneios informativa.
- Conta registrada, 30 membros, um clã por conta. Pedidos 7 dias, limite 10 por candidato, cooldown de 5 minutos após recusa. Dono pode convidar pelo perfil público, inclusive via busca, ou pela lista do clã. Chat privado em texto puro, 500 caracteres, últimas 50 mensagens, 5 envios/10 s; paginação antiga, denúncia, moderação e retenção ainda pendentes. Não há exclusão automática por queda de estatísticas.
- Nível conforme fórmula abaixo, conquistas oficiais permitidas explicitamente; média exibida com uma casa. Gestão: dono transfere liderança, remove membros ou dissolve somente quando for o único membro; saída de dono bloqueada. Requisitos editáveis. Notificações acionáveis sem timer local, revalidação no servidor.
- Testes SQLite em test_clas.py; CI inclui regressões da Torre e gerais. Nenhum prêmio debitado, nenhuma mudança de PH. Torneios internos, cofre, desempates e auditoria continuam próximos passos.

## Refinamento visual publicado
PR #6, commit e522bf09430b3a6eb7ec94dcb4df6f27dd5cb588, Render dep-dbsbidu1egvs73dculog live. Salão de ferro/dourado, abas compactas, busca em grid, campos legíveis e carta de fundação com prévia em tempo real do nome, sigla, descrição e brasão. Menu Clãs usa secondary. Sigla preserva regra 2–6 letras/números, sem pontos; aviso antes do envio. CI 43633284488 aprovou Chromium em 375/758/1280 px, 18 testes Python e SELFTEST. Teste de ingresso entre duas contas reais ainda pendente. Nenhuma mudança em banco, requisitos ou economia.

## Brasões personalizados
Editor na fundação e Administração, com símbolo, symbol_color, frame_style, frame_color e background_color. Sete símbolos (incluindo Cruz de Jerusalém em SVG), seis molduras (Real, Militar, Sombria, Sagrada, Antiga, Mística), doze cores independentes, sem regra de contraste e sem cobrança. Tabela clan_crests (clan_id, design JSON); clãs antigos recebem padrão derivado do emblem. API create aceita crest; clans/crest altera apenas design, exclusivamente pelo dono. Brasão compartilhado nas listas, sede, chat e pedidos. Testes de persistência e Chromium aprovados (CI 43634204285, 19 testes Python e três larguras). PR #7 publicada: commit 2f5719b0ab84a75abd0b75e865ab9b0cfb6378cb, Render dep-dbsbn8ek1f9s738rakc0 live. Validação manual em conta real pendente.

## Molduras heráldicas refinadas
Renderer SVG compartilhado: heraldicFrames e paintCrestFrame em clube.js, CSS em camadas; seis estilos com geometria curva/armadura/sombria/sagrada/antiga/arabescos, contornos, relevo e ornamentos. Mantém os IDs e todas as cores salvas, sem regra de contraste, sem migração. Cruz de Jerusalém é o sétimo símbolo, SVG de cinco cruzes. Testes Chromium de geometria e cores; publicação do refinamento a confirmar.

## Produto
- Clube → Clãs: busca por nome/sigla, lista paginada, criar clã, Meu clã.
- Clã: nome único normalizado, sigla, brasão, descrição, dono, membros, data, nível, chat e torneios.
- Proposta inicial: um clã por conta, até 30 membros, somente conta com login para ingresso/criação e torneios financiados. Visitantes podem consultar clãs. Não exigir CPF, e-mail ou novos dados pessoais.
- Dono administra requisitos, convites, solicitações, remoção de membros, transferência de liderança e dissolução. Somente dono decide ingresso e recebe pedido de entrada. Membros organizam torneios, não aprovam recrutamento.
- Ao sair, dono transfere liderança ou dissolve após resolver torneios e reservas; não deixar clã órfão. Troca de dono atômica. Não remover membro para alterar chave de torneio em andamento.

## Recrutamento
Requisitos independentes, todos opcionais (null = Nenhum). Combinação AND:
PH mínimo, vitórias mínimas, derrotas mínimas, taxa mínima de vitória, nível mínimo.
Propostas adicionais: máximo de derrotas e mínimo de partidas concluídas.
Taxa = vitórias / (vitórias + derrotas + empates) × 100; zero partidas = sem taxa, não qualifica se taxa exigida. Usar dados de ranking do servidor, não dados enviados pelo cliente. Sem expulsão automática quando a estatística cai depois de entrar; regras valem para admissão.
- Candidato consulta requisitos e diagnóstico; se não atende, não pode solicitar.
- Solicitação pendente única por candidato/clã. Apenas dono recebe notificação com nome, stats públicos, requisitos e status de cada um, Aceitar/Recusar/X. Revalidação no aceite (requisitos atuais, vaga, conta e ausência de outro clã). Entra numa única transação; pedidos concorrentes invalidados.
- Dono pode convidar um perfil; convidado escolhe aceitar/recusar; mesma validação, sem bypass. Fechar cartão não recusa. Pedido de clã persiste; política de validade proposta 7 dias, notificação acionável sem timer local. Limites de envio e cooldown após recusa. Chat nunca expõe tokens, sessões, senhas.
- Se requisitos forem alterados, comparar regras atuais e informar candidato, não aprovar silenciosamente com regra antiga.

## Nível
Hoje não há nível numérico canônico no perfil: existem PH, vitórias/derrotas/empates, cosmetics.completed, achievements, cups e journey.completed; Torre possui highest por modalidade. Criar nível derivado de feitos, não do saldo de PH/moedas ou compras.
Proposta v1: XP = 10×vitórias + 3×empates + 2×partidas ranqueadas concluídas (cosmetics.completed, exclui desistência) + 25×conquistas oficiais distintas + 50×capítulos concluídos da Jornada. Nível = 1 + floor(sqrt(XP/50)). Ex.: XP 800 → nível 5. Valores propostos, não medidos. Não contar conquistas cosméticas compradas, não contar torneios privados como vitórias ranqueadas. Torre e campeonatos futuros poderão somar feitos únicos após validação. Persistir fórmula versionada, calcular servidor, não conceder XP com PH transferido. Evitar farming de partidas rápidas/mesmos pares; inicialmente exibir nível como progresso, não rank de habilidade.
Nível do clã = média aritmética dos níveis dos membros atuais, exibida com uma casa decimal; ranking usa valor preciso. Ex.: 5, 8, 11 → 8. Média pode cair ao entrar/sair; mostrar também total de membros, conquistas e troféus. Proposta: ranking de clãs só com >=5 membros e 7 dias de existência; não expulsar iniciantes para melhorar média. Nível não é força competitiva.

## Chat
Mensagens persistidas no Neon por clã, autor, texto, timestamp e ID. Só membros leem/escrevem; servidor confere associação a cada requisição. Texto puro, escape via textContent, comprimento <=500, paginação incremental, limite de envio, denúncia/silenciar, dono pode moderar com trilha. Não logar texto privado em console. Retenção inicial 90 dias proposta. Notificações existentes e polling incremental; não reconsultar histórico inteiro a cada atualização.

## Torneios internos e premiação
Membros podem organizar, sem taxa de entrada. Escolhem nome, regra oficial suportada, horário/inscrições, participantes (4 ou 8 inicialmente), formato eliminatório, prazo por rodada e prêmio. Chave e regras congeladas após início; empate exige revanche com limite e regra de desempate publicada; W.O. por ausência e desconexão com janela de reconexão. Resultado exclusivamente do motor servidor, não botão do organizador.
Prêmios:
- Moedas: organizador informa inteiro positivo, servidor verifica saldo, debita e cria reserva na mesma transação. Limite inicial sugerido 500 por evento, 1 evento financiado ativo por organizador, ajustar após testes. Sem dinheiro real.
- Skin: compra para prêmio dentro do clã, no catálogo SHOP_ITEMS elegível (não relíquia exclusiva, item campeão, grátis ou sazonal fechado). Preço validado servidor, débito em moedas, reserva registra SKU e preço. Não remover skin já pertencente ao organizador; comprar uma licença de presente separada. Ao campeão, inserir purchases ON CONFLICT; não equipar automaticamente. Se já possui, política divulgada previamente: creditar moedas equivalentes ao preço pago (não duplicar item, sem alteração de custo). Sem entrega antes da final.
- PH: **fragilidade crítica**. Atualmente players.points é saldo e ranking simultaneamente; visitante começa com 1000, vitória +25, derrota -15, desistência -20, empate +5. Transferir PH diretamente permitiria contas alternativas financiar um campeão, distorcer ranking e requisitos. Não liberar transferência direta no MVP. Alternativas: (A) honra de torneio/clã separada, sem afetar ranking; (B) se criador exigir PH reais, separar PH competitivo (obtido em partidas oficiais) de saldo de honra presenteável, migrar ranking e requisitos para competitivo, definir origem elegível e limites; não financiar com PH inicial/gratuito. Decisão explícita antes da implementação. Sem converter moedas em PH.
- Criador não altera vencedor, prêmio ou regras depois da inscrição; proposta de torneio financiado: criador pode competir, se vencer recebe devolução da própria reserva (não recompensa duplicada), registrar resultado e transparência. Avaliar proibir sua participação em caso de abuso. Sem recompensa competitiva oficial, sem PH de partidas internas e sem duplicar conquistas oficiais.
- Cancelamento pré-início devolve reserva exata ao patrocinador. Após início: sem cancelamento unilateral; só timeout/falha objetiva/regras publicadas e auditoria. Organizador sair do clã não cancela obrigação. Se final decidida, prêmio entregue mesmo se clã mudar de dono. Não permitir dissolução com reserva em aberto.

## Desempate dos torneios — proposta 14/11/2026
- Propor ou aceitar empate não é derrota, desistência, W.O. nem eliminação.
  Empate por acordo e empate automático do motor têm o mesmo efeito sobre a
  chave. Recusa mantém a partida e o relógio. Limitar frequência de propostas
  por jogador, sem bloquear empates regulamentares. UI temática já existente
  do pedido de empate deve explicar a revanche e não prometer PH ranqueado.
- Primeira partida empatada: revanche completa, mesma regra e relógio
  original, cores invertidas, novo match_id. Não repetir o resultado anterior.
- Segunda partida empatada: par de rápidas com 5 minutos por jogador em cada,
  cores alternadas, placar 1 vitória / 0,5 empate / 0 derrota. Dois jogos
  completos; quem tiver mais pontos avança. Outros confrontos da rodada
  podem terminar, mas a chave só avança quando o adversário estiver definido.
- Se o par rápido terminar empatado: última sessão com novo par rápido,
  horário definido por regras publicadas antes da inscrição e prazo objetivo,
  persistindo o placar e a reserva. W.O. somente por ausência/desistência
  comprovada conforme regras, com janela de reconexão; não confundir empate.
- Proposta para impasse final: após esgotar as sessões previstas, dois
  co-campeões dividem o prêmio de moedas; valor ímpar devolve sobra ao
  patrocinador. Skin indivisível: converter o custo já reservado em moedas
  e dividir; não criar duas licenças nem cobrar extra. PH somente após
  decisão de economia separada, com regra equivalente de divisão. Não
  premiar nem criar campeão por sorteio, material restante ou PH prévio.
- Em quartas/semifinal, empate persistente não gera dois classificados
  para a mesma vaga. Se prazo final expirar sem desempate, suspender o
  confronto; sem resolução dentro do prazo objetivo publicado, cancelar
  o torneio e devolver a reserva integral (sem pagamento de campeão).
  Esta é a alternativa conservadora para o MVP; avaliar desempate por
  desafios de damas equivalentes em fase futura, não por sorteio.
- Nenhum empate paga recompensa parcial ou altera o ranking oficial.
  Liquidação da final (campeão único ou divisão) ou refund acontece uma
  vez, transacionalmente, após decisão autoritativa. Persistir partidas,
  placares, cores, prazos e transições; nenhuma ação do dono pode escolher
  vencedor ou cancelar unilateralmente uma final empatada.
- Testes: acordo/recusa, empate automático, inversão de cores, dois jogos
  rápidos, placar empatado, reconexão, deadline e W.O. distintos, co-campeões,
  divisão ímpar e skin, refund por impasse, idempotência/queda/restart.
  Política proposta, não aprovada nem implementada; os eventos oficiais
  atuais permanecem inalterados. event_tick hoje cria outra sala a cada
  empate sem limite explícito; não reutilizar esse comportamento para prêmios.

## Persistência e segurança
O código atual usa TOURNAMENTS em memória; event_champions grava campeão, mas estado de evento/salas não é suficiente para valores depositados. Não usar eventos atuais como cofre. Antes de torneios financiados persistir chave, participantes, regras, partidas, IDs, snapshots/movimentos, prazos e estado de liquidação; retomar após restart Render e reconexão. Ações de cancelamento/resultado verificadas servidor.
Esquema aditivo proposto: clans, clan_members (unique player_id), clan_requests (pending único, tipo, status), clan_messages, clan_tournaments, clan_tournament_entries, clan_tournament_matches, clan_prize_escrow, clan_ledger. FK/constraints, índices por clã e status, transações PostgreSQL/SQLite. Saldo não negativo, atualização condicional coins>=amount, lock de linhas e ordem consistente; reserva, débito e criação atômicos. Liquidação/refund com estado único reserved→paid/refunded e chave idempotente por torneio, no mesmo commit que crédito/purchase. Não confiar em preço, saldo, dono, nível, requisitos, vencedor ou idempotência do cliente.
- Abuse: conta vinculada + mínimo de partidas ranqueadas concluídas e idade da conta (metadado novo, sem inferir passado), participantes distintos, limites por dia/organizador, histórico e auditoria de transações, alertas de partidas repetidas e desistências suspeitas, sem automatizar ban apenas por heurística. Não criar taxa de entrada/apostas. Privacidade: mostrar só campos públicos de perfil.
- Testes: autorização dono/membro/terceiro, requisitos todos null/AND/zero, revalidação concorrente, único clã e vagas, chat XSS/rate/paginação, saldo insuficiente/negativo, dois débitos simultâneos, duplicação de confirmação, campeão único, skin já possuída, cancelamento/refund, queda antes/depois de commit, retomada de chave/partida, clã dissolvido, isolamento Jornada/Torre/ranking.

## Entrega por etapas
1. Núcleo social: nível derivado, criação, busca, membros, pedidos/convites e notificações; chat. Testes e UI temática, branch isolada, banco aditivo. Sem prêmios.
2. Torneios internos persistidos sem prêmios, regras/partidas/reconexão e testes de resultado.
3. Cofre de moedas e skins, auditoria, testes de concorrência e falha. Publicar primeiro beta controlada.
4. Decidir PH com criador, se necessário migrar economia/ranking com testes e política de saldo. Só então liberar.
Registrar cada mudança em CHANGELOG.md e atualizar AGENTS.md com link. A implementação social usa migração aditiva no startup; nenhuma tabela existente é removida.
