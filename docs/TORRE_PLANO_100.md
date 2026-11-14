# Torre dos Reis — plano da campanha de 100 andares

Status: **planejamento**, não implementado. Decisão do criador em 14/11/2026:
quatro reinos de 25 andares; conservar o layout de partida tradicional aprovado,
o cenário SVG em tela cheia e a independência entre ambiente e cosméticos.
Os detalhes de balanceamento, narrativa e recompensas abaixo são propostas para
teste e aprovação, não funcionalidades já publicadas.

## Detalhamento por reino

- [Castelo Esquecido — 25 andares](TORRE_CASTELO_25.md): catálogo individual de inimigos,
  classes, dificuldades, cinco estágios visuais, HUD e mapa 5×5.
- Catacumbas, Império e Trono do Fim: detalhamento individual futuro.

Decisão posterior do criador: o mapa mostra exclusivamente os 25 andares do
reino atual, com ícones de inimigos e chefes; HUD tematizado por reino.

## 1. Distribuição definitiva

| Andares | Domínio (ID existente) | Chefe | Identidade |
|---|---|---|---|
| 1–25 | Castelo Esquecido (castle) | O Cavaleiro Sem Nome | Pedra, ferro, tochas, brasões |
| 26–50 | Catacumbas dos Reis (crypt) | O Rei Esquecido | Lápides, inscrições, névoa, estátuas |
| 51–75 | Império Dourado (gold) | O Imperador de Ouro | Mármore, ouro, estandartes, poder |
| 76–100 | Trono do Fim (cosmos) | O Rei Primordial | Cristais, constelações, órbitas, infinito |

O tabuleiro continua com 64 casas, 12 pedras por lado, regras brasileiras, IA
autoritativa do servidor e a skin/tema escolhidos pelo jogador. Não trocar as regras,
atribuir vantagens ao adversário ou forçar cosméticos por causa do reino.

## 2. Identidade visual, sem quatro interfaces incompatíveis

Preservar a composição aprovada: cenário fixo de viewport atrás da shell; cabeçalho
Casa de Damas, navegação, banner do reino, indicação de turno, cartas de jogadores,
tabuleiro tradicional grande com moldura da skin, controles abaixo, painel de
progresso e histórico à direita. Em celular, os painéis passam para baixo; a mesa
continua utilizável sem rolagem horizontal. Não reverter para tabuleiro minúsculo
dentro do SVG. Não ocultar a arquitetura com uma camada opaca.

| Elemento | Castelo | Catacumbas | Império | Trono do Fim |
|---|---|---|---|---|
| Painéis | Pedra e ferro, cantos com rebites | Lápides em relevo, inscrições discretas | Mármore, moldura dourada, brasão | Cristal, cantos geométricos, linhas orbitais |
| Banner | Brasão e estandarte rasgado | Selo funerário, runas | Decreto imperial, estandarte vermelho | Constelação e selo primordial |
| Mapa (25 casas) | Caminho de pedras / muralha | Nichos numerados / inscrições | Registro imperial de conquistas | Órbita de 25 estrelas numeradas |
| Coroas | Ferro e ouro envelhecido | Coroa espectral | Coroa de ouro | Coroa astral |
| Entrada do chefe | Portões e tochas | Selo da tumba se abre | Estandartes se erguem | Anéis alinham-se e trono aparece |
| Áudio opcional | Vento e tochas | Eco, correntes | Percussão e sinos | Ambiência espacial |

Ornamentos são CSS/SVG, não imagens geradas. Não criar uma segunda grade de
tabuleiro ou alterar data-theme/data-skin para tematizar o HUD. Use data-realm
na camada .tower-world e no container .arena; adicionar data-stage=1..5.
A mesma arquitetura deve ser reconhecível nos cinco estágios; variar detalhes,
não apenas cor. Priorizar profundidade, iluminação e objetos bem apoiados.
Preservar contraste das casas, foco de teclado, contadores legíveis e botões.
Reusar SVG estático/cache; animar transform/opacity em poucas camadas, pausar
em aba oculta, respeitar prefers-reduced-motion e o seletor de efeitos.
Testar 2560×1080, notebook 1366×768 e celular (360–430px), inclusive rolagem.

## 3. Progressão de 100 andares

Cada reino possui cinco capítulos de cinco andares. A cada capítulo há uma nova
característica de jogo e mudança visual; o último andar do bloco é um encontro
especial. Os andares intermediários continuam partidas completas (não tutoriais).
A escala D1–D10 é uma meta de dificuldade relativa a calibrar, não Elo medido nem
profundidade real. O quadro cobre os 100 andares; os nomes são propostas.

| Andares | Capítulo / adversário marcante no fim | Foco da IA | Meta D | Evolução visual |
|---|---|---|---|---|
| 1–5 | Portões / Sentinela | Posicionamento, erros humanos plausíveis | 1 | Lua e poucas tochas |
| 6–10 | Muralhas / Capitão | Centro, capturas simples | 1–2 | Bandeiras, tochas acesas |
| 11–15 | Salão das armas / Carrasco | Trocas e capturas múltiplas | 2 | Armaduras, brasões |
| 16–20 | Salão da guarda / Estrategista | Proteção, promoção | 2–3 | Luz nos vitrais |
| 21–25 | Trono abandonado / Cavaleiro Sem Nome | Defesa, contra-ataque | 3,3–4,5 | Trono e portões revelados |
| 26–30 | Entrada da cripta / Guardião das Tumbas | Contra-ataque e segurança | 3–4 | Névoa rente ao chão |
| 31–35 | Galeria dos nomes / Vigia das Almas | Armadilhas de captura | 4 | Inscrições iluminadas |
| 36–40 | Sepulcros / Carrasco Espectral | Combinações de sacrifício | 4–5 | Estátuas e nichos ativos |
| 41–45 | Câmara dos reis / Oráculo | Finais e repetição | 5 | Chamas espectrais |
| 46–50 | Tumba real / Rei Esquecido | Mobilidade, cálculo de finais | 5–6 | Selo da tumba e coroa |
| 51–55 | Portão imperial / Pretor | Centro e mobilidade | 5–6 | Guardas e mármore |
| 56–60 | Galeria de vitórias / General | Pressão e trocas favoráveis | 6 | Estandartes |
| 61–65 | Conselho / Chanceler | Defesa estruturada | 6–7 | Brasões de conquista |
| 66–70 | Salão do sol / Marechal | Ataque coordenado e promoções | 7 | Raios de luz dourada |
| 71–75 | Trono imperial / Imperador de Ouro | Busca profunda, finais | 7–8 | Trono imperial revelado |
| 76–80 | Limiar / Arauto Astral | Flexibilidade tática | 7–8 | Estrelas e cristais |
| 81–85 | Órbita / Guardião das Órbitas | Mobilidade e controle de damas | 8 | Anéis orbitais |
| 86–90 | Véu / Cronista do Vazio | Combinações e avaliação de finais | 8–9 | Constelações se conectam |
| 91–95 | Horizonte / Eclipse | Pressão profunda e paciência | 9 | Eclipse e energia |
| 96–100 | Trono do Fim / Rei Primordial | Melhor perfil calibrado, sem trapaça | 9–10 | Trono e singularidade |

Regra de dificuldade: subir gradualmente dentro de cada capítulo; no encontro
especial, pequeno pico; começo do próximo capítulo pode estabilizar. O nível
real não depende só de profundidade: medir tempo, qualidade de lances, taxa de
vitória/empate, duração e satisfação. O motor hoje oferece cinco perfis de busca
(3/5/7/9/11 de profundidade máxima; orçamento 0,12/0,23/0,38/0,60/0,85 s).
Proposta: configurar perfil, orçamento de nós/tempo, pesos posicionais e
variabilidade controlada por andar. Nos níveis iniciais, escolher legalmente
entre candidatos próximos; nos altos, usar avaliação mais precisa, não
aleatoriedade injusta. Não reutilizar os cinco perfis como se fossem 100 níveis
distintos sem calibrar. Não aumentar o tempo de resposta ilimitadamente.
Os chefes não recebem peças extras, turnos extras ou vitórias por material.
Respeitar a lei da maioria, promoção, repetição e contagem oficial dos finais.

## 4. Coroas, rotas e santuários (proposta)

- Ascensão: três coroas, uma por derrota/desistência confirmada. Empate mantém
  andar e coroas. Perder todas retorna ao último santuário, preservando recorde.
- A cada 10/20 andares dentro do reino e ao concluir o reino (25), santuário:
  restaura três coroas e grava checkpoint. Começos: 1, 11, 21, 26, 36, 46,
  51, 61, 71, 76, 86, 96. Fim no 100. Isso evita exigir 25 vitórias quase
  consecutivas antes de salvar. Aprovação/balanceamento pendentes.
- Expedição: três coroas, sem santuário/retorno; recorde pessoal separado da
  Ascensão, sem ranking competitivo até validar a campanha.
- Guardião: força-base, escolha segura. Carrasco: adversário um pouco mais forte,
  bônus cosmético/medalha futuramente. Desconhecido: estilo/força variável
  dentro de limites previsíveis, recompensa futura; nunca punir sem avisar.
- Rotas não alteram as regras do tabuleiro. Chefes dos andares 25/50/75/100
  são encontros fixos; rotas podem preparar a chegada, não eliminar o chefe.
- Eventos narrativos e caminhos/finais podem ser desenhados depois da
  estabilidade dos modos; hoje as rotas são somente seleção de força.

## 5. Recompensas e prestígio (não implementadas)

Proposta: 25 — ambiente do Castelo e brasão/moldura; 50 — ambiente das Catacumbas,
efeito espectral; 75 — ambiente imperial, selo/moldura dourados. A liberação
de ambientes para partidas normais precisa ser isolada de tema/skin e exige
definição do modelo de inventário. Nenhum item concede vantagem na partida.
O prêmio do 100 **não será outro tabuleiro do Rei Cósmico**, que já existe na
Jornada dos Reis. Opção em aberto: título Soberano da Torre, coroa de
singularidade como cosmético de perfil e cerimônia exclusiva do Trono do Fim.
Definir a identidade final com o criador antes de implementar. Não atribuir
recompensas retroativamente sem política explícita.

## 6. Migração e implementação

A produção atual é beta 1–30, com domínios 1–10, 11–20, 21–30. Não alterar
somente RELEASE_MAX_FLOOR: domínio, chefe, checkpoint, dificuldade e UI estão
distribuídos entre torre.py, servidor.py, torre.html e testes.
- Criar catálogo versionado de 100 andares no servidor; expor metadados de domínio,
  estágio, adversário, força e santuário no payload. Frontend renderiza esse
  catálogo, sem constantes duplicadas de 30, módulo 10 ou arrays de 3 reinos.
- Migração aditiva/versionada: preservar id da tentativa, floor, highest, lives,
  partida ativa, board, sequence, moves, repeats, status e versão. Não excluir,
  resetar, sobrescrever Journey/PH ou alterar Neon manualmente. Proposta:
  manter números já conquistados; checkpoint antigo 11/21 permanece válido
  até o próximo novo santuário; tentativa completed da beta com 30 vitórias
  reabre no 31 sem zerar recorde; partidas ativas mantêm sua configuração
  até terminar, depois usam catálogo novo. Testar em cópia/SQLite primeiro.
- Desacoplar dificuldade da Jornada: parametrizar o motor já existente de forma
  retrocompatível, sem mudar perfis da Jornada nem online. Persistir o perfil
  exato da partida para recarga estável; não aceitar resultado do cliente.
- Interface: mapear 25 andares com cinco grupos; usar data-stage para variantes
  decorativas; integrar Cosmos ao quarto reino; conservar estrutura e escala
  da mesa aprovada. Testar todas as fronteiras de domínio e o 100.
- Verificar primeira fase em branch de teste: 1–25 com visuais e progressão;
  depois 26–50, 51–75 e 76–100. Só publicar o que tiver sido testado; não
  liberar níveis incompletos. Definir limite de release separado do total.
- Testes de regressão: 100 níveis e chefes 25/50/75/100; santuários e restauração;
  perda total de coroas; empate; duas modalidades; migração de tentativa
  ativa/completa; idempotência; movimentos e promoção; API autenticada;
  nenhuma alteração de PH/Jornada; render 64 casas, troca de reino/estágio,
  skins, responsividade, redução de movimento e desempenho.
- Depois do teste funcional, registrar feedback de dificuldade do criador,
  ajustar e validar visualmente antes de ampliar produção. Documentar cada
  mudança e correção no changelog.
