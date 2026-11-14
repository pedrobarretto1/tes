# Torre dos Reis — Reino I: Castelo Esquecido (1–25)

Status: especificação de design proposta em 14/11/2026, após escolha da opção B
pelo criador. Não implementado. Ver TORRE_PLANO_100.md para plano global,
TORRE_DOS_REIS.md para produção atual e CHANGELOG.md para histórico.

## Decisões confirmadas
- Quatro reinos com 25 andares cada, total 100.
- O mapa lateral exibe somente o reino atual, em cinco linhas de cinco casas:
  1–25, depois 26–50, 51–75 e 76–100. Ícones de inimigos e chefes.
- HUD próprio por reino, cenário SVG original em tela cheia, mesa tradicional
  grande e cosméticos do jogador independentes. Não gerar imagens no lugar do SVG.
- Partidas completas de damas brasileiras, 12 pedras por lado, IA sem privilégios.
- Castelo termina com O Cavaleiro Sem Nome. Catacumbas começa no andar 26.

## 1. História
O castelo está abandonado, mas seus defensores continuam guardando as lembranças
de uma guerra esquecida. O jogador atravessa portões, muralhas, arsenal, guarda
real e trono. O Cavaleiro Sem Nome, fiel ao reino desaparecido, protege a passagem
para as Catacumbas. Narrativa curta antes dos encontros especiais; não bloquear
a partida com cutscenes longas nem repetir introduções a cada tentativa.
Nomes, falas e detalhes de narrativa são propostas desta sessão.

## 2. Catálogo de 25 andares

D = meta relativa de dificuldade na escala 1–10 da campanha inteira, não Elo,
profundidade efetiva ou resultado medido. A descida pequena após elites é
intencional; o desafio cresce por capítulo. Todos os encontros começam com
tabuleiro completo e posição inicial oficial. IDs estáveis sugeridos: castle-01
a castle-25. Classes normal, elite, preboss, boss. Total: 19 normais, 4 elites,
1 pré-boss, 1 boss. Estilo indica objetivo de IA, não habilidade já implementada.

| Andar | Capítulo | Inimigo | Classe | D | Estilo |
|---:|---|---|---|---:|---|
| 1 | Portões | O Escudeiro Perdido | normal | 1,0 | Posicionamento simples |
| 2 | Portões | O Vigia da Ponte | normal | 1,1 | Proteção de peças |
| 3 | Portões | O Soldado de Ferro | normal | 1,2 | Capturas imediatas |
| 4 | Portões | O Guardião do Portão | normal | 1,3 | Defesa e espaço |
| 5 | Portões | O Sentinela | elite | 1,7 | Defesa e ataque |
| 6 | Muralhas | O Arqueiro da Muralha | normal | 1,5 | Diagonais |
| 7 | Muralhas | O Lanceiro | normal | 1,6 | Avanço agressivo |
| 8 | Muralhas | O Protetor da Fortaleza | normal | 1,8 | Defesa em grupos |
| 9 | Muralhas | O Tenente da Guarda | normal | 1,9 | Capturas múltiplas |
| 10 | Muralhas | O Capitão | elite | 2,3 | Centro, trocas, contra-ataques |
| 11 | Salão das Armas | O Ferreiro Real | normal | 2,1 | Estrutura defensiva |
| 12 | Salão das Armas | O Espadachim | normal | 2,2 | Ataques rápidos |
| 13 | Salão das Armas | O Mestre dos Escudos | normal | 2,3 | Proteção de ameaçadas |
| 14 | Salão das Armas | O Duelista da Coroa | normal | 2,5 | Sacrifícios e combinações |
| 15 | Salão das Armas | O Carrasco | elite | 2,9 | Armadilhas de captura obrigatória |
| 16 | Salão da Guarda | O Cavaleiro de Bronze | normal | 2,7 | Rotas de promoção |
| 17 | Salão da Guarda | O Vigia Real | normal | 2,8 | Antecipação |
| 18 | Salão da Guarda | O Comandante de Ferro | normal | 3,0 | Pressão coordenada |
| 19 | Salão da Guarda | O Conselheiro da Coroa | normal | 3,2 | Trocas favoráveis e finais |
| 20 | Salão da Guarda | O Estrategista | elite | 3,6 | Planejamento e promoção |
| 21 | Trono Abandonado | O Último Sentinela | normal | 3,3 | Defesa e paciência |
| 22 | Trono Abandonado | O Arauto do Trono | normal | 3,5 | Diagonais e damas |
| 23 | Trono Abandonado | O Guardião da Coroa | normal | 3,7 | Pressão e contra-ataque |
| 24 | Trono Abandonado | O Portador do Selo | preboss | 4,0 | Defesa avançada, finais |
| 25 | Trono Abandonado | O Cavaleiro Sem Nome | boss | 4,5 | Estilo completo, adaptável |

O D4,5 do chefe é um refinamento proposto do intervalo D3–4 do plano inicial;
calibrar antes de publicar. O início das Catacumbas pode estabilizar abaixo
do pico do chefe, sem reduzir a tendência geral.

## 3. Cinco estágios visuais (data-stage)

| Estágio | Andares | Cenário original + detalhes | Transição |
|---|---|---|---|
| 1 | 1–5 | Lua nos vitrais quebrados, tochas fracas, pedra e ferro, brasão antigo | Portão interno se abre após 5 |
| 2 | 6–10 | Mais tochas, bandeiras e marcas de antigos guardas | Estandarte revelado após 10 |
| 3 | 11–15 | Armaduras, escudos e brasões no salão; apoio no piso/paredes | Insígnia do Carrasco após 15 |
| 4 | 16–20 | Vitrais iluminados, símbolos restaurados da guarda | Brasão real revelado após 20 |
| 5 | 21–25 | Trono, estandartes reais e luz majestosa, sem exagerar no brilho | Selo aberto no 24; passagem para a cripta após 25 |

Não trocar o SVG base aprovado por outro cenário. Usar grupos SVG decorativos
por estágio, classes/atributos, opacidade/transform e elementos estáticos.
Ajustar posição dos objetos no chão (não flutuar). Sem filtros animados caros,
sem redesenho contínuo do SVG, sem regressão do desempenho da mesa/skins.
A animação de transição pode durar 1–2 segundos, pulável, sem bloquear
recarregamento; respeitar redução de movimento e desligamento de efeitos.

## 4. HUD e mapa
Preservar estrutura da mesa aprovada, com .tower-world fixo em viewport,
shell, banner, cartas dos jogadores, tabuleiro, ações, painel lateral e histórico.
Castelo: painel pedra escura, ferro envelhecido, rebites, brasão e dourado gasto;
cantos em metal, separadores de pedra, ícones SVG de elmo (normal), escudo com
insígnia (elite), portão selado (pré-boss), coroa/trono (boss).
Mapa 5x5, cada linha identificada pelo capítulo. Casas mostram número e
ícone. Estado atual em destaque com contraste e texto acessível; conquistado
com marca, futuro bloqueado; progresso histórico e piso atual distintos após
retorno ao santuário. Não usar apenas cor para indicar estado. Andares não são
atalhos para pular a campanha. Pode consultar nome/classe ao clicar ou focar.
No topo do painel: adversário atual, classe, estilo, capítulo, D relativo,
coroas e checkpoint; histórico recolhível em telas pequenas.
Mapa não mostra 26–50 antes de entrar nas Catacumbas. Depois troca integralmente
o bloco e a temática, mantendo mesa/skins. Adicionar legendas de símbolos,
santuários e estados. SVG/CSS sem imagens externas.

## 5. Coroas, rotas, chefes e recompensas
- Ascensão: três coroas; derrota ou desistência validada perde uma, empate não
  avança/não perde. Após vencer 10, santuário 11; após 20, santuário 21;
  após 25, santuário 26. Restaura três coroas. Ao zerar, voltar ao último
  santuário e preservar recorde. Expedição sem retorno nem restauração.
- Rotas Guardião/Carrasco/Desconhecido permanecem nos normais. Guardião = base;
  Carrasco = pressão maior; Desconhecido = estilo/força dentro de limites.
  Proposta para elites 5/10/15/20, pré-boss 24 e boss 25: encontro fixo,
  sem rota que pule inimigo ou reduza sua força; botão "Enfrentar".
- Boss 25: partida completa, mesma regra, sem bônus materiais, sem vitórias
  por vantagem material e sem poderes que alterem as regras.
  Fala de entrada: "Meu nome se perdeu com o reino. Meu juramento, não."
  Fala de vitória: "A coroa não é minha para guardar. Siga para onde repousam os reis."
- Proposta de conquista: ambiente Castelo Esquecido para partidas normais,
  brasão/moldura Herança do Castelo e título Herdeiro do Castelo. Requer
  inventário/validação de recompensa futura; não distribuir na beta agora.
  Recompensa do 100 segue reservada e distinta do tabuleiro cósmico da Jornada.

## 6. Implementação e validação (próxima fase)
- Catálogo versionado no servidor (domínio, capítulo, adversário, classe, D,
  estágio, checkpoint, perfil IA e limites de rota). Frontend recebe metadados;
  não duplicar constantes de 10/30. Definir release cap sem bloquear jogadores
  existentes no 26–30; migração compatível antes de publicar.
- Calibrar IA: manter motor oficial; usar orçamento de busca, pesos de estilo
  e seleção controlada entre lances legais, nunca quebrar lei da maioria.
  Estilos e D da tabela são metas, não configurações medidas.
- Testar todos 25, limites 25→26, santuários 10→11 e 20→21, derrota no 24,
  empate e reabertura, chefes fixos, partidas ativas da beta, isolamento
  Jornada/PH/skins. Testar mapa 25 casas, estados, classe, bloco do reino,
  renderização em ultrawide, notebook e celular e efeitos pausados.
- Sem alteração de código nesta etapa. Registrar implementação, testes e
  publicação futura no CHANGELOG. Não reiniciar ou reclassificar progresso.
