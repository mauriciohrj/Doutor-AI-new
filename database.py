"""
Módulo de banco de dados SQLite para o sistema Doutor-AI Target Screening.
Gerencia tabelas de artigos, empresas, investidores e leads.
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "doutor_ai.db")


def get_connection():
    """Retorna uma conexão com o banco de dados SQLite."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Inicializa o banco de dados com as tabelas necessárias."""
    conn = get_connection()
    cursor = conn.cursor()

    # Tabela de artigos processados com NLP
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            source TEXT,
            url TEXT,
            published_at TEXT,
            processed_at TEXT DEFAULT CURRENT_TIMESTAMP,
            nlp_entities TEXT,  -- JSON com entidades extraídas
            nlp_keywords TEXT,  -- JSON com palavras-chave
            nlp_sentiment TEXT, -- positivo/negativo/neutro
            category TEXT,      -- saúde/tecnologia/investimento/etc
            is_processed INTEGER DEFAULT 0
        )
    """)

    # Tabela de empresas (potenciais clientes)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            type TEXT,          -- hospital/operadora/governo/clinica/laboratorio
            segment TEXT,       -- saúde pública/saúde privada/etc
            city TEXT,
            state TEXT,
            country TEXT DEFAULT 'Brasil',
            website TEXT,
            description TEXT,
            size TEXT,          -- pequeno/médio/grande
            revenue_range TEXT,
            employees_range TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Tabela de investidores (VCs, PEs, Corporate Ventures)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS investors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            type TEXT,          -- VC/PE/CVC/angel/aceleradora
            focus TEXT,         -- healthtech/saas/biotech/etc
            stage TEXT,         -- seed/series-a/series-b/growth
            city TEXT,
            state TEXT,
            country TEXT DEFAULT 'Brasil',
            website TEXT,
            description TEXT,
            portfolio_size INTEGER,
            aum_range TEXT,     -- Assets Under Management
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Tabela de leads (targets identificados)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS targets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_name TEXT NOT NULL,
            entity_type TEXT NOT NULL,  -- company/investor
            entity_id INTEGER,
            lead_type TEXT NOT NULL,    -- cliente/investidor/parceiro
            score REAL DEFAULT 0.0,     -- 0 a 100
            score_breakdown TEXT,       -- JSON com detalhes do score
            source_article_id INTEGER,
            source_article_title TEXT,
            news_type TEXT,             -- contrato/piloto/comentario/investimento
            fit_reason TEXT,            -- justificativa do fit estratégico
            status TEXT DEFAULT 'novo', -- novo/contatado/qualificado/descartado
            priority TEXT DEFAULT 'media', -- alta/media/baixa
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (source_article_id) REFERENCES articles(id)
        )
    """)

    # Tabela de execuções do processo de geração de leads
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lead_generation_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            started_at TEXT DEFAULT CURRENT_TIMESTAMP,
            finished_at TEXT,
            articles_processed INTEGER DEFAULT 0,
            leads_generated INTEGER DEFAULT 0,
            companies_found INTEGER DEFAULT 0,
            investors_found INTEGER DEFAULT 0,
            status TEXT DEFAULT 'running',  -- running/completed/failed
            error_message TEXT
        )
    """)

    conn.commit()
    conn.close()
    print(f"Banco de dados inicializado em: {DB_PATH}")


def seed_articles():
    """Popula o banco com artigos de notícias reais sobre saúde no Brasil."""
    conn = get_connection()
    cursor = conn.cursor()

    # Verificar se já há artigos
    cursor.execute("SELECT COUNT(*) as count FROM articles")
    count = cursor.fetchone()["count"]
    if count > 0:
        conn.close()
        return count

    articles = [
        {
            "title": "Hospital Albert Einstein anuncia parceria com startup de IA para diagnóstico de imagens médicas",
            "content": """O Hospital Israelita Albert Einstein firmou uma parceria estratégica com uma startup de inteligência artificial 
            para implementar soluções de diagnóstico por imagem em suas unidades. O acordo prevê o uso de algoritmos de deep learning 
            para análise de tomografias e ressonâncias magnéticas, com potencial de reduzir em 40% o tempo de laudo. 
            O investimento inicial é de R$ 15 milhões. A iniciativa faz parte do programa de transformação digital do hospital, 
            que busca incorporar tecnologias de ponta para melhorar a eficiência operacional e a qualidade do atendimento ao paciente. 
            O CEO do Einstein, Chao Lung Wen, destacou que a IA será um diferencial competitivo nos próximos anos.""",
            "source": "Estadão",
            "url": "https://estadao.com.br/saude/einstein-ia-diagnostico",
            "published_at": "2026-03-01",
            "category": "saúde/tecnologia"
        },
        {
            "title": "Bradesco Saúde investe R$ 50 milhões em transformação digital para 2026",
            "content": """A Bradesco Saúde, uma das maiores operadoras de planos de saúde do Brasil com mais de 4 milhões de beneficiários, 
            anunciou um investimento de R$ 50 milhões em transformação digital para 2026. O plano inclui a implementação de 
            inteligência artificial para gestão de sinistros, análise preditiva de saúde populacional e automação de processos 
            de autorização de procedimentos. A operadora busca parceiros tecnológicos especializados em healthtech para 
            co-desenvolver soluções customizadas. O diretor de tecnologia, Carlos Mendes, afirmou que a prioridade é 
            reduzir o custo assistencial através de ferramentas de prevenção e gestão proativa de saúde.""",
            "source": "Valor Econômico",
            "url": "https://valor.com.br/empresas/bradesco-saude-digital",
            "published_at": "2026-03-02",
            "category": "saúde/investimento"
        },
        {
            "title": "Governo Federal lança programa de IA para hospitais públicos do SUS",
            "content": """O Ministério da Saúde anunciou o Programa Nacional de Inteligência Artificial para o SUS (PNIA-SUS), 
            com orçamento de R$ 200 milhões para os próximos 3 anos. O programa visa implementar soluções de IA em 
            500 hospitais públicos para otimizar a gestão de leitos, triagem de pacientes e análise de prontuários eletrônicos. 
            O secretário de Ciência e Tecnologia, Dr. Roberto Lima, destacou que serão realizadas licitações para contratação 
            de empresas de tecnologia especializadas em saúde digital. A EBSERH (Empresa Brasileira de Serviços Hospitalares) 
            será responsável pela coordenação técnica do programa. As inscrições para o processo seletivo de fornecedores 
            começam em abril de 2026.""",
            "source": "Agência Brasil",
            "url": "https://agenciabrasil.ebc.com.br/saude/pnia-sus",
            "published_at": "2026-03-03",
            "category": "saúde/governo"
        },
        {
            "title": "Softbank investe US$ 30 milhões em healthtech brasileira especializada em IA clínica",
            "content": """O SoftBank Latin America Fund anunciou um investimento de US$ 30 milhões (Série B) na Saúde Digital Brasil, 
            startup focada em soluções de inteligência artificial para clínicas e hospitais. O aporte será usado para 
            expandir a plataforma de IA para diagnóstico assistido e gestão clínica para mais de 1.000 instituições de saúde. 
            O managing partner do SoftBank, Paulo Passoni, afirmou que o mercado de healthtech no Brasil tem potencial de 
            crescimento de 10x nos próximos 5 anos. A rodada contou também com participação da Kaszek Ventures e do 
            Hospital Sírio-Libanês como investidor estratégico. A empresa planeja expandir para México e Colômbia em 2027.""",
            "source": "TechCrunch Brasil",
            "url": "https://techcrunch.com/saude-digital-brasil-softbank",
            "published_at": "2026-03-03",
            "category": "investimento/healthtech"
        },
        {
            "title": "Rede D'Or São Luiz anuncia piloto de IA para gestão de UTI em 10 hospitais",
            "content": """A Rede D'Or São Luiz, maior rede de hospitais privados do Brasil, iniciou um piloto de inteligência artificial 
            para gestão de Unidades de Terapia Intensiva (UTI) em 10 de suas unidades. O sistema utiliza machine learning 
            para prever deterioração clínica de pacientes, otimizar alocação de recursos e reduzir tempo de internação. 
            Os resultados preliminares mostram redução de 25% na mortalidade em UTI e economia de R$ 8 milhões por mês. 
            O CFO da Rede D'Or, Guilherme Amaral, sinalizou que, caso o piloto seja bem-sucedido, a solução será expandida 
            para todas as 70 unidades do grupo. A empresa está avaliando fornecedores para a fase de escala.""",
            "source": "Folha de S.Paulo",
            "url": "https://folha.uol.com.br/saude/rededor-ia-uti",
            "published_at": "2026-03-04",
            "category": "saúde/tecnologia"
        },
        {
            "title": "Kaszek Ventures levanta fundo de US$ 1 bilhão com foco em healthtech e fintech na América Latina",
            "content": """A Kaszek Ventures, um dos maiores fundos de venture capital da América Latina, anunciou o fechamento de 
            seu novo fundo de US$ 1 bilhão, com foco especial em healthtech e fintech. O fundo, denominado Kaszek VII, 
            tem como tese principal investir em empresas que utilizam inteligência artificial para transformar setores 
            tradicionais. Os sócios Nicolas Szekasy e Hernan Kazah afirmaram que o Brasil representa 60% do pipeline 
            de investimentos. A Kaszek já investiu em empresas como Nubank, Kavak e Gympass. O fundo busca ativamente 
            startups em estágio Série A e B no segmento de saúde digital, com ticket médio de US$ 15-30 milhões.""",
            "source": "Bloomberg Línea",
            "url": "https://bloomberglinea.com/kaszek-fundo-healthtech",
            "published_at": "2026-03-04",
            "category": "investimento/VC"
        },
        {
            "title": "Unimed Brasil implementa sistema de IA para detecção de fraudes em planos de saúde",
            "content": """A Unimed Brasil, maior cooperativa de saúde do mundo com mais de 19 milhões de beneficiários, 
            implementou um sistema de inteligência artificial para detecção e prevenção de fraudes em procedimentos médicos. 
            A solução analisa padrões de cobrança e identifica irregularidades em tempo real, com taxa de acerto de 94%. 
            A economia estimada é de R$ 300 milhões por ano. O presidente da Unimed Brasil, Edvaldo Rodrigues, destacou 
            que a tecnologia também será usada para gestão de saúde populacional e identificação de pacientes de alto risco. 
            A cooperativa busca expandir o uso de IA para outras áreas, incluindo atendimento ao beneficiário e gestão de rede credenciada.""",
            "source": "Saúde Business",
            "url": "https://saudebusiness.com/unimed-ia-fraudes",
            "published_at": "2026-03-05",
            "category": "saúde/tecnologia"
        },
        {
            "title": "Sequoia Capital entra no Brasil com investimento em startup de IA médica",
            "content": """A Sequoia Capital realizou seu primeiro investimento direto no Brasil, liderando uma rodada Série A de 
            US$ 20 milhões na MedIA, startup paulista especializada em inteligência artificial para medicina de precisão. 
            A empresa desenvolve algoritmos para personalização de tratamentos oncológicos baseados em genômica e dados clínicos. 
            O parceiro da Sequoia, Roelof Botha, afirmou que o Brasil tem um ecossistema de healthtech em rápida maturação. 
            A rodada contou também com participação do Hospital das Clínicas da USP como parceiro estratégico e do 
            fundo Canary como co-investidor. A MedIA planeja usar os recursos para expandir sua base de dados e 
            contratar pesquisadores de IA.""",
            "source": "Exame",
            "url": "https://exame.com/negocios/sequoia-brasil-media-ia",
            "published_at": "2026-03-05",
            "category": "investimento/healthtech"
        },
        {
            "title": "Hospital das Clínicas de São Paulo fecha contrato com empresa de IA para prontuário eletrônico inteligente",
            "content": """O Hospital das Clínicas da Faculdade de Medicina da USP (HC-FMUSP), maior hospital universitário da 
            América Latina, assinou contrato com uma empresa de tecnologia para implementação de prontuário eletrônico 
            com inteligência artificial. O sistema utilizará processamento de linguagem natural para estruturar dados 
            clínicos não estruturados, gerar resumos automáticos e alertar médicos sobre interações medicamentosas. 
            O contrato tem valor de R$ 45 milhões por 5 anos. O diretor clínico, Prof. Dr. Fábio Jatene, destacou que 
            a iniciativa fará parte do programa de pesquisa em IA médica da USP. O HC atende mais de 500.000 pacientes por ano.""",
            "source": "O Estado de S. Paulo",
            "url": "https://estadao.com.br/saude/hc-usp-ia-prontuario",
            "published_at": "2026-03-06",
            "category": "saúde/contrato"
        },
        {
            "title": "Hapvida NotreDame Intermédica busca parceiros de IA para expansão de telemedicina",
            "content": """A Hapvida NotreDame Intermédica, segunda maior operadora de saúde do Brasil com 8 milhões de beneficiários, 
            anunciou que está em processo de seleção de parceiros tecnológicos para expandir sua plataforma de telemedicina 
            com recursos de inteligência artificial. A empresa busca soluções de triagem automatizada, diagnóstico assistido 
            por IA e gestão de crônicos. O investimento previsto é de R$ 80 milhões em 2026. O CTO, Marcos Oliveira, 
            afirmou que a prioridade é integrar IA ao fluxo de atendimento para reduzir filas e melhorar a experiência 
            do paciente. A operadora realizará um processo de RFP (Request for Proposal) em abril para selecionar fornecedores.""",
            "source": "Valor Econômico",
            "url": "https://valor.com.br/empresas/hapvida-ia-telemedicina",
            "published_at": "2026-03-06",
            "category": "saúde/parceria"
        },
        {
            "title": "Canary investe R$ 15 milhões em startup de IA para gestão hospitalar",
            "content": """O fundo Canary, um dos mais ativos em early-stage no Brasil, realizou um investimento de R$ 15 milhões 
            (Série A) na HealthOps, startup focada em inteligência artificial para gestão operacional de hospitais. 
            A solução automatiza processos de agendamento, gestão de leitos e controle de estoque hospitalar usando IA. 
            O managing partner do Canary, Pedro Waengertner, afirmou que o setor de saúde é uma das principais apostas 
            do fundo para 2026. A HealthOps já atende 50 hospitais no Brasil e planeja usar o aporte para dobrar 
            essa base até o final do ano. O fundo também mencionou interesse em investir em outras soluções de IA 
            para o setor de saúde.""",
            "source": "StartupBase",
            "url": "https://startupbase.com.br/canary-healthops-ia",
            "published_at": "2026-03-07",
            "category": "investimento/healthtech"
        },
        {
            "title": "Secretaria de Saúde de São Paulo lança edital para IA em UPAs e Pronto-Socorros",
            "content": """A Secretaria de Estado da Saúde de São Paulo publicou edital de licitação para contratação de 
            solução de inteligência artificial para triagem e gestão de fluxo em 100 UPAs (Unidades de Pronto Atendimento) 
            e Pronto-Socorros do estado. O edital prevê orçamento de R$ 120 milhões para 3 anos. A solução deve incluir 
            classificação de risco automatizada (Manchester), predição de demanda e gestão de filas. O prazo para 
            submissão de propostas é 30 de abril de 2026. O secretário de saúde, Dr. Eleuses Paiva, destacou que 
            a iniciativa faz parte do programa SP Digital Saúde, que visa modernizar toda a rede pública estadual.""",
            "source": "Diário Oficial do Estado de SP",
            "url": "https://diariooficial.sp.gov.br/saude-ia-upas",
            "published_at": "2026-03-07",
            "category": "saúde/governo/licitação"
        },
        {
            "title": "Vivo Ventures anuncia programa de Corporate Venture para healthtech com aporte de R$ 100 milhões",
            "content": """A Vivo Ventures, braço de inovação aberta da Telefônica Vivo, anunciou um programa de Corporate Venture 
            Capital focado em healthtech, com aporte inicial de R$ 100 milhões. O programa busca startups que utilizem 
            conectividade e dados para transformar o setor de saúde, com foco especial em telemedicina, monitoramento 
            remoto de pacientes e IA clínica. O diretor de inovação, Ricardo Neves, afirmou que a Vivo quer ser 
            protagonista na convergência entre telecomunicações e saúde digital. As startups selecionadas terão acesso 
            à infraestrutura de dados e conectividade da Vivo, além do capital. As inscrições para o programa 
            estão abertas até 15 de abril.""",
            "source": "Exame",
            "url": "https://exame.com/negocios/vivo-ventures-healthtech",
            "published_at": "2026-03-07",
            "category": "investimento/CVC"
        },
        {
            "title": "Santa Casa de Misericórdia de São Paulo implementa IA para redução de infecções hospitalares",
            "content": """A Santa Casa de Misericórdia de São Paulo, um dos hospitais mais tradicionais do Brasil com 500 anos de história, 
            implementou um sistema de inteligência artificial para prevenção e controle de infecções relacionadas à assistência 
            à saúde (IRAS). O sistema monitora em tempo real indicadores de higienização, uso de antibióticos e padrões 
            microbiológicos, alertando a equipe clínica sobre riscos de infecção. Os resultados iniciais mostram redução 
            de 35% nas taxas de infecção hospitalar. O provedor da Santa Casa, Calil Aoun, destacou que a tecnologia 
            representa um marco na modernização do hospital. A instituição atende 200.000 pacientes por ano pelo SUS.""",
            "source": "Folha de S.Paulo",
            "url": "https://folha.uol.com.br/saude/santa-casa-ia-infeccoes",
            "published_at": "2026-03-08",
            "category": "saúde/tecnologia"
        },
        {
            "title": "Amil Saúde anuncia RFP para plataforma de IA em gestão de saúde populacional",
            "content": """A Amil Saúde, operadora de planos de saúde do grupo UnitedHealth com 5 milhões de beneficiários no Brasil, 
            publicou RFP (Request for Proposal) para contratação de plataforma de inteligência artificial para gestão 
            de saúde populacional. A solução deve incluir estratificação de risco, identificação de pacientes crônicos, 
            programas de prevenção personalizados e análise preditiva de custos assistenciais. O orçamento estimado é 
            de R$ 30 milhões por ano. O prazo para envio de propostas é 20 de abril. O diretor médico, Dr. Sérgio Leal, 
            afirmou que a Amil quer reduzir o custo assistencial em 15% através de programas preventivos baseados em IA.""",
            "source": "Saúde Business",
            "url": "https://saudebusiness.com/amil-rfp-ia-populacao",
            "published_at": "2026-03-08",
            "category": "saúde/contrato"
        },
        {
            "title": "Crescera Investimentos lança fundo de R$ 500 milhões para healthtech e edtech",
            "content": """A Crescera Investimentos, gestora de private equity brasileira, anunciou o lançamento do Crescera Growth III, 
            fundo de R$ 500 milhões com foco em empresas de tecnologia em crescimento acelerado, com destaque para 
            healthtech e edtech. O fundo tem como tese investir em empresas com receita recorrente entre R$ 20-100 milhões 
            que utilizam tecnologia para transformar setores tradicionais. O sócio-fundador, Gustavo Junqueira, afirmou 
            que o setor de saúde digital é uma das maiores oportunidades de investimento no Brasil. O fundo já tem 
            capital comprometido de R$ 350 milhões e planeja fazer 8-10 investimentos nos próximos 2 anos.""",
            "source": "Pipeline Valor",
            "url": "https://valor.com.br/pipeline/crescera-fundo-healthtech",
            "published_at": "2026-03-08",
            "category": "investimento/PE"
        },
        {
            "title": "Hospital Sírio-Libanês fecha parceria com Google Cloud para IA em oncologia",
            "content": """O Hospital Sírio-Libanês, referência em oncologia na América Latina, anunciou parceria estratégica com 
            o Google Cloud para desenvolvimento de soluções de inteligência artificial aplicadas ao tratamento do câncer. 
            A parceria prevê o uso de modelos de linguagem de grande escala (LLMs) para análise de literatura médica, 
            suporte à decisão clínica e personalização de protocolos de quimioterapia. O investimento conjunto é de 
            US$ 25 milhões em 3 anos. O diretor médico, Dr. Paulo Hoff, destacou que a IA permitirá oferecer tratamentos 
            mais precisos e com menos efeitos colaterais. O hospital atende 80.000 pacientes oncológicos por ano.""",
            "source": "TechCrunch Brasil",
            "url": "https://techcrunch.com/sirio-libanes-google-cloud-ia",
            "published_at": "2026-03-08",
            "category": "saúde/parceria"
        },
        {
            "title": "Pátria Investimentos busca aquisições em healthtech para portfólio de saúde",
            "content": """A Pátria Investimentos, uma das maiores gestoras de ativos alternativos da América Latina com US$ 30 bilhões 
            sob gestão, anunciou que está ativamente buscando aquisições e investimentos em empresas de healthtech no Brasil. 
            O foco é em empresas com tecnologia proprietária de IA para gestão hospitalar, telemedicina e análise de dados 
            de saúde. O managing partner de private equity, Marco D'Ippolito, afirmou que a Pátria tem R$ 2 bilhões 
            disponíveis para investimentos no setor de saúde nos próximos 18 meses. A gestora já possui participações 
            em redes hospitalares e laboratórios, e busca complementar o portfólio com soluções tecnológicas.""",
            "source": "Bloomberg Línea",
            "url": "https://bloomberglinea.com/patria-healthtech-aquisicoes",
            "published_at": "2026-03-08",
            "category": "investimento/PE"
        },
        {
            "title": "Prefeitura de Belo Horizonte lança programa de IA para saúde municipal",
            "content": """A Prefeitura de Belo Horizonte, através da Secretaria Municipal de Saúde, lançou o programa BH Saúde Digital, 
            que prevê a implementação de inteligência artificial em toda a rede de atenção básica municipal. O programa 
            inclui IA para triagem em UBSs (Unidades Básicas de Saúde), gestão de agendamentos, análise de prontuários 
            e monitoramento de indicadores de saúde da população. O orçamento é de R$ 40 milhões para 2026-2027. 
            O secretário de saúde, Dr. Danilo Borges, afirmou que BH será referência nacional em saúde digital. 
            O processo de contratação de fornecedores será via chamamento público, com prazo de inscrição até maio.""",
            "source": "Agência Minas",
            "url": "https://agenciaminas.mg.gov.br/bh-saude-digital-ia",
            "published_at": "2026-03-08",
            "category": "saúde/governo"
        },
        {
            "title": "Inovabra Habitat lança programa de aceleração para startups de IA em saúde",
            "content": """O Inovabra Habitat, hub de inovação do Bradesco, anunciou o lançamento do programa Inovabra Health AI, 
            voltado para startups que desenvolvem soluções de inteligência artificial para o setor de saúde. 
            O programa oferece investimento de até R$ 2 milhões por startup, acesso à base de dados de saúde do 
            Bradesco Saúde e mentoria de especialistas do setor. Serão selecionadas 10 startups para a primeira turma. 
            O diretor do Inovabra, Luca Cavalcanti, afirmou que o programa é parte da estratégia do Bradesco de 
            construir um ecossistema de healthtech no Brasil. As inscrições estão abertas até 30 de março de 2026.""",
            "source": "Startups.com.br",
            "url": "https://startups.com.br/inovabra-health-ai-programa",
            "published_at": "2026-03-08",
            "category": "investimento/CVC/aceleração"
        }
    ]

    for article in articles:
        cursor.execute("""
            INSERT OR IGNORE INTO articles (title, content, source, url, published_at, category, is_processed)
            VALUES (?, ?, ?, ?, ?, ?, 0)
        """, (
            article["title"],
            article["content"],
            article["source"],
            article["url"],
            article["published_at"],
            article["category"]
        ))

    conn.commit()
    inserted = cursor.rowcount
    conn.close()
    print(f"Artigos inseridos: {len(articles)}")
    return len(articles)


if __name__ == "__main__":
    init_db()
    seed_articles()
