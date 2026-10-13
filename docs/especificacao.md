# O governo cumpriu o plano?

Especificação aprovada em 13/10/2026; aplicação ainda não implementada.

## Objetivo e isolamento
Aplicação local apartidária para auditar os seis planos presidenciais vencedores de 2002 a 2022. Nome do app mantido. Implementação independente em ~/Projects/sera-que-cumpriu; repositório público: lauralopes/sera-que-cumpriu. O Claude trabalha em outra pasta com outro nome; não alterar arquivos dele.

## Arquitetura recomendada
Backend Python com SQLite e API local; frontend de planilha em TypeScript. Processo de pesquisa separado do servidor. Dependências fixadas, comandos documentados, servidor limitado a localhost. PDF, texto extraído e banco ficam locais e fora do Git. Código com MIT; direitos de terceiros documentados separadamente.

Alternativas consideradas: aplicação inteiramente no navegador simplifica a interface, mas dificulta a pesquisa persistente; servidor remoto permite colaboração, mas exige hospedagem e gestão de acesso. A aplicação local atende ao pedido sem depender de hospedagem.

## Armazenamento e rastreabilidade
Tabelas para planos, documentos, páginas, compromissos, referências de origem, evidências, avaliações, revisões e tarefas. Documentos preservados por SHA-256, URL, data de obtenção, metadados e versão. Número físico da página do PDF e número impresso separados. Identidade e versão só ficam confirmadas após conferência; legibilidade e hash não comprovam autenticidade. Preservar múltiplas referências para promessas repetidas.

Cada compromisso registra descrição, natureza, tema, citação literal, páginas, meta, unidade, prazo e critério fixado antes da pesquisa. Histórico de critérios e avaliações imutável. Resultados automatizados identificados; revisão humana nunca presumida.

## Pesquisa
Leitura integral por página, com progresso separado de extração e avaliação. Candidatos automáticos não são tratados como compromissos auditados. Revisão de duplicações e ambiguidades antes dos indicadores. Nenhum dado fictício.

Fontes primárias, auditorias, estudos acadêmicos e imprensa de diferentes linhas editoriais, incluindo Gazeta do Povo e Revista Oeste quando houver material pertinente. Registrar posição editorial por contexto e período quando sustentada; não fixar situação/oposição como atributo permanente. Não sustentar conclusões só no IBGE, nem substituir evidência por equilíbrio artificial de opiniões. Registrar conflitos e lacunas. Ausência de evidência não significa descumprimento.

Wayback Availability API consultada pelo backend, com URL original, timestamp solicitado, timestamp retornado, resultado JSON e link da captura. Captura próxima não comprova publicação na data solicitada. Cache, timeout, limites e erros registrados.

Escavador oferece consulta ao DOU fora de gov.br; é espelho de documento oficial, não uma fonte independente dos fatos publicados. Verificar edição, seção, página e integridade. Não presumir isenção, acesso gratuito integral ou licença de redistribuição. Não contornar restrições de acesso.

## Períodos
2002: 2003–2006; 2006: 2007–2010; 2010: 2011–2014; 2014: exercício até afastamento em 12/05/2016, término do mandato em 31/08/2016, entregas Temer separadas; 2018: 2019–2022; 2022: desde 2023 até corte, provisório. Datas de início e fim verificadas antes de avaliação. Metas futuras recebem prazo ainda não vencido apenas quando há prazo explícito futuro.

## Indicadores
Estados: concluída, parcialmente concluída, não concluída, revertida, evidência insuficiente, prazo ainda não vencido, não mensurável, requer revisão. Pesquisa pendente é estado de trabalho separado da classificação.

Indicador principal: mensuráveis concluídos / todos os mensuráveis extraídos. Indicador determinado: concluídos / (concluídos + parciais + não concluídos + revertidos). Ambos com denominador, excluídos, uma casa decimal e peso igual. Se a extração estiver incompleta, mostrar que o universo é parcial e impedir apresentação como percentual de todo o plano. Cobertura = itens com pesquisa finalizada / mensuráveis extraídos; evidência insuficiente pode resultar de pesquisa finalizada. Mostrar também cobertura documental de páginas revisadas. Sem atribuir 50% a parciais.

## Interface
Tabela principal com todas as colunas solicitadas, filtros, busca, ordenação, cabeçalho fixo, seleção/copiar células, navegação por teclado e detalhes laterais. Resumo por plano, metodologia e painel de pesquisa. Exportações CSV e XLSX com fontes, histórico, contagens e fórmulas descritas. Textos iniciados por caracteres de fórmula tratados como texto nas exportações.

Correções locais com justificativa obrigatória, evidências e histórico anterior preservados. Contratos da API validados; nenhuma alteração via GET. Conteúdo externo renderizado como texto.

## Trabalho retomável
Fila SQLite com tarefas únicas, leases e recuperação de tarefas interrompidas. Separar extração, obtenção de fontes, preparação e classificação. Salvar após cada unidade. Pausa/cancelamento persistidos, retentativas limitadas, backoff por domínio, timeout e log. Coleta de páginas não equivale a julgamento: conclusão sem evidência permanece pendente. Operação autônoma será descrita apenas após verificação de processo ativo; caso contrário, instruções de retomada.

## Sequência de implementação e validação
1. Conferir documentos, obter 2006, preservar cópias locais e registrar origem e direitos.
2. Implementar banco, ingestão e um compromisso real com critério anterior à pesquisa.
3. Pesquisar e registrar evidências diversas, avaliação e histórico.
4. Construir tabela, detalhes, resumos e exportações.
5. Implementar fila, retomada, pausa, cancelamento e cache Wayback.
6. Ampliar extração e pesquisa dos seis planos, salvando pendências sem alegar auditoria completa.
7. Testar denominadores, duplicações, limites temporais, histórico, exportação e recuperação de interrupção; testar interface em navegador.
8. Verificar segredos e direitos, publicar código autorizado no GitHub e entregar instruções de abertura com progresso real.

## Situação inicial verificada
Cinco PDFs locais legíveis: 2002 (73 páginas), 2010 (11), 2014 (42), 2018 (81), 2022 (21). Inventário com hashes em inventario-documentos.json. Arquivo de 2010 se apresenta como “Os 13 compromissos programáticos ... para debate”; verificar a versão antes de tratá-lo como plano eleitoral completo. Fonte de 2006 acessível pela web, com 30 páginas; ainda não preservada localmente. Não houve leitura integral nem classificação de compromissos.

CLI gh: credencial local inválida para lauralopes; verificar também conexão GitHub disponível antes de considerar publicação bloqueada. Não pedir tokens ou senhas no chat. Nenhum repositório criado, nenhuma hospedagem publicada.

Prioridade confirmada: mandatos encerrados de 2002 a 2018; 2022 provisório. Planos de Lula e Flávio Bolsonaro para 2026 ficam no backlog, sem bloquear a auditoria histórica.
