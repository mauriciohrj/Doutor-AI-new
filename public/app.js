import { DEFAULT_WEIGHTS, computeMatchScore } from '../src/matching.js';
import {
  loadConfig,
  saveConfig,
  recordJustification,
  loadJustifications,
  recordAudit,
  loadAudit,
} from '../src/storage.js';

const sampleStartup = {
  id: 'startup-102',
  stage: 'Seed',
  ticketSize: 800000,
  sectors: ['Health', 'AI'],
  thesis: ['IA aplicada', 'Saúde digital'],
  geography: 'Brasil',
  relationshipStrength: 0.7,
};

const sampleInvestor = {
  id: 'investor-42',
  preferredStages: ['Seed', 'Series A'],
  ticketRange: { min: 500000, max: 1500000 },
  sectors: ['AI', 'Fintech', 'Health'],
  theses: ['Saúde digital', 'Automação'],
  geographies: ['Brasil', 'LatAm'],
};

const state = {
  userId: 'usuario-demo',
  config: loadConfig({ weights: DEFAULT_WEIGHTS }),
};

const form = document.querySelector('[data-config-form]');
const userInput = document.querySelector('[data-user-id]');
const resultScore = document.querySelector('[data-score]');
const resultReasons = document.querySelector('[data-reasons]');
const historyList = document.querySelector('[data-justifications]');
const auditList = document.querySelector('[data-audit]');

function renderWeights() {
  Object.entries(state.config.weights).forEach(([key, value]) => {
    const input = form.querySelector(`[name="${key}"]`);
    if (input) {
      input.value = value;
    }
  });
}

function renderHistory() {
  const history = loadJustifications();
  historyList.innerHTML = history
    .map(
      (entry) =>
        `<li><strong>${entry.score}</strong> — ${entry.justifications.join(
          ' • '
        )} <em>(${entry.timestamp})</em></li>`
    )
    .join('');
}

function renderAudit() {
  const history = loadAudit();
  auditList.innerHTML = history
    .map(
      (entry) =>
        `<li><strong>${entry.userId}</strong> ajustou pesos: ${entry.changes.join(
          ', '
        )} <em>(${entry.timestamp})</em></li>`
    )
    .join('');
}

function updateScore() {
  const match = computeMatchScore({
    startup: sampleStartup,
    investor: sampleInvestor,
    weights: state.config.weights,
  });

  resultScore.textContent = match.score;
  resultReasons.innerHTML = match.justifications
    .map((reason) => `<li>${reason}</li>`)
    .join('');

  recordJustification({
    matchId: `${sampleStartup.id}-${sampleInvestor.id}`,
    score: match.score,
    justifications: match.justifications,
    criteriaScores: match.criteriaScores,
    timestamp: new Date().toLocaleString('pt-BR'),
  });
  renderHistory();
}

form.addEventListener('submit', (event) => {
  event.preventDefault();
  const formData = new FormData(form);
  const updatedWeights = { ...state.config.weights };
  const changes = [];

  for (const [key, value] of formData.entries()) {
    if (key === 'userId') {
      continue;
    }
    const numericValue = Number(value);
    if (!Number.isNaN(numericValue)) {
      if (updatedWeights[key] !== numericValue) {
        changes.push(`${key}: ${updatedWeights[key]} → ${numericValue}`);
      }
      updatedWeights[key] = numericValue;
    }
  }

  state.userId = userInput.value.trim() || state.userId;
  state.config = { ...state.config, weights: updatedWeights };
  saveConfig(state.config);

  if (changes.length > 0) {
    recordAudit({
      userId: state.userId,
      changes,
      timestamp: new Date().toLocaleString('pt-BR'),
    });
  }

  updateScore();
  renderAudit();
});

userInput.value = state.userId;
renderWeights();
renderHistory();
renderAudit();
updateScore();
