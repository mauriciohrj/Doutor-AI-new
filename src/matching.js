const DEFAULT_WEIGHTS = {
  stage: 0.2,
  ticketSize: 0.2,
  sector: 0.2,
  thesis: 0.2,
  geography: 0.1,
  history: 0.1,
};

function normalizeWeights(weights) {
  const total = Object.values(weights).reduce((sum, value) => sum + value, 0);
  if (total === 0) {
    return { ...DEFAULT_WEIGHTS };
  }

  return Object.fromEntries(
    Object.entries(weights).map(([key, value]) => [key, value / total])
  );
}

function computeCriteriaScores(startup, investor) {
  const stageMatch = investor.preferredStages.includes(startup.stage) ? 1 : 0;
  const ticketMatch =
    startup.ticketSize >= investor.ticketRange.min &&
    startup.ticketSize <= investor.ticketRange.max
      ? 1
      : 0;
  const sectorMatch =
    investor.sectors.filter((sector) => startup.sectors.includes(sector))
      .length > 0
      ? 1
      : 0;
  const thesisMatch =
    investor.theses.filter((thesis) => startup.thesis.includes(thesis)).length >
    0
      ? 1
      : 0;
  const geographyMatch =
    investor.geographies.includes(startup.geography) ? 1 : 0;
  const historyMatch = startup.relationshipStrength >= 0.6 ? 1 : 0;

  return {
    stage: stageMatch,
    ticketSize: ticketMatch,
    sector: sectorMatch,
    thesis: thesisMatch,
    geography: geographyMatch,
    history: historyMatch,
  };
}

function buildJustifications(criteriaScores, startup, investor) {
  const reasons = [];
  if (criteriaScores.stage) {
    reasons.push(`Stage compatível: ${startup.stage}`);
  }
  if (criteriaScores.ticketSize) {
    reasons.push(
      `Ticket dentro do intervalo ${investor.ticketRange.min}-${investor.ticketRange.max}`
    );
  }
  if (criteriaScores.sector) {
    reasons.push(`Setor alinhado: ${startup.sectors.join(', ')}`);
  }
  if (criteriaScores.thesis) {
    reasons.push(`Tese alinhada: ${startup.thesis.join(', ')}`);
  }
  if (criteriaScores.geography) {
    reasons.push(`Geografia compatível: ${startup.geography}`);
  }
  if (criteriaScores.history) {
    reasons.push('Histórico positivo com o investidor');
  }
  return reasons;
}

function computeMatchScore({ startup, investor, weights }) {
  const normalizedWeights = normalizeWeights(weights);
  const criteriaScores = computeCriteriaScores(startup, investor);
  const weightedScore = Object.entries(criteriaScores).reduce(
    (total, [key, value]) => total + value * (normalizedWeights[key] || 0),
    0
  );
  const justifications = buildJustifications(
    criteriaScores,
    startup,
    investor
  );

  return {
    score: Number(weightedScore.toFixed(2)),
    criteriaScores,
    weights: normalizedWeights,
    justifications,
  };
}

export { DEFAULT_WEIGHTS, computeMatchScore };
