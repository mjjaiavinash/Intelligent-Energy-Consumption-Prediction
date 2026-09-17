import React, { useState } from 'react';
import {
  ResponsiveContainer,
  ComposedChart,
  Area,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
  ReferenceLine
} from 'recharts';
import { BarChart2, Calendar, ZoomIn } from 'lucide-react';

export default function EnergyChart({
  historyData,
  baselineKwh,
  predictedKwh,
  isLoading,
  onRangeChange,
  currentRange
}) {
  const [showBaseline, setShowBaseline] = useState(true);

  // Format data for Recharts
  const chartData = (historyData || []).map((item) => ({
    timestamp: item.timestamp?.slice(5, 16) || item.timestamp,
    fullTimestamp: item.timestamp,
    consumption: item.energy_consumption_kwh,
    rolling24h: item.rolling_mean_24h_kwh,
    baseline: showBaseline && baselineKwh ? baselineKwh : null
  }));

  // Custom Glassmorphic Tooltip
  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const dataPoint = payload[0].payload;
      return (
        <div style={{
          background: 'rgba(15, 23, 42, 0.92)',
          border: '1px solid rgba(255, 255, 255, 0.15)',
          borderRadius: '12px',
          padding: '12px 16px',
          boxShadow: '0 10px 25px rgba(0,0,0,0.5)',
          backdropFilter: 'blur(10px)',
          fontSize: '0.85rem'
        }}>
          <div style={{ fontWeight: 700, color: '#e2e8f0', marginBottom: '8px', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '4px' }}>
            {dataPoint.fullTimestamp || label}
          </div>
          {payload.map((entry, index) => (
            <div key={index} style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
              <span style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: entry.color }}></span>
              <span style={{ color: 'var(--text-muted)' }}>{entry.name}:</span>
              <span style={{ fontWeight: 700, color: '#ffffff' }}>
                {typeof entry.value === 'number' ? `${entry.value.toFixed(3)} kWh` : entry.value}
              </span>
            </div>
          ))}
        </div>
      );
    }
    return null;
  };

  const ranges = [
    { label: 'Last 24 Hours', value: 24 },
    { label: 'Last 48 Hours', value: 48 },
    { label: 'Last 7 Days (168h)', value: 168 },
    { label: 'Last 300 Hours', value: 300 }
  ];

  return (
    <div className="glass-panel" style={{ padding: '24px', marginBottom: '24px' }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '14px',
        marginBottom: '20px'
      }}>
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
            <BarChart2 size={20} />
          </div>
          <div>
            <h2 style={{ fontSize: '1.2rem', fontWeight: 700, color: '#ffffff' }}>
              Historical Energy Consumption & Trend
            </h2>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
              Actual smart-meter readings retrieved directly from MySQL
            </p>
          </div>
        </div>

        {/* Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
          {ranges.map((r) => (
            <button
              key={r.value}
              onClick={() => onRangeChange(r.value)}
              className={currentRange === r.value ? 'btn-primary' : 'btn-secondary'}
              style={{ padding: '6px 12px', fontSize: '0.82rem' }}
            >
              {r.label}
            </button>
          ))}

          {baselineKwh !== null && baselineKwh !== undefined && (
            <button
              onClick={() => setShowBaseline(!showBaseline)}
              className="btn-secondary"
              style={{
                padding: '6px 12px',
                fontSize: '0.82rem',
                backgroundColor: showBaseline ? 'rgba(6, 182, 212, 0.2)' : 'transparent',
                borderColor: showBaseline ? '#06b6d4' : 'var(--border-color)'
              }}
            >
              Baseline ({baselineKwh.toFixed(2)} kWh): {showBaseline ? 'ON' : 'OFF'}
            </button>
          )}
        </div>
      </div>

      {/* Chart container */}
      <div style={{ height: '360px', width: '100%' }}>
        {isLoading ? (
          <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: '12px' }}>
            <div className="spinner" style={{ width: '32px', height: '32px' }}></div>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Loading actual MySQL consumption records...</span>
          </div>
        ) : chartData.length === 0 ? (
          <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
            No consumption records found.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="consumptionGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.08)" />
              <XAxis
                dataKey="timestamp"
                stroke="#94a3b8"
                fontSize={11}
                tickLine={false}
                interval="preserveStartEnd"
              />
              <YAxis
                stroke="#94a3b8"
                fontSize={11}
                tickLine={false}
                unit=" kWh"
                domain={[0, 'auto']}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend verticalAlign="top" height={36} wrapperStyle={{ fontSize: '0.85rem' }} />

              {/* Baseline Reference Line */}
              {showBaseline && baselineKwh && (
                <ReferenceLine
                  y={baselineKwh}
                  stroke="#10b981"
                  strokeDasharray="4 4"
                  strokeWidth={2}
                  label={{
                    value: `Baseline: ${baselineKwh.toFixed(2)} kWh`,
                    fill: '#34d399',
                    fontSize: 12,
                    position: 'top'
                  }}
                />
              )}

              {/* Predicted Energy Consumption Overlay */}
              {predictedKwh !== null && predictedKwh !== undefined && (
                <ReferenceLine
                  y={predictedKwh}
                  stroke="#f43f5e"
                  strokeDasharray="6 3"
                  strokeWidth={2}
                  label={{
                    value: `Predicted: ${predictedKwh.toFixed(2)} kWh`,
                    fill: '#fb7185',
                    fontSize: 12,
                    position: 'insideBottomRight'
                  }}
                />
              )}

              {/* Area for actual consumption */}
              <Area
                type="monotone"
                dataKey="consumption"
                name="Actual Energy Consumption"
                stroke="#3b82f6"
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#consumptionGradient)"
              />

              {/* 24h rolling average line */}
              <Line
                type="monotone"
                dataKey="rolling24h"
                name="24h Rolling Mean"
                stroke="#f59e0b"
                strokeWidth={1.5}
                dot={false}
              />
            </ComposedChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
