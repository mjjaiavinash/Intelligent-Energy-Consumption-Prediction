import React, { useState } from 'react';
import {
  GitCompare,
  Play,
  RotateCcw,
  Sparkles,
  TrendingDown,
  TrendingUp,
  CheckCircle,
  AlertTriangle,
  ShieldAlert,
  Info,
  Database,
  ArrowRight,
  Activity
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  Cell
} from 'recharts';
import { runWhatIf } from '../services/api';

const DEFAULT_BASE = {
  hour: 18,
  day: 26,
  day_of_week: 4,
  month: 11,
  weekend: 0,
  lag_1h_kwh: 1.6593,
  lag_24h_kwh: 1.5735,
  rolling_mean_24h_kwh: 1.7259
};

const DEFAULT_SCENARIO = {
  hour: 19,
  day: 26,
  day_of_week: 4,
  month: 11,
  weekend: 0,
  lag_1h_kwh: 1.4000,
  lag_24h_kwh: 1.5000,
  rolling_mean_24h_kwh: 1.6000
};

export default function WhatIfSimulator({ latestRecord }) {
  const [baseForm, setBaseForm] = useState(DEFAULT_BASE);
  const [scenarioForm, setScenarioForm] = useState(DEFAULT_SCENARIO);
  const [result, setResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleBaseChange = (field, val) => {
    setBaseForm((prev) => ({ ...prev, [field]: val }));
  };

  const handleScenarioChange = (field, val) => {
    setScenarioForm((prev) => ({ ...prev, [field]: val }));
  };

  const handleUseLatestData = () => {
    if (!latestRecord) return;
    const updated = {
      hour: latestRecord.hour ?? DEFAULT_BASE.hour,
      day: latestRecord.day ?? DEFAULT_BASE.day,
      day_of_week: latestRecord.day_of_week ?? DEFAULT_BASE.day_of_week,
      month: latestRecord.month ?? DEFAULT_BASE.month,
      weekend: latestRecord.weekend ? 1 : 0,
      lag_1h_kwh: parseFloat(latestRecord.lag_1h_kwh ?? DEFAULT_BASE.lag_1h_kwh),
      lag_24h_kwh: parseFloat(latestRecord.lag_24h_kwh ?? DEFAULT_BASE.lag_24h_kwh),
      rolling_mean_24h_kwh: parseFloat(latestRecord.rolling_mean_24h_kwh ?? DEFAULT_BASE.rolling_mean_24h_kwh)
    };
    setBaseForm(updated);
  };

  const applyPreset = (type) => {
    if (type === 'peak_shift') {
      // Shift hour from peak evening to off-peak afternoon or night
      setScenarioForm({
        ...baseForm,
        hour: (baseForm.hour >= 4 ? baseForm.hour - 4 : (baseForm.hour + 8) % 24)
      });
    } else if (type === 'efficiency') {
      // Reduce lags by 20%
      setScenarioForm({
        ...baseForm,
        lag_1h_kwh: Number((baseForm.lag_1h_kwh * 0.8).toFixed(4)),
        lag_24h_kwh: Number((baseForm.lag_24h_kwh * 0.8).toFixed(4)),
        rolling_mean_24h_kwh: Number((baseForm.rolling_mean_24h_kwh * 0.85).toFixed(4))
      });
    } else if (type === 'surge') {
      // High peak scenario
      setScenarioForm({
        ...baseForm,
        hour: 20,
        lag_1h_kwh: Number((baseForm.lag_1h_kwh * 1.5).toFixed(4)),
        lag_24h_kwh: Number((baseForm.lag_24h_kwh * 1.4).toFixed(4)),
        rolling_mean_24h_kwh: Number((baseForm.rolling_mean_24h_kwh * 1.35).toFixed(4))
      });
    }
  };

  const handleReset = () => {
    setBaseForm(DEFAULT_BASE);
    setScenarioForm(DEFAULT_SCENARIO);
    setResult(null);
    setError(null);
  };

  const handleSubmit = async (e) => {
    if (e) e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      const payload = {
        base_features: {
          hour: parseInt(baseForm.hour, 10),
          day: parseInt(baseForm.day, 10),
          day_of_week: parseInt(baseForm.day_of_week, 10),
          month: parseInt(baseForm.month, 10),
          weekend: parseInt(baseForm.weekend, 10),
          lag_1h_kwh: parseFloat(baseForm.lag_1h_kwh),
          lag_24h_kwh: parseFloat(baseForm.lag_24h_kwh),
          rolling_mean_24h_kwh: parseFloat(baseForm.rolling_mean_24h_kwh)
        },
        scenario_features: {
          hour: parseInt(scenarioForm.hour, 10),
          day: parseInt(scenarioForm.day, 10),
          day_of_week: parseInt(scenarioForm.day_of_week, 10),
          month: parseInt(scenarioForm.month, 10),
          weekend: parseInt(scenarioForm.weekend, 10),
          lag_1h_kwh: parseFloat(scenarioForm.lag_1h_kwh),
          lag_24h_kwh: parseFloat(scenarioForm.lag_24h_kwh),
          rolling_mean_24h_kwh: parseFloat(scenarioForm.rolling_mean_24h_kwh)
        }
      };

      const res = await runWhatIf(payload);
      setResult(res);
    } catch (err) {
      setError(err.message || 'What-if simulation failed.');
    } finally {
      setIsLoading(false);
    }
  };

  const renderBadge = (status) => {
    const s = (status || '').toUpperCase();
    if (s === 'NORMAL') {
      return (
        <span className="badge-normal" style={{ fontSize: '0.78rem' }}>
          <CheckCircle size={12} /> NORMAL
        </span>
      );
    } else if (s === 'HIGH') {
      return (
        <span className="badge-high" style={{ fontSize: '0.78rem' }}>
          <AlertTriangle size={12} /> HIGH
        </span>
      );
    } else if (s === 'PEAK') {
      return (
        <span className="badge-peak" style={{ fontSize: '0.78rem' }}>
          <ShieldAlert size={12} /> PEAK
        </span>
      );
    }
    return <span>{status}</span>;
  };

  // Chart data preparation
  const chartData = result ? [
    {
      name: 'Base Scenario',
      predicted: result.base_prediction_kwh,
      baseline: result.base_baseline_kwh,
      status: result.base_status
    },
    {
      name: 'What-If Scenario',
      predicted: result.scenario_prediction_kwh,
      baseline: result.scenario_baseline_kwh,
      status: result.scenario_status
    }
  ] : [];

  return (
    <div className="glass-panel" style={{ padding: '28px', marginBottom: '24px' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px', marginBottom: '20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            width: '42px',
            height: '42px',
            borderRadius: '10px',
            background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(59, 130, 246, 0.2))',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#a78bfa',
            border: '1px solid rgba(139, 92, 246, 0.3)'
          }}>
            <GitCompare size={22} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <h2 style={{ fontSize: '1.3rem', fontWeight: 700, color: '#ffffff' }}>
                What-If Energy Consumption Simulation
              </h2>
              <span style={{
                background: 'rgba(139, 92, 246, 0.15)',
                color: '#c4b5fd',
                fontSize: '0.72rem',
                fontWeight: 600,
                padding: '2px 8px',
                borderRadius: '6px',
                border: '1px solid rgba(139, 92, 246, 0.3)'
              }}>
                Phase 6
              </span>
            </div>
            <p style={{ fontSize: '0.86rem', color: 'var(--text-muted)', marginTop: '2px' }}>
              Simulate operational changes, temporal shifts, and efficiency scenarios against the 8 XGBoost model features.
            </p>
          </div>
        </div>

        {/* Action buttons */}
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          {latestRecord && (
            <button
              type="button"
              onClick={handleUseLatestData}
              className="btn-secondary"
              style={{ fontSize: '0.84rem', padding: '7px 14px' }}
              title="Populate Base features from latest MySQL record"
            >
              <Database size={14} />
              Use Latest Data
            </button>
          )}
          <button
            type="button"
            onClick={handleReset}
            className="btn-secondary"
            style={{ fontSize: '0.84rem', padding: '7px 14px' }}
          >
            <RotateCcw size={14} />
            Reset
          </button>
        </div>
      </div>

      {/* Simulation Disclaimer */}
      <div style={{
        marginBottom: '18px',
        padding: '10px 14px',
        background: 'rgba(59, 130, 246, 0.08)',
        border: '1px solid rgba(59, 130, 246, 0.25)',
        borderRadius: '8px',
        display: 'flex',
        alignItems: 'center',
        gap: '10px',
        fontSize: '0.82rem',
        color: '#93c5fd'
      }}>
        <Info size={16} color="#60a5fa" style={{ flexShrink: 0 }} />
        <span>
          <strong>Note:</strong> What-If simulation explores changes in the model's supported forecasting inputs. It does not directly simulate individual appliances or guarantee real-world energy savings.
        </span>
      </div>

      {/* Quick scenario presets */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        marginBottom: '20px',
        padding: '10px 14px',
        background: 'rgba(255, 255, 255, 0.02)',
        borderRadius: '10px',
        border: '1px solid var(--border-color)',
        flexWrap: 'wrap'
      }}>
        <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '4px' }}>
          <Sparkles size={14} style={{ color: '#a78bfa' }} /> Quick Scenario Presets:
        </span>
        <button
          type="button"
          onClick={() => applyPreset('peak_shift')}
          style={{
            background: 'rgba(59, 130, 246, 0.1)',
            color: '#60a5fa',
            border: '1px solid rgba(59, 130, 246, 0.25)',
            borderRadius: '6px',
            padding: '4px 10px',
            fontSize: '0.78rem',
            cursor: 'pointer',
            fontWeight: 500
          }}
        >
          Shift Load (-4h Off-Peak)
        </button>
        <button
          type="button"
          onClick={() => applyPreset('efficiency')}
          style={{
            background: 'rgba(16, 185, 129, 0.1)',
            color: '#34d399',
            border: '1px solid rgba(16, 185, 129, 0.25)',
            borderRadius: '6px',
            padding: '4px 10px',
            fontSize: '0.78rem',
            cursor: 'pointer',
            fontWeight: 500
          }}
        >
          20% Efficiency Improvement
        </button>
        <button
          type="button"
          onClick={() => applyPreset('surge')}
          style={{
            background: 'rgba(244, 63, 94, 0.1)',
            color: '#fb7185',
            border: '1px solid rgba(244, 63, 94, 0.25)',
            borderRadius: '6px',
            padding: '4px 10px',
            fontSize: '0.78rem',
            cursor: 'pointer',
            fontWeight: 500
          }}
        >
          Peak Evening Surge (+40% Lags)
        </button>
      </div>

      {/* Two Column Input Form */}
      <form onSubmit={handleSubmit}>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))',
          gap: '20px',
          marginBottom: '20px'
        }}>
          {/* Base Scenario Column */}
          <div style={{
            background: 'rgba(255, 255, 255, 0.02)',
            padding: '18px',
            borderRadius: '12px',
            border: '1px solid rgba(255, 255, 255, 0.06)'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
              <h3 style={{ fontSize: '0.98rem', fontWeight: 700, color: '#e2e8f0', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#3b82f6' }}></span>
                Base Scenario (Baseline Features)
              </h3>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>Reference Point</span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
              <div>
                <label className="form-label">Hour of Day (0–23)</label>
                <input
                  type="number"
                  min="0"
                  max="23"
                  className="form-input"
                  value={baseForm.hour}
                  onChange={(e) => handleBaseChange('hour', e.target.value)}
                  required
                />
              </div>
              <div>
                <label className="form-label">Day of Month (1–31)</label>
                <input
                  type="number"
                  min="1"
                  max="31"
                  className="form-input"
                  value={baseForm.day}
                  onChange={(e) => handleBaseChange('day', e.target.value)}
                  required
                />
              </div>
              <div>
                <label className="form-label">Day of Week</label>
                <select
                  className="form-input"
                  value={baseForm.day_of_week}
                  onChange={(e) => {
                    const dow = parseInt(e.target.value, 10);
                    handleBaseChange('day_of_week', dow);
                    handleBaseChange('weekend', (dow === 5 || dow === 6) ? 1 : 0);
                  }}
                >
                  <option value={0}>0 - Monday</option>
                  <option value={1}>1 - Tuesday</option>
                  <option value={2}>2 - Wednesday</option>
                  <option value={3}>3 - Thursday</option>
                  <option value={4}>4 - Friday</option>
                  <option value={5}>5 - Saturday</option>
                  <option value={6}>6 - Sunday</option>
                </select>
              </div>
              <div>
                <label className="form-label">Month (1–12)</label>
                <input
                  type="number"
                  min="1"
                  max="12"
                  className="form-input"
                  value={baseForm.month}
                  onChange={(e) => handleBaseChange('month', e.target.value)}
                  required
                />
              </div>
              <div>
                <label className="form-label">Weekend Flag</label>
                <select
                  className="form-input"
                  value={baseForm.weekend}
                  onChange={(e) => handleBaseChange('weekend', parseInt(e.target.value, 10))}
                >
                  <option value={0}>0 - Weekday</option>
                  <option value={1}>1 - Weekend</option>
                </select>
              </div>
              <div>
                <label className="form-label">Lag 1h (kWh)</label>
                <input
                  type="number"
                  step="0.0001"
                  min="0"
                  className="form-input"
                  value={baseForm.lag_1h_kwh}
                  onChange={(e) => handleBaseChange('lag_1h_kwh', e.target.value)}
                  required
                />
              </div>
              <div>
                <label className="form-label">Lag 24h (kWh)</label>
                <input
                  type="number"
                  step="0.0001"
                  min="0"
                  className="form-input"
                  value={baseForm.lag_24h_kwh}
                  onChange={(e) => handleBaseChange('lag_24h_kwh', e.target.value)}
                  required
                />
              </div>
              <div>
                <label className="form-label">Rolling Mean 24h (kWh)</label>
                <input
                  type="number"
                  step="0.0001"
                  min="0"
                  className="form-input"
                  value={baseForm.rolling_mean_24h_kwh}
                  onChange={(e) => handleBaseChange('rolling_mean_24h_kwh', e.target.value)}
                  required
                />
              </div>
            </div>
          </div>

          {/* What-If Scenario Column */}
          <div style={{
            background: 'rgba(139, 92, 246, 0.03)',
            padding: '18px',
            borderRadius: '12px',
            border: '1px solid rgba(139, 92, 246, 0.15)'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
              <h3 style={{ fontSize: '0.98rem', fontWeight: 700, color: '#c4b5fd', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#8b5cf6' }}></span>
                What-If Scenario (Modified Features)
              </h3>
              <span style={{ fontSize: '0.72rem', color: '#a78bfa' }}>Exploratory Variant</span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
              <div>
                <label className="form-label">Hour of Day (0–23)</label>
                <input
                  type="number"
                  min="0"
                  max="23"
                  className="form-input"
                  value={scenarioForm.hour}
                  onChange={(e) => handleScenarioChange('hour', e.target.value)}
                  required
                />
              </div>
              <div>
                <label className="form-label">Day of Month (1–31)</label>
                <input
                  type="number"
                  min="1"
                  max="31"
                  className="form-input"
                  value={scenarioForm.day}
                  onChange={(e) => handleScenarioChange('day', e.target.value)}
                  required
                />
              </div>
              <div>
                <label className="form-label">Day of Week</label>
                <select
                  className="form-input"
                  value={scenarioForm.day_of_week}
                  onChange={(e) => {
                    const dow = parseInt(e.target.value, 10);
                    handleScenarioChange('day_of_week', dow);
                    handleScenarioChange('weekend', (dow === 5 || dow === 6) ? 1 : 0);
                  }}
                >
                  <option value={0}>0 - Monday</option>
                  <option value={1}>1 - Tuesday</option>
                  <option value={2}>2 - Wednesday</option>
                  <option value={3}>3 - Thursday</option>
                  <option value={4}>4 - Friday</option>
                  <option value={5}>5 - Saturday</option>
                  <option value={6}>6 - Sunday</option>
                </select>
              </div>
              <div>
                <label className="form-label">Month (1–12)</label>
                <input
                  type="number"
                  min="1"
                  max="12"
                  className="form-input"
                  value={scenarioForm.month}
                  onChange={(e) => handleScenarioChange('month', e.target.value)}
                  required
                />
              </div>
              <div>
                <label className="form-label">Weekend Flag</label>
                <select
                  className="form-input"
                  value={scenarioForm.weekend}
                  onChange={(e) => handleScenarioChange('weekend', parseInt(e.target.value, 10))}
                >
                  <option value={0}>0 - Weekday</option>
                  <option value={1}>1 - Weekend</option>
                </select>
              </div>
              <div>
                <label className="form-label">Lag 1h (kWh)</label>
                <input
                  type="number"
                  step="0.0001"
                  min="0"
                  className="form-input"
                  value={scenarioForm.lag_1h_kwh}
                  onChange={(e) => handleScenarioChange('lag_1h_kwh', e.target.value)}
                  required
                />
              </div>
              <div>
                <label className="form-label">Lag 24h (kWh)</label>
                <input
                  type="number"
                  step="0.0001"
                  min="0"
                  className="form-input"
                  value={scenarioForm.lag_24h_kwh}
                  onChange={(e) => handleScenarioChange('lag_24h_kwh', e.target.value)}
                  required
                />
              </div>
              <div>
                <label className="form-label">Rolling Mean 24h (kWh)</label>
                <input
                  type="number"
                  step="0.0001"
                  min="0"
                  className="form-input"
                  value={scenarioForm.rolling_mean_24h_kwh}
                  onChange={(e) => handleScenarioChange('rolling_mean_24h_kwh', e.target.value)}
                  required
                />
              </div>
            </div>
          </div>
        </div>

        {/* Submit action */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
          <button
            type="submit"
            disabled={isLoading}
            className="btn-primary"
            style={{
              padding: '12px 28px',
              fontSize: '1rem',
              background: 'linear-gradient(135deg, #8b5cf6, #3b82f6)'
            }}
          >
            {isLoading ? (
              <>
                <span className="spinner"></span>
                <span>Running Simulation...</span>
              </>
            ) : (
              <>
                <Play size={18} />
                <span>Run What-If Simulation</span>
              </>
            )}
          </button>
        </div>
      </form>

      {/* Error message */}
      {error && (
        <div style={{
          marginTop: '18px',
          padding: '14px 18px',
          borderRadius: '10px',
          background: 'rgba(244, 63, 94, 0.12)',
          border: '1px solid rgba(244, 63, 94, 0.3)',
          color: '#fb7185',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          fontSize: '0.9rem'
        }}>
          <AlertTriangle size={18} />
          <span>{error}</span>
        </div>
      )}

      {/* Simulation Results Section */}
      {result && (
        <div style={{ marginTop: '28px', borderTop: '1px solid var(--border-color)', paddingTop: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '18px' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#ffffff', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Activity size={18} style={{ color: '#8b5cf6' }} />
              Simulation Results & Comparison
            </h3>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
              Model: <strong style={{ color: '#38bdf8' }}>{result.model_name}</strong> • Ephemeral / Non-persisted
            </span>
          </div>

          {/* 6 Metric KPI Cards */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
            gap: '14px',
            marginBottom: '20px'
          }}>
            {/* Card 1: Base Prediction */}
            <div style={{
              background: 'rgba(255, 255, 255, 0.03)',
              padding: '16px',
              borderRadius: '12px',
              border: '1px solid rgba(255, 255, 255, 0.08)'
            }}>
              <span style={{ fontSize: '0.76rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                Base Prediction
              </span>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px', margin: '6px 0' }}>
                <span style={{ fontSize: '1.5rem', fontWeight: 700, color: '#ffffff' }}>
                  {result.base_prediction_kwh.toFixed(4)}
                </span>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>kWh</span>
              </div>
              <div style={{ marginTop: '4px' }}>
                {renderBadge(result.base_status)}
              </div>
            </div>

            {/* Card 2: Scenario Prediction */}
            <div style={{
              background: 'rgba(139, 92, 246, 0.05)',
              padding: '16px',
              borderRadius: '12px',
              border: '1px solid rgba(139, 92, 246, 0.25)'
            }}>
              <span style={{ fontSize: '0.76rem', color: '#c4b5fd', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                What-If Scenario
              </span>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px', margin: '6px 0' }}>
                <span style={{ fontSize: '1.5rem', fontWeight: 700, color: '#c4b5fd' }}>
                  {result.scenario_prediction_kwh.toFixed(4)}
                </span>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>kWh</span>
              </div>
              <div style={{ marginTop: '4px' }}>
                {renderBadge(result.scenario_status)}
              </div>
            </div>

            {/* Card 3: Difference */}
            <div style={{
              background: result.difference_kwh <= 0 ? 'rgba(16, 185, 129, 0.08)' : 'rgba(244, 63, 94, 0.08)',
              padding: '16px',
              borderRadius: '12px',
              border: `1px solid ${result.difference_kwh <= 0 ? 'rgba(16, 185, 129, 0.3)' : 'rgba(244, 63, 94, 0.3)'}`
            }}>
              <span style={{ fontSize: '0.76rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                Difference
              </span>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px', margin: '6px 0' }}>
                <span style={{
                  fontSize: '1.5rem',
                  fontWeight: 700,
                  color: result.difference_kwh <= 0 ? '#34d399' : '#fb7185',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px'
                }}>
                  {result.difference_kwh <= 0 ? <TrendingDown size={20} /> : <TrendingUp size={20} />}
                  {result.difference_kwh > 0 ? `+${result.difference_kwh.toFixed(4)}` : result.difference_kwh.toFixed(4)}
                </span>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>kWh</span>
              </div>
              <span style={{ fontSize: '0.74rem', color: result.difference_kwh <= 0 ? '#34d399' : '#fb7185' }}>
                {result.difference_kwh <= 0 ? 'Predicted reduction' : 'Predicted increase'}
              </span>
            </div>

            {/* Card 4: Percentage Change */}
            <div style={{
              background: result.percentage_change <= 0 ? 'rgba(16, 185, 129, 0.08)' : 'rgba(244, 63, 94, 0.08)',
              padding: '16px',
              borderRadius: '12px',
              border: `1px solid ${result.percentage_change <= 0 ? 'rgba(16, 185, 129, 0.3)' : 'rgba(244, 63, 94, 0.3)'}`
            }}>
              <span style={{ fontSize: '0.76rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                Percentage Change
              </span>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px', margin: '6px 0' }}>
                <span style={{
                  fontSize: '1.5rem',
                  fontWeight: 700,
                  color: result.percentage_change <= 0 ? '#34d399' : '#fb7185'
                }}>
                  {result.percentage_change > 0 ? `+${result.percentage_change.toFixed(2)}` : result.percentage_change.toFixed(2)}%
                </span>
              </div>
              <span style={{ fontSize: '0.74rem', color: 'var(--text-dim)' }}>
                Relative to base prediction
              </span>
            </div>

            {/* Card 5: Base Baseline */}
            <div style={{
              background: 'rgba(255, 255, 255, 0.02)',
              padding: '16px',
              borderRadius: '12px',
              border: '1px solid rgba(255, 255, 255, 0.06)'
            }}>
              <span style={{ fontSize: '0.76rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                Base Baseline
              </span>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px', margin: '6px 0' }}>
                <span style={{ fontSize: '1.4rem', fontWeight: 600, color: '#e2e8f0' }}>
                  {result.base_baseline_kwh.toFixed(4)}
                </span>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>kWh</span>
              </div>
              <span style={{ fontSize: '0.74rem', color: 'var(--text-dim)' }}>
                Hour {baseForm.hour} mean
              </span>
            </div>

            {/* Card 6: Scenario Baseline */}
            <div style={{
              background: 'rgba(255, 255, 255, 0.02)',
              padding: '16px',
              borderRadius: '12px',
              border: '1px solid rgba(255, 255, 255, 0.06)'
            }}>
              <span style={{ fontSize: '0.76rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                Scenario Baseline
              </span>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px', margin: '6px 0' }}>
                <span style={{ fontSize: '1.4rem', fontWeight: 600, color: '#e2e8f0' }}>
                  {result.scenario_baseline_kwh.toFixed(4)}
                </span>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>kWh</span>
              </div>
              <span style={{ fontSize: '0.74rem', color: 'var(--text-dim)' }}>
                Hour {scenarioForm.hour} mean
              </span>
            </div>
          </div>

          {/* Interpretation Card */}
          <div style={{
            background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.08), rgba(139, 92, 246, 0.08))',
            border: '1px solid rgba(139, 92, 246, 0.25)',
            borderRadius: '12px',
            padding: '18px',
            marginBottom: '22px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px', color: '#c4b5fd' }}>
              <Info size={16} />
              <strong style={{ fontSize: '0.92rem' }}>Exploratory Model Interpretation</strong>
            </div>
            <p style={{ color: '#e2e8f0', fontSize: '0.9rem', lineHeight: '1.6' }}>
              {result.interpretation}
            </p>
          </div>

          {/* Bar Chart Comparison */}
          <div style={{
            background: 'rgba(0, 0, 0, 0.2)',
            borderRadius: '12px',
            padding: '20px',
            border: '1px solid rgba(255, 255, 255, 0.06)'
          }}>
            <h4 style={{ fontSize: '0.92rem', fontWeight: 600, color: '#cbd5e1', marginBottom: '14px' }}>
              Side-by-Side Comparison: Predicted Consumption vs. Historical Baseline
            </h4>
            <div style={{ width: '100%', height: 260 }}>
              <ResponsiveContainer>
                <BarChart data={chartData} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.08)" />
                  <XAxis dataKey="name" stroke="#94a3b8" />
                  <YAxis stroke="#94a3b8" unit=" kWh" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'rgba(17, 24, 39, 0.95)',
                      borderColor: 'rgba(255, 255, 255, 0.15)',
                      borderRadius: '8px',
                      color: '#fff'
                    }}
                    formatter={(val) => [`${val.toFixed(4)} kWh`]}
                  />
                  <Legend />
                  <Bar dataKey="predicted" name="Predicted Energy (kWh)" fill="#8b5cf6" radius={[6, 6, 0, 0]} />
                  <Bar dataKey="baseline" name="Historical Baseline (kWh)" fill="#06b6d4" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
