# Guia de continuidade — Casa de Damas

Leia este arquivo antes de modificar qualquer parte do jogo. Este é o guia para
assistentes, colaboradores e futuras sessões. A fonte de verdade é o Git,
não uma lembrança isolada da conversa.

## Antes de alterar
1. Conferir branch, commit atual, estado publicado no Render e o último registro
   de docs/CHANGELOG.md. Não confundir código integrado com publicação confirmada.
2. Ler docs/TORRE_DOS_REIS.md para a implementação atual e
   docs/TORRE_PLANO_100.md para o planejamento da campanha completa.
3. Verificar os arquivos reais afetados; distinguir decisões aprovadas pelo
   criador de propostas ainda em discussão. Não substituir trabalho aprovado
   sem necessidade. Pedir confirmação para mudanças de escopo importantes.
4. Não alterar código de produção se o pedido for somente planejamento.

## Arquitetura e restrições
- index.html é a mesa tradicional; servidor.py é o servidor HTTP Python e
  motor oficial; torre.py é a progressão; torre.html é a interface da Torre.
- jornada.js / jornada.css e reis.js / reis.css pertencem à Jornada e aos
  cosméticos reais. Não misturar a Torre com a Jornada do Mestre.
- Persistência de produção: Neon PostgreSQL, com setup aditivo. Não apagar
  tabelas, perfis, cosméticos, PH, partidas ou progresso. Não expor tokens,
  senhas, DATABASE_URL ou dados pessoais em docs/logs/commits.
- Torre: ambiente em SVG de viewport inteira atrás da interface; data-realm
  independente de data-theme/data-skin. Preservar as texturas, animações
  existentes, tamanho do tabuleiro, geometria e regras brasileiras.
- Não usar imagens geradas no lugar dos cenários em código. Preservar
  o estilo aprovado, a posição dos pilares no piso e os efeitos sem degradar
  o desempenho; testar notebook, celular e ultrawide quando possível.
- Planejamento confirmado: 100 andares, 4 reinos de 25 cada. A produção ainda
  é beta 1–30 até uma migração explícita testada. O prêmio do 100 deve ser
  distinto do tabuleiro do Rei Cósmico da Jornada.

## Ciclo obrigatório por mudança/correção
Estudar o código → reproduzir o problema → propor solução → modificar o mínimo
necessário → testar → analisar resultados → repetir se necessário → documentar →
commit → publicar somente quando autorizado pela tarefa e pronto.

Em **cada** alteração, inclusive uma pequena correção visual, atualizar
docs/CHANGELOG.md no mesmo commit sempre que possível. Cada entrada registra:
- data, resumo, pedido/bug e comportamento esperado;
- arquivos e funções/seletores modificados, motivo e abordagem;
- comportamento antes/depois, decisões, efeitos colaterais e limites;
- testes executados com resultado real (se não rodou, dizer não executado);
- commit/PR e status da publicação; se publicada, anotar deploy e validação.
- pendências, como retomar e condições de rollback/reversão.

Atualizar também docs/TORRE_DOS_REIS.md quando mudar a implementação atual,
docs/TORRE_PLANO_100.md quando houver nova decisão de design. Não sobrescrever
o histórico de mudanças; acrescentar entradas. Registrar publicação posterior
em nova entrada de documentação se necessário. Não escrever que algo foi
testado visualmente se apenas houve validação de JS/servidor.

## Testes e publicação
- python -m py_compile servidor.py torre.py
- python -m unittest test_torre.py test_torre_api.py -v
- python -c "import servidor,selftest; selftest.run(servidor)"
- Verificar sintaxe JS, fluxo da interface, renderização real e acessibilidade;
  para cenários: transição de domínio, skins independentes e animações pausadas.
- Para produção, confirmar que o Render usa main e que o deploy correto está
  live; o serviço é casa-de-damas (não o serviço de migração). Não disparar
  deploy por alterações exclusivamente documentais. Se automático não
  ocorrer, conferir e disparar manualmente somente para publicação autorizada.
- Se ocorrer erro, manter versão estável/rollback por commit; não apagar
  progresso para corrigir interface. Informar o criador com clareza.

## Links
- Jogo: https://casa-de-damas.onrender.com/
- Torre: https://casa-de-damas.onrender.com/torre.html
- Repositório: https://github.com/pedrobarretto1/tes
