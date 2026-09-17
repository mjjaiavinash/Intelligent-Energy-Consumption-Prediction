import React, { useState } from 'react';
import { Cpu, Play, Database, CheckCircle2, AlertCircle } from 'lucide-react';
import { predictEnergy } from '../services/api';

export default function PredictionPanel({
  latestRecord,
  onPredictionSuccess,
  onRunOptimization
}) {
  const [formData, setFormData] = useState({
    hour: 18,
    day: 26,
    day_of_week: 4,  // Friday
    month: 11,       // November
    weekend: 0,
    lag_1h_kwh: 2.15,
    lag_24h_kwh: 1.95,
    rolling_mean_24h_kwh: 1.45
  });

  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleInputChange = (field, val) => {
    setFormData((prev) => ({
      ...prev,
      [field]: parseFloat(val) || 0
    }));
  };

  // Populate form with latest row from MySQL
  const handleAutoFill = () => {
    if (latestRecord) {
      setFormData({
        hour: latestRecord.hour ?? 18,
        day: latestRecord.day ?? 26,
        day_of_week: latestRecord.day_of_week ?? 4,
        month: latestRecord.month ?? 11,
        weekend: latestRecord.weekend ? 1 : 0,
        lag_1h_kwh: parseFloat(latestRecord.lag_1h_kwh) || 1.65,
        lag_24h_kwh: parseFloat(latestRecord.lag_24h_kwh) || 1.72,
        rolling_mean_24h_kwh: parseFloat(latestRecord.rolling_mean_24h_kwh) || 1.15
      });
      setError(null);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      const payload = {
        hour: parseInt(formData.hour, 10),
        day: parseInt(formData.day, 10),
        day_of_week: parseInt(formData.day_of_week, 10),
        month: parseInt(formData.month, 10),
        weekend: parseInt(formData.weekend, 10),
        lag_1h_kwh: parseFloat(formData.lag_1h_kwh),
        lag_24h_kwh: parseFloat(formData.lag_24h_kwh),
        rolling_mean_24h_kwh: parseFloat(formData.rolling_mean_24h_kwh)
      };

      const res = await predictEnergy(payload);
      setResult(res);
      if (onPredictionSuccess) {
        onPredictionSuccess(res, payload);
      }
    } catch (err) {
      setError(err.message || 'Prediction failed. Verify API connection.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="glass-panel" style={{ padding: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{
            width: '36px',
            height: '36px',
            borderRadius: '8px',
            background: 'rgba(59, 130, 246, 0.15)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#3b82f6'
          }}>
            <Cpu size={20} />
          </div>
          <div>
            <h2 style={{ fontSize: '1.2rem', fontWeight: 700, color: '#ffffff' }}>
              Next-Hour Energy Prediction
            </h2>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
              Feature-level prediction using the trained XGBoost model
            </p>
          </div>
        </div>

        {latestRecord && (
          <button
            type="button"
            onClick={handleAutoFill}
            className="btn-secondary"
            style={{ fontSize: '0.82rem', padding: '6px 12px' }}
            title="Load values from latest MySQL smart-meter reading"
          >
            <Database size={14} />
            <span>Load Latest DB Values</span>
          </button>
        )}
      </div>

      <form onSubmit={handleSubmit}>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
          gap: '12px',
          marginBottom: '20px'
        }}>
          <div>
            <label style={{ fontSize: '0.78rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
              Hour (0-23)
            </label>
            <input
              type="number"
              min="0"
              max="23"
              className="input-field"
              value={formData.hour}
              onChange={(e) => handleInputChange('hour', e.target.value)}
              required
            />
          </div>

          <div>
            <label style={{ fontSize: '0.78rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
              Day of Month (1-31)
            </label>
            <input
              type="number"
              min="1"
              max="31"
              className="input-field"
              value={formData.day}
              onChange={(e) => handleInputChange('day', e.target.value)}
              required
            />
          </div>

          <div>
            <label style={{ fontSize: '0.78rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
              Day of Week (0-6)
            </label>
            <select
              className="input-field"
              value={formData.day_of_week}
              onChange={(e) => {
                const dow = parseInt(e.target.value, 10);
                setFormData(p => ({
                  ...p,
                  day_of_week: dow,
                  weekend: dow in [5, 6] ? 1 : 0
                }));
              }}
            >
              <option value="0">0 - Monday</option>
              <option value="1">1 - Tuesday</option>
              <option value="2">2 - Wednesday</option>
              <option value="3">3 - Thursday</option>
              <option value="4">4 - Friday</option>
              <option value="5">5 - Saturday</option>
              <option value="6">6 - Sunday</option>
            </select>
          </div>

          <div>
            <label style={{ fontSize: '0.78rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
              Month (1-12)
            </label>
            <input
              type="number"
              min="1"
              max="12"
              className="input-field"
              value={formData.month}
              onChange={(e) => handleInputChange('month', e.target.value)}
              required
            />
          </div>

          <div>
            <label style={{ fontSize: '0.78rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
              Weekend (0 or 1)
            </label>
            <select
              className="input-field"
              value={formData.weekend}
              onChange={(e) => handleInputChange('weekend', e.target.value)}
            >
              <option value="0">0 - Weekday</option>
              <option value="1">1 - Weekend</option>
            </select>
          </div>

          <div>
            <label style={{ fontSize: '0.78rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
              Lag 1h (kWh)
            </label>
            <input
              type="number"
              step="0.01"
              min="0"
              className="input-field"
              value={formData.lag_1h_kwh}
              onChange={(e) => handleInputChange('lag_1h_kwh', e.target.value)}
              required
            />
          </div>

          <div>
            <label style={{ fontSize: '0.78rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
              Lag 24h (kWh)
            </label>
            <input
              type="number"
              step="0.01"
              min="0"
              className="input-field"
              value={formData.lag_24h_kwh}
              onChange={(e) => handleInputChange('lag_24h_kwh', e.target.value)}
              required
            />
          </div>

          <div>
            <label style={{ fontSize: '0.78rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
              Rolling Mean 24h
            </label>
            <input
              type="number"
              step="0.01"
              min="0"
              className="input-field"
              value={formData.rolling_mean_24h_kwh}
              onChange={(e) => handleInputChange('rolling_mean_24h_kwh', e.target.value)}
              required
            />
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
          <button
            type="submit"
            disabled={isLoading}
            className="btn-primary"
          >
            {isLoading ? (
              <>
                <div className="spinner" />
                <span>Running XGBoost Model...</span>
              </>
            ) : (
              <>
                <Play size={16} />
                <span>Run Prediction</span>
              </>
            )}
          </button>
        </div>
      </form>

      {/* Error Banner */}
      {error && (
        <div style={{
          marginTop: '16px',
          padding: '12px 16px',
          background: 'rgba(239, 68, 68, 0.15)',
          border: '1px solid rgba(239, 68, 68, 0.4)',
          borderRadius: '10px',
          color: '#fca5a5',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          fontSize: '0.88rem'
        }}>
          <AlertCircle size={18} color="#ef4444" />
          <span>{error}</span>
        </div>
      )}

      {/* Prediction Output Card */}
      {result && (
        <div style={{
          marginTop: '18px',
          padding: '18px',
          background: 'rgba(6, 182, 212, 0.08)',
          border: '1px solid rgba(6, 182, 212, 0.3)',
          borderRadius: '12px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '16px'
        }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
              <CheckCircle2 size={18} color="#06b6d4" />
              <span style={{ fontSize: '0.85rem', color: '#67e8f9', fontWeight: 600 }}>
                Status: {result.status}
              </span>
              <span style={{
                fontSize: '0.75rem',
                background: 'rgba(255, 255, 255, 0.1)',
                padding: '2px 8px',
                borderRadius: '6px',
                color: '#e2e8f0'
              }}>
                Model: {result.model_name}
              </span>
            </div>

            <div style={{ fontSize: '1.65rem', fontWeight: 800, color: '#ffffff' }}>
              Predicted Energy: <span style={{ color: '#38bdf8' }}>{result.predicted_energy_kwh.toFixed(3)} kWh</span>
            </div>
          </div>

          <button
            type="button"
            onClick={() => onRunOptimization && onRunOptimization(result.predicted_energy_kwh, formData)}
            className="btn-primary"
            style={{ background: 'linear-gradient(135deg, #10b981, #06b6d4)' }}
          >
            <span>Run Energy Optimization →</span>
          </button>
        </div>
      )}
    </div>
  );
}
