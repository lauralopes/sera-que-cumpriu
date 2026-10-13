# O governo cumpriu o plano?

**Planos de governo, execução e evidências.** Aplicativo local em português para investigar os planos vencedores das eleições presidenciais brasileiras de 2002 a 2022.

**Estado real:** software funcional com SQLite, planilha, histórico e fila retomável; auditoria histórica incompleta. O conjunto inicial possui 23 itens reais: quatro avaliações substantivas, uma orientação não mensurável e 18 itens pendentes. Todos os planos têm extração parcial. Não há dados demonstrativos na interface, ranking global ou revisão humana presumida. Veja [progresso](docs/progress.md).

## Instalação e abertura

Requisitos: Python 3.11+ e Node.js 20.19+; npm; curl recomendado no macOS para a cadeia de certificados do sistema. Sem chave de API.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
npm --prefix frontend ci
npm --prefix frontend run build
.venv/bin/python -m backend.bootstrap documentos
./scripts/start.sh
```

Abra http://127.0.0.1:8765. A pasta `documentos` deve conter seus PDFs, com o ano da eleição no nome. São copiados para `data/documents` com nome baseado no hash, sem modificar os originais. A pasta `data` contém banco, cópias, manifestos e checkpoints, e **não é publicada no GitHub**. Não apagar `data` para atualizar a aplicação.

A ingestão e o bootstrap são idempotentes: não duplicam arquivos, compromissos, evidências ou tarefas. O bootstrap aplica o conjunto inicial apenas quando não há uma avaliação prévia do item, preservando correções locais. Ele não conclui a extração dos planos. Versões de fontes são conferidas no inventário; identificar a capa não equivale a validar autenticidade no TSE.

```sh
.venv/bin/python -m backend.ingest documentos
```

O PDF de 2006 foi fornecido pelo usuário e importado com 30 páginas. Os seis planos agora têm cópias locais preservadas. A captura Wayback e as falhas anteriores de download permanecem registradas como histórico; leitura integral e extração de 2006 continuam pendentes.

## Pesquisa em processo separado

O script de abertura inicia servidor e worker. Para separá-los em dois terminais:

```sh
.venv/bin/python -m uvicorn backend.api:app --host 127.0.0.1 --port 8765
.venv/bin/python -m backend.worker
```

Processar só uma unidade:

```sh
.venv/bin/python -m backend.worker --once
```

Na visão Pesquisa é possível pausar, retomar, cancelar e tentar novamente. Cada tarefa salva seu resultado em SQLite; leases vencidos retornam à fila, as chaves impedem duplicação e erros têm três tentativas com intervalo. Cancelamento impede o salvamento de resultado de uma tarefa cancelada, mas não interrompe um pedido de rede já iniciado. Pausa impede novas tarefas; uma tarefa em andamento termina primeiro. Há limite por domínio, timeout, resposta máxima e cache da API.

**Limite essencial:** o worker faz triagem de páginas e consultas ao Internet Archive. Ele não realiza julgamento autônomo de promessas nem inventa evidências. Tarefas `needs_review` aguardam pesquisa substantiva de Codex ou revisão de uma pessoa. Execute a continuidade conforme [RETOMAR.md](docs/RETOMAR.md). O processo depende do computador e do comando em execução; este projeto não instala um serviço permanente nem cria uma automação em conta externa.

## Planilha

Filtros por eleição/governo, tema, estado, confiança e busca textual; ordenação por cabeçalho; cabeçalho fixo; seleção com clique, arraste ou Shift + clique; Ctrl/Cmd + C copia o intervalo; setas navegam e Enter abre detalhe. As 19 colunas solicitadas estão disponíveis com rolagem horizontal. Colunas de consulta mais frequente aparecem primeiro.

Detalhes mostram citação, página física, PDF preservado, hash, resultado, fontes e limites. É possível adicionar evidência, corrigir classificação com motivo e refinar critérios. Avaliação anterior e critério usado são preservados; mudar o critério torna a avaliação pendente de revisão. Não marcar revisão humana sem leitura pessoal das fontes.

CSV e XLSX exportam o filtro atual. XLSX inclui evidências, histórico, histórico de critérios, metodologia e resumo do banco inteiro — o resumo não é recalculado como se o filtro fosse um plano completo. Textos de fórmula são neutralizados. Nenhuma revisão opera por GET.

## Metodologia e neutralidade

[Regras completas](docs/methodology.md). Todos os governos seguem o mesmo critério. Promessas, anúncio, execução, impacto e causalidade são distintos. Fonte partidária, governamental ou estatística não vira verdade pela identidade do autor. Documentos primários, auditorias e estudos são cruzados com veículos de diferentes linhas editoriais; o piloto inclui Gazeta do Povo e Revista Oeste, além de TCU, Câmara, Senado e FAO. Conflitos de datas e limitações são preservados.

Principal = mensuráveis concluídos / mensuráveis extraídos × 100. Determinado = concluídos / (concluídos + parciais + não concluídos + revertidos) × 100. Peso igual, uma casa decimal, denominadores visíveis. Parciais não valem automaticamente 50%. Ausência de evidência não prova descumprimento. Extração incompleta implica **universo parcial**, inadequado para comparação global de governos.

Dilma 2014 tem entregas posteriores separadas: último dia completo de exercício 11/05/2016; o afastamento de 12/05 requer horário para entregas desse dia, e término formal em 31/08/2016. Lula 2022 é provisório até o corte. Não há percentual agregado por presidente. Planos de 2026 são backlog.

## Internet Archive e Diário Oficial

A visão Pesquisa usa a [Wayback Availability API](https://archive.org/help/wayback_api.php): URL original, timestamp solicitado, timestamp retornado, JSON bruto, data de consulta e link. Data próxima não prova que a página existia na data solicitada. Nenhuma captura é inventada quando a API falha ou não encontra resultado. Captura disponível não garante download ou autenticidade do conteúdo original.

[Escavador](https://www.escavador.com/diarios) oferece consulta ao DOU fora de gov.br. É espelho privado de documentos oficiais; não presumimos isenção nem livre redistribuição do acervo. Edição, seção e página precisam ser verificadas. No piloto, a LC 179/2021 é consultada na reprodução da Câmara: DOU, seção 1, 25/02/2021, página 3. Nenhum scraping de acervo protegido é implementado.

## Testes

```sh
.venv/bin/python -m pytest -q
npm --prefix frontend run build
```

Cobrem hashes e reimportação; referências de outra eleição; denominadores; estado pendente; limites temporais inclusive sem data pontual; revisão/histórico; datas; recuperação da fila; pausa/cancelamento; URL pública; timestamps de arquivo; proteção de host/origem e CSV/XLSX. Testes usam exemplos isolados em bancos temporários, nunca apresentados como dados pesquisados.

## Direitos e publicação

Código MIT. [SOURCES.md](SOURCES.md) documenta fontes e direitos separados. PDFs, cópias de artigos, banco local e documentos pessoais ficam fora do Git. O repositório contém métodos, seletores curtos de busca, referências e resumos autorais das avaliações iniciais, para reprodução com os documentos locais. A licença MIT não se estende aos materiais de terceiros. Hospedagem pública do aplicativo depende de decisão separada.
