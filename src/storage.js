const CONFIG_KEY = 'matching_config';
const JUSTIFICATIONS_KEY = 'matching_justifications';
const AUDIT_KEY = 'matching_config_audit';

function loadConfig(defaultConfig) {
  const stored = localStorage.getItem(CONFIG_KEY);
  if (!stored) {
    return defaultConfig;
  }

  try {
    return { ...defaultConfig, ...JSON.parse(stored) };
  } catch (error) {
    console.warn('Falha ao carregar configuração, usando padrão.', error);
    return defaultConfig;
  }
}

function saveConfig(config) {
  localStorage.setItem(CONFIG_KEY, JSON.stringify(config));
}

function recordJustification(entry) {
  const stored = localStorage.getItem(JUSTIFICATIONS_KEY);
  const history = stored ? JSON.parse(stored) : [];
  history.unshift(entry);
  localStorage.setItem(JUSTIFICATIONS_KEY, JSON.stringify(history.slice(0, 50)));
}

function loadJustifications() {
  const stored = localStorage.getItem(JUSTIFICATIONS_KEY);
  return stored ? JSON.parse(stored) : [];
}

function recordAudit(change) {
  const stored = localStorage.getItem(AUDIT_KEY);
  const history = stored ? JSON.parse(stored) : [];
  history.unshift(change);
  localStorage.setItem(AUDIT_KEY, JSON.stringify(history.slice(0, 50)));
}

function loadAudit() {
  const stored = localStorage.getItem(AUDIT_KEY);
  return stored ? JSON.parse(stored) : [];
}

export {
  loadConfig,
  saveConfig,
  recordJustification,
  loadJustifications,
  recordAudit,
  loadAudit,
};
