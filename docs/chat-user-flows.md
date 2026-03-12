# Mapas de fluxo do usuário no chat

## Visão geral
Este documento descreve os fluxos principais do chat, define memória de curto e longo prazo, especifica quick actions e status de execução dos agentes, e estabelece como registrar histórico contextual com auditoria e rollback de sugestões.

## Fluxos do usuário (exemplos)

### 1) Captar (lead/investidor/cliente)
**Objetivo:** qualificar contato e registrar no CRM.

**Etapas do fluxo**
1. Usuário inicia intenção: “Quero captar investidores”.
2. Chat solicita contexto mínimo: setor, estágio, ticket, geografia, diferenciais.
3. Agentes sugerem pesquisa de alvos (lista preliminar de investidores).
4. Usuário confirma ou ajusta filtros.
5. Chat gera shortlist e propõe próxima ação (ex.: criar pitch, enviar email).
6. CRM recebe registros com campos completos e tags.

**Saídas esperadas**
- Lista de alvos no CRM.
- Próximos passos recomendados.
- Histórico de decisão (por que cada alvo foi incluído).

### 2) Criar pitch
**Objetivo:** produzir narrativa e materiais de apresentação.

**Etapas do fluxo**
1. Usuário pede: “criar pitch”.
2. Chat pergunta fase, público e formato (deck, 1-pager, roteiro).
3. Agente de conteúdo estrutura tópicos (problema, solução, mercado, tração, equipe, pedido).
4. Usuário revisa e aprova cada seção.
5. Chat gera versão final e registra no histórico.

**Saídas esperadas**
- Pitch estruturado (com versão e autor).
- Sugestões de ajustes baseadas em feedback.
- Registro de mudanças por iteração.

### 3) Email investidores
**Objetivo:** criar mensagens personalizadas e rastreáveis.

**Etapas do fluxo**
1. Usuário pede: “email investidores”.
2. Chat identifica destinatários do CRM ou solicita lista.
3. Agente cria template base + variações por segmento.
4. Usuário aprova texto e CTA.
5. Chat gera emails finais e registra no histórico.

**Saídas esperadas**
- Emails versionados por destinatário.
- Log de aprovação.
- Registro de envio (quando integrado).

## Memória curta vs. longa

### Memória curta (sessão)
- **Escopo:** conversa atual.
- **Uso:** contexto imediato, rascunhos temporários, decisões ainda não confirmadas.
- **Persistência:** expira com a sessão ou após inatividade definida (ex.: 24h).
- **Exemplos:** notas do briefing, versões intermediárias de pitch.

### Memória longa (CRM)
- **Escopo:** perfil contínuo do usuário/empresa e histórico de relacionamento.
- **Uso:** dados confiáveis e aprovados (contatos, preferências, templates oficiais).
- **Persistência:** até exclusão explícita.
- **Exemplos:** contatos de investidores, pitch aprovado, histórico de emails enviados.

### Regras de sincronização
- **Somente após aprovação explícita**: itens passam da sessão para o CRM.
- **Metadados obrigatórios**: autor, timestamp, fonte e nível de confiança.
- **Reversibilidade**: tudo que foi sincronizado deve poder ser revertido.

## Quick actions (ações sugeridas)

### Tipos
- **Contextuais**: baseadas na intenção detectada (ex.: “Gerar deck”, “Buscar investidores”).
- **Sequenciais**: próximos passos de fluxo (ex.: “Revisar seção Mercado”).
- **Operacionais**: tarefas rápidas (ex.: “Adicionar ao CRM”).

### Regras de exibição
- Mostrar até 3 ações por turno para evitar sobrecarga.
- Priorizar ações com maior impacto e menor esforço.
- Indicar efeitos colaterais (ex.: gravação no CRM).

## Status de execução dos agentes

### Estados padrão
- **Pendente**: aguardando entrada do usuário.
- **Em execução**: processando (mostrar ETA aproximado).
- **Concluído**: pronto para revisão.
- **Falhou**: erro com causa e tentativa de recuperação.

### Metadados do status
- Agente responsável (nome/role).
- Objetivo da tarefa.
- Dependências (se houver).
- Última atualização (timestamp).

## Histórico contextual, auditoria e rollback

### Registro de histórico
- Salvar cada sugestão com versão, autor (agente/usuário) e contexto.
- Vincular sugestões ao fluxo em execução.
- Armazenar mudanças como diffs quando possível.

### Auditoria
- Permitir rastrear quem aprovou o quê e quando.
- Exibir trilha completa de decisões (audit trail).
- Oferecer visualização comparativa entre versões.

### Rollback
- Reverter sugestões ou conteúdo sincronizado com o CRM.
- Registrar motivo do rollback.
- Manter versões anteriores acessíveis.

## Checklist de implementação
- [ ] Detectar intenção e iniciar fluxo correto.
- [ ] Separar memória curta e longa com confirmação explícita.
- [ ] Exibir quick actions consistentes com o fluxo.
- [ ] Mostrar status dos agentes em tempo real.
- [ ] Persistir histórico e permitir auditoria/rollback.
