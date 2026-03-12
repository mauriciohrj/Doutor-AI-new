# Perfis, permissões e auditoria

## Objetivo
Definir perfis de acesso (founder, analista, gestor, admin), regras de permissão e requisitos de auditoria para proteger dados sensíveis, controle de emails e exportações.

## Perfis
### Founder
- Responsável pela estratégia e visão do negócio.
- Acesso completo a métricas, decisões e configurações críticas.

### Analista
- Responsável por análises e operação tática.
- Acesso limitado a dados, sem poder aprovar mudanças críticas.

### Gestor
- Responsável por coordenação de equipes e governança operacional.
- Pode aprovar algumas ações críticas, exceto mudanças estruturais.

### Admin
- Responsável por administração técnica e segurança.
- Acesso completo a configurações, permissões e auditoria.

## Matriz de permissões
| Ação | Founder | Analista | Gestor | Admin |
| --- | --- | --- | --- | --- |
| Visualizar dados não sensíveis | ✅ | ✅ | ✅ | ✅ |
| Visualizar dados sensíveis (PII, contratos, saúde) | ✅ | ❌ | ✅ (somente leitura) | ✅ |
| Editar templates de email | ✅ | ❌ | ✅ | ✅ |
| Aprovar envio de emails | ✅ | ❌ | ✅ | ✅ |
| Disparar envio de emails | ✅ | ✅ (somente rascunho/teste) | ✅ | ✅ |
| Exportar dados não sensíveis | ✅ | ✅ (escopo limitado) | ✅ | ✅ |
| Exportar dados sensíveis | ✅ | ❌ | ✅ (com justificativa) | ✅ |
| Gerir permissões de usuários | ✅ | ❌ | ❌ | ✅ |
| Configurar políticas de segurança | ✅ | ❌ | ✅ (propor) | ✅ |
| Acessar registros de auditoria | ✅ | ✅ (somente leitura) | ✅ | ✅ |

## Regras de restrição
1. **Edição de emails**
   - Analistas não podem editar templates nem aprovar envios.
   - Gestores podem editar e aprovar, com registro de justificativa.
   - Founder/Admin têm acesso completo.

2. **Aprovação de emails**
   - Envios a listas completas exigem aprovação de Gestor ou superior.
   - Envios com dados sensíveis exigem aprovação dupla (Gestor + Admin ou Founder).

3. **Dados sensíveis**
   - Apenas Founder, Gestor (leitura) e Admin podem acessar.
   - Qualquer exportação de dados sensíveis exige justificativa e registro de auditoria.

4. **Exportações**
   - Analista pode exportar apenas dados não sensíveis e com escopo limitado.
   - Gestor pode exportar dados sensíveis mediante justificativa.
   - Admin/Founder sem restrições, mas sempre com auditoria.

## Auditoria por usuário
Todas as ações abaixo devem gerar registro obrigatório em log de auditoria:
- Login/logout e falhas de autenticação.
- Criação, edição ou exclusão de templates de email.
- Aprovações e disparos de emails.
- Acesso, consulta e exportação de dados sensíveis.
- Mudanças de permissões e perfil de usuário.
- Alterações de políticas de segurança.

### Campos mínimos do log
- `timestamp` (UTC)
- `user_id`
- `role`
- `action`
- `resource`
- `result` (sucesso/erro)
- `justificativa` (quando aplicável)
- `ip_address`

### Retenção
- Mínimo de 12 meses de retenção.
- Logs protegidos contra alteração e com acesso restrito a Admin/Founder.
