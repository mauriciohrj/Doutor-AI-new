# Orquestração de agentes

Este documento descreve a especificação do orquestrador de filas/tarefas, estados, cadências, dependências de etapas e auditoria de execução para agentes.

## 1. Orquestrador de filas e tarefas

### 1.1 Componentes
- **Scheduler**: responsável por gerar instâncias de tarefas (jobs) a partir de cadências e regras de execução.
- **Worker**: responsável por consumir a fila e executar as tarefas.
- **Fila**: estrutura FIFO (ou por prioridade) que contém tarefas com estado persistido.

### 1.2 Estados de tarefa
- **pending**: criada e aguardando execução.
- **running**: em execução por um worker.
- **failed**: terminou com erro.
- **completed**: terminou com sucesso.

### 1.3 Transições permitidas
- `pending -> running`
- `running -> completed`
- `running -> failed`
- `failed -> pending` (somente se houver retry)

## 2. Cadências por tipo de agente e regras de retry

### 2.1 Tipos de agente
Cada tipo de agente declara:
- **cadência**: diária, semanal ou mensal.
- **janela de execução** (opcional): horários permitidos.
- **prioridade** (opcional): ordem de consumo da fila.

### 2.2 Cadências
- **Diária**: executa uma vez por dia em horário definido (ex.: 02:00).
- **Semanal**: executa em dia da semana definido (ex.: segunda-feira às 03:00).
- **Mensal**: executa em dia do mês definido (ex.: dia 01 às 04:00).

### 2.3 Regra de retry
Definições mínimas:
- **max_attempts**: número máximo de tentativas (ex.: 3).
- **backoff**: estratégia exponencial (ex.: 5 min, 15 min, 45 min).
- **retry_on**: lista de erros elegíveis para retry.

## 3. Workflow steps com dependências

### 3.1 Estrutura do workflow
Um workflow é composto por etapas (steps) com dependências explícitas:

Exemplo (pipeline padrão):
1. **coleta**
2. **enriquecimento** (depende de `coleta`)
3. **scoring** (depende de `enriquecimento`)
4. **email** (depende de `scoring`)

### 3.2 Regras de execução
- Um step só pode iniciar quando todos os seus predecessores estiverem em **completed**.
- Se um step falhar, os dependentes ficam bloqueados até que a falha seja resolvida (ou o retry seja bem-sucedido).
- Possibilidade de **steps paralelos** quando não há dependência direta.

## 4. Auditoria de execução

### 4.1 Campos obrigatórios
- **job_id**: identificador único da tarefa.
- **workflow_id**: identificador do workflow.
- **step_id**: identificador da etapa (quando aplicável).
- **status**: pending, running, failed, completed.
- **started_at**: timestamp de início.
- **finished_at**: timestamp de término.
- **duration_ms**: duração total em milissegundos.
- **output_summary**: saída resumida (ex.: número de registros processados).
- **error_message**: mensagem de erro (quando status = failed).
- **attempt**: número da tentativa atual.

### 4.2 Persistência
- Registrar auditoria em storage central (ex.: banco relacional ou log estruturado).
- Cada transição de estado deve gerar um registro de auditoria.
- Permitir consulta por **intervalo de data**, **status**, **agente** e **workflow**.

## 5. Exemplo de configuração (pseudomodelo)

```yaml
agent_type: "score_agent"
schedule:
  cadence: "daily"
  time: "02:00"
retry:
  max_attempts: 3
  backoff_minutes: [5, 15, 45]
  retry_on:
    - "TimeoutError"
    - "ConnectionError"
workflow:
  id: "lead_scoring"
  steps:
    - id: "coleta"
    - id: "enriquecimento"
      depends_on: ["coleta"]
    - id: "scoring"
      depends_on: ["enriquecimento"]
    - id: "email"
      depends_on: ["scoring"]
```
