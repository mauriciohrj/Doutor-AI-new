# Doutor-AI — Canonical Truth & Deduplicação

Este pacote define critérios de “verdade canônica”, pontuação de confiança por fonte,
deduplicação de perfis e alertas de inconsistência para revisão humana.

## Critérios de verdade canônica

1. **Fonte autoritativa vence**: fontes `government` ou `primary` têm maior peso.
2. **Independência de fontes**: o mesmo valor confirmado por 2+ fontes independentes ganha bônus.
3. **Recência**: evidências recentes têm maior pontuação.
4. **Verificação explícita**: evidências verificadas recebem bônus.
5. **Confiança mínima**: se não houver confirmação por 2+ fontes ou uma fonte autoritativa, a confiança cai automaticamente.

## Deduplicação

A deduplicação considera:
- E-mail exato (score 1.0)
- URL do LinkedIn normalizada (score 1.0)
- Domínio compartilhado (score 0.6)
- Nome similar (score >= 0.9)

## Alertas de inconsistência

Os alertas são gerados quando uma evidência divergente contradiz campos canônicos
com confiança acima de 0.7, ou quando múltiplos valores competem por um mesmo campo.
