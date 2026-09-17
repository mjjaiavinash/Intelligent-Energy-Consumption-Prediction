import React from 'react';
import { Activity, Flame, TrendingUp, DollarSign, Clock, ShieldCheck } from 'lucide-react';

export default function KpiCards({ summary, latestPrediction, latestOptimization, isLoading }) {
  // Use dynamically retrieved values
  const avgConsumption = summary?.average_consumption !== undefined 
    ? `${summary.average_consumption.toFixed(3)} kWh` 
    : (isLoading ? 'Loading...' : 'N/A');
    
  const peakConsumption = summary?.peak_consumption !== undefined 
    ? `${summary.peak_consumption.toFixed(3)} kWh` 
    : (isLoading ? 'Loading...' : 'N/A');
  
  // Latest or predicted consumption
  const displayConsumption = latestPrediction?.predicted_energy_kwh !== undefined
    ? `${latestPrediction.predicted_energy_kwh.toFixed(3)} kWh`
    : (summary?.latest_consumption !== undefined 
        ? `${summary.latest_consumption.toFixed(3)} kWh` 
        : (isLoading ? 'Loading...' : 'N/A'));
    
  const consumptionLabel = latestPrediction?.predicted_energy_kwh !== undefined
    ? 'Latest Predicted Consumption'
    : 'Latest Recorded Consumption';

  // Potential saving
  const potentialSaving = latestOptimization?.potential_saving !== undefined
    ? `${latestOptimization.potential_saving.toFixed(3)} kWh (${latestOptimization.saving_percentage}%)`
    : (summary?.average_potential_saving !== undefined && summary.average_potential_saving > 0
        ? `${summary.average_potential_saving.toFixed(3)} kWh`
        : (isLoading ? 'Loading...' : 'N/A'));

  const cards = [
    {
      title: 'Average Consumption',
      value: avgConsumption,
      subtitle: summary?.total_records 
        ? `Across ${summary.total_records.toLocaleString()} records` 
        : (isLoading ? 'Loading records...' : 'Dataset records: N/A'),
      icon: Activity,
      color: '#3b82f6',
      gradient: 'linear-gradient(135deg, rgba(59, 130, 246, 0.15), rgba(6, 182, 212, 0.05))',
      borderGlow: 'rgba(59, 130, 246, 0.3)'
    },
    {
      title: consumptionLabel,
      value: displayConsumption,
      subtitle: latestPrediction?.model_name 
        ? `Model: ${latestPrediction.model_name}` 
        : (summary?.latest_timestamp ? `Recorded at ${summary.latest_timestamp.slice(0, 16)}` : 'Awaiting data'),
      icon: Clock,
      color: '#06b6d4',
      gradient: 'linear-gradient(135deg, rgba(6, 182, 212, 0.15), rgba(16, 185, 129, 0.05))',
      borderGlow: 'rgba(6, 182, 212, 0.3)'
    },
    {
      title: 'Peak Consumption',
      value: peakConsumption,
      subtitle: 'Maximum recorded surge',
      icon: Flame,
      color: '#f43f5e',
      gradient: 'linear-gradient(135deg, rgba(244, 63, 94, 0.15), rgba(245, 158, 11, 0.05))',
      borderGlow: 'rgba(244, 63, 94, 0.3)'
    },
    {
      title: 'Potential Saving',
      value: potentialSaving,
      subtitle: latestOptimization?.status ? `Status: ${latestOptimization.status}` : 'Data-driven optimization',
      icon: TrendingUp,
      color: '#10b981',
      gradient: 'linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(59, 130, 246, 0.05))',
      borderGlow: 'rgba(16, 185, 129, 0.3)'
    }
  ];

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
      gap: '20px',
      marginBottom: '24px'
    }}>
      {cards.map((card, idx) => {
        const Icon = card.icon;
        return (
          <div
            key={idx}
            className="glass-panel"
            style={{
              padding: '22px',
              background: card.gradient,
              border: `1px solid ${card.borderGlow}`,
              position: 'relative',
              overflow: 'hidden'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '14px' }}>
              <span style={{ fontSize: '0.88rem', fontWeight: 600, color: 'var(--text-muted)' }}>
                {card.title}
              </span>
              <div style={{
                width: '38px',
                height: '38px',
                borderRadius: '10px',
                background: 'rgba(255, 255, 255, 0.08)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: card.color
              }}>
                <Icon size={20} />
              </div>
            </div>

            <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#ffffff', letterSpacing: '-0.02em', marginBottom: '4px' }}>
              {isLoading ? <div className="spinner" style={{ width: '22px', height: '22px' }} /> : card.value}
            </div>

            <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)', fontWeight: 500 }}>
              {card.subtitle}
            </div>
          </div>
        );
      })}
    </div>
  );
}
