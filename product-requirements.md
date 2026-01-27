# Requisitos de workflow e CRM

## Etapas do fluxo
- **Rascunho** → **Revisão/Aprovação** → **Envio** → **Acompanhamento**.
- Permitir transições explícitas entre etapas, com validação de pré-requisitos por etapa.

## Métricas por campanha e investidor
- Registrar métricas por **campanha** e por **investidor**:
  - `open`
  - `reply`
  - `bounce`
  - `unsubscribe`
- As métricas devem ser agregáveis por período e exportáveis para relatórios.

## Templates e personalização
- Configurar **templates** de comunicação com variáveis obrigatórias.
- Validar o preenchimento das variáveis antes do envio.
- Exemplos de variáveis obrigatórias:
  - `{{investidor_nome}}`
  - `{{campanha_nome}}`
  - `{{empresa_nome}}`

## Integração com CRM e kanban
- Associar respostas recebidas ao registro do **CRM** correspondente.
- Mover automaticamente o card no **kanban** conforme regras definidas (ex.: resposta positiva → etapa de acompanhamento).
- Registrar a regra aplicada e o histórico de movimentações.
