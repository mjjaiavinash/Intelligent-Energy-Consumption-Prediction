import React from 'react';
import { Lightbulb, ArrowRight, ShieldCheck, AlertCircle } from 'lucide-react';

export default function RecommendationCard({ optimization }) {
  if (!optimization || !optimization.recommendation) {
    return null;
  }

  const isPeak = optimization.status === 'PEAK';
  const isHigh = optimization.status === 'HIGH';

  const borderColor = isPeak ? 'rgba(244, 63, 94, 0.4)' : (isHigh ? 'rgba(245, 158, 11, 0.4)' : 'rgba(16, 185, 129, 0.4)');
  const bgGlow = isPeak ? 'rgba(244, 63, 94, 0.08)' : (isHigh ? 'rgba(245, 158, 11, 0.08)' : 'rgba(16, 185, 129, 0.08)');
  const iconColor = isPeak ? '#fb7185' : (isHigh ? '#fbbf24' : '#34d399');

  return (
    <div
      className="glass-panel"
      style={{
        padding: '24px',
        marginBottom: '24px',
        border: `1px solid ${borderColor}`,
        background: bgGlow
      }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '16px' }}>
        <div style={{
          width: '44px',
          height: '44px',
          borderRadius: '12px',
          background: 'rgba(255, 255, 255, 0.08)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: iconColor,
          flexShrink: 0
        }}>
          <Lightbulb size={24} />
        </div>

        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px', flexWrap: 'wrap' }}>
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#ffffff' }}>
              Actionable AI Energy Recommendation
            </h3>
            <span style={{
              fontSize: '0.78rem',
              fontWeight: 700,
              padding: '2px 8px',
              borderRadius: '6px',
              background: 'rgba(255, 255, 255, 0.08)',
              color: iconColor
            }}>
              Tier: {optimization.status}
            </span>
            {optimization.potential_saving > 0 && (
              <span style={{
                fontSize: '0.78rem',
                fontWeight: 600,
                color: '#34d399',
                background: 'rgba(16, 185, 129, 0.12)',
                padding: '2px 8px',
                borderRadius: '6px'
              }}>
                Potential Saving: {optimization.potential_saving.toFixed(2)} kWh ({optimization.saving_percentage}%)
              </span>
            )}
          </div>

          <p style={{ fontSize: '0.96rem', color: '#e2e8f0', lineHeight: 1.6 }}>
            {optimization.recommendation}
          </p>
        </div>
      </div>
    </div>
  );
}
