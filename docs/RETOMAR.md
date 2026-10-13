# Retomar a auditoria

Abra o projeto e leia docs/progress.md e o banco `data/audit.sqlite`. Não substituir o banco pelo bootstrap nem reaplicar avaliação já corrigida.

1. Consulte `/api/progress` e `/api/documents`. A fila distingue tarefas de pesquisa substantiva (`research_commitment`) e revisão de página (`review_page`). Triagem `needs_review` não equivale a promessa extraída, página revisada ou classificação concluída.
2. Obtenha o plano de 2006 indicado em `sources/plans.json`. Existe captura Wayback de 04/12/2008, mas download foi limitado por HTTP 429. Preserve o PDF somente se a assinatura for PDF, registre SHA-256 e verifique a equivalência textual. Não contornar limitações de acesso.
3. Leia páginas inteiras por `GET /api/documents/{id}/pages/{n}` e confira visualmente o PDF quando houver problemas de ordem, colunas ou caracteres. Não confiar só nos candidatos automáticos. Contabilizar diagnósticos e valores sem critério como não mensuráveis, mantendo-os visíveis.
4. Extraia compromissos independentes; una repetições. `POST /api/commitments` recebe id, plan_id, theme, description, nature, measurable, criterion, document_id, page e quote. A citação deve estar literalmente na página e o documento pertencer à eleição. A extração via biblioteca permite também meta, unidade e prazo. Para exemplos de contrato, veja testes e backend/bootstrap.py.
5. Fixe critério específico antes da pesquisa de cumprimento. Refinar via `POST /api/commitments/{id}/criterion` com criterion, reason e actor. Critérios anteriores ficam no histórico; uma mudança invalida a conclusão atual até nova avaliação.
6. Faça pesquisa substantiva em fontes primárias, auditorias, academia e veículos diversos. Adicione evidências via `/api/commitments/{id}/evidence`. Registro exige título, instituição, URL, dados de suporte e natureza; datas e período devem sustentar atribuição ao mandato, mesmo em estudo retrospectivo.
7. Avalie por `/api/commitments/{id}/revisions`. Justifique conclusão, confiança, corte e seleção de evidence_ids; sem evidências datadas dentro do período não há conclusão determinada. Evidência insuficiente não é não concluída. Não marcar revisão humana para trabalho de Codex.
8. Só marque a página integralmente revisada após terminar extração e reconciliação de duplicações: `POST /api/documents/{id}/pages/{n}/review`, com reason. Essa ação registra cobertura e termina a tarefa correspondente. Não marcar página lida como extração completa se ainda houver promessas pendentes.
9. Apenas depois de revisar todas as páginas, todas as versões e duplicações, fazer revisão final do universo e definir `plans.extraction_complete=1` por transação documentada. A aplicação não ativa essa flag automaticamente ao terminar a triagem.
10. Salve cada item, atualize docs/progress.md e exporte XLSX para conferência. Prioridade: 2002, 2006, 2010, 2014, 2018; 2022 provisório; 2026 backlog.

Cabeçalho para POST local: `X-Audit-Client: local-browser`. API ligada a localhost. Não publicar o banco ou dados de terceiros sem verificar direitos. O usuário já autorizou publicação do código no GitHub; hospedagem pública é decisão separada.
