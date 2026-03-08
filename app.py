"""
Servidor Flask para o sistema Doutor-AI Target Screening.
Fornece painel administrativo e API REST para gestão de leads.
"""

import json
import threading
from datetime import datetime
from flask import Flask, render_template_string, jsonify, request
from flask_cors import CORS
from database import get_connection, init_db, seed_articles
from lead_generator import process_articles

app = Flask(__name__)
CORS(app)

# Estado global da execução em andamento
execution_state = {
    "running": False,
    "last_result": None,
    "progress": ""
}


# ─────────────────────────────────────────────
# TEMPLATE HTML DO PAINEL ADMINISTRATIVO
# ─────────────────────────────────────────────

ADMIN_TEMPLATE = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Doutor-AI | Painel Administrativo</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Segoe UI', sans-serif; background: #f0f4f8; color: #1a202c; }
    
    /* Header */
    .header {
      background: linear-gradient(135deg, #1a56db 0%, #0e3a8c 100%);
      color: white; padding: 16px 32px;
      display: flex; align-items: center; gap: 16px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    }
    .header .logo { font-size: 24px; font-weight: 700; letter-spacing: -0.5px; }
    .header .logo span { color: #60a5fa; }
    .header .subtitle { font-size: 13px; opacity: 0.8; }
    .header .badge { 
      margin-left: auto; background: rgba(255,255,255,0.15); 
      padding: 4px 12px; border-radius: 20px; font-size: 12px; 
    }
    
    /* Nav */
    .nav { background: white; border-bottom: 1px solid #e2e8f0; padding: 0 32px; }
    .nav a {
      display: inline-block; padding: 14px 20px; font-size: 14px; font-weight: 500;
      color: #64748b; text-decoration: none; border-bottom: 3px solid transparent;
      transition: all 0.2s;
    }
    .nav a.active, .nav a:hover { color: #1a56db; border-bottom-color: #1a56db; }
    
    /* Main */
    .main { max-width: 1400px; margin: 0 auto; padding: 32px; }
    .page-title { font-size: 22px; font-weight: 700; color: #1a202c; margin-bottom: 8px; }
    .page-subtitle { font-size: 14px; color: #64748b; margin-bottom: 28px; }
    
    /* Stats Grid */
    .stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 32px; }
    .stat-card {
      background: white; border-radius: 12px; padding: 20px;
      box-shadow: 0 1px 4px rgba(0,0,0,0.08); border: 1px solid #e2e8f0;
    }
    .stat-card .label { font-size: 12px; color: #64748b; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px; }
    .stat-card .value { font-size: 32px; font-weight: 700; color: #1a202c; margin: 8px 0 4px; }
    .stat-card .change { font-size: 12px; color: #10b981; }
    .stat-card .icon { font-size: 28px; float: right; margin-top: -40px; opacity: 0.15; }
    
    /* Cards Grid */
    .cards-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 32px; }
    .card {
      background: white; border-radius: 12px; padding: 24px;
      box-shadow: 0 1px 4px rgba(0,0,0,0.08); border: 1px solid #e2e8f0;
    }
    .card h3 { font-size: 16px; font-weight: 600; color: #1a202c; margin-bottom: 8px; }
    .card p { font-size: 13px; color: #64748b; line-height: 1.6; margin-bottom: 16px; }
    .card .meta { font-size: 12px; color: #94a3b8; margin-bottom: 16px; }
    
    /* Buttons */
    .btn {
      display: inline-flex; align-items: center; gap: 8px;
      padding: 10px 20px; border-radius: 8px; font-size: 14px; font-weight: 600;
      cursor: pointer; border: none; transition: all 0.2s; text-decoration: none;
    }
    .btn-primary { background: #1a56db; color: white; }
    .btn-primary:hover { background: #1447c0; transform: translateY(-1px); box-shadow: 0 4px 12px rgba(26,86,219,0.3); }
    .btn-primary:disabled { background: #93c5fd; cursor: not-allowed; transform: none; box-shadow: none; }
    .btn-secondary { background: #f1f5f9; color: #475569; border: 1px solid #e2e8f0; }
    .btn-secondary:hover { background: #e2e8f0; }
    .btn-success { background: #10b981; color: white; }
    .btn-success:hover { background: #059669; }
    
    /* Alert */
    .alert {
      padding: 14px 18px; border-radius: 8px; font-size: 14px;
      margin-bottom: 20px; display: flex; align-items: center; gap: 10px;
    }
    .alert-info { background: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; }
    .alert-success { background: #f0fdf4; color: #166534; border: 1px solid #bbf7d0; }
    .alert-warning { background: #fffbeb; color: #92400e; border: 1px solid #fde68a; }
    .alert-error { background: #fef2f2; color: #991b1b; border: 1px solid #fecaca; }
    
    /* Progress */
    .progress-bar {
      width: 100%; height: 8px; background: #e2e8f0; border-radius: 4px; overflow: hidden;
      margin: 12px 0;
    }
    .progress-fill {
      height: 100%; background: linear-gradient(90deg, #1a56db, #60a5fa);
      border-radius: 4px; transition: width 0.5s ease;
      animation: pulse 1.5s ease-in-out infinite;
    }
    @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.7; } }
    
    /* Table */
    .table-container { background: white; border-radius: 12px; box-shadow: 0 1px 4px rgba(0,0,0,0.08); border: 1px solid #e2e8f0; overflow: hidden; }
    .table-header { padding: 16px 20px; border-bottom: 1px solid #e2e8f0; display: flex; align-items: center; justify-content: space-between; }
    .table-header h3 { font-size: 15px; font-weight: 600; }
    table { width: 100%; border-collapse: collapse; }
    th { background: #f8fafc; padding: 12px 16px; text-align: left; font-size: 12px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid #e2e8f0; }
    td { padding: 12px 16px; font-size: 13px; border-bottom: 1px solid #f1f5f9; vertical-align: top; }
    tr:last-child td { border-bottom: none; }
    tr:hover td { background: #f8fafc; }
    
    /* Badges */
    .badge {
      display: inline-block; padding: 3px 10px; border-radius: 20px;
      font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.3px;
    }
    .badge-alta { background: #fef2f2; color: #dc2626; }
    .badge-media { background: #fffbeb; color: #d97706; }
    .badge-baixa { background: #f0fdf4; color: #16a34a; }
    .badge-cliente { background: #eff6ff; color: #1d4ed8; }
    .badge-investidor { background: #f5f3ff; color: #7c3aed; }
    .badge-parceiro { background: #f0fdfa; color: #0f766e; }
    .badge-hospital { background: #fef3c7; color: #92400e; }
    .badge-operadora { background: #e0f2fe; color: #0369a1; }
    .badge-governo { background: #f0fdf4; color: #166534; }
    .badge-vc { background: #fdf4ff; color: #7e22ce; }
    .badge-pe { background: #fdf4ff; color: #6d28d9; }
    .badge-cvc { background: #fff1f2; color: #be123c; }
    
    /* Score */
    .score-bar { display: flex; align-items: center; gap: 8px; }
    .score-value { font-weight: 700; font-size: 15px; min-width: 36px; }
    .score-mini-bar { flex: 1; height: 6px; background: #e2e8f0; border-radius: 3px; overflow: hidden; }
    .score-mini-fill { height: 100%; border-radius: 3px; }
    .score-high { background: #ef4444; }
    .score-med { background: #f59e0b; }
    .score-low { background: #10b981; }
    
    /* Spinner */
    .spinner { 
      display: inline-block; width: 16px; height: 16px; border: 2px solid rgba(255,255,255,0.3);
      border-top-color: white; border-radius: 50%; animation: spin 0.8s linear infinite;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
    
    /* Result box */
    .result-box {
      background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 10px;
      padding: 20px; margin-top: 16px;
    }
    .result-box h4 { color: #166534; font-size: 15px; margin-bottom: 12px; }
    .result-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
    .result-item { text-align: center; }
    .result-item .num { font-size: 28px; font-weight: 700; color: #166534; }
    .result-item .lbl { font-size: 11px; color: #4ade80; font-weight: 500; }
    
    /* Tabs */
    .tabs { display: flex; gap: 4px; margin-bottom: 20px; }
    .tab {
      padding: 8px 16px; border-radius: 8px; font-size: 13px; font-weight: 500;
      cursor: pointer; border: 1px solid #e2e8f0; background: white; color: #64748b;
      transition: all 0.2s;
    }
    .tab.active { background: #1a56db; color: white; border-color: #1a56db; }
    
    /* Empty state */
    .empty-state { text-align: center; padding: 60px 20px; color: #94a3b8; }
    .empty-state .icon { font-size: 48px; margin-bottom: 16px; }
    .empty-state p { font-size: 14px; }
    
    /* Responsive */
    @media (max-width: 1024px) {
      .stats-grid { grid-template-columns: repeat(2, 1fr); }
      .cards-grid { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>

<div class="header">
  <div>
    <div class="logo">Doutor<span>-AI</span></div>
    <div class="subtitle">Target Screening & Lead Intelligence</div>
  </div>
  <div class="badge">v1.0 · Série A</div>
</div>

<div class="nav">
  <a href="/admin" class="active">Dashboard</a>
  <a href="/leads">Leads</a>
  <a href="/companies">Empresas</a>
  <a href="/investors">Investidores</a>
  <a href="/articles">Artigos</a>
</div>

<div class="main">
  <div class="page-title">Painel Administrativo</div>
  <div class="page-subtitle">Geração e gestão de leads a partir de notícias do setor de saúde</div>
  
  <!-- Stats -->
  <div class="stats-grid" id="stats-grid">
    <div class="stat-card">
      <div class="label">Total de Leads</div>
      <div class="value" id="stat-leads">—</div>
      <div class="change" id="stat-leads-change">carregando...</div>
    </div>
    <div class="stat-card">
      <div class="label">Leads Alta Prioridade</div>
      <div class="value" id="stat-high">—</div>
      <div class="change">Score ≥ 75</div>
    </div>
    <div class="stat-card">
      <div class="label">Empresas Mapeadas</div>
      <div class="value" id="stat-companies">—</div>
      <div class="change">Hospitais, Operadoras, Governo</div>
    </div>
    <div class="stat-card">
      <div class="label">Investidores Mapeados</div>
      <div class="value" id="stat-investors">—</div>
      <div class="change">VCs, PEs, CVCs</div>
    </div>
  </div>
  
  <!-- Action Cards -->
  <div class="cards-grid">
    
    <!-- Card: Gerar Leads -->
    <div class="card">
      <h3>🎯 Gerar Leads</h3>
      <p>Processa até 20 artigos não analisados, extrai entidades com NLP via LLM e cria registros de leads com score de fit estratégico.</p>
      <div class="meta" id="articles-pending">Verificando artigos disponíveis...</div>
      
      <div id="execution-area">
        <button class="btn btn-primary" id="btn-generate" onclick="generateLeads()">
          ▶ Executar
        </button>
      </div>
      
      <div id="progress-area" style="display:none; margin-top:16px;">
        <div class="alert alert-info">
          <span class="spinner"></span>
          <span id="progress-text">Iniciando processamento...</span>
        </div>
        <div class="progress-bar"><div class="progress-fill" style="width:100%"></div></div>
      </div>
      
      <div id="result-area" style="display:none;"></div>
    </div>
    
    <!-- Card: Processar Notícias -->
    <div class="card">
      <h3>📰 Artigos Processados</h3>
      <p>Artigos de notícias do setor de saúde coletados e prontos para análise de leads. Cada artigo pode gerar múltiplos leads.</p>
      <div class="meta" id="articles-stats">Carregando estatísticas...</div>
      <a href="/articles" class="btn btn-secondary">Ver Artigos</a>
    </div>
    
    <!-- Card: Últimas Execuções -->
    <div class="card">
      <h3>📊 Última Execução</h3>
      <p>Histórico das execuções do processo de geração de leads com métricas de performance.</p>
      <div id="last-run-info" class="meta">Nenhuma execução registrada</div>
      <a href="/leads" class="btn btn-secondary">Ver Todos os Leads</a>
    </div>
    
  </div>
  
  <!-- Recent Leads Table -->
  <div class="table-container">
    <div class="table-header">
      <h3>Leads Recentes</h3>
      <a href="/leads" class="btn btn-secondary" style="font-size:12px; padding:6px 14px;">Ver todos →</a>
    </div>
    <div id="recent-leads-table">
      <div class="empty-state">
        <div class="icon">🎯</div>
        <p>Nenhum lead gerado ainda.<br>Clique em "Executar" no card "Gerar Leads" para iniciar.</p>
      </div>
    </div>
  </div>
</div>

<script>
  // Carregar estatísticas ao abrir a página
  async function loadStats() {
    try {
      const r = await fetch('/api/stats');
      const data = await r.json();
      
      document.getElementById('stat-leads').textContent = data.total_leads;
      document.getElementById('stat-high').textContent = data.high_priority_leads;
      document.getElementById('stat-companies').textContent = data.total_companies;
      document.getElementById('stat-investors').textContent = data.total_investors;
      
      const pending = data.articles_pending;
      document.getElementById('articles-pending').textContent = 
        pending > 0 ? `${pending} artigo(s) aguardando processamento` : 'Todos os artigos já foram processados';
      
      document.getElementById('articles-stats').textContent = 
        `${data.articles_total} artigos coletados · ${data.articles_processed} processados`;
      
      if (data.last_run) {
        const run = data.last_run;
        document.getElementById('last-run-info').innerHTML = 
          `<strong>${run.articles_processed} artigos</strong> processados · <strong>${run.leads_generated} leads</strong> gerados<br>` +
          `Status: <span style="color:${run.status === 'completed' ? '#16a34a' : '#dc2626'}">${run.status}</span> · ${run.started_at}`;
      }
      
      if (data.total_leads === 0) {
        document.getElementById('stat-leads-change').textContent = 'Execute para gerar leads';
      } else {
        document.getElementById('stat-leads-change').textContent = `${data.leads_today} novos hoje`;
      }
      
    } catch(e) {
      console.error('Erro ao carregar stats:', e);
    }
  }
  
  async function loadRecentLeads() {
    try {
      const r = await fetch('/api/leads?limit=8');
      const data = await r.json();
      
      if (!data.leads || data.leads.length === 0) return;
      
      const priorityBadge = (p) => `<span class="badge badge-${p}">${p}</span>`;
      const typeBadge = (t) => `<span class="badge badge-${t}">${t}</span>`;
      const scoreColor = (s) => s >= 75 ? 'score-high' : s >= 50 ? 'score-med' : 'score-low';
      
      let html = `<table>
        <thead><tr>
          <th>Empresa / Organização</th>
          <th>Tipo</th>
          <th>Lead</th>
          <th>Score</th>
          <th>Prioridade</th>
          <th>Notícia</th>
        </tr></thead><tbody>`;
      
      for (const lead of data.leads) {
        html += `<tr>
          <td><strong>${lead.entity_name}</strong></td>
          <td>${typeBadge(lead.entity_type_display || lead.entity_type)}</td>
          <td>${typeBadge(lead.lead_type)}</td>
          <td>
            <div class="score-bar">
              <span class="score-value">${lead.score}</span>
              <div class="score-mini-bar">
                <div class="score-mini-fill ${scoreColor(lead.score)}" style="width:${lead.score}%"></div>
              </div>
            </div>
          </td>
          <td>${priorityBadge(lead.priority)}</td>
          <td style="max-width:200px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;" title="${lead.source_article_title || ''}">${lead.news_type || '—'}</td>
        </tr>`;
      }
      
      html += '</tbody></table>';
      document.getElementById('recent-leads-table').innerHTML = html;
      
    } catch(e) {
      console.error('Erro ao carregar leads:', e);
    }
  }
  
  async function generateLeads() {
    const btn = document.getElementById('btn-generate');
    const progressArea = document.getElementById('progress-area');
    const resultArea = document.getElementById('result-area');
    
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Processando...';
    progressArea.style.display = 'block';
    resultArea.style.display = 'none';
    
    try {
      const r = await fetch('/api/generate-leads', { method: 'POST' });
      const data = await r.json();
      
      progressArea.style.display = 'none';
      
      if (data.success) {
        const stats = data.stats;
        resultArea.innerHTML = `
          <div class="result-box">
            <h4>✅ Geração concluída com sucesso!</h4>
            <div class="result-grid">
              <div class="result-item">
                <div class="num">${stats.articles_processed}</div>
                <div class="lbl">Artigos Processados</div>
              </div>
              <div class="result-item">
                <div class="num">${stats.leads_generated}</div>
                <div class="lbl">Leads Gerados</div>
              </div>
              <div class="result-item">
                <div class="num">${stats.companies_found}</div>
                <div class="lbl">Empresas</div>
              </div>
              <div class="result-item">
                <div class="num">${stats.investors_found}</div>
                <div class="lbl">Investidores</div>
              </div>
            </div>
          </div>`;
        resultArea.style.display = 'block';
        
        // Recarregar dados
        setTimeout(() => { loadStats(); loadRecentLeads(); }, 500);
      } else {
        resultArea.innerHTML = `<div class="alert alert-error">❌ Erro: ${data.error || 'Falha no processamento'}</div>`;
        resultArea.style.display = 'block';
      }
      
    } catch(e) {
      progressArea.style.display = 'none';
      resultArea.innerHTML = `<div class="alert alert-error">❌ Erro de conexão: ${e.message}</div>`;
      resultArea.style.display = 'block';
    }
    
    btn.disabled = false;
    btn.innerHTML = '▶ Executar';
  }
  
  // Inicializar
  loadStats();
  loadRecentLeads();
</script>
</body>
</html>"""


LEADS_TEMPLATE = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Doutor-AI | Leads</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Segoe UI', sans-serif; background: #f0f4f8; color: #1a202c; }
    .header { background: linear-gradient(135deg, #1a56db 0%, #0e3a8c 100%); color: white; padding: 16px 32px; display: flex; align-items: center; gap: 16px; }
    .header .logo { font-size: 24px; font-weight: 700; }
    .header .logo span { color: #60a5fa; }
    .header .subtitle { font-size: 13px; opacity: 0.8; }
    .header .badge { margin-left: auto; background: rgba(255,255,255,0.15); padding: 4px 12px; border-radius: 20px; font-size: 12px; }
    .nav { background: white; border-bottom: 1px solid #e2e8f0; padding: 0 32px; }
    .nav a { display: inline-block; padding: 14px 20px; font-size: 14px; font-weight: 500; color: #64748b; text-decoration: none; border-bottom: 3px solid transparent; }
    .nav a.active, .nav a:hover { color: #1a56db; border-bottom-color: #1a56db; }
    .main { max-width: 1400px; margin: 0 auto; padding: 32px; }
    .page-title { font-size: 22px; font-weight: 700; margin-bottom: 8px; }
    .page-subtitle { font-size: 14px; color: #64748b; margin-bottom: 28px; }
    .filters { display: flex; gap: 12px; margin-bottom: 20px; flex-wrap: wrap; }
    .filter-btn { padding: 7px 16px; border-radius: 20px; font-size: 13px; cursor: pointer; border: 1px solid #e2e8f0; background: white; color: #64748b; transition: all 0.2s; }
    .filter-btn.active { background: #1a56db; color: white; border-color: #1a56db; }
    .table-container { background: white; border-radius: 12px; box-shadow: 0 1px 4px rgba(0,0,0,0.08); border: 1px solid #e2e8f0; overflow: hidden; }
    .table-header { padding: 16px 20px; border-bottom: 1px solid #e2e8f0; display: flex; align-items: center; justify-content: space-between; }
    .table-header h3 { font-size: 15px; font-weight: 600; }
    table { width: 100%; border-collapse: collapse; }
    th { background: #f8fafc; padding: 12px 16px; text-align: left; font-size: 12px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid #e2e8f0; }
    td { padding: 12px 16px; font-size: 13px; border-bottom: 1px solid #f1f5f9; vertical-align: top; }
    tr:last-child td { border-bottom: none; }
    tr:hover td { background: #f8fafc; }
    .badge { display: inline-block; padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 600; text-transform: uppercase; }
    .badge-alta { background: #fef2f2; color: #dc2626; }
    .badge-media { background: #fffbeb; color: #d97706; }
    .badge-baixa { background: #f0fdf4; color: #16a34a; }
    .badge-cliente { background: #eff6ff; color: #1d4ed8; }
    .badge-investidor { background: #f5f3ff; color: #7c3aed; }
    .badge-parceiro { background: #f0fdfa; color: #0f766e; }
    .score-bar { display: flex; align-items: center; gap: 8px; }
    .score-value { font-weight: 700; font-size: 15px; min-width: 36px; }
    .score-mini-bar { flex: 1; height: 6px; background: #e2e8f0; border-radius: 3px; overflow: hidden; min-width: 60px; }
    .score-mini-fill { height: 100%; border-radius: 3px; }
    .score-high { background: #ef4444; }
    .score-med { background: #f59e0b; }
    .score-low { background: #10b981; }
    .fit-reason { font-size: 12px; color: #64748b; max-width: 300px; line-height: 1.4; }
    .empty-state { text-align: center; padding: 60px 20px; color: #94a3b8; }
    .empty-state .icon { font-size: 48px; margin-bottom: 16px; }
    .count-badge { background: #1a56db; color: white; border-radius: 12px; padding: 2px 8px; font-size: 12px; font-weight: 600; margin-left: 8px; }
  </style>
</head>
<body>
<div class="header">
  <div>
    <div class="logo">Doutor<span>-AI</span></div>
    <div class="subtitle">Target Screening & Lead Intelligence</div>
  </div>
  <div class="badge">v1.0 · Série A</div>
</div>
<div class="nav">
  <a href="/admin">Dashboard</a>
  <a href="/leads" class="active">Leads</a>
  <a href="/companies">Empresas</a>
  <a href="/investors">Investidores</a>
  <a href="/articles">Artigos</a>
</div>
<div class="main">
  <div class="page-title">Leads Identificados <span class="count-badge" id="total-count">0</span></div>
  <div class="page-subtitle">Empresas e investidores identificados a partir de notícias do setor de saúde</div>
  
  <div class="filters">
    <button class="filter-btn active" onclick="filterLeads('all', this)">Todos</button>
    <button class="filter-btn" onclick="filterLeads('cliente', this)">Clientes</button>
    <button class="filter-btn" onclick="filterLeads('investidor', this)">Investidores</button>
    <button class="filter-btn" onclick="filterLeads('parceiro', this)">Parceiros</button>
    <button class="filter-btn" onclick="filterLeads('alta', this)">Alta Prioridade</button>
  </div>
  
  <div class="table-container">
    <div class="table-header">
      <h3>Lista de Leads</h3>
    </div>
    <div id="leads-table">
      <div class="empty-state">
        <div class="icon">🎯</div>
        <p>Carregando leads...</p>
      </div>
    </div>
  </div>
</div>

<script>
  let allLeads = [];
  let currentFilter = 'all';
  
  async function loadLeads() {
    const r = await fetch('/api/leads?limit=200');
    const data = await r.json();
    allLeads = data.leads || [];
    renderLeads(allLeads);
    document.getElementById('total-count').textContent = allLeads.length;
  }
  
  function filterLeads(type, btn) {
    currentFilter = type;
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    
    let filtered = allLeads;
    if (type === 'alta') filtered = allLeads.filter(l => l.priority === 'alta');
    else if (type !== 'all') filtered = allLeads.filter(l => l.lead_type === type);
    
    renderLeads(filtered);
  }
  
  function renderLeads(leads) {
    if (!leads || leads.length === 0) {
      document.getElementById('leads-table').innerHTML = `
        <div class="empty-state">
          <div class="icon">🎯</div>
          <p>Nenhum lead encontrado.<br>Execute a geração de leads no painel admin.</p>
        </div>`;
      return;
    }
    
    const scoreColor = (s) => s >= 75 ? 'score-high' : s >= 50 ? 'score-med' : 'score-low';
    
    let html = `<table>
      <thead><tr>
        <th>#</th>
        <th>Empresa / Organização</th>
        <th>Tipo de Lead</th>
        <th>Score</th>
        <th>Prioridade</th>
        <th>Tipo de Notícia</th>
        <th>Fit Estratégico</th>
        <th>Data</th>
      </tr></thead><tbody>`;
    
    leads.forEach((lead, i) => {
      html += `<tr>
        <td style="color:#94a3b8">${i+1}</td>
        <td><strong>${lead.entity_name}</strong></td>
        <td><span class="badge badge-${lead.lead_type}">${lead.lead_type}</span></td>
        <td>
          <div class="score-bar">
            <span class="score-value">${lead.score}</span>
            <div class="score-mini-bar">
              <div class="score-mini-fill ${scoreColor(lead.score)}" style="width:${lead.score}%"></div>
            </div>
          </div>
        </td>
        <td><span class="badge badge-${lead.priority}">${lead.priority}</span></td>
        <td>${lead.news_type || '—'}</td>
        <td class="fit-reason">${lead.fit_reason || '—'}</td>
        <td style="color:#94a3b8; white-space:nowrap">${lead.created_at ? lead.created_at.substring(0,10) : '—'}</td>
      </tr>`;
    });
    
    html += '</tbody></table>';
    document.getElementById('leads-table').innerHTML = html;
  }
  
  loadLeads();
</script>
</body>
</html>"""


# ─────────────────────────────────────────────
# ROTAS DA APLICAÇÃO
# ─────────────────────────────────────────────

@app.route("/admin")
@app.route("/")
def admin():
    return render_template_string(ADMIN_TEMPLATE)


@app.route("/leads")
def leads_page():
    return render_template_string(LEADS_TEMPLATE)


@app.route("/companies")
def companies_page():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM companies ORDER BY updated_at DESC")
    companies = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    rows = ""
    for c in companies:
        rows += f"""<tr>
          <td><strong>{c['name']}</strong></td>
          <td><span class="badge badge-{c.get('type','outro')}">{c.get('type','—')}</span></td>
          <td>{c.get('city') or '—'}, {c.get('state') or '—'}</td>
          <td>{c.get('size') or '—'}</td>
          <td>{c.get('revenue_range') or '—'}</td>
          <td style="font-size:12px;color:#64748b;max-width:250px">{(c.get('description') or '—')[:120]}...</td>
        </tr>"""
    
    return f"""<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8">
    <title>Empresas | Doutor-AI</title>
    <style>
    * {{box-sizing:border-box;margin:0;padding:0}} body{{font-family:'Segoe UI',sans-serif;background:#f0f4f8}}
    .header{{background:linear-gradient(135deg,#1a56db,#0e3a8c);color:white;padding:16px 32px;display:flex;align-items:center;gap:16px}}
    .logo{{font-size:24px;font-weight:700}} .logo span{{color:#60a5fa}}
    .subtitle{{font-size:13px;opacity:.8}} .badge-h{{margin-left:auto;background:rgba(255,255,255,.15);padding:4px 12px;border-radius:20px;font-size:12px}}
    .nav{{background:white;border-bottom:1px solid #e2e8f0;padding:0 32px}}
    .nav a{{display:inline-block;padding:14px 20px;font-size:14px;font-weight:500;color:#64748b;text-decoration:none;border-bottom:3px solid transparent}}
    .nav a.active,.nav a:hover{{color:#1a56db;border-bottom-color:#1a56db}}
    .main{{max-width:1400px;margin:0 auto;padding:32px}}
    .page-title{{font-size:22px;font-weight:700;margin-bottom:8px}}
    .page-subtitle{{font-size:14px;color:#64748b;margin-bottom:28px}}
    .table-container{{background:white;border-radius:12px;box-shadow:0 1px 4px rgba(0,0,0,.08);border:1px solid #e2e8f0;overflow:hidden}}
    table{{width:100%;border-collapse:collapse}}
    th{{background:#f8fafc;padding:12px 16px;text-align:left;font-size:12px;font-weight:600;color:#64748b;text-transform:uppercase;letter-spacing:.5px;border-bottom:1px solid #e2e8f0}}
    td{{padding:12px 16px;font-size:13px;border-bottom:1px solid #f1f5f9;vertical-align:top}}
    tr:last-child td{{border-bottom:none}} tr:hover td{{background:#f8fafc}}
    .badge{{display:inline-block;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600;text-transform:uppercase}}
    .badge-hospital{{background:#fef3c7;color:#92400e}} .badge-operadora{{background:#e0f2fe;color:#0369a1}}
    .badge-governo{{background:#f0fdf4;color:#166534}} .badge-outro{{background:#f1f5f9;color:#475569}}
    </style></head><body>
    <div class="header"><div><div class="logo">Doutor<span>-AI</span></div><div class="subtitle">Target Screening</div></div><div class="badge-h">v1.0</div></div>
    <div class="nav"><a href="/admin">Dashboard</a><a href="/leads">Leads</a><a href="/companies" class="active">Empresas</a><a href="/investors">Investidores</a><a href="/articles">Artigos</a></div>
    <div class="main">
    <div class="page-title">Empresas Mapeadas ({len(companies)})</div>
    <div class="page-subtitle">Hospitais, operadoras e órgãos governamentais identificados como potenciais clientes</div>
    <div class="table-container">
    <table><thead><tr><th>Nome</th><th>Tipo</th><th>Localização</th><th>Porte</th><th>Receita</th><th>Descrição</th></tr></thead>
    <tbody>{rows}</tbody></table></div></div></body></html>"""


@app.route("/investors")
def investors_page():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM investors ORDER BY updated_at DESC")
    investors = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    rows = ""
    for inv in investors:
        rows += f"""<tr>
          <td><strong>{inv['name']}</strong></td>
          <td><span class="badge badge-{inv.get('type','VC').lower()}">{inv.get('type','—')}</span></td>
          <td>{inv.get('focus') or '—'}</td>
          <td>{inv.get('city') or '—'}, {inv.get('state') or '—'}</td>
          <td>{inv.get('aum_range') or '—'}</td>
          <td style="font-size:12px;color:#64748b;max-width:250px">{(inv.get('description') or '—')[:120]}...</td>
        </tr>"""
    
    return f"""<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8">
    <title>Investidores | Doutor-AI</title>
    <style>
    * {{box-sizing:border-box;margin:0;padding:0}} body{{font-family:'Segoe UI',sans-serif;background:#f0f4f8}}
    .header{{background:linear-gradient(135deg,#1a56db,#0e3a8c);color:white;padding:16px 32px;display:flex;align-items:center;gap:16px}}
    .logo{{font-size:24px;font-weight:700}} .logo span{{color:#60a5fa}}
    .subtitle{{font-size:13px;opacity:.8}} .badge-h{{margin-left:auto;background:rgba(255,255,255,.15);padding:4px 12px;border-radius:20px;font-size:12px}}
    .nav{{background:white;border-bottom:1px solid #e2e8f0;padding:0 32px}}
    .nav a{{display:inline-block;padding:14px 20px;font-size:14px;font-weight:500;color:#64748b;text-decoration:none;border-bottom:3px solid transparent}}
    .nav a.active,.nav a:hover{{color:#1a56db;border-bottom-color:#1a56db}}
    .main{{max-width:1400px;margin:0 auto;padding:32px}}
    .page-title{{font-size:22px;font-weight:700;margin-bottom:8px}}
    .page-subtitle{{font-size:14px;color:#64748b;margin-bottom:28px}}
    .table-container{{background:white;border-radius:12px;box-shadow:0 1px 4px rgba(0,0,0,.08);border:1px solid #e2e8f0;overflow:hidden}}
    table{{width:100%;border-collapse:collapse}}
    th{{background:#f8fafc;padding:12px 16px;text-align:left;font-size:12px;font-weight:600;color:#64748b;text-transform:uppercase;letter-spacing:.5px;border-bottom:1px solid #e2e8f0}}
    td{{padding:12px 16px;font-size:13px;border-bottom:1px solid #f1f5f9;vertical-align:top}}
    tr:last-child td{{border-bottom:none}} tr:hover td{{background:#f8fafc}}
    .badge{{display:inline-block;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600;text-transform:uppercase}}
    .badge-vc{{background:#fdf4ff;color:#7e22ce}} .badge-pe{{background:#fdf4ff;color:#6d28d9}}
    .badge-cvc{{background:#fff1f2;color:#be123c}} .badge-aceleradora{{background:#f0fdfa;color:#0f766e}}
    </style></head><body>
    <div class="header"><div><div class="logo">Doutor<span>-AI</span></div><div class="subtitle">Target Screening</div></div><div class="badge-h">v1.0</div></div>
    <div class="nav"><a href="/admin">Dashboard</a><a href="/leads">Leads</a><a href="/companies">Empresas</a><a href="/investors" class="active">Investidores</a><a href="/articles">Artigos</a></div>
    <div class="main">
    <div class="page-title">Investidores Mapeados ({len(investors)})</div>
    <div class="page-subtitle">VCs, PEs e Corporate Ventures identificados como potenciais investidores</div>
    <div class="table-container">
    <table><thead><tr><th>Nome</th><th>Tipo</th><th>Foco</th><th>Localização</th><th>AUM</th><th>Descrição</th></tr></thead>
    <tbody>{rows}</tbody></table></div></div></body></html>"""


@app.route("/articles")
def articles_page():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, source, published_at, category, is_processed FROM articles ORDER BY published_at DESC")
    articles = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    rows = ""
    for a in articles:
        status = "✅ Processado" if a["is_processed"] else "⏳ Pendente"
        status_color = "#16a34a" if a["is_processed"] else "#d97706"
        rows += f"""<tr>
          <td>{a['id']}</td>
          <td><strong>{a['title']}</strong></td>
          <td>{a.get('source') or '—'}</td>
          <td>{a.get('published_at') or '—'}</td>
          <td style="font-size:12px">{a.get('category') or '—'}</td>
          <td style="color:{status_color};font-weight:600;font-size:12px">{status}</td>
        </tr>"""
    
    return f"""<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8">
    <title>Artigos | Doutor-AI</title>
    <style>
    * {{box-sizing:border-box;margin:0;padding:0}} body{{font-family:'Segoe UI',sans-serif;background:#f0f4f8}}
    .header{{background:linear-gradient(135deg,#1a56db,#0e3a8c);color:white;padding:16px 32px;display:flex;align-items:center;gap:16px}}
    .logo{{font-size:24px;font-weight:700}} .logo span{{color:#60a5fa}}
    .subtitle{{font-size:13px;opacity:.8}} .badge-h{{margin-left:auto;background:rgba(255,255,255,.15);padding:4px 12px;border-radius:20px;font-size:12px}}
    .nav{{background:white;border-bottom:1px solid #e2e8f0;padding:0 32px}}
    .nav a{{display:inline-block;padding:14px 20px;font-size:14px;font-weight:500;color:#64748b;text-decoration:none;border-bottom:3px solid transparent}}
    .nav a.active,.nav a:hover{{color:#1a56db;border-bottom-color:#1a56db}}
    .main{{max-width:1400px;margin:0 auto;padding:32px}}
    .page-title{{font-size:22px;font-weight:700;margin-bottom:8px}}
    .page-subtitle{{font-size:14px;color:#64748b;margin-bottom:28px}}
    .table-container{{background:white;border-radius:12px;box-shadow:0 1px 4px rgba(0,0,0,.08);border:1px solid #e2e8f0;overflow:hidden}}
    table{{width:100%;border-collapse:collapse}}
    th{{background:#f8fafc;padding:12px 16px;text-align:left;font-size:12px;font-weight:600;color:#64748b;text-transform:uppercase;letter-spacing:.5px;border-bottom:1px solid #e2e8f0}}
    td{{padding:12px 16px;font-size:13px;border-bottom:1px solid #f1f5f9;vertical-align:top}}
    tr:last-child td{{border-bottom:none}} tr:hover td{{background:#f8fafc}}
    </style></head><body>
    <div class="header"><div><div class="logo">Doutor<span>-AI</span></div><div class="subtitle">Target Screening</div></div><div class="badge-h">v1.0</div></div>
    <div class="nav"><a href="/admin">Dashboard</a><a href="/leads">Leads</a><a href="/companies">Empresas</a><a href="/investors">Investidores</a><a href="/articles" class="active">Artigos</a></div>
    <div class="main">
    <div class="page-title">Artigos de Notícias ({len(articles)})</div>
    <div class="page-subtitle">Notícias do setor de saúde coletadas para análise de leads</div>
    <div class="table-container">
    <table><thead><tr><th>#</th><th>Título</th><th>Fonte</th><th>Data</th><th>Categoria</th><th>Status</th></tr></thead>
    <tbody>{rows}</tbody></table></div></div></body></html>"""


# ─────────────────────────────────────────────
# API ENDPOINTS
# ─────────────────────────────────────────────

@app.route("/api/stats")
def api_stats():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as c FROM targets")
    total_leads = cursor.fetchone()["c"]
    
    cursor.execute("SELECT COUNT(*) as c FROM targets WHERE priority = 'alta'")
    high_priority = cursor.fetchone()["c"]
    
    cursor.execute("SELECT COUNT(*) as c FROM companies")
    total_companies = cursor.fetchone()["c"]
    
    cursor.execute("SELECT COUNT(*) as c FROM investors")
    total_investors = cursor.fetchone()["c"]
    
    cursor.execute("SELECT COUNT(*) as c FROM articles")
    articles_total = cursor.fetchone()["c"]
    
    cursor.execute("SELECT COUNT(*) as c FROM articles WHERE is_processed = 1")
    articles_processed = cursor.fetchone()["c"]
    
    cursor.execute("SELECT COUNT(*) as c FROM articles WHERE is_processed = 0")
    articles_pending = cursor.fetchone()["c"]
    
    cursor.execute("SELECT COUNT(*) as c FROM targets WHERE DATE(created_at) = DATE('now')")
    leads_today = cursor.fetchone()["c"]
    
    cursor.execute("""
        SELECT articles_processed, leads_generated, companies_found, investors_found, 
               status, started_at
        FROM lead_generation_runs 
        ORDER BY id DESC LIMIT 1
    """)
    last_run_row = cursor.fetchone()
    last_run = dict(last_run_row) if last_run_row else None
    
    conn.close()
    
    return jsonify({
        "total_leads": total_leads,
        "high_priority_leads": high_priority,
        "total_companies": total_companies,
        "total_investors": total_investors,
        "articles_total": articles_total,
        "articles_processed": articles_processed,
        "articles_pending": articles_pending,
        "leads_today": leads_today,
        "last_run": last_run
    })


@app.route("/api/leads")
def api_leads():
    limit = request.args.get("limit", 50, type=int)
    lead_type = request.args.get("type", None)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT t.*, 
               CASE WHEN t.entity_type = 'company' THEN c.type ELSE i.type END as entity_type_display
        FROM targets t
        LEFT JOIN companies c ON t.entity_type = 'company' AND t.entity_id = c.id
        LEFT JOIN investors i ON t.entity_type = 'investor' AND t.entity_id = i.id
    """
    
    params = []
    if lead_type:
        query += " WHERE t.lead_type = ?"
        params.append(lead_type)
    
    query += " ORDER BY t.score DESC, t.created_at DESC LIMIT ?"
    params.append(limit)
    
    cursor.execute(query, params)
    leads = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify({"leads": leads, "total": len(leads)})


@app.route("/api/generate-leads", methods=["POST"])
def api_generate_leads():
    global execution_state
    
    if execution_state["running"]:
        return jsonify({"success": False, "error": "Já existe uma execução em andamento"}), 409
    
    execution_state["running"] = True
    execution_state["progress"] = "Iniciando..."
    
    try:
        stats = process_articles(max_articles=20)
        execution_state["last_result"] = stats
        execution_state["running"] = False
        
        return jsonify({
            "success": True,
            "stats": {
                "articles_processed": stats["articles_processed"],
                "leads_generated": stats["leads_generated"],
                "companies_found": stats["companies_found"],
                "investors_found": stats["investors_found"],
                "errors": len(stats.get("errors", []))
            }
        })
    except Exception as e:
        execution_state["running"] = False
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/companies")
def api_companies():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM companies ORDER BY updated_at DESC")
    companies = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({"companies": companies, "total": len(companies)})


@app.route("/api/investors")
def api_investors():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM investors ORDER BY updated_at DESC")
    investors = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({"investors": investors, "total": len(investors)})


# ─────────────────────────────────────────────
# INICIALIZAÇÃO
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("Inicializando banco de dados...")
    init_db()
    seed_articles()
    print("Servidor iniciando na porta 3000...")
    app.run(host="0.0.0.0", port=3000, debug=False)
