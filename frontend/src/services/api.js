/**
 * frontend/src/services/api.js
 * Centralized API client connecting to FastAPI backend.
 * No MySQL credentials or secrets are stored here.
 */

const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

export async function checkHealth() {
  const resp = await fetch(`${API_BASE}/health`);
  if (!resp.ok) throw new Error(`Health check failed: ${resp.statusText}`);
  return await resp.json();
}

export async function getEnergySummary() {
  const resp = await fetch(`${API_BASE}/energy/summary`);
  if (!resp.ok) throw new Error(`Failed to fetch summary: ${resp.statusText}`);
  return await resp.json();
}

export async function getEnergyHistory(limit = 100, forChart = false) {
  const resp = await fetch(`${API_BASE}/energy/history?limit=${limit}&for_chart=${forChart}`);
  if (!resp.ok) throw new Error(`Failed to fetch history: ${resp.statusText}`);
  return await resp.json();
}

export async function predictEnergy(features) {
  const resp = await fetch(`${API_BASE}/predict`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(features)
  });
  if (!resp.ok) {
    const errorData = await resp.json().catch(() => ({}));
    throw new Error(errorData.detail || `Prediction failed (${resp.status})`);
  }
  return await resp.json();
}

export async function optimizeEnergy(payload) {
  const resp = await fetch(`${API_BASE}/optimize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!resp.ok) {
    const errorData = await resp.json().catch(() => ({}));
    throw new Error(errorData.detail || `Optimization failed (${resp.status})`);
  }
  return await resp.json();
}

export async function getPredictions(limit = 10) {
  const resp = await fetch(`${API_BASE}/predictions?limit=${limit}`);
  if (!resp.ok) throw new Error(`Failed to fetch predictions: ${resp.statusText}`);
  return await resp.json();
}

export async function getOptimizationResults(limit = 10) {
  const resp = await fetch(`${API_BASE}/optimization-results?limit=${limit}`);
  if (!resp.ok) throw new Error(`Failed to fetch optimization history: ${resp.statusText}`);
  return await resp.json();
}

export async function runWhatIf(payload) {
  const resp = await fetch(`${API_BASE}/what-if`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!resp.ok) {
    const errorData = await resp.json().catch(() => ({}));
    throw new Error(errorData.detail || `What-if simulation failed (${resp.status})`);
  }
  return await resp.json();
}

