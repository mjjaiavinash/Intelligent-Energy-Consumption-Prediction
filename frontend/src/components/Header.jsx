import React from 'react';
import { Zap, Activity, RefreshCw, Server } from 'lucide-react';

export default function Header({ isOnline, modelName, onRefresh, isRefreshing }) {
  return (
    <header className="glass-panel" style={{ padding: '20px 28px', marginBottom: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{
            width: '48px',
            height: '48px',
            borderRadius: '12px',
            background: 'linear-gradient(135deg, #3b82f6, #06b6d4)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 20px rgba(6, 182, 212, 0.4)'
          }}>
            <Zap size={28} color="#ffffff" />
          </div>
          <div>
            <h1 style={{ fontSize: '1.65rem', fontWeight: 800, letterSpacing: '-0.02em', color: '#ffffff' }}>
              Intelligent Energy Consumption Prediction & Optimization
            </h1>
            <p style={{ fontSize: '0.92rem', color: 'var(--text-muted)' }}>
              AI-powered energy forecasting and optimization
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {/* Backend Status Indicator */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            background: 'rgba(255, 255, 255, 0.05)',
            border: '1px solid var(--border-color)',
            padding: '7px 14px',
            borderRadius: '9999px',
            fontSize: '0.85rem'
          }}>
            <span style={{
              width: '10px',
              height: '10px',
              borderRadius: '50%',
              backgroundColor: isOnline ? '#10b981' : '#ef4444',
              boxShadow: isOnline ? '0 0 10px #10b981' : '0 0 10px #ef4444'
            }}></span>
            <span style={{ fontWeight: 600 }}>
              {isOnline ? `API Online (${modelName || 'XGBoost'})` : 'API Disconnected'}
            </span>
          </div>

          {/* Refresh Button */}
          <button
            onClick={onRefresh}
            disabled={isRefreshing}
            className="btn-secondary"
            title="Refresh dashboard data"
          >
            <RefreshCw size={16} className={isRefreshing ? 'spin' : ''} />
            <span>Refresh</span>
          </button>
        </div>
      </div>
    </header>
  );
}
