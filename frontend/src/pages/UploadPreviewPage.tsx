import React, { useState, useRef } from 'react';
import {
  UploadCloud,
  FileSpreadsheet,
  Trash2,
  Search,
  CheckCircle2,
  AlertCircle,
  Table as TableIcon,
  Columns,
  Hash,
} from 'lucide-react';
import { Dataset } from '../types';
import { api } from '../services/api';

interface UploadPreviewPageProps {
  datasets: Dataset[];
  selectedDataset: Dataset | null;
  onSelectDataset: (dataset: Dataset) => void;
  onDatasetUploaded: (newDataset: Dataset) => void;
  onDatasetDeleted: (datasetId: string) => void;
  onDatasetUpdated?: (updatedDataset: Dataset) => void;
}

export const UploadPreviewPage: React.FC<UploadPreviewPageProps> = ({
  datasets,
  selectedDataset,
  onSelectDataset,
  onDatasetUploaded,
  onDatasetDeleted,
  onDatasetUpdated,
}) => {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [searchFilter, setSearchFilter] = useState('');
  const [rowLimit, setRowLimit] = useState<number | 'all'>('all');
  const [isSwitchingSheet, setIsSwitchingSheet] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileUpload = async (file: File) => {
    setIsUploading(true);
    setUploadError(null);
    try {
      const newDataset = await api.uploadDataset(file);
      onDatasetUploaded(newDataset);
    } catch (err: any) {
      setUploadError(err.response?.data?.detail || 'Gagal mengunggah file.');
    } finally {
      setIsUploading(false);
    }
  };

  const handleSheetChange = async (sheetName: string) => {
    if (!selectedDataset) return;
    setIsSwitchingSheet(true);
    try {
      const updated = await api.switchSheet(selectedDataset.id, sheetName);
      if (onDatasetUpdated) onDatasetUpdated(updated);
      onSelectDataset(updated);
    } catch (err) {
      alert('Gagal berganti sheet Excel.');
    } finally {
      setIsSwitchingSheet(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  const previewRows = selectedDataset?.preview_data || [];
  const columns = selectedDataset?.columns && selectedDataset.columns.length > 0
    ? selectedDataset.columns
    : (selectedDataset?.profiling?.columns || []);

  const availableSheets = selectedDataset?.available_sheets || [];
  const currentSheet = selectedDataset?.selected_sheet;

  const filteredRows = previewRows.filter((row) =>
    Object.values(row).some((val) =>
      String(val).toLowerCase().includes(searchFilter.toLowerCase())
    )
  );

  const displayedRows = rowLimit === 'all' ? filteredRows : filteredRows.slice(0, rowLimit);

  return (
    <div className="content-body animate-fade-in">
      {/* Page Title Header */}
      <div style={{ marginBottom: '1.5rem' }}>
        <h1 style={{ fontSize: '1.6rem', fontWeight: 800, color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <UploadCloud size={28} color="#10b981" />
          Upload & Preview Data Excel
        </h1>
        <p style={{ color: '#94a3b8', fontSize: '0.9rem', marginTop: '0.25rem' }}>
          Unggah data mentah operasional perkebunan/logistik PTPN dalam format .xlsx, .xls, atau .csv untuk dianalisis secara otomatis.
        </p>
      </div>

      {/* Upload Drag & Drop Area */}
      <div
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleDrop}
        className="glass-panel"
        style={{
          padding: '2rem',
          textAlign: 'center',
          border: '2px dashed rgba(16, 185, 129, 0.35)',
          background: 'rgba(16, 185, 129, 0.03)',
          marginBottom: '2rem',
          cursor: 'pointer',
          position: 'relative'
        }}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".xlsx,.xls,.csv"
          style={{ display: 'none' }}
          onChange={(e) => {
            if (e.target.files && e.target.files.length > 0) {
              handleFileUpload(e.target.files[0]);
            }
          }}
        />

        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{
            width: '56px',
            height: '56px',
            borderRadius: '50%',
            background: 'rgba(16, 185, 129, 0.15)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <FileSpreadsheet size={28} color="#10b981" />
          </div>
          <div>
            <div style={{ fontWeight: 700, fontSize: '1.05rem', color: '#f8fafc' }}>
              {isUploading ? 'Sedang Memproses & Melakukan Profiling...' : 'Klik atau Tarik File Excel / CSV ke Sini'}
            </div>
            <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginTop: '0.2rem' }}>
              Mendukung file .xlsx, .xls, .csv (Sistem membaca seluruh struktur kolom dinamis)
            </div>
          </div>
        </div>

        {uploadError && (
          <div style={{
            marginTop: '1rem',
            padding: '0.75rem 1rem',
            borderRadius: '8px',
            background: 'rgba(244, 63, 94, 0.15)',
            border: '1px solid rgba(244, 63, 94, 0.3)',
            color: '#fb7185',
            fontSize: '0.85rem',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}>
            <AlertCircle size={16} />
            <span>{uploadError}</span>
          </div>
        )}
      </div>

      {/* Dataset Details & Preview Section */}
      {selectedDataset ? (
        <div className="glass-panel" style={{ padding: '1.5rem' }}>
          {/* Header Bar */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '1rem',
            marginBottom: '1.25rem',
            paddingBottom: '1rem',
            borderBottom: '1px solid rgba(255, 255, 255, 0.08)'
          }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                <span style={{ fontWeight: 700, fontSize: '1.1rem', color: '#f8fafc' }}>
                  {selectedDataset.filename}
                </span>
                <span className="badge badge-categorical">
                  <CheckCircle2 size={12} /> Terprofiling
                </span>
              </div>
              <div style={{ display: 'flex', gap: '1.25rem', color: '#94a3b8', fontSize: '0.8rem', marginTop: '0.35rem', flexWrap: 'wrap', alignItems: 'center' }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                  <Hash size={14} color="#10b981" /> <strong>{selectedDataset.row_count}</strong> Baris
                </span>
                <span style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                  <Columns size={14} color="#3b82f6" /> <strong>{selectedDataset.column_count}</strong> Kolom
                </span>
                <span>
                  Ukuran: {(selectedDataset.file_size_bytes / 1024).toFixed(1)} KB
                </span>

                {availableSheets.length > 1 && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginLeft: '0.5rem', background: 'rgba(59, 130, 246, 0.15)', padding: '0.2rem 0.6rem', borderRadius: '6px' }}>
                    <span style={{ color: '#60a5fa', fontWeight: 600 }}>Pilih Sheet:</span>
                    <select
                      value={currentSheet || availableSheets[0]}
                      disabled={isSwitchingSheet}
                      onChange={(e) => handleSheetChange(e.target.value)}
                      style={{
                        background: '#131c2e',
                        color: '#f8fafc',
                        border: '1px solid rgba(59, 130, 246, 0.4)',
                        borderRadius: '4px',
                        padding: '0.15rem 0.45rem',
                        fontSize: '0.75rem',
                        fontWeight: 600,
                        cursor: 'pointer'
                      }}
                    >
                      {availableSheets.map((s) => (
                        <option key={s} value={s}>
                          Sheet: {s}
                        </option>
                      ))}
                    </select>
                  </div>
                )}
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              {/* Search Bar */}
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                background: '#131c2e',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: '8px',
                padding: '0.4rem 0.75rem'
              }}>
                <Search size={14} color="#64748b" />
                <input
                  type="text"
                  placeholder="Cari dalam baris..."
                  value={searchFilter}
                  onChange={(e) => setSearchFilter(e.target.value)}
                  style={{
                    background: 'transparent',
                    border: 'none',
                    color: '#f8fafc',
                    fontSize: '0.8rem',
                    outline: 'none',
                    width: '180px'
                  }}
                />
              </div>

              {/* Row Limit Selector */}
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.25rem',
                background: 'rgba(255, 255, 255, 0.04)',
                padding: '0.2rem 0.4rem',
                borderRadius: '6px',
                border: '1px solid rgba(255, 255, 255, 0.08)'
              }}>
                <span style={{ fontSize: '0.72rem', color: '#94a3b8', marginRight: '0.2rem' }}>Tampilkan:</span>
                {[50, 100, 500, 'all'].map((lim) => (
                  <button
                    key={lim}
                    onClick={() => setRowLimit(lim as any)}
                    className="btn btn-ghost"
                    style={{
                      padding: '0.2rem 0.5rem',
                      fontSize: '0.72rem',
                      borderRadius: '4px',
                      background: rowLimit === lim ? 'rgba(16, 185, 129, 0.25)' : 'transparent',
                      color: rowLimit === lim ? '#34d399' : '#94a3b8',
                      fontWeight: rowLimit === lim ? 700 : 500,
                      border: rowLimit === lim ? '1px solid rgba(16, 185, 129, 0.4)' : '1px solid transparent'
                    }}
                  >
                    {lim === 'all' ? `Semua (${filteredRows.length})` : lim}
                  </button>
                ))}
              </div>

              {/* Delete Button */}
              <button
                onClick={async () => {
                  if (confirm(`Hapus dataset "${selectedDataset.filename}"?`)) {
                    await api.deleteDataset(selectedDataset.id);
                    onDatasetDeleted(selectedDataset.id);
                  }
                }}
                className="btn btn-ghost"
                style={{ color: '#f43f5e', padding: '0.45rem 0.75rem' }}
                title="Hapus Dataset"
              >
                <Trash2 size={16} />
              </button>
            </div>
          </div>

          {/* Interactive Data Grid */}
          <div className="modern-table-container" style={{ maxHeight: '520px', overflowY: 'auto' }}>
            <table className="modern-table">
              <thead>
                <tr>
                  <th style={{ width: '50px', textAlign: 'center' }}>#</th>
                  {columns.map((col) => (
                    <th key={col.sanitized_name}>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
                        <span style={{
                          fontFamily: 'var(--font-mono)',
                          color: '#10b981',
                          fontSize: '0.75rem',
                          background: 'rgba(16, 185, 129, 0.1)',
                          padding: '0.1rem 0.35rem',
                          borderRadius: '4px',
                          display: 'inline-block',
                          width: 'fit-content'
                        }}>
                          Col {col.excel_column_letter}
                        </span>
                        <span>{col.original_name}</span>
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {displayedRows.length > 0 ? (
                  displayedRows.map((row, rIdx) => (
                    <tr key={rIdx}>
                      <td style={{ textAlign: 'center', color: '#64748b', fontSize: '0.75rem', fontFamily: 'var(--font-mono)' }}>
                        {rIdx + 1}
                      </td>
                      {columns.map((col) => (
                        <td key={col.sanitized_name}>
                          {row[col.original_name] !== undefined && row[col.original_name] !== null
                            ? String(row[col.original_name])
                            : <span style={{ color: '#475569', fontStyle: 'italic' }}>null</span>}
                        </td>
                      ))}
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={columns.length + 1} style={{ textAlign: 'center', padding: '2rem', color: '#64748b' }}>
                      Tidak ada data yang cocok dengan pencarian.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
          <div style={{
            marginTop: '0.75rem',
            fontSize: '0.78rem',
            color: '#94a3b8',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '0.5rem'
          }}>
            <div style={{ fontSize: '0.75rem', color: '#64748b' }}>
              💡 Menampilkan data mentah langsung dari lembar Excel. AI akan selalu memproses <strong>seluruh {selectedDataset.row_count.toLocaleString('id-ID')} baris data</strong> saat perhitungan query.
            </div>
            <div style={{ fontWeight: 600, color: '#38bdf8' }}>
              Menampilkan {displayedRows.length} dari {filteredRows.length} baris (Total Populasi File: {selectedDataset.row_count.toLocaleString('id-ID')} baris)
            </div>
          </div>
        </div>
      ) : (
        <div className="glass-panel" style={{ padding: '3rem', textAlign: 'center', color: '#94a3b8' }}>
          <TableIcon size={40} color="#64748b" style={{ margin: '0 auto 1rem' }} />
          <div>Belum ada dataset yang dipilih. Silakan upload file Excel di atas.</div>
        </div>
      )}
    </div>
  );
};
