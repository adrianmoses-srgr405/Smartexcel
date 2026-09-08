import React, { useState, useEffect } from 'react';
import {
  FileCheck2,
  Calendar,
  Layers,
  ArrowRight,
  Sparkles,
  CheckCircle2,
  Play,
} from 'lucide-react';
import { Dataset } from '../types';
import { api } from '../services/api';

interface TemplatesPageProps {
  selectedDataset: Dataset | null;
  onApplyTemplateQuery: (query: string) => void;
}

export const TemplatesPage: React.FC<TemplatesPageProps> = ({
  selectedDataset,
  onApplyTemplateQuery,
}) => {
  const [templates, setTemplates] = useState<any[]>([]);
  const [selectedMonth, setSelectedMonth] = useState('Februari 2024');

  useEffect(() => {
    const fetchTemplates = async () => {
      try {
        const data = await api.getTemplates();
        setTemplates(data);
      } catch (err) {
        console.error('Failed to load templates', err);
      }
    };
    fetchTemplates();
  }, []);

  const months = [
    'Januari 2024',
    'Februari 2024',
    'Maret 2024',
    'April 2024',
    'Mei 2024',
    'Juni 2024',
  ];

  return (
    <div className="content-body animate-fade-in">
      {/* Header */}
      <div style={{ marginBottom: '1.5rem' }}>
        <h1 style={{ fontSize: '1.6rem', fontWeight: 800, color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <FileCheck2 size={28} color="#10b981" />
          Template Pemodelan Laporan & Tutup Buku
        </h1>
        <p style={{ color: '#94a3b8', fontSize: '0.9rem', marginTop: '0.25rem' }}>
          Otomasi pelaporan berkala berulang tanpa perlu merumuskan kriteria dari nol. Pilih template, tentukan periode, dan jalankan otomatis.
        </p>
      </div>

      {/* Period Selection Bar */}
      <div className="glass-panel" style={{
        padding: '1.25rem 1.5rem',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '1rem',
        marginBottom: '2rem'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <Calendar size={20} color="#10b981" />
          <span style={{ fontWeight: 600, color: '#f8fafc', fontSize: '0.95rem' }}>
            Pilih Periode Tutup Buku Target:
          </span>
        </div>

        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
          {months.map((m) => (
            <button
              key={m}
              onClick={() => setSelectedMonth(m)}
              className="btn"
              style={{
                padding: '0.4rem 0.85rem',
                fontSize: '0.8rem',
                background: selectedMonth === m ? 'rgba(16, 185, 129, 0.2)' : 'rgba(255, 255, 255, 0.05)',
                color: selectedMonth === m ? '#34d399' : '#94a3b8',
                borderColor: selectedMonth === m ? 'rgba(16, 185, 129, 0.4)' : 'rgba(255, 255, 255, 0.08)',
                borderRadius: '8px'
              }}
            >
              {m}
            </button>
          ))}
        </div>
      </div>

      {/* Template Cards Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))',
        gap: '1.5rem'
      }}>
        {templates.map((tpl) => (
          <div key={tpl.id} className="glass-panel-interactive" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
              <span className="badge badge-categorical">{tpl.category}</span>
              <span className="badge badge-formula">Op: {tpl.operation}</span>
            </div>

            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc', marginBottom: '0.5rem' }}>
              {tpl.name}
            </h3>

            <p style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '1.25rem', flex: 1 }}>
              {tpl.description}
            </p>

            <div style={{
              background: 'rgba(0, 0, 0, 0.25)',
              padding: '0.75rem',
              borderRadius: '8px',
              fontSize: '0.8rem',
              color: '#cbd5e1',
              marginBottom: '1rem'
            }}>
              <div><strong>Group By:</strong> {tpl.group_by.join(', ') || 'None'}</div>
              <div><strong>Target Field:</strong> {tpl.target_field}</div>
            </div>

            <button
              onClick={() => {
                const finalQuery = tpl.default_query.replace('Februari 2024', selectedMonth);
                onApplyTemplateQuery(finalQuery);
              }}
              className="btn btn-primary"
              style={{ width: '100%', fontSize: '0.85rem' }}
            >
              <Play size={16} />
              <span>Jalankan Template ({selectedMonth})</span>
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};
