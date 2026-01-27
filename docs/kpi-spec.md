# KPIs, módulos e visão de next step

## KPIs

### Taxa de resposta
- **Definição**: proporção de leads/investidores que responderam pelo menos uma vez após o primeiro contato.
- **Cálculo**: `respostas_unicas / contatos_iniciados`.
- **Regras**:
  - Contar resposta única por lead/investidor (primeira resposta dentro do período).
  - Excluir mensagens automáticas (out-of-office) da contagem de resposta.
  - Período padrão: últimos 30 dias, com filtros por canal e campanha.

### Tempo médio por etapa
- **Definição**: média de tempo entre a entrada e a saída de cada etapa do pipeline.
- **Cálculo**: `soma(tempo_em_etapa) / total_de_transições`.
- **Regras**:
  - Considerar apenas transições concluídas no período.
  - Etapas pausadas devem ser excluídas do tempo (status “em pausa”).
  - Exibir por etapa e por segmento (canal, campanha, investidor).

### Conversão por canal
- **Definição**: taxa de evolução do estágio inicial para o estágio-alvo por canal.
- **Cálculo**: `conversões_para_estágio_alvo / entradas_no_estágio_inicial`.
- **Regras**:
  - Estágio-alvo padrão: “reunião agendada” ou “commit” (configurável).
  - Canais: e-mail, LinkedIn, indicação, eventos, inbound, outros.
  - Permitir janelas de atribuição (ex.: 30/60/90 dias).

### Qualidade do match
- **Definição**: aderência entre perfil do investidor e tese da startup/campanha.
- **Cálculo**: `pontuação_média` baseada em critérios ponderados.
- **Critérios sugeridos** (peso configurável):
  - Setor/vertical (0–30)
  - Ticket médio (0–20)
  - Estágio de investimento (0–20)
  - Geografia (0–15)
  - Fit estratégico (0–15)
- **Regras**:
  - Exibir score médio e distribuição por faixas (alto/médio/baixo).
  - Atualizar score quando tese ou perfil do investidor for alterado.

## Mapeamento de módulos

### Pipeline
- **Objetivo**: acompanhar estágios do funil de fundraising.
- **Componentes**:
  - Estágios configuráveis (ex.: pesquisa, contato, resposta, reunião, negociação, commit, fechado).
  - Métricas por estágio (tempo médio, taxa de conversão, drop-off).
  - Alertas de estagnação (SLA por etapa).

### Fundraising timeline
- **Objetivo**: visualizar o cronograma global da rodada.
- **Componentes**:
  - Marcos (kickoff, abertura de data room, demo day, fechamento).
  - Dependências entre marcos.
  - Variação planejado vs. realizado.

### Investor activity
- **Objetivo**: consolidar interações por investidor.
- **Componentes**:
  - Log de contatos (data, canal, responsável, resultado).
  - Próxima ação e prioridade.
  - Engagement score (baseado em respostas e reuniões).

### Campaign performance
- **Objetivo**: medir eficiência das campanhas de outreach.
- **Componentes**:
  - Taxa de resposta por campanha.
  - Conversão por canal e copy.
  - Volume de contatos vs. reuniões agendadas.

## Periodicidade de atualização e regras de cálculo

- **Atualização diária (D+1)**:
  - KPIs de taxa de resposta, conversão por canal e performance de campanha.
  - Justificativa: dependem de novos eventos de contato/resposta.
- **Atualização semanal**:
  - Tempo médio por etapa (reduz ruído de curto prazo).
  - Revisão de thresholds de drop-off.
- **Atualização em tempo real/event-driven**:
  - Qualidade do match (quando houver mudança de tese/investidor).
  - Próxima ação do investidor (quando houver nova interação).

**Regras gerais**:
- Sempre registrar eventos com carimbo de data/hora e responsável.
- Normalizar canais e campanhas (tabela de referência para evitar duplicidade).
- Guardar histórico de mudanças de estágio para auditoria.

## Visão “next step” com regras de prioridade

### Objetivo
- Listar a próxima ação recomendada para cada investidor/lead.

### Regras de priorização (ordem)
1. **SLA estourado**: etapas com tempo acima do limite.
2. **Engajamento recente**: respostas ou reuniões nos últimos 7 dias.
3. **Qualidade do match alta**: score acima do limiar (ex.: >80).
4. **Estágio avançado**: investidores próximos de “commit” ou “fechado”.
5. **Campanhas estratégicas**: campanhas sinalizadas como prioridade.

### Regras de ação
- **Sem resposta após primeiro contato**: enviar follow-up em 3–5 dias.
- **Resposta recebida**: agendar reunião em até 48h.
- **Reunião realizada**: enviar materiais/dataroom no mesmo dia.
- **Negociação em andamento**: definir próximo checkpoint em até 7 dias.

### Campos exibidos
- Investidor/lead, estágio atual, última interação, próxima ação, prioridade, responsável.
- Indicadores: SLA, match score, canal, campanha.
