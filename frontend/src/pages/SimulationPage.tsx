import React, { useState } from 'react';
import {
  SlidersHorizontal,
  TrendingUp,
  Percent,
  RefreshCw,
  Layers,
  ArrowRight,
} from 'lucide-react';
import { Dataset } from '../types';

interface SimulationPageProps {
  selectedDataset: Dataset | null;
}

export const SimulationPage: React.FC<SimulationPageProps> = ({ selectedDataset }) => {
  const [demandMultiplier, setDemandMultiplier] = useState<number>(1.10); // +10% default
  const [selectedBrand, setSelectedBrand] = useState<string>('ALL');

  if (!selectedDataset) {
    return (
      <div className="content-body animate-fade-in">
        <div className="glass-panel" style={{ padding: '3rem', textAlign: 'center', color: '#94a3b8' }}>
          <SlidersHorizontal size={40} color="#64748b" style={{ margin: '0 auto 1rem' }} />
          <h3>Silakan pilih dataset terlebih dahulu untuk menjalankan simulasi What-If PKS CPO.</h3>
        </div>
      </div>
    );
  }

  const previewRows = selectedDataset.preview_data || [];
  const targetCol = selectedDataset.columns?.find((c) => c.original_name.includes('CPO') || c.inferred_type === 'Numeric')?.original_name || 'Produksi CPO (Kg)';
  const brandCol = selectedDataset.columns?.find((c) => c.original_name.includes('Kebun') || c.inferred_type === 'Categorical')?.original_name || 'Asal Kebun';

  const brandOptions = ['ALL', ...Array.from(new Set(previewRows.map((r) => String(r[brandCol])).filter(Boolean)))];

  const baseTotal = previewRows.reduce((acc, r) => acc + (Number(r[targetCol]) || 0), 0);
  const simulatedTotal = previewRows.reduce((acc, r) => {
    const val = Number(r[targetCol]) || 0;
    const isMatched = selectedBrand === 'ALL' || String(r[brandCol]) === selectedBrand;
    return acc + (isMatched ? Math.round(val * demandMultiplier) : val);
  }, 0);

  const delta = simulatedTotal - baseTotal;
  const deltaPct = baseTotal > 0 ? ((delta / baseTotal) * 100).toFixed(1) : '0';

  return (
    <div className="content-body animate-fade-in">
      {/* Header */}
      <div style={{ marginBottom: '1.5rem' }}>
        <h1 style={{ fontSize: '1.6rem', fontWeight: 800, color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <SlidersHorizontal size={28} color="#10b981" />
          What-If Scenario Simulation & Modeling
        </h1>
        <p style={{ color: '#94a3b8', fontSize: '0.9rem', marginTop: '0.25rem' }}>
          Simulasikan skenario perubahan kuantitas operasional dan analisis dampaknya terhadap total pemodelan rumus Excel secara instan.
        </p>
      </div>

      {/* Control Panel */}
      <div className="glass-panel" style={{ padding: '1.75rem', marginBottom: '2rem' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.5rem' }}>
          {/* Multiplier Slider */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
              <span style={{ fontSize: '0.85rem', fontWeight: 600, color: '#f8fafc' }}>
                Faktor Perubahan Kuantitas ({targetCol}):
              </span>
              <span style={{ fontWeight: 800, color: '#10b981', fontFamily: 'var(--font-mono)' }}>
                {((demandMultiplier - 1) * 100).toFixed(0)}% ({demandMultiplier}x)
              </span>
            </div>
            <input
              type="range"
              min="0.5"
              max="2.0"
              step="0.05"
              value={demandMultiplier}
              onChange={(e) => setDemandMultiplier(parseFloat(e.target.value))}
              style={{ width: '100%', accentColor: '#10b981', cursor: 'pointer' }}
            />
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: '#64748b', marginTop: '0.25rem' }}>
              <span>-50% (Penurunan)</span>
              <span>Normal (1.0x)</span>
              <span>+100% (Kenaikan)</span>
            </div>
          </div>

          {/* Brand Selector */}
          <div>
            <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#f8fafc', marginBottom: '0.5rem' }}>
              Kategori / Merek Target Simulasi:
            </label>
            <select
              value={selectedBrand}
              onChange={(e) => setSelectedBrand(e.target.value)}
              style={{
                width: '100%',
                padding: '0.65rem 1rem',
                background: '#131c2e',
                color: '#f8fafc',
                border: '1px solid rgba(255, 255, 255, 0.12)',
                borderRadius: '8px',
                outline: 'none',
                cursor: 'pointer'
              }}
            >
              {brandOptions.map((b) => (
                <option key={b} value={b}>
                  {b === 'ALL' ? 'Semua Kategori (Global Multiplier)' : `Hanya Kategori: ${b}`}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Comparison KPI Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
        gap: '1.25rem',
        marginBottom: '2rem'
      }}>
        <div className="glass-panel" style={{ padding: '1.25rem' }}>
          <div style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Total Aktual Baseline</div>
          <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#f8fafc', fontFamily: 'var(--font-mono)', marginTop: '0.25rem' }}>
            {baseTotal.toLocaleString()}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Formula: =SUM({targetCol})</div>
        </div>

        <div className="glass-panel" style={{ padding: '1.25rem', border: '1px solid rgba(16, 185, 129, 0.35)' }}>
          <div style={{ fontSize: '0.8rem', color: '#34d399' }}>Total Hasil Simulasi</div>
          <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#34d399', fontFamily: 'var(--font-mono)', marginTop: '0.25rem' }}>
            {simulatedTotal.toLocaleString()}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Model: Simulated Dynamic Aggregation</div>
        </div>

        <div className="glass-panel" style={{ padding: '1.25rem' }}>
          <div style={{ fontSize: '0.8rem', color: '#60a5fa' }}>Selisih Varians (Delta)</div>
          <div style={{ fontSize: '1.6rem', fontWeight: 800, color: delta >= 0 ? '#60a5fa' : '#f43f5e', fontFamily: 'var(--font-mono)', marginTop: '0.25rem' }}>
            {delta >= 0 ? `+${delta.toLocaleString()}` : delta.toLocaleString()}
          </div>
          <div style={{ fontSize: '0.75rem', color: delta >= 0 ? '#34d399' : '#f43f5e' }}>
            {delta >= 0 ? `+${deltaPct}%` : `${deltaPct}%`} perubahan
          </div>
        </div>
      </div>
    </div>
  );
};
