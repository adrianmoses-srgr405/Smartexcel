import React from 'react';
import {
  Binary,
  Calendar,
  Hash,
  Layers,
  CheckCircle,
  HelpCircle,
  TrendingUp,
  Percent,
} from 'lucide-react';
import { Dataset, ColumnProfiling } from '../types';

interface ProfilingPageProps {
  selectedDataset: Dataset | null;
}

export const ProfilingPage: React.FC<ProfilingPageProps> = ({ selectedDataset }) => {
  if (!selectedDataset) {
    return (
      <div className="content-body animate-fade-in">
        <div className="glass-panel" style={{ padding: '3rem', textAlign: 'center', color: '#94a3b8' }}>
          <Binary size={40} color="#64748b" style={{ margin: '0 auto 1rem' }} />
          <h3>Silakan pilih atau unggah dataset terlebih dahulu untuk melihat hasil profiling data.</h3>
        </div>
      </div>
    );
  }

  const columns = selectedDataset.columns || [];
  const numericCount = columns.filter((c) => c.inferred_type === 'Numeric').length;
  const dateCount = columns.filter((c) => c.inferred_type === 'Date').length;
  const categoricalCount = columns.filter((c) => c.inferred_type === 'Categorical').length;
  const textCount = columns.filter((c) => c.inferred_type === 'Text').length;

  const getTypeBadge = (type: string) => {
    switch (type) {
      case 'Numeric':
        return <span className="badge badge-numeric"><Hash size={12} /> Numeric</span>;
      case 'Date':
        return <span className="badge badge-date"><Calendar size={12} /> Date</span>;
      case 'Categorical':
        return <span className="badge badge-categorical"><Layers size={12} /> Categorical</span>;
      default:
        return <span className="badge badge-text"><HelpCircle size={12} /> Text</span>;
    }
  };

  return (
    <div className="content-body animate-fade-in">
      {/* Title */}
      <div style={{ marginBottom: '1.5rem' }}>
        <h1 style={{ fontSize: '1.6rem', fontWeight: 800, color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <Binary size={28} color="#10b981" />
          Data Profiling & Schema Recognition
        </h1>
        <p style={{ color: '#94a3b8', fontSize: '0.9rem', marginTop: '0.25rem' }}>
          Analisis otomatis tipe data, sebaran kolom, statistik, nilai unik, dan kelengkapan dataset: <strong>{selectedDataset.filename}</strong>
        </p>
      </div>

      {/* Top Overview KPI Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '1rem',
        marginBottom: '2rem'
      }}>
        <div className="glass-panel" style={{ padding: '1.25rem' }}>
          <div style={{ color: '#94a3b8', fontSize: '0.8rem', fontWeight: 600 }}>Total Baris & Kolom</div>
          <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#f8fafc', marginTop: '0.25rem' }}>
            {selectedDataset.row_count} <span style={{ fontSize: '0.9rem', color: '#64748b' }}>baris</span> × {selectedDataset.column_count} <span style={{ fontSize: '0.9rem', color: '#64748b' }}>kolom</span>
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '1.25rem' }}>
          <div style={{ color: '#60a5fa', fontSize: '0.8rem', fontWeight: 600 }}>Kolom Kuantitatif (Numeric)</div>
          <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#60a5fa', marginTop: '0.25rem' }}>
            {numericCount} Kolom
          </div>
          <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '0.15rem' }}>Kompatibel untuk SUM, AVG, MAX, MIN</div>
        </div>

        <div className="glass-panel" style={{ padding: '1.25rem' }}>
          <div style={{ color: '#fbbf24', fontSize: '0.8rem', fontWeight: 600 }}>Kolom Waktu (Date/Period)</div>
          <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#fbbf24', marginTop: '0.25rem' }}>
            {dateCount} Kolom
          </div>
          <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '0.15rem' }}>Kompatibel untuk Filter Tutup Buku</div>
        </div>

        <div className="glass-panel" style={{ padding: '1.25rem' }}>
          <div style={{ color: '#34d399', fontSize: '0.8rem', fontWeight: 600 }}>Dimensi Kategori / Teks</div>
          <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#34d399', marginTop: '0.25rem' }}>
            {categoricalCount + textCount} Kolom
          </div>
          <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '0.15rem' }}>Kompatibel untuk Group By & Kriteria</div>
        </div>
      </div>

      {/* Column Cards Grid */}
      <h2 style={{ fontSize: '1.2rem', fontWeight: 700, color: '#f8fafc', marginBottom: '1rem' }}>
        Detail Struktur & Profiling Tiap Kolom
      </h2>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))',
        gap: '1.25rem'
      }}>
        {columns.map((col: ColumnProfiling) => (
          <div key={col.sanitized_name} className="glass-panel-interactive" style={{ padding: '1.35rem' }}>
            {/* Header with Excel Column Letter & Type */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span style={{
                  fontFamily: 'var(--font-mono)',
                  background: 'rgba(16, 185, 129, 0.15)',
                  color: '#34d399',
                  border: '1px solid rgba(16, 185, 129, 0.3)',
                  padding: '0.2rem 0.5rem',
                  borderRadius: '6px',
                  fontWeight: 700,
                  fontSize: '0.8rem'
                }}>
                  Col {col.excel_column_letter}
                </span>
                <span style={{ fontWeight: 700, fontSize: '1.05rem', color: '#f8fafc' }}>
                  {col.original_name}
                </span>
              </div>
              {getTypeBadge(col.inferred_type)}
            </div>

            {/* Quick Metrics */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: '0.75rem',
              background: 'rgba(0, 0, 0, 0.25)',
              padding: '0.75rem',
              borderRadius: '8px',
              marginBottom: '1rem'
            }}>
              <div>
                <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Nilai Unik</div>
                <div style={{ fontWeight: 700, fontSize: '0.95rem', color: '#f8fafc' }}>
                  {col.unique_count} <span style={{ fontSize: '0.75rem', color: '#64748b' }}>({col.unique_percentage}%)</span>
                </div>
              </div>
              <div>
                <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Missing / Null</div>
                <div style={{ fontWeight: 700, fontSize: '0.95rem', color: col.null_count > 0 ? '#f43f5e' : '#10b981' }}>
                  {col.null_count} <span style={{ fontSize: '0.75rem', color: '#64748b' }}>({col.null_percentage}%)</span>
                </div>
              </div>
            </div>

            {/* Numeric Stats */}
            {col.inferred_type === 'Numeric' && (
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                fontSize: '0.8rem',
                color: '#cbd5e1',
                padding: '0.5rem 0',
                borderTop: '1px solid rgba(255, 255, 255, 0.06)',
                borderBottom: '1px solid rgba(255, 255, 255, 0.06)',
                marginBottom: '0.75rem'
              }}>
                <div>Min: <strong style={{ color: '#60a5fa' }}>{col.min_value ?? '-'}</strong></div>
                <div>Mean: <strong style={{ color: '#34d399' }}>{col.mean_value ?? '-'}</strong></div>
                <div>Max: <strong style={{ color: '#f59e0b' }}>{col.max_value ?? '-'}</strong></div>
              </div>
            )}

            {/* Sample Values Tags */}
            <div>
              <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginBottom: '0.4rem', fontWeight: 600 }}>
                Sample Nilai:
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem' }}>
                {col.sample_values && col.sample_values.length > 0 ? (
                  col.sample_values.slice(0, 6).map((s, idx) => (
                    <span key={idx} style={{
                      background: 'rgba(255, 255, 255, 0.06)',
                      color: '#cbd5e1',
                      padding: '0.2rem 0.5rem',
                      borderRadius: '6px',
                      fontSize: '0.75rem',
                      fontFamily: col.inferred_type === 'Numeric' ? 'var(--font-mono)' : 'inherit'
                    }}>
                      {String(s)}
                    </span>
                  ))
                ) : (
                  <span style={{ fontSize: '0.75rem', color: '#64748b' }}>Tidak ada sample</span>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
