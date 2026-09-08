import React, { useState } from 'react';
import {
  Sparkles,
  Send,
  CheckCircle2,
  ArrowRight,
  FileSpreadsheet,
  Download,
  Copy,
  Check,
  BarChart3,
  ListFilter,
  ShieldCheck,
  Clock,
  Layers,
  Award,
  AlertCircle,
} from 'lucide-react';

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts';
import { Dataset, AnalysisResult } from '../types';
import { api } from '../services/api';

interface AIQueryPageProps {
  selectedDataset: Dataset | null;
}

export const AIQueryPage: React.FC<AIQueryPageProps> = ({ selectedDataset }) => {
  const [queryInput, setQueryInput] = useState('Buat rekap produksi CPO per asal kebun untuk Februari 2024');
  const [isLoading, setIsLoading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [copiedFormula, setCopiedFormula] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [evalSubmitted, setEvalSubmitted] = useState(false);

  const isCarDataset = selectedDataset?.filename?.toLowerCase().includes('mobil') || selectedDataset?.filename?.toLowerCase().includes('penjualan');

  const sampleQueries = isCarDataset ? [
    'Ambil data mobil Brio',
    'Tampilkan semua data mobil Brio dalam bentuk tabel',
    'Total penjualan Toyota di Pekanbaru pada Februari 2024',
    'Filter data mobil Daihatsu transmisi Matic',
    'Berapa rata-rata harga jual mobil Honda?',
    'Rekap total penjualan mobil per merek',
  ] : [
    'Buat rekap produksi CPO per asal kebun untuk Februari 2024',
    'Berapa total produksi CPO Kebun Tandun pada Februari 2024?',
    'Berapa total TBS Olah Kebun Tandun?',
    'Berapa rata-rata rendemen CPO per asal kebun?',
    'Cari hari dengan produksi CPO paling tinggi.',
    'Berapa total keseluruhan Produksi CPO?',
  ];


  const handleAnalyze = async (queryText?: string) => {
    const q = queryText || queryInput;
    if (!q.trim() || !selectedDataset) return;

    setIsLoading(true);
    setErrorMessage(null);
    setEvalSubmitted(false);

    try {
      const result = await api.analyzeQuery(selectedDataset.id, q);
      setAnalysisResult(result);
    } catch (err: any) {
      setErrorMessage(err.response?.data?.detail || 'Gagal memproses query.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopyFormula = (formula: string) => {
    navigator.clipboard.writeText(formula);
    setCopiedFormula(true);
    setTimeout(() => setCopiedFormula(false), 2000);
  };

  const handleExportExcel = async () => {
    if (!analysisResult) return;
    setIsExporting(true);
    try {
      const res = await api.exportReport(analysisResult.analysis_id, {
        table_headers: analysisResult.table_headers,
        table_rows: analysisResult.table_rows,
        calculation_summary: analysisResult.calculation_summary,
      });
      // Trigger download
      window.open(`http://localhost:8000${res.download_url}`, '_blank');
    } catch (err) {
      alert('Gagal mengekspor file Excel.');
    } finally {
      setIsExporting(false);
    }
  };

  const handleSubmitEvaluation = async () => {
    if (!analysisResult) return;
    try {
      await api.submitEvaluation({
        analysis_id: analysisResult.analysis_id,
        expected_formula: analysisResult.decision.formula_id,
        is_formula_correct: true,
        manual_time_seconds: 135.0,
        notes: 'Verifikasi ground truth pengguna',
      });
      setEvalSubmitted(true);
    } catch (err) {
      alert('Gagal mencatat evaluasi.');
    }
  };

  if (!selectedDataset) {
    return (
      <div className="content-body animate-fade-in">
        <div className="glass-panel" style={{ padding: '3rem', textAlign: 'center', color: '#94a3b8' }}>
          <Sparkles size={40} color="#64748b" style={{ margin: '0 auto 1rem' }} />
          <h3>Silakan pilih atau unggah dataset terlebih dahulu untuk menjalankan AI Data Query.</h3>
        </div>
      </div>
    );
  }

  return (
    <div className="content-body animate-fade-in">
      {/* Header */}
      <div style={{ marginBottom: '1.5rem' }}>
        <h1 style={{ fontSize: '1.6rem', fontWeight: 800, color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <Sparkles size={28} color="#10b981" />
          AI Natural Language Query & Formula Modeling
        </h1>
        <p style={{ color: '#94a3b8', fontSize: '0.9rem', marginTop: '0.25rem' }}>
          Jelaskan kebutuhan laporan tutup buku dalam bahasa alami. Sistem otomatis mengekstrak intent, mencocokkan kolom, menentukan formula Excel secara deterministik, dan menjalankan kalkulasi.
        </p>
      </div>

      {/* Query Input Box */}
      <div className="glass-panel" style={{ padding: '1.5rem', marginBottom: '2rem' }}>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleAnalyze();
          }}
          style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}
        >
          <div style={{ flex: 1, minWidth: '280px', position: 'relative' }}>
            <input
              type="text"
              value={queryInput}
              onChange={(e) => setQueryInput(e.target.value)}
              placeholder="Contoh: Buat rekap jumlah barang keluar per merek untuk Februari 2024"
              style={{
                width: '100%',
                padding: '0.85rem 1.25rem',
                background: '#0d1322',
                border: '1px solid rgba(16, 185, 129, 0.4)',
                borderRadius: '12px',
                color: '#f8fafc',
                fontSize: '0.95rem',
                outline: 'none',
                boxShadow: '0 0 16px rgba(16, 185, 129, 0.15)'
              }}
            />
          </div>
          <button
            type="submit"
            disabled={isLoading}
            className="btn btn-primary"
            style={{ padding: '0.85rem 1.75rem', fontSize: '0.95rem' }}
          >
            {isLoading ? (
              <span>Memproses AI & Decision Engine...</span>
            ) : (
              <>
                <Send size={18} />
                <span>Analisis & Tentukan Rumus</span>
              </>
            )}
          </button>
        </form>

        {/* Suggestion Chips */}
        <div style={{ marginTop: '1rem' }}>
          <div style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 600, marginBottom: '0.5rem' }}>
            Contoh Pertanyaan Cepat (Klik untuk coba):
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
            {sampleQueries.map((sq, idx) => (
              <button
                key={idx}
                onClick={() => {
                  setQueryInput(sq);
                  handleAnalyze(sq);
                }}
                className="btn btn-ghost"
                style={{
                  background: 'rgba(255, 255, 255, 0.04)',
                  border: '1px solid rgba(255, 255, 255, 0.08)',
                  padding: '0.35rem 0.75rem',
                  fontSize: '0.75rem',
                  borderRadius: '999px',
                  color: '#cbd5e1'
                }}
              >
                {sq}
              </button>
            ))}
          </div>
        </div>

        {errorMessage && (
          <div style={{
            marginTop: '1rem',
            padding: '0.75rem',
            borderRadius: '8px',
            background: 'rgba(244, 63, 94, 0.15)',
            color: '#fb7185',
            fontSize: '0.85rem'
          }}>
            {errorMessage}
          </div>
        )}
      </div>

      {/* Visual Pipeline & Results */}
      {analysisResult && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {/* STEP-BY-STEP HYBRID AI PIPELINE CARD */}
          <div className="glass-panel" style={{ padding: '1.5rem', border: '1px solid rgba(16, 185, 129, 0.3)' }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: '1.25rem',
              paddingBottom: '0.75rem',
              borderBottom: '1px solid rgba(255, 255, 255, 0.08)'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                <ShieldCheck size={22} color="#10b981" />
                <div>
                  <span style={{ fontWeight: 800, fontSize: '1.15rem', color: '#f8fafc' }}>
                    Hybrid AI Decision Pipeline
                  </span>
                  <span style={{ marginLeft: '0.6rem', fontSize: '0.75rem', padding: '0.2rem 0.6rem', borderRadius: '12px', background: 'rgba(99, 102, 241, 0.2)', color: '#818cf8', fontWeight: 700 }}>
                    LLM + ML Classifier + Rule Gatekeeper
                  </span>
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#94a3b8', fontSize: '0.8rem' }}>
                <Clock size={14} color="#60a5fa" />
                <span>Waktu Pemrosesan: <strong>{analysisResult.execution_time_ms} ms</strong></span>
              </div>
            </div>

            {/* Low Confidence Warning Gate (< 70%) */}
            {(!analysisResult.decision.is_confident || (analysisResult.decision.ml_confidence && analysisResult.decision.ml_confidence < 0.70)) && (
              <div style={{
                marginBottom: '1.25rem',
                padding: '0.85rem 1.15rem',
                borderRadius: '8px',
                background: 'rgba(245, 158, 11, 0.15)',
                border: '1px solid rgba(245, 158, 11, 0.4)',
                color: '#fde68a',
                fontSize: '0.88rem',
                display: 'flex',
                alignItems: 'center',
                gap: '0.6rem'
              }}>
                <AlertCircle size={18} color="#f59e0b" />
                <span>
                  <strong>Peringatan AI:</strong> AI belum yakin dengan metode yang dipilih (Confidence: {((analysisResult.decision.ml_confidence || 0.5) * 100).toFixed(0)}% &lt; 70%). Silakan konfirmasi kebutuhan laporan atau sesuaikan kriteria filter.
                </span>
              </div>
            )}

            {/* 8-Stage Pipeline Grid */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
              gap: '0.85rem',
              marginBottom: '1.25rem'
            }}>
              {/* 1. User Request */}
              <div style={{ background: 'rgba(0, 0, 0, 0.25)', padding: '0.9rem', borderRadius: '10px', border: '1px solid rgba(255, 255, 255, 0.06)' }}>
                <div style={{ fontSize: '0.7rem', color: '#94a3b8', fontWeight: 700, textTransform: 'uppercase', marginBottom: '0.3rem' }}>
                  1. User Request
                </div>
                <div style={{ fontSize: '0.82rem', color: '#f8fafc', fontWeight: 600, fontStyle: 'italic', wordBreak: 'break-word' }}>
                  "{analysisResult.user_query}"
                </div>
              </div>

              {/* 2. AI Interpretation */}
              <div style={{ background: 'rgba(0, 0, 0, 0.25)', padding: '0.9rem', borderRadius: '10px', border: '1px solid rgba(255, 255, 255, 0.06)' }}>
                <div style={{ fontSize: '0.7rem', color: '#10b981', fontWeight: 700, textTransform: 'uppercase', marginBottom: '0.3rem' }}>
                  2. AI Interpretation
                </div>
                <div style={{ fontSize: '0.85rem', color: '#f8fafc', fontWeight: 600 }}>
                  Op: <span style={{ color: '#34d399' }}>{analysisResult.parsed_intent.operation}</span> ({analysisResult.parsed_intent.intent})
                </div>
                <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '0.2rem' }}>
                  Granularity: {analysisResult.parsed_intent.time_granularity}
                </div>
              </div>

              {/* 3. Detected Fields */}
              <div style={{ background: 'rgba(0, 0, 0, 0.25)', padding: '0.9rem', borderRadius: '10px', border: '1px solid rgba(255, 255, 255, 0.06)' }}>
                <div style={{ fontSize: '0.7rem', color: '#3b82f6', fontWeight: 700, textTransform: 'uppercase', marginBottom: '0.3rem' }}>
                  3. Detected Fields
                </div>
                <div style={{ fontSize: '0.8rem', color: '#f8fafc' }}>
                  Target: <strong style={{ color: '#60a5fa' }}>{analysisResult.parsed_intent.target_field || '-'}</strong>
                </div>
                <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '0.15rem' }}>
                  Group: {analysisResult.parsed_intent.group_by.join(', ') || 'Grand Total'}
                </div>
              </div>

              {/* 4. Filters */}
              <div style={{ background: 'rgba(0, 0, 0, 0.25)', padding: '0.9rem', borderRadius: '10px', border: '1px solid rgba(255, 255, 255, 0.06)' }}>
                <div style={{ fontSize: '0.7rem', color: '#f59e0b', fontWeight: 700, textTransform: 'uppercase', marginBottom: '0.3rem' }}>
                  4. Filters ({analysisResult.parsed_intent.filters.length})
                </div>
                {analysisResult.parsed_intent.filters.length > 0 ? (
                  analysisResult.parsed_intent.filters.map((f, i) => (
                    <div key={i} style={{ fontSize: '0.75rem', color: '#fbbf24', marginTop: '0.15rem' }}>
                      • {f.field} {f.operator} {Array.isArray(f.value) ? f.value.join(' .. ') : String(f.value)}
                    </div>
                  ))
                ) : (
                  <div style={{ fontSize: '0.75rem', color: '#64748b' }}>0 filter criteria</div>
                )}
              </div>

              {/* 5. ML Prediction & Confidence */}
              <div style={{ background: 'rgba(139, 92, 246, 0.12)', padding: '0.9rem', borderRadius: '10px', border: '1px solid rgba(139, 92, 246, 0.35)' }}>
                <div style={{ fontSize: '0.7rem', color: '#a78bfa', fontWeight: 700, textTransform: 'uppercase', marginBottom: '0.3rem' }}>
                  5. ML Prediction (Random Forest)
                </div>
                <div style={{ fontSize: '1rem', fontWeight: 800, color: '#c084fc' }}>
                  {analysisResult.decision.ml_prediction || analysisResult.decision.formula_name}
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginTop: '0.25rem' }}>
                  <span style={{ fontSize: '0.75rem', color: '#cbd5e1' }}>Confidence:</span>
                  <span style={{
                    fontSize: '0.75rem',
                    fontWeight: 700,
                    color: (analysisResult.decision.ml_confidence || 0.95) >= 0.7 ? '#34d399' : '#f59e0b'
                  }}>
                    {(((analysisResult.decision.ml_confidence || 0.95)) * 100).toFixed(0)}%
                  </span>
                </div>
              </div>

              {/* 6. Rule Validation Gatekeeper */}
              <div style={{ background: 'rgba(0, 0, 0, 0.25)', padding: '0.9rem', borderRadius: '10px', border: '1px solid rgba(255, 255, 255, 0.06)' }}>
                <div style={{ fontSize: '0.7rem', color: '#ec4899', fontWeight: 700, textTransform: 'uppercase', marginBottom: '0.3rem' }}>
                  6. Rule Validation Gate
                </div>
                <div style={{ marginTop: '0.2rem' }}>
                  <span style={{
                    display: 'inline-block',
                    padding: '0.2rem 0.6rem',
                    borderRadius: '6px',
                    fontSize: '0.75rem',
                    fontWeight: 800,
                    background: analysisResult.decision.rule_validation_status === 'CORRECTED_BY_RULE'
                      ? 'rgba(245, 158, 11, 0.2)'
                      : 'rgba(16, 185, 129, 0.2)',
                    color: analysisResult.decision.rule_validation_status === 'CORRECTED_BY_RULE'
                      ? '#fbbf24'
                      : '#34d399',
                    border: `1px solid ${analysisResult.decision.rule_validation_status === 'CORRECTED_BY_RULE' ? 'rgba(245, 158, 11, 0.4)' : 'rgba(16, 185, 129, 0.4)'}`
                  }}>
                    {analysisResult.decision.rule_validation_status || 'VALID'}
                  </span>
                </div>
                <div style={{ fontSize: '0.72rem', color: '#94a3b8', marginTop: '0.35rem', lineHeight: '1.2' }}>
                  {analysisResult.decision.rule_validation_status === 'CORRECTED_BY_RULE'
                    ? 'Rule Engine mengoreksi prediksi ML'
                    : 'Lolos verifikasi aturan Knowledge Base'}
                </div>
              </div>

              {/* 7. Final Formula */}
              <div style={{ background: 'rgba(16, 185, 129, 0.1)', padding: '0.9rem', borderRadius: '10px', border: '1px solid rgba(16, 185, 129, 0.35)' }}>
                <div style={{ fontSize: '0.7rem', color: '#34d399', fontWeight: 700, textTransform: 'uppercase', marginBottom: '0.3rem' }}>
                  7. Final Formula
                </div>
                <div style={{ fontSize: '1.05rem', fontWeight: 800, color: '#10b981' }}>
                  {analysisResult.decision.formula_name}
                </div>
                <div style={{ fontSize: '0.72rem', color: '#a7f3d0', marginTop: '0.2rem' }}>
                  {analysisResult.decision.category}
                </div>
              </div>

              {/* 8. Result Preview */}
              <div style={{ background: 'rgba(59, 130, 246, 0.1)', padding: '0.9rem', borderRadius: '10px', border: '1px solid rgba(59, 130, 246, 0.35)' }}>
                <div style={{ fontSize: '0.7rem', color: '#60a5fa', fontWeight: 700, textTransform: 'uppercase', marginBottom: '0.3rem' }}>
                  8. Calculation Result
                </div>
                <div style={{ fontSize: '0.95rem', fontWeight: 800, color: '#93c5fd', wordBreak: 'break-word' }}>
                  {analysisResult.calculation_summary?.calculated_result != null
                    ? (typeof analysisResult.calculation_summary.calculated_result === 'number'
                        ? Number(analysisResult.calculation_summary.calculated_result).toLocaleString('id-ID')
                        : String(analysisResult.calculation_summary.calculated_result))
                    : (analysisResult.calculation_summary?.grand_total != null
                        ? (typeof analysisResult.calculation_summary.grand_total === 'number'
                            ? Number(analysisResult.calculation_summary.grand_total).toLocaleString('id-ID')
                            : String(analysisResult.calculation_summary.grand_total))
                        : `${analysisResult.table_rows.length} Baris Data`)}
                </div>
                <div style={{ fontSize: '0.72rem', color: '#cbd5e1', marginTop: '0.2rem' }}>
                  {analysisResult.table_rows.length} baris diproses
                </div>
              </div>
            </div>

            {/* Generated Excel Formula Banner */}
            <div style={{ marginBottom: '1rem' }}>
              <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#94a3b8', marginBottom: '0.4rem' }}>
                Formula Excel yang Dihasilkan (Posisi Kolom Aktual Sesuai Dataset):
              </div>
              <div className="formula-code">
                <span>{analysisResult.decision.generated_excel_formula}</span>
                <button
                  onClick={() => handleCopyFormula(analysisResult.decision.generated_excel_formula)}
                  className="btn btn-ghost"
                  style={{ padding: '0.3rem 0.6rem', color: '#38bdf8', fontSize: '0.75rem' }}
                >
                  {copiedFormula ? <Check size={14} color="#10b981" /> : <Copy size={14} />}
                  <span>{copiedFormula ? 'Tersalin' : 'Salin Formula'}</span>
                </button>
              </div>
            </div>

            {/* Rule Decision / Knowledge Base Explanation Box */}
            <div style={{
              background: 'rgba(16, 185, 129, 0.08)',
              border: '1px solid rgba(16, 185, 129, 0.25)',
              borderRadius: '8px',
              padding: '0.85rem 1.15rem',
              fontSize: '0.85rem',
              color: '#d1fae5'
            }}>
              <strong>Log Keputusan Rule & Knowledge Base: </strong>
              {analysisResult.decision.rule_decision || analysisResult.decision.reason}
            </div>
          </div>

          {/* RESULTS TABLE & CHART SECTION */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: analysisResult.chart_data && analysisResult.chart_data.length > 0 ? '1fr 1fr' : '1fr',
            gap: '1.5rem',
            maxWidth: '100%',
            overflow: 'hidden'
          }}>
            {/* Table Result */}
            <div className="glass-panel" style={{ padding: '1.5rem', maxWidth: '100%', overflow: 'hidden' }}>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                flexWrap: 'wrap',
                gap: '0.75rem',
                marginBottom: '1rem'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', flexWrap: 'wrap' }}>
                  <span style={{ fontWeight: 700, fontSize: '1.05rem', color: '#f8fafc' }}>
                    {analysisResult.decision.formula_id === 'FILTER' || analysisResult.parsed_intent.intent === 'filter_recap'
                      ? 'Tabel Data Baris Terfilter'
                      : 'Tabel Hasil Perhitungan'}
                  </span>
                  <span style={{
                    fontSize: '0.75rem',
                    padding: '0.15rem 0.55rem',
                    borderRadius: '10px',
                    background: 'rgba(59, 130, 246, 0.2)',
                    color: '#60a5fa',
                    fontWeight: 600
                  }}>
                    {analysisResult.table_rows.length} Baris Data
                  </span>
                  <span style={{
                    fontSize: '0.75rem',
                    padding: '0.15rem 0.55rem',
                    borderRadius: '10px',
                    background: 'rgba(16, 185, 129, 0.2)',
                    color: '#34d399',
                    fontWeight: 600
                  }}>
                    {analysisResult.table_headers.length} Kolom
                  </span>
                  <span style={{ fontSize: '0.72rem', color: '#64748b', fontStyle: 'italic' }}>
                    (Scroll ↕ dan ↔ di dalam tabel)
                  </span>
                </div>
                <button
                  onClick={handleExportExcel}
                  disabled={isExporting}
                  className="btn btn-primary"
                  style={{ padding: '0.45rem 0.85rem', fontSize: '0.8rem' }}
                >
                  <Download size={14} />
                  <span>{isExporting ? 'Generating...' : 'Export Excel (.xlsx)'}</span>
                </button>
              </div>

              <div className="modern-table-container" style={{ maxHeight: '460px', overflowY: 'auto', overflowX: 'auto', maxWidth: '100%' }}>
                <table className="modern-table" style={{ minWidth: '100%', width: 'max-content' }}>
                  <thead>
                    <tr>
                      {analysisResult.table_headers.map((h, i) => (
                        <th key={i}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {analysisResult.table_rows.map((row, rIdx) => (
                      <tr key={rIdx}>
                        {analysisResult.table_headers.map((h, cIdx) => (
                          <td key={cIdx} style={{
                            fontWeight: typeof row[h] === 'number' ? 600 : 400,
                            fontFamily: typeof row[h] === 'number' ? 'var(--font-mono)' : 'inherit',
                            textAlign: typeof row[h] === 'number' ? 'right' : 'left'
                          }}>
                            {typeof row[h] === 'number' ? row[h].toLocaleString() : String(row[h] ?? '-')}
                          </td>
                        ))}
                      </tr>

                    ))}
                  </tbody>
                </table>
              </div>

              {/* Grand Total Footer if calculated */}
              {analysisResult.calculation_summary.grand_total !== undefined && (
                <div style={{
                  marginTop: '1rem',
                  padding: '0.75rem 1rem',
                  background: 'rgba(16, 185, 129, 0.12)',
                  borderRadius: '8px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  fontWeight: 700
                }}>
                  <span style={{ color: '#f8fafc' }}>GRAND TOTAL</span>
                  <span style={{ color: '#34d399', fontSize: '1.2rem', fontFamily: 'var(--font-mono)' }}>
                    {analysisResult.calculation_summary.grand_total.toLocaleString()}
                  </span>
                </div>
              )}
            </div>

            {/* Dynamic Recharts Chart */}
            {analysisResult.chart_data && analysisResult.chart_data.length > 0 && (
              <div className="glass-panel" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column' }}>
                <div style={{ fontWeight: 700, fontSize: '1.05rem', color: '#f8fafc', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <BarChart3 size={18} color="#60a5fa" />
                  <span>Visualisasi Distribusi</span>
                </div>
                <div style={{ flex: 1, minHeight: '280px' }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={analysisResult.chart_data}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                      <XAxis dataKey="name" stroke="#94a3b8" fontSize={12} />
                      <YAxis stroke="#94a3b8" fontSize={12} />
                      <Tooltip
                        contentStyle={{
                          background: '#131c2e',
                          border: '1px solid rgba(255,255,255,0.1)',
                          borderRadius: '8px',
                          color: '#f8fafc'
                        }}
                      />
                      <Bar dataKey="value" fill="#10b981" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )}
          </div>

          {/* Research Evaluation Feedback Card */}
          <div className="glass-panel" style={{
            padding: '1.25rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '1rem',
            border: '1px solid rgba(59, 130, 246, 0.25)',
            background: 'rgba(59, 130, 246, 0.05)'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <Award size={24} color="#60a5fa" />
              <div>
                <div style={{ fontWeight: 700, fontSize: '0.9rem', color: '#f8fafc' }}>
                  Modul Evaluasi & Riset Magang
                </div>
                <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
                  Simpan hasil pengujian ini ke dalam basis data benchmark untuk menghitung Formula Selection Accuracy.
                </div>
              </div>
            </div>

            <button
              onClick={handleSubmitEvaluation}
              disabled={evalSubmitted}
              className="btn btn-secondary"
              style={{
                fontSize: '0.8rem',
                borderColor: evalSubmitted ? 'rgba(16, 185, 129, 0.4)' : undefined,
                color: evalSubmitted ? '#34d399' : undefined
              }}
            >
              {evalSubmitted ? <CheckCircle2 size={16} color="#10b981" /> : <Award size={16} />}
              <span>{evalSubmitted ? 'Tercatat di Evaluasi' : 'Validasi Sebagai Ground Truth'}</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
