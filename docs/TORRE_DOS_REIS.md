# Torre dos Reis — base de desenvolvimento (não publicada)

A Torre é um modo solo com partidas completas de damas tradicionais. A versão inicial
terá 10 andares do Castelo Esquecido, culminando no Cavaleiro Sem Nome.
O visual V4 das Catacumbas aprovado em 14/11/2026, junto com Castelo, Império e
Trono do Fim, será a referência para os cenários. As quatro arenas existem na
prévia HTML da conversa; o jogo ainda não contém os arquivos finais desses cenários.

## Contratos
- Ambiente e skin independentes: um atributo de domínio exclusivo da Torre, nunca
  substituir os atributos data-theme/data-skin do jogador.
- Cenário em camada atrás do tabuleiro; HUD e efeitos decorativos não interceptam
  cliques nem alteram geometria ou regras. Pilares e pedestais no mesmo plano
  do piso, exceto objetos celestes deliberadamente flutuantes.
- Ascensão: três coroas, santuário por domínio, derrota final volta ao último
  santuário preservando o recorde. Expedição: três coroas, fim da tentativa ao
  esgotar. Empate não avança nem consome coroa.
- Rotas guardião/carrasco/desconhecido preparadas; balanceamento, bênçãos,
  eventos secretos e recompensas ainda não implementados.
- O núcleo torre.py só recebe resultados terminais do motor existente, nunca
  de dados enviados pelo cliente. O primeiro domínio é o único habilitado
  no núcleo. Domínios intermediários 31–90 permanecem em aberto.

## Próxima integração
1. Criar persistência aditiva no Neon com tower_runs (player_id, run_id, payload,
   version) e tower_results (run_id, match_id, outcome) com chave única;
   transação e checagem de versão, autenticação obrigatória e salvamento de
   tabuleiro, sequência, lado, histórico e estado do motor.
2. Reaproveitar a validação autoritativa de movimentos e IA da Jornada, sem
   reescrever regras, com perfis de comportamento e limites medidos.
3. Montar o ambiente V4 como SVG em camada separada e isolada; pausar quando
   oculto, respeitar redução de movimento e manter a skin equipada.
4. Menu Torre, HUD, escolha de rota, partida, derrota, vitória, retomada;
   não ativar a entrada antes de testes completos.
5. Recompensas idempotentes e ranking assíncrono separados de PH e da Jornada.
6. Testes reais desktop/celular, baixo desempenho, recarga no meio da partida,
   captura múltipla, promoção, derrota, empate e recuperação do Neon.
 
Esta branch é uma fundação sem rotas HTTP, migrações ou mudanças na produção.
