import React, { useState, useEffect, useCallback } from 'react';
import Header from './components/Header';
import KpiCards from './components/KpiCards';
import EnergyChart from './components/EnergyChart';
import PredictionPanel from './components/PredictionPanel';
import OptimizationPanel from './components/OptimizationPanel';
import WhatIfSimulator from './components/WhatIfSimulator';
import RecommendationCard from './components/RecommendationCard';
import HistoricalDataTable from './components/HistoricalDataTable';
import {
  checkHealth,
  getEnergySummary,
  getEnergyHistory,
  optimizeEnergy
} from './services/api';
import { AlertTriangle } from 'lucide-react';

export default function App() {
  const [isOnline, setIsOnline] = useState(false);
  const [modelName, setModelName] = useState('XGBoost');
  const [summary, setSummary] = useState(null);
  const [chartData, setChartData] = useState([]);
  const [tableData, setTableData] = useState([]);
  const [tableLimit, setTableLimit] = useState(50);
  const [chartRange, setChartRange] = useState(168); // 7 days default
  const [latestRecord, setLatestRecord] = useState(null);

  const [latestPrediction, setLatestPrediction] = useState(null);
  const [predictionContext, setPredictionContext] = useState(null);
  const [latestOptimization, setLatestOptimization] = useState(null);

  const [isLoadingSummary, setIsLoadingSummary] = useState(true);
  const [isLoadingChart, setIsLoadingChart] = useState(true);
  const [isLoadingTable, setIsLoadingTable] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [apiError, setApiError] = useState(null);

  // Check health and model status
  const checkApiHealth = useCallback(async () => {
    try {
      const data = await checkHealth();
      setIsOnline(data.status === 'healthy');
      setModelName(data.model_name || 'XGBoost');
      setApiError(null);
    } catch (err) {
      setIsOnline(false);
      setApiError('Backend API is currently offline. Please start FastAPI (uvicorn api.main:app --port 8000).');
    }
  }, []);

  // Fetch summary KPIs
  const fetchSummary = useCallback(async () => {
    setIsLoadingSummary(true);
    try {
      const data = await getEnergySummary();
      setSummary(data);
    } catch (err) {
      console.warn('Failed to load summary:', err);
    } finally {
      setIsLoadingSummary(false);
    }
  }, []);

  // Fetch chart history (chronological)
  const fetchChartHistory = useCallback(async (hours = chartRange) => {
    setIsLoadingChart(true);
    try {
      const data = await getEnergyHistory(hours, true);
      setChartData(data);
    } catch (err) {
      console.warn('Failed to load chart history:', err);
    } finally {
      setIsLoadingChart(false);
    }
  }, [chartRange]);

  // Fetch table history (recent first)
  const fetchTableHistory = useCallback(async (limit = tableLimit) => {
    setIsLoadingTable(true);
    try {
      const data = await getEnergyHistory(limit, false);
      setTableData(data);
      if (data && data.length > 0) {
        setLatestRecord(data[0]);
      }
    } catch (err) {
      console.warn('Failed to load table history:', err);
    } finally {
      setIsLoadingTable(false);
    }
  }, [tableLimit]);

  // Initial load
  useEffect(() => {
    checkApiHealth();
    fetchSummary();
    fetchChartHistory(168);
    fetchTableHistory(50);
  }, [checkApiHealth, fetchSummary, fetchChartHistory, fetchTableHistory]);

  // Refresh handler
  const handleRefresh = async () => {
    setIsRefreshing(true);
    await Promise.all([
      checkApiHealth(),
      fetchSummary(),
      fetchChartHistory(chartRange),
      fetchTableHistory(tableLimit)
    ]);
    setIsRefreshing(false);
  };

  // When a prediction is made from PredictionPanel
  const handlePredictionSuccess = (predResult, context) => {
    setLatestPrediction(predResult);
    setPredictionContext(context);
  };

  // Immediate optimization trigger
  const handleRunOptimization = async (predKwh, context) => {
    try {
      const payload = {
        predicted_consumption: predKwh,
        hour: context.hour,
        day_of_week: context.day_of_week,
        weekend: context.weekend
      };
      const optResult = await optimizeEnergy(payload);
      setLatestOptimization(optResult);
      // Refresh summary to reflect updated optimization statistics
      fetchSummary();
    } catch (err) {
      console.error('Optimization failed:', err);
    }
  };

  return (
    <div style={{ maxWidth: '1440px', margin: '0 auto', padding: '24px 20px 60px' }}>
      {/* 1. Header */}
      <Header
        isOnline={isOnline}
        modelName={modelName}
        onRefresh={handleRefresh}
        isRefreshing={isRefreshing}
      />

      {/* API Disconnected Alert */}
      {apiError && (
        <div style={{
          marginBottom: '24px',
          padding: '14px 20px',
          background: 'rgba(239, 68, 68, 0.15)',
          border: '1px solid rgba(239, 68, 68, 0.4)',
          borderRadius: '12px',
          color: '#fca5a5',
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          fontSize: '0.9rem'
        }}>
          <AlertTriangle size={20} color="#ef4444" />
          <div>
            <strong>Service Connection Alert:</strong> {apiError}
          </div>
        </div>
      )}

      {/* 2. KPI Cards */}
      <KpiCards
        summary={summary}
        latestPrediction={latestPrediction}
        latestOptimization={latestOptimization}
        isLoading={isLoadingSummary}
      />

      {/* 3. Recommendation Card (displays once optimization is run) */}
      <RecommendationCard optimization={latestOptimization} />

      {/* 4. Energy Consumption Interactive Line/Area Chart */}
      <EnergyChart
        historyData={chartData}
        baselineKwh={latestOptimization?.baseline_consumption || null}
        predictedKwh={latestPrediction?.predicted_energy_kwh || null}
        isLoading={isLoadingChart}
        onRangeChange={(range) => {
          setChartRange(range);
          fetchChartHistory(range);
        }}
        currentRange={chartRange}
      />

      {/* 5. Prediction and Optimization Grid (2 columns on desktop, 1 on mobile) */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(480px, 1fr))',
        gap: '24px',
        marginBottom: '24px'
      }}>
        {/* Prediction Panel */}
        <PredictionPanel
          latestRecord={latestRecord}
          onPredictionSuccess={handlePredictionSuccess}
          onRunOptimization={handleRunOptimization}
        />

        {/* Optimization Panel */}
        <OptimizationPanel
          predictedConsumption={latestPrediction?.predicted_energy_kwh}
          predictionContext={predictionContext}
          onOptimizationSuccess={(optResult) => {
            setLatestOptimization(optResult);
            fetchSummary();
          }}
        />
      </div>

      {/* 6. What-If Energy Consumption Simulation Panel */}
      <WhatIfSimulator latestRecord={latestRecord} />

      {/* 7. Historical Data Table */}

      <HistoricalDataTable
        records={tableData}
        isLoading={isLoadingTable}
        limit={tableLimit}
        onLimitChange={(lim) => {
          setTableLimit(lim);
          fetchTableHistory(lim);
        }}
      />

      {/* 7. Footer */}
      <footer style={{
        marginTop: '36px',
        padding: '20px 0',
        textAlign: 'center',
        borderTop: '1px solid var(--border-color)',
        color: 'var(--text-dim)',
        fontSize: '0.84rem'
      }}>
        <p>
          <strong>Intelligent Energy Consumption Prediction & Optimization System</strong> • Phase 5 Dashboard
        </p>
        <p style={{ marginTop: '4px', fontSize: '0.78rem' }}>
          Backend: FastAPI + XGBoost Regressor • Database: MySQL 8.0 {summary?.total_records ? `(${summary.total_records.toLocaleString()} records)` : ''} • Frontend: React + Vite + Recharts
        </p>
      </footer>
    </div>
  );
}
