import React, { useState } from 'react';
import { Table, Search, ChevronLeft, ChevronRight, Download } from 'lucide-react';

export default function HistoricalDataTable({
  records,
  isLoading,
  limit,
  onLimitChange
}) {
  const [searchTerm, setSearchTerm] = useState('');
  const [page, setPage] = useState(0);
  const rowsPerPage = 10;

  const dowNames = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

  const filtered = (records || []).filter((r) => {
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    return (
      (r.timestamp && r.timestamp.toLowerCase().includes(term)) ||
      (r.hour !== undefined && r.hour.toString().includes(term)) ||
      (r.energy_consumption_kwh !== undefined && r.energy_consumption_kwh.toString().includes(term))
    );
  });

  const totalPages = Math.ceil(filtered.length / rowsPerPage) || 1;
  const currentRows = filtered.slice(page * rowsPerPage, (page + 1) * rowsPerPage);

  return (
    <div className="glass-panel" style={{ padding: '24px' }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '14px',
        marginBottom: '18px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{
            width: '36px',
            height: '36px',
            borderRadius: '8px',
            background: 'rgba(139, 92, 246, 0.15)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#8b5cf6'
          }}>
            <Table size={20} />
          </div>
          <div>
            <h2 style={{ fontSize: '1.2rem', fontWeight: 700, color: '#ffffff' }}>
              Historical Smart-Meter Records
            </h2>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
              Actual MySQL database records from the energy_consumption table
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
          {/* Search box */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            background: 'rgba(10, 14, 26, 0.8)',
            border: '1px solid var(--border-color)',
            borderRadius: '8px',
            padding: '4px 10px',
            width: '200px'
          }}>
            <Search size={14} color="var(--text-dim)" />
            <input
              type="text"
              placeholder="Search timestamp / kWh..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setPage(0);
              }}
              style={{
                background: 'transparent',
                border: 'none',
                color: 'var(--text-main)',
                fontSize: '0.82rem',
                outline: 'none',
                width: '100%'
              }}
            />
          </div>

          {/* Limit selector */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Fetch:</span>
            <select
              className="input-field"
              value={limit}
              onChange={(e) => {
                onLimitChange(parseInt(e.target.value, 10));
                setPage(0);
              }}
              style={{ width: '80px', padding: '4px 8px', fontSize: '0.82rem' }}
            >
              <option value="25">25</option>
              <option value="50">50</option>
              <option value="100">100</option>
              <option value="200">200</option>
            </select>
          </div>
        </div>
      </div>

      {/* Table Container */}
      <div style={{ overflowX: 'auto', borderRadius: '10px', border: '1px solid var(--border-color)' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
          <thead>
            <tr style={{ background: 'rgba(255, 255, 255, 0.04)', textAlign: 'left', borderBottom: '1px solid var(--border-color)' }}>
              <th style={{ padding: '12px 14px', color: 'var(--text-muted)', fontWeight: 600 }}>Timestamp</th>
              <th style={{ padding: '12px 14px', color: 'var(--text-muted)', fontWeight: 600 }}>Hour</th>
              <th style={{ padding: '12px 14px', color: 'var(--text-muted)', fontWeight: 600 }}>Day</th>
              <th style={{ padding: '12px 14px', color: 'var(--text-muted)', fontWeight: 600 }}>Day of Week</th>
              <th style={{ padding: '12px 14px', color: 'var(--text-muted)', fontWeight: 600 }}>Weekend</th>
              <th style={{ padding: '12px 14px', color: 'var(--text-muted)', fontWeight: 600 }}>Lag 1h (kWh)</th>
              <th style={{ padding: '12px 14px', color: 'var(--text-muted)', fontWeight: 600 }}>Lag 24h (kWh)</th>
              <th style={{ padding: '12px 14px', color: 'var(--text-muted)', fontWeight: 600 }}>Rolling Mean 24h</th>
              <th style={{ padding: '12px 14px', color: '#38bdf8', fontWeight: 700 }}>Consumption (kWh)</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td colSpan="9" style={{ padding: '30px', textAlign: 'center', color: 'var(--text-muted)' }}>
                  <div className="spinner" style={{ margin: '0 auto 8px' }}></div>
                  Loading database records...
                </td>
              </tr>
            ) : currentRows.length === 0 ? (
              <tr>
                <td colSpan="9" style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)' }}>
                  No records match your query.
                </td>
              </tr>
            ) : (
              currentRows.map((row, idx) => (
                <tr
                  key={row.id || idx}
                  style={{
                    borderBottom: '1px solid rgba(255, 255, 255, 0.04)',
                    background: idx % 2 === 0 ? 'transparent' : 'rgba(255, 255, 255, 0.015)',
                    transition: 'background 0.15s'
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.background = 'rgba(59, 130, 246, 0.08)')}
                  onMouseLeave={(e) => (e.currentTarget.style.background = idx % 2 === 0 ? 'transparent' : 'rgba(255, 255, 255, 0.015)')}
                >
                  <td style={{ padding: '10px 14px', fontWeight: 600, color: '#f8fafc' }}>
                    {row.timestamp}
                  </td>
                  <td style={{ padding: '10px 14px', color: 'var(--text-muted)' }}>{row.hour}</td>
                  <td style={{ padding: '10px 14px', color: 'var(--text-muted)' }}>{row.day}</td>
                  <td style={{ padding: '10px 14px', color: 'var(--text-muted)' }}>
                    {dowNames[row.day_of_week] || row.day_of_week}
                  </td>
                  <td style={{ padding: '10px 14px' }}>
                    <span style={{
                      fontSize: '0.72rem',
                      padding: '2px 6px',
                      borderRadius: '4px',
                      background: row.weekend ? 'rgba(139, 92, 246, 0.2)' : 'rgba(255, 255, 255, 0.06)',
                      color: row.weekend ? '#c4b5fd' : 'var(--text-muted)'
                    }}>
                      {row.weekend ? 'Weekend' : 'Weekday'}
                    </span>
                  </td>
                  <td style={{ padding: '10px 14px', color: 'var(--text-muted)' }}>
                    {parseFloat(row.lag_1h_kwh).toFixed(3)}
                  </td>
                  <td style={{ padding: '10px 14px', color: 'var(--text-muted)' }}>
                    {parseFloat(row.lag_24h_kwh).toFixed(3)}
                  </td>
                  <td style={{ padding: '10px 14px', color: 'var(--text-muted)' }}>
                    {parseFloat(row.rolling_mean_24h_kwh).toFixed(3)}
                  </td>
                  <td style={{ padding: '10px 14px', fontWeight: 700, color: '#38bdf8' }}>
                    {parseFloat(row.energy_consumption_kwh).toFixed(3)}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Controls */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '16px' }}>
        <span style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>
          Showing {filtered.length > 0 ? page * rowsPerPage + 1 : 0} to {Math.min((page + 1) * rowsPerPage, filtered.length)} of {filtered.length} retrieved records
        </span>

        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <button
            onClick={() => setPage((p) => Math.max(0, p - 1))}
            disabled={page === 0}
            className="btn-secondary"
            style={{ padding: '4px 10px', fontSize: '0.8rem' }}
          >
            <ChevronLeft size={14} />
            <span>Prev</span>
          </button>
          <span style={{ fontSize: '0.82rem', padding: '0 8px', color: 'var(--text-muted)' }}>
            Page {page + 1} of {totalPages}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
            disabled={page >= totalPages - 1}
            className="btn-secondary"
            style={{ padding: '4px 10px', fontSize: '0.8rem' }}
          >
            <span>Next</span>
            <ChevronRight size={14} />
          </button>
        </div>
      </div>
    </div>
  );
}
