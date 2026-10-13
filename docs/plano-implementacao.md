# Plano de implementação — O governo cumpriu o plano?

> **Para execução:** aplicar superpowers:executing-plans, tarefa por tarefa, nesta sessão.

**Objetivo:** entregar um aplicativo local persistente e reproduzível para auditar compromissos reais dos seis planos, preservando pendências.

**Arquitetura:** API Python em localhost, SQLite, frontend TypeScript com grade interativa. Worker separado com fila, cache e checkpoints. Nenhum percentual é apresentado como completo enquanto a extração do plano estiver incompleta.

**Tecnologias:** Python 3, FastAPI, SQLite, pypdf, openpyxl; Vite e TypeScript na interface.

**Especificação:** especificacao.md, aprovada; prioridade histórica de 2002–2018.

## Restrições globais
- Pasta ~/Projects/sera-que-cumpriu; repositório lauralopes/sera-que-cumpriu.
- Português brasileiro, pesos iguais, percentuais com uma casa decimal e denominadores.
- Dados reais, todos os oito estados, pesquisa pendente separada da classificação, nenhuma revisão humana presumida.
- Documentos e banco locais fora do Git; licença MIT apenas para código.
- Sem hospedagem pública; publicação do código autorizada após verificações.

## Foco de revisão
1. PDF legível com identidade incorreta deve permanecer com validação pendente.
2. Falta de evidência não deve virar não concluída.
3. Entrega posterior a 12/05/2016 não deve contar para Dilma em exercício.
4. Interrupção de worker deve preservar itens e permitir recuperação sem duplicação.
5. Fórmulas em texto exportado e conteúdo HTML externo não devem executar.

## Tarefa 1 — documentos e banco
Arquivos: backend/db.py, backend/ingest.py, backend/schema.sql, sources/plans.json; tests/test_ingest.py.
Interfaces: ingest_document(plan_id, path) -> document_id; init_db(path) -> connection.
- [ ] Teste: SHA-256 e páginas persistidos, origem preservada, reimportação sem duplicação, identidade pendente não automaticamente validada.
- [ ] Rodar teste e confirmar falha antes da implementação.
- [ ] Implementar esquema e ingestão com transações, páginas físicas e impressas separadas.
- [ ] Conferir seis documentos, obter 2006, registrar identidade/versão/data e limitações.
- [ ] Rodar testes; salvar checkpoint e commit.

## Tarefa 2 — compromissos, evidências e avaliações
Arquivos: backend/research.py, backend/metrics.py, research/assessments.json; tests/test_metrics.py, tests/test_research.py.
Interfaces: add_commitment(record) -> id; add_evidence(record) -> id; assess(id, assessment, reason) -> revision_id; summary(plan_id) -> dict.
- [ ] Testes: duplicações não inflam universo, revisão preserva estado e fontes, classificação sem evidência rejeitada, entrega fora de período excluída, fórmulas respeitam todos os estados e denominador zero.
- [ ] Confirmar testes falham antes da implementação.
- [ ] Implementar contratos e histórico; fixar critérios antes da pesquisa de evidências.
- [ ] Ler documentos integralmente e extrair compromissos por páginas, com checkpoints; se não finalizar, páginas restantes explicitamente pendentes.
- [ ] Pesquisar um primeiro conjunto real com fontes primárias e corroboradoras de diferentes linhas editoriais; preservar conflitos.
- [ ] Rodar testes; salvar avaliações e commit.

## Tarefa 3 — API, planilha e exportação
Arquivos: backend/api.py, backend/export.py, frontend/src/main.ts, frontend/src/style.css; tests/test_api.py, tests/test_export.py.
Interfaces: GET /api/plans, /api/commitments, /api/summary, /api/progress; POST /api/commitments/{id}/revisions; GET /api/export?format=csv|xlsx.
- [ ] Testes: filtros, entrada inválida, histórico, CSV/XLSX com texto de fórmula neutralizado, nenhum GET altera banco.
- [ ] Confirmar testes falham antes da implementação.
- [ ] Implementar grade com filtros, busca, ordenação, seleção/cópia e teclado, detalhe com fontes, resumo e metodologia.
- [ ] Implementar exportação com referências e campos solicitados; dados externos renderizados como texto.
- [ ] Validar em navegador: filtros, detalhe, cópia, exportação, layout e acessibilidade básica; rodar testes/build e commit.

## Tarefa 4 — pesquisa retomável e arquivos históricos
Arquivos: backend/worker.py, backend/archive.py, backend/queue.py; tests/test_queue.py, tests/test_archive.py.
Interfaces: enqueue(kind, key, payload) -> id; claim(worker_id) -> task; run_worker(once=False); wayback(url, timestamp) -> snapshot.
- [ ] Testes: chave única, pausa/cancelamento, lease expirado, salvar por item, erro persistido, timeout/cache e captura com timestamp diferente.
- [ ] Confirmar testes falham antes da implementação.
- [ ] Implementar fila persistente, backoff e limitação por domínio; separar coleta de classificação.
- [ ] Disponibilizar pesquisa de Wayback e referências do DOU no Escavador com proveniência.
- [ ] Verificar retomada após interrupção; só descrever processo ativo após constatar atividade real.
- [ ] Rodar testes e commit.

## Tarefa 5 — entrega e publicação
Arquivos: README.md, LICENSE, SOURCES.md, .gitignore, scripts/start.sh, docs/methodology.md, docs/progress.md.
- [ ] Documentar instalação, abertura, worker, retomada e todos os limites reais.
- [ ] Verificar distribuição de documentos/dados; publicar apenas código e materiais com direitos adequados.
- [ ] Rodar suíte, build e testes de integração; revisar segredos nos arquivos e histórico.
- [ ] Verificar autenticação da conexão GitHub e CLI; criar repo público autorizado e enviar código caso acesso permita.
- [ ] Entregar endereço local, repositório e contagens reais de pesquisa; nunca chamar auditoria pendente de completa.

## Revisão do plano
Os requisitos da especificação estão associados às cinco tarefas. Comparação temporal, universos incompletos, arquivos incorretos, recuperação e exportações têm verificações explícitas. O processo deve guardar progresso mesmo quando a pesquisa substantiva precisar continuar em outra sessão.
