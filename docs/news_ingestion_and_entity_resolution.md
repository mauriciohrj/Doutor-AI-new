# Pipeline de notícias: fontes, normalização e associação

## 1) Fontes de notícias e frequência de coleta

### 1.1 RSS
- **Portais financeiros locais**: Infomoney, Valor Econômico, Exame, Suno, NeoFeed.
- **Agências globais**: Reuters (feeds públicos), Bloomberg (se licenciado), CNBC, FT.
- **Fundos/gestoras**: blogs oficiais das gestoras e páginas de RI.
- **Reguladores**: CVM e B3 (comunicados e fatos relevantes).

**Frequência sugerida**:
- RSS de portais e agências: a cada **15 minutos** (noticiário rápido).
- Blogs/RI/reguladores: a cada **60 minutos**.

### 1.2 APIs de notícias
- **GDELT 2.1** (eventos globais, open data)
- **NewsAPI** (se licenciado para uso comercial)
- **Alpha Vantage / Marketaux / Finnhub** (notícias financeiras)

**Frequência sugerida**:
- APIs com limites de rate: **a cada 30–60 minutos**, com janelas de tempo (ex.: `now-1h`).

### 1.3 Newsletters
- **Casa de pesquisa/gestoras**: Nord Research, Empiricus, Eleven, XP, BTG, entre outros.
- **Mídia especializada**: newsletters de veículos e analistas.

**Frequência sugerida**:
- Coleta **diária** (ex.: 07:00 e 18:00), ou conforme o envio real.

## 2) Normalização de entidades (fundos/investidores/portfólios)

### 2.1 Estratégia de entity resolution
1. **Dicionário canônico**
   - Tabela `entities` com `entity_id`, `tipo` (fundo, investidor, portfólio, empresa), `nome_oficial`, `aliases`, `cnpj`/`identificador` e `fonte_de_origem`.
2. **Normalização de texto**
   - Lowercase, remoção de acentos, stopwords jurídicas ("S.A.", "LTDA", "Gestora", "Fundo de Investimento").
3. **Matching em camadas**
   - **Exato**: CNPJ/ISIN/ticker.
   - **Prefixo/alias**: match direto em aliases.
   - **Fuzzy**: similaridade Jaro-Winkler/Levenshtein + embeddings (opcional).
4. **Resolução de conflitos**
   - Score composto: exato (1.0), alias (0.9), fuzzy (0.7), embedding (0.6).
   - Se múltiplos candidatos: manter top-1 com gap mínimo de 0.1; caso contrário, marcar como **ambíguo**.

### 2.2 Exemplo de features para o score
- Similaridade textual (Jaro-Winkler).
- Coincidência de identificador (CNPJ/ISIN/ticker).
- Coocorrência com termos setoriais (ex.: "FII", "gestora", "asset").
- Contexto geográfico (Brasil vs. internacional).

## 3) Armazenamento de notícias com metadata

### 3.1 Estrutura de dados sugerida
Tabela `news_items`:
- `news_id` (UUID)
- `titulo`
- `resumo`
- `conteudo`
- `url`
- `fonte` (RSS/API/Newsletter + nome do provedor)
- `data_publicacao`
- `data_coleta`
- `idioma`
- `relevancia` (0–1)
- `tags` (array)
- `entities_mencionadas` (array de `entity_id`)
- `raw_payload` (JSON original da fonte)

### 3.2 Relevância
- Score calculado com base em:
  - frequência de menções à entidade,
  - presença em título,
  - proximidade semântica com o universo de investimento.

## 4) Regra de associação notícia ↔ fundos/investidores

### 4.1 Regras de associação
1. **Menção direta**: entidade aparece no título ou resumo (peso alto).
2. **Menção indireta**: aparece no corpo completo (peso médio).
3. **Sinais contextuais**: setor, holdings, empresas participadas (peso adicional).

### 4.2 Cálculo de confiança
- `confiança = w1*menção_título + w2*menção_resumo + w3*menção_corpo + w4*contexto`.
- Pesos sugeridos: `w1=0.4, w2=0.3, w3=0.2, w4=0.1`.

### 4.3 Registro de associação
Tabela `news_entity_links`:
- `news_id`
- `entity_id`
- `match_type` (exato/alias/fuzzy/embedding)
- `confidence`
- `resolved_at`

---

## Observações finais
- Começar com regras simples + dicionário canônico; evoluir para modelos de NER específicos do domínio financeiro.
- Validar amostras manualmente para ajustar pesos e reduzir falsos positivos.
