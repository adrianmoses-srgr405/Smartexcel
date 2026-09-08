import React from 'react';
import { Database, FileSpreadsheet, Sparkles, PlusCircle } from 'lucide-react';
import { Dataset } from '../../types';

interface NavbarProps {
  datasets: Dataset[];
  selectedDataset: Dataset | null;
  onSelectDataset: (dataset: Dataset) => void;
  onUploadClick: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  datasets,
  selectedDataset,
  onSelectDataset,
  onUploadClick,
}) => {
  return (
    <header style={{
      height: '64px',
      background: 'rgba(13, 19, 34, 0.85)',
      backdropFilter: 'blur(12px)',
      borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 2rem',
      position: 'sticky',
      top: 0,
      zIndex: 20
    }}>
      {/* Active Dataset Selector */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#94a3b8', fontSize: '0.85rem' }}>
          <Database size={16} color="#10b981" />
          <span>Active Dataset:</span>
        </div>

        {datasets.length > 0 ? (
          <select
            value={selectedDataset?.id || ''}
            onChange={(e) => {
              const ds = datasets.find((d) => d.id === e.target.value);
              if (ds) onSelectDataset(ds);
            }}
            style={{
              background: '#1a2234',
              color: '#f8fafc',
              border: '1px solid rgba(255, 255, 255, 0.12)',
              borderRadius: '8px',
              padding: '0.45rem 0.85rem',
              fontSize: '0.85rem',
              fontWeight: 600,
              outline: 'none',
              cursor: 'pointer',
              minWidth: '220px'
            }}
          >
            {datasets.map((d) => (
              <option key={d.id} value={d.id}>
                {d.filename} ({d.row_count} baris, {d.column_count} kolom)
              </option>
            ))}
          </select>
        ) : (
          <span style={{ fontSize: '0.85rem', color: '#f59e0b', fontStyle: 'italic' }}>
            Belum ada dataset (Silakan upload)
          </span>
        )}
      </div>

      {/* Action Buttons */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <button
          onClick={onUploadClick}
          className="btn btn-primary"
          style={{ padding: '0.45rem 0.9rem', fontSize: '0.8rem' }}
        >
          <PlusCircle size={16} />
          <span>Upload Excel Baru</span>
        </button>
      </div>
    </header>
  );
};
