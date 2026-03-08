"""
Módulo de geração de leads para o sistema Doutor-AI Target Screening.
Processa artigos com NLP via LLM para identificar e classificar leads.
"""

import json
import os
import re
from datetime import datetime
from openai import OpenAI
from database import get_connection

# Cliente OpenAI configurado via variável de ambiente
client = OpenAI()

# Contexto estratégico do Doutor-AI para cálculo de fit
DOUTOR_AI_CONTEXT = """
A Doutor-AI é uma startup brasileira de healthtech que desenvolve soluções de 
Inteligência Artificial para o setor de saúde. Seus principais produtos são:

1. IA para diagnóstico assistido (radiologia, patologia, dermatologia)
2. Processamento de Linguagem Natural para prontuários eletrônicos
3. Gestão inteligente de leitos e fluxo hospitalar
4. Análise preditiva de saúde populacional para operadoras
5. Automação de processos administrativos hospitalares

Clientes-alvo prioritários:
- Hospitais privados de médio e grande porte (acima de 100 leitos)
- Operadoras de planos de saúde (acima de 500.000 beneficiários)
- Redes hospitalares com múltiplas unidades
- Secretarias estaduais e municipais de saúde
- EBSERH e hospitais universitários federais

Investidores-alvo prioritários:
- VCs com foco em healthtech/SaaS (ticket Série A/B: US$ 5-30M)
- Corporate Ventures de grandes grupos de saúde
- Private Equity com portfólio em saúde
- Fundos de impacto social com foco em saúde

Estágio atual: Série A, buscando R$ 25 milhões para expansão nacional.
"""


def extract_entities_with_llm(article_title: str, article_content: str) -> dict:
    """
    Usa LLM para extrair entidades, classificar o tipo de notícia e identificar leads.
    Retorna um dicionário com entidades, tipo de notícia e análise de fit.
    """
    prompt = f"""Você é um analista de inteligência de mercado especializado em healthtech brasileiro.

Analise o seguinte artigo de notícia e extraia informações relevantes para geração de leads para a Doutor-AI.

CONTEXTO DA DOUTOR-AI:
{DOUTOR_AI_CONTEXT}

ARTIGO:
Título: {article_title}
Conteúdo: {article_content}

Extraia e retorne um JSON com a seguinte estrutura:
{{
  "entities": [
    {{
      "name": "Nome da empresa/organização",
      "type": "hospital|operadora|governo|VC|PE|CVC|aceleradora|clinica|laboratorio|outro",
      "lead_type": "cliente|investidor|parceiro",
      "relevance": "alta|media|baixa",
      "description": "Breve descrição da empresa",
      "city": "Cidade (se mencionada)",
      "state": "Estado (se mencionado)",
      "size": "grande|medio|pequeno (estimativa)",
      "fit_reason": "Por que esta empresa tem fit com a Doutor-AI (2-3 frases)",
      "fit_score_components": {{
        "semantic_relevance": 0-30,
        "news_type_score": 0-30,
        "strategic_fit": 0-40
      }}
    }}
  ],
  "news_type": "contrato|piloto|parceria|investimento|comentario|licitacao|rfp|programa",
  "news_summary": "Resumo em 1 frase da notícia",
  "overall_relevance": "alta|media|baixa"
}}

Regras para pontuação:
- semantic_relevance (0-30): Quão relevante semanticamente é a notícia para IA em saúde
- news_type_score (0-30): contrato=30, licitacao=28, rfp=25, piloto=22, parceria=20, programa=18, investimento=15, comentario=5
- strategic_fit (0-40): Quão bem a empresa se encaixa no perfil de cliente/investidor ideal da Doutor-AI

Retorne APENAS o JSON, sem texto adicional."""

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=2000
        )
        
        content = response.choices[0].message.content.strip()
        # Remover possíveis marcadores de código markdown
        content = re.sub(r'^```json\s*', '', content)
        content = re.sub(r'\s*```$', '', content)
        
        return json.loads(content)
    except json.JSONDecodeError as e:
        print(f"Erro ao parsear JSON do LLM: {e}")
        return {"entities": [], "news_type": "comentario", "news_summary": "", "overall_relevance": "baixa"}
    except Exception as e:
        print(f"Erro ao chamar LLM: {e}")
        return {"entities": [], "news_type": "comentario", "news_summary": "", "overall_relevance": "baixa"}


def enrich_firmographic_data(entity_name: str, entity_type: str) -> dict:
    """
    Enriquece dados firmográficos de uma empresa/investidor via LLM.
    """
    prompt = f"""Você é um analista de inteligência de mercado especializado no setor de saúde brasileiro.

Forneça dados firmográficos sobre a seguinte organização:
Nome: {entity_name}
Tipo: {entity_type}

Retorne um JSON com:
{{
  "website": "URL do site oficial (se souber)",
  "employees_range": "1-50|51-200|201-1000|1001-5000|5000+",
  "revenue_range": "até R$10M|R$10-50M|R$50-200M|R$200M-1B|acima de R$1B",
  "description": "Descrição detalhada da organização (3-4 frases)",
  "key_facts": ["fato 1", "fato 2", "fato 3"]
}}

Retorne APENAS o JSON, sem texto adicional. Se não souber alguma informação, use null."""

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=500
        )
        
        content = response.choices[0].message.content.strip()
        content = re.sub(r'^```json\s*', '', content)
        content = re.sub(r'\s*```$', '', content)
        
        return json.loads(content)
    except Exception as e:
        print(f"Erro ao enriquecer dados de {entity_name}: {e}")
        return {}


def calculate_final_score(fit_components: dict, news_type: str) -> float:
    """
    Calcula o score final do lead baseado nos componentes de fit.
    """
    semantic = fit_components.get("semantic_relevance", 0)
    news_score = fit_components.get("news_type_score", 0)
    strategic = fit_components.get("strategic_fit", 0)
    
    # Score base = soma dos componentes (máximo 100)
    base_score = semantic + news_score + strategic
    
    # Bônus por tipo de notícia de alta qualidade
    news_bonus = {
        "contrato": 5,
        "licitacao": 4,
        "rfp": 4,
        "piloto": 3,
        "parceria": 2,
        "programa": 2,
        "investimento": 2,
        "comentario": 0
    }
    bonus = news_bonus.get(news_type, 0)
    
    final_score = min(100, base_score + bonus)
    return round(final_score, 1)


def get_priority(score: float) -> str:
    """Determina a prioridade do lead baseado no score."""
    if score >= 75:
        return "alta"
    elif score >= 50:
        return "media"
    else:
        return "baixa"


def save_company(conn, entity: dict, firmographic: dict) -> int:
    """Salva ou atualiza uma empresa no banco de dados."""
    cursor = conn.cursor()
    
    # Mapear tipo de entidade
    type_mapping = {
        "hospital": "hospital",
        "operadora": "operadora",
        "governo": "governo",
        "clinica": "clinica",
        "laboratorio": "laboratorio",
        "outro": "outro"
    }
    
    entity_type = type_mapping.get(entity.get("type", "outro"), "outro")
    
    cursor.execute("""
        INSERT INTO companies (name, type, segment, city, state, website, description, size, 
                               revenue_range, employees_range, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(name) DO UPDATE SET
            type = excluded.type,
            city = excluded.city,
            state = excluded.state,
            website = COALESCE(excluded.website, website),
            description = COALESCE(excluded.description, description),
            size = COALESCE(excluded.size, size),
            revenue_range = COALESCE(excluded.revenue_range, revenue_range),
            employees_range = COALESCE(excluded.employees_range, employees_range),
            updated_at = CURRENT_TIMESTAMP
    """, (
        entity.get("name"),
        entity_type,
        "saúde",
        entity.get("city"),
        entity.get("state"),
        firmographic.get("website"),
        firmographic.get("description") or entity.get("description"),
        entity.get("size"),
        firmographic.get("revenue_range"),
        firmographic.get("employees_range")
    ))
    
    cursor.execute("SELECT id FROM companies WHERE name = ?", (entity.get("name"),))
    row = cursor.fetchone()
    return row["id"] if row else None


def save_investor(conn, entity: dict, firmographic: dict) -> int:
    """Salva ou atualiza um investidor no banco de dados."""
    cursor = conn.cursor()
    
    type_mapping = {
        "VC": "VC",
        "PE": "PE",
        "CVC": "CVC",
        "aceleradora": "aceleradora",
        "angel": "angel"
    }
    
    investor_type = type_mapping.get(entity.get("type", "VC"), "VC")
    
    cursor.execute("""
        INSERT INTO investors (name, type, focus, city, state, website, description, aum_range, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(name) DO UPDATE SET
            type = excluded.type,
            focus = COALESCE(excluded.focus, focus),
            city = excluded.city,
            state = excluded.state,
            website = COALESCE(excluded.website, website),
            description = COALESCE(excluded.description, description),
            aum_range = COALESCE(excluded.aum_range, aum_range),
            updated_at = CURRENT_TIMESTAMP
    """, (
        entity.get("name"),
        investor_type,
        "healthtech/saúde digital",
        entity.get("city"),
        entity.get("state"),
        firmographic.get("website"),
        firmographic.get("description") or entity.get("description"),
        firmographic.get("revenue_range")
    ))
    
    cursor.execute("SELECT id FROM investors WHERE name = ?", (entity.get("name"),))
    row = cursor.fetchone()
    return row["id"] if row else None


def process_articles(max_articles: int = 20) -> dict:
    """
    Processa artigos não processados e gera leads.
    Retorna estatísticas da execução.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Criar registro de execução
    cursor.execute("""
        INSERT INTO lead_generation_runs (status) VALUES ('running')
    """)
    run_id = cursor.lastrowid
    conn.commit()
    
    stats = {
        "run_id": run_id,
        "articles_processed": 0,
        "leads_generated": 0,
        "companies_found": 0,
        "investors_found": 0,
        "errors": []
    }
    
    try:
        # Buscar artigos não processados
        cursor.execute("""
            SELECT id, title, content, source, url, published_at, category
            FROM articles
            WHERE is_processed = 0
            ORDER BY published_at DESC
            LIMIT ?
        """, (max_articles,))
        
        articles = cursor.fetchall()
        print(f"Processando {len(articles)} artigos...")
        
        for article in articles:
            article_id = article["id"]
            print(f"\n[{stats['articles_processed']+1}/{len(articles)}] Processando: {article['title'][:60]}...")
            
            try:
                # Extrair entidades com LLM
                analysis = extract_entities_with_llm(article["title"], article["content"])
                
                entities = analysis.get("entities", [])
                news_type = analysis.get("news_type", "comentario")
                
                print(f"  → Entidades encontradas: {len(entities)} | Tipo: {news_type}")
                
                for entity in entities:
                    entity_name = entity.get("name", "").strip()
                    if not entity_name:
                        continue
                    
                    lead_type = entity.get("lead_type", "cliente")
                    entity_type = entity.get("type", "outro")
                    
                    # Enriquecer dados firmográficos
                    firmographic = enrich_firmographic_data(entity_name, entity_type)
                    
                    # Salvar empresa ou investidor
                    entity_id = None
                    if lead_type in ["cliente", "parceiro"]:
                        entity_id = save_company(conn, entity, firmographic)
                        stats["companies_found"] += 1
                    elif lead_type == "investidor":
                        entity_id = save_investor(conn, entity, firmographic)
                        stats["investors_found"] += 1
                    
                    # Calcular score final
                    fit_components = entity.get("fit_score_components", {})
                    final_score = calculate_final_score(fit_components, news_type)
                    priority = get_priority(final_score)
                    
                    # Verificar se já existe target para esta entidade neste artigo
                    cursor.execute("""
                        SELECT id FROM targets 
                        WHERE entity_name = ? AND source_article_id = ?
                    """, (entity_name, article_id))
                    
                    existing = cursor.fetchone()
                    
                    if not existing:
                        # Criar registro de target/lead
                        cursor.execute("""
                            INSERT INTO targets (
                                entity_name, entity_type, entity_id, lead_type, 
                                score, score_breakdown, source_article_id, source_article_title,
                                news_type, fit_reason, priority
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            entity_name,
                            "company" if lead_type in ["cliente", "parceiro"] else "investor",
                            entity_id,
                            lead_type,
                            final_score,
                            json.dumps(fit_components, ensure_ascii=False),
                            article_id,
                            article["title"],
                            news_type,
                            entity.get("fit_reason", ""),
                            priority
                        ))
                        stats["leads_generated"] += 1
                        print(f"  ✓ Lead criado: {entity_name} | Score: {final_score} | Prioridade: {priority}")
                
                # Marcar artigo como processado
                cursor.execute("""
                    UPDATE articles SET is_processed = 1 WHERE id = ?
                """, (article_id,))
                
                stats["articles_processed"] += 1
                conn.commit()
                
            except Exception as e:
                error_msg = f"Erro no artigo {article_id}: {str(e)}"
                print(f"  ✗ {error_msg}")
                stats["errors"].append(error_msg)
                # Continuar processando outros artigos
                continue
        
        # Atualizar registro de execução como concluído
        cursor.execute("""
            UPDATE lead_generation_runs SET
                finished_at = CURRENT_TIMESTAMP,
                articles_processed = ?,
                leads_generated = ?,
                companies_found = ?,
                investors_found = ?,
                status = 'completed'
            WHERE id = ?
        """, (
            stats["articles_processed"],
            stats["leads_generated"],
            stats["companies_found"],
            stats["investors_found"],
            run_id
        ))
        conn.commit()
        
    except Exception as e:
        error_msg = f"Erro crítico na execução: {str(e)}"
        print(f"ERRO CRÍTICO: {error_msg}")
        stats["errors"].append(error_msg)
        
        cursor.execute("""
            UPDATE lead_generation_runs SET
                finished_at = CURRENT_TIMESTAMP,
                status = 'failed',
                error_message = ?
            WHERE id = ?
        """, (error_msg, run_id))
        conn.commit()
    
    finally:
        conn.close()
    
    return stats


if __name__ == "__main__":
    from database import init_db, seed_articles
    init_db()
    seed_articles()
    
    print("\n=== INICIANDO GERAÇÃO DE LEADS ===\n")
    stats = process_articles(max_articles=20)
    
    print(f"\n=== RESULTADO ===")
    print(f"Artigos processados: {stats['articles_processed']}")
    print(f"Leads gerados: {stats['leads_generated']}")
    print(f"Empresas encontradas: {stats['companies_found']}")
    print(f"Investidores encontrados: {stats['investors_found']}")
    if stats["errors"]:
        print(f"Erros: {len(stats['errors'])}")
