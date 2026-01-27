# OAuth: escopos mínimos, consentimento, revogação, armazenamento e auditoria

## Escopos OAuth mínimos

### Enviar e ler e-mails
- **Gmail (Google)**
  - Envio: `https://www.googleapis.com/auth/gmail.send`
  - Leitura (apenas metadados): `https://www.googleapis.com/auth/gmail.readonly`
  - Leitura + modificações (se necessário): `https://www.googleapis.com/auth/gmail.modify`
  - Observação: prefira `readonly` e faça upgrade para `modify` apenas se for necessário marcar lido/mover.
- **Microsoft Graph (Outlook/Exchange)**
  - Envio: `Mail.Send`
  - Leitura: `Mail.Read` (ou `Mail.ReadBasic` se apenas cabeçalhos)
  - Evite `Mail.ReadWrite` a menos que precise alterar mensagens.

### Criar eventos de calendário
- **Google Calendar**
  - Criar/editar eventos: `https://www.googleapis.com/auth/calendar.events`
  - Apenas leitura (se necessário para disponibilidade): `https://www.googleapis.com/auth/calendar.readonly`
- **Microsoft Graph (Outlook/Exchange)**
  - Criar/editar eventos: `Calendars.ReadWrite`
  - Apenas leitura (se necessário para disponibilidade): `Calendars.Read`

### Regras gerais
- Solicitar somente o mínimo necessário para a funcionalidade ativa do usuário.
- Isolar escopos por recurso (email vs. calendário) para permitir consentimento granular.
- Preferir escopos restritivos (readonly) e subir permissões via fluxo incremental.

## Fluxo de consentimento e revogação

### Consentimento (incremental e explícito)
1. **Pré-consentimento**: Tela explicando o motivo dos escopos solicitados e exemplos de uso.
2. **Consentimento granular**: usuário escolhe habilitar Email, Calendário ou ambos.
3. **OAuth**: redirecionar para o provedor apenas com escopos selecionados.
4. **Pós-consentimento**: mostrar resumo do acesso concedido, com link direto para revogar.

### Revogação
- **No app**: opção de “Revogar acesso” para cada provedor, que remove tokens locais e aciona revogação no provedor (endpoint de revogação).
- **No provedor**: informar que a revogação também pode ser feita nas configurações da conta (Google/Microsoft). Detectar falha de refresh e sinalizar ao usuário.
- **Auditoria**: registrar revogação e o estado final do token (revogado, expirado, inválido).

## Armazenamento seguro e rotação de tokens

### Armazenamento
- **Criptografia em repouso**: tokens armazenados criptografados com KMS/Vault.
- **Separação de chaves**: chave de criptografia gerenciada fora do banco (KMS/Vault), com rotação periódica.
- **Escopo mínimo**: guardar apenas o necessário (refresh token, access token, expiração, escopos).
- **Segregação**: associar tokens a um tenant/usuário e prover controle de acesso baseado em papel (RBAC).

### Rotação e renovação
- **Refresh tokens**: usar rotação automática quando o provedor suportar (Google/Microsoft).
- **Access tokens**: renovar com antecedência (ex.: 5 min antes de expirar).
- **Revogação interna**: ao detectar uso suspeito, revogar localmente e no provedor.
- **Detecção de inconsistências**: se refresh falhar, invalidar e solicitar novo consentimento.

### Manuseio seguro
- Nunca expor tokens em logs.
- Remover tokens de memória o mais rápido possível.
- Usar variáveis de ambiente/secret manager para credenciais do cliente OAuth.

## Auditoria: log de acesso a dados do usuário

### O que registrar
- Identificador do usuário/tenant.
- Provedor (Google/Microsoft), recurso acessado (email/calendário).
- Ação (ler email, enviar email, criar evento).
- Escopo utilizado.
- Timestamp, IP/serviço chamador.
- Resultado (sucesso/erro) e código de status.

### Requisitos de auditoria
- **Imutabilidade**: logs somente de append (WORM), retenção configurável.
- **Privacidade**: evitar conteúdo de mensagens; armazenar apenas metadados essenciais.
- **Rastreabilidade**: correlacionar com ID de requisição.
- **Alertas**: monitorar acessos anômalos (ex.: volume fora do padrão).

### Exemplo de evento de auditoria (JSON)
```json
{
  "user_id": "123",
  "tenant_id": "abc",
  "provider": "google",
  "resource": "gmail",
  "action": "send_email",
  "scope": "https://www.googleapis.com/auth/gmail.send",
  "timestamp": "2024-01-01T12:00:00Z",
  "request_id": "req-xyz",
  "status": "success"
}
```
