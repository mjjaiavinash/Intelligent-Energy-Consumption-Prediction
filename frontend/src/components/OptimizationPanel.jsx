import React, { useState, useEffect } from 'react';
import { Sliders, Sparkles, TrendingDown, Percent, Info, AlertTriangle, CheckCircle, ShieldAlert } from 'lucide-react';
import { optimizeEnergy } from '../services/api';

export default function OptimizationPanel({
  predictedConsumption,
  predictionContext,
  onOptimizationSuccess
}) {
  const [targetPred, setTargetPred] = useState(
    predictedConsumption !== undefined && predictedConsumption !== null ? predictedConsumption : ''
  );
  const [hour, setHour] = useState(predictionContext?.hour ?? 18);
  const [dayOfWeek, setDayOfWeek] = useState(predictionContext?.day_of_week ?? 4);
  const [weekend, setWeekend] = useState(predictionContext?.weekend ?? 0);

  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  // Sync with prediction updates
  useEffect(() => {
    if (predictedConsumption !== undefined && predictedConsumption !== null) {
      setTargetPred(predictedConsumption);
    }
    if (predictionContext) {
      if (predictionContext.hour !== undefined) setHour(predictionContext.hour);
      if (predictionContext.day_of_week !== undefined) setDayOfWeek(predictionContext.day_of_week);
      if (predictionContext.weekend !== undefined) setWeekend(predictionContext.weekend);
    }
  }, [predictedConsumption, predictionContext]);

  const handleOptimize = async (e) => {
    if (e) e.preventDefault();
    if (targetPred === '' || isNaN(parseFloat(targetPred))) {
      setError('Please provide a valid predicted energy consumption value or run a prediction first.');
      return;
    }
    setIsLoading(true);
    setError(null);

    try {
      const payload = {
        predicted_consumption: parseFloat(targetPred),
        hour: parseInt(hour, 10),
        day_of_week: parseInt(dayOfWeek, 10),
        weekend: parseInt(weekend, 10)
      };

      const res = await optimizeEnergy(payload);
      setResult(res);
      if (onOptimizationSuccess) {
        onOptimizationSuccess(res);
      }
    } catch (err) {
      setError(err.message || 'Optimization request failed.');
    } finally {
      setIsLoading(false);
    }
  };

  const renderStatusBadge = (status) => {
    const s = (status || '').toUpperCase();
    if (s === 'NORMAL') {
      return (
        <div className="badge-normal">
          <CheckCircle size={14} />
          <span>NORMAL CONSUMPTION</span>
        </div>
      );
    } else if (s === 'HIGH') {
      return (
        <div className="badge-high">
          <AlertTriangle size={14} />
          <span>HIGH CONSUMPTION</span>
        </div>
      );
    } else if (s === 'PEAK') {
      return (
        <div className="badge-peak">
          <ShieldAlert size={14} />
          <span>PEAK SURGE DETECTED</span>
        </div>
      );
    }
    return <span className="badge-normal">{status}</span>;
  };

  return (
    <div className="glass-panel" style={{ padding: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{
            width: '36px',
            height: '36px',
            borderRadius: '8px',
            background: 'rgba(16, 185, 129, 0.15)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#10b981'
          }}>
            <Sliders size={20} />
          </div>
          <div>
            <h2 style={{ fontSize: '1.2rem', fontWeight: 700, color: '#ffffff' }}>
              Data-Driven Energy Optimization Engine
            </h2>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
              Compares predicted consumption against historical MySQL smart-meter baselines
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={handleOptimize}
          disabled={isLoading}
          className="btn-primary"
          style={{ background: 'linear-gradient(135deg, #10b981, #06b6d4)' }}
        >
          {isLoading ? <div className="spinner" /> : <Sparkles size={16} />}
          <span>{isLoading ? 'Optimizing...' : 'Calculate Optimization'}</span>
        </button>
      </div>

      {/* Input parameters row */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
        gap: '12px',
        padding: '14px',
        background: 'rgba(255, 255, 255, 0.03)',
        borderRadius: '10px',
        marginBottom: '18px'
      }}>
        <div>
          <label style={{ fontSize: '0.78rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
            Target Prediction (kWh)
          </label>
          <input
            type="number"
            step="0.001"
            min="0"
            className="input-field"
            placeholder="Run prediction or enter kWh..."
            value={targetPred}
            onChange={(e) => setTargetPred(e.target.value)}
          />
        </div>

        <div>
          <label style={{ fontSize: '0.78rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
            Target Hour (0-23)
          </label>
          <input
            type="number"
            min="0"
            max="23"
            className="input-field"
            value={hour}
            onChange={(e) => setHour(e.target.value)}
          />
        </div>

        <div>
          <label style={{ fontSize: '0.78rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
            Day of Week
          </label>
          <select
            className="input-field"
            value={dayOfWeek}
            onChange={(e) => {
              const d = parseInt(e.target.value, 10);
              setDayOfWeek(d);
              setWeekend(d in [5, 6] ? 1 : 0);
            }}
          >
            <option value="0">Monday</option>
            <option value="1">Tuesday</option>
            <option value="2">Wednesday</option>
            <option value="3">Thursday</option>
            <option value="4">Friday</option>
            <option value="5">Saturday</option>
            <option value="6">Sunday</option>
          </select>
        </div>

        <div>
          <label style={{ fontSize: '0.78rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
            Day Type
          </label>
          <select
            className="input-field"
            value={weekend}
            onChange={(e) => setWeekend(e.target.value)}
          >
            <option value="0">Weekday</option>
            <option value="1">Weekend</option>
          </select>
        </div>
      </div>

      {error && (
        <div style={{
          padding: '12px 16px',
          background: 'rgba(239, 68, 68, 0.15)',
          border: '1px solid rgba(239, 68, 68, 0.4)',
          borderRadius: '10px',
          color: '#fca5a5',
          fontSize: '0.88rem',
          marginBottom: '16px'
        }}>
          {error}
        </div>
      )}

      {/* Optimization Results Cards */}
      {result && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
            <span style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-muted)' }}>
              Optimization Metrics & Analysis
            </span>
            {renderStatusBadge(result.status)}
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
            gap: '14px',
            marginBottom: '18px'
          }}>
            <div style={{ padding: '16px', background: 'rgba(255, 255, 255, 0.04)', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Historical Baseline</div>
              <div style={{ fontSize: '1.45rem', fontWeight: 800, color: '#34d399' }}>
                {result.baseline_consumption.toFixed(3)} <span style={{ fontSize: '0.85rem' }}>kWh</span>
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '2px' }}>
                MySQL smart-meter mean
              </div>
            </div>

            <div style={{ padding: '16px', background: 'rgba(255, 255, 255, 0.04)', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Predicted Consumption</div>
              <div style={{ fontSize: '1.45rem', fontWeight: 800, color: '#38bdf8' }}>
                {result.predicted_consumption.toFixed(3)} <span style={{ fontSize: '0.85rem' }}>kWh</span>
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '2px' }}>
                Model forecast
              </div>
            </div>

            <div style={{ padding: '16px', background: 'rgba(255, 255, 255, 0.04)', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Excess Above Baseline</div>
              <div style={{ fontSize: '1.45rem', fontWeight: 800, color: result.excess_consumption > 0 ? '#fb7185' : '#34d399' }}>
                {result.excess_consumption.toFixed(3)} <span style={{ fontSize: '0.85rem' }}>kWh</span>
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '2px' }}>
                max(predicted - baseline, 0)
              </div>
            </div>

            <div style={{ padding: '16px', background: 'rgba(255, 255, 255, 0.04)', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Potential Saving</div>
              <div style={{ fontSize: '1.45rem', fontWeight: 800, color: '#fbbf24' }}>
                {result.potential_saving.toFixed(3)} <span style={{ fontSize: '0.85rem' }}>kWh ({result.saving_percentage}%)</span>
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '2px' }}>
                Conservative projected reduction
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
