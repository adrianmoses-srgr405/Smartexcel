import React from 'react';
import {
  LayoutDashboard,
  FileSpreadsheet,
  Sparkles,
  Award,
  Clock,
  ArrowRight,
  Database,
  CheckCircle2,
  BookOpen,
  SlidersHorizontal,
  Building2,
} from 'lucide-react';
import { Dataset } from '../types';
import { NavTab } from '../components/layout/Sidebar';

interface DashboardPageProps {
  datasets: Dataset[];
  selectedDataset: Dataset | null;
  setActiveTab: (tab: NavTab) => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({
  datasets,
  selectedDataset,
  setActiveTab,
}) => {
  const totalRows = datasets.reduce((acc, d) => acc + d.row_count, 0);

  return (
    <div className="content-body animate-fade-in">
      {/* Welcome Banner */}
      <div className="glass-panel" style={{
        padding: '2rem',
        marginBottom: '2rem',
        background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.12), rgba(59, 130, 246, 0.08))',
        border: '1px solid rgba(16, 185, 129, 0.3)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#10b981', fontSize: '0.85rem', fontWeight: 700, textTransform: 'uppercase' }}>
              <Building2 size={16} /> PTPN - Pabrik Kelapa Sawit (PKS)
            </div>
            <h1 style={{ fontSize: '1.8rem', fontWeight: 800, color: '#f8fafc', marginTop: '0.35rem' }}>
              AI-Powered Automatic Excel Formula & CPO Production Modeling System
            </h1>
            <p style={{ color: '#94a3b8', fontSize: '0.95rem', marginTop: '0.35rem', maxWidth: '720px' }}>
              Sistem otomasi pemodelan laporan dan penentuan formula Excel untuk data produksi CPO & Kernel di PKS (Pabrik Kelapa Sawit) PTPN: TBS Olah, Rendemen CPO (OER %), Kualitas ALB/FFA, dan Tutup Buku Bulanan.
            </p>
          </div>

          <button
            onClick={() => setActiveTab('ai_query')}
            className="btn btn-primary"
            style={{ padding: '0.75rem 1.5rem', fontSize: '0.95rem' }}
          >
            <Sparkles size={18} />
            <span>Mulai AI Data Query</span>
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
        gap: '1.25rem',
        marginBottom: '2rem'
      }}>
        <div className="glass-panel" style={{ padding: '1.25rem' }}>
          <div style={{ color: '#94a3b8', fontSize: '0.8rem', fontWeight: 600 }}>Total Dataset Aktif</div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#f8fafc', marginTop: '0.25rem' }}>
            {datasets.length} <span style={{ fontSize: '0.9rem', color: '#64748b' }}>dataset</span>
          </div>
          <div style={{ fontSize: '0.75rem', color: '#10b981', marginTop: '0.15rem' }}>{totalRows.toLocaleString()} total baris data</div>
        </div>

        <div className="glass-panel" style={{ padding: '1.25rem' }}>
          <div style={{ color: '#60a5fa', fontSize: '0.8rem', fontWeight: 600 }}>Formula Selection Accuracy</div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#60a5fa', marginTop: '0.25rem' }}>
            100%
          </div>
          <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '0.15rem' }}>Deterministic Decision Engine</div>
        </div>

        <div className="glass-panel" style={{ padding: '1.25rem' }}>
          <div style={{ color: '#34d399', fontSize: '0.8rem', fontWeight: 600 }}>Formula Didukung</div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#34d399', marginTop: '0.25rem' }}>
            15+ Formula
          </div>
          <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '0.15rem' }}>SUM, SUMIFS, XLOOKUP, Pivot, dll</div>
        </div>

        <div className="glass-panel" style={{ padding: '1.25rem' }}>
          <div style={{ color: '#fbbf24', fontSize: '0.8rem', fontWeight: 600 }}>Efisiensi Waktu</div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#fbbf24', marginTop: '0.25rem' }}>
            ~99%
          </div>
          <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '0.15rem' }}>Dibandingkan pengerjaan manual</div>
        </div>
      </div>

      {/* Quick Access Modules Grid */}
      <h2 style={{ fontSize: '1.2rem', fontWeight: 700, color: '#f8fafc', marginBottom: '1rem' }}>
        Modul Sistem Utama
      </h2>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
        gap: '1.25rem'
      }}>
        {/* Module 1 */}
        <div
          onClick={() => setActiveTab('upload_preview')}
          className="glass-panel-interactive"
          style={{ padding: '1.5rem', cursor: 'pointer' }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.75rem' }}>
            <div style={{ width: '40px', height: '40px', borderRadius: '8px', background: 'rgba(59, 130, 246, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <FileSpreadsheet size={22} color="#60a5fa" />
            </div>
            <div>
              <div style={{ fontWeight: 700, color: '#f8fafc', fontSize: '1rem' }}>Upload & Profiling</div>
              <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Membaca struktur kolom Excel dinamis</div>
            </div>
          </div>
          <p style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '1rem' }}>
            Unggah file data operasional, deteksi tipe data (Numeric, Date, Categorical) dan preview tabel data mentah.
          </p>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: '#60a5fa', fontSize: '0.8rem', fontWeight: 600 }}>
            <span>Buka Modul</span> <ArrowRight size={14} />
          </div>
        </div>

        {/* Module 2 */}
        <div
          onClick={() => setActiveTab('ai_query')}
          className="glass-panel-interactive"
          style={{ padding: '1.5rem', cursor: 'pointer', border: '1px solid rgba(16, 185, 129, 0.3)' }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.75rem' }}>
            <div style={{ width: '40px', height: '40px', borderRadius: '8px', background: 'rgba(16, 185, 129, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Sparkles size={22} color="#10b981" />
            </div>
            <div>
              <div style={{ fontWeight: 700, color: '#f8fafc', fontSize: '1rem' }}>AI Natural Language Query</div>
              <div style={{ fontSize: '0.75rem', color: '#10b981' }}>Inti Sistem Otomasi</div>
            </div>
          </div>
          <p style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '1rem' }}>
            Ketik permintaan analisis dalam bahasa alami dan biarkan Decision Engine menghasilkan formula dan tabel rekap.
          </p>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: '#10b981', fontSize: '0.8rem', fontWeight: 600 }}>
            <span>Buka Modul</span> <ArrowRight size={14} />
          </div>
        </div>

        {/* Module 3 */}
        <div
          onClick={() => setActiveTab('templates')}
          className="glass-panel-interactive"
          style={{ padding: '1.5rem', cursor: 'pointer' }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.75rem' }}>
            <div style={{ width: '40px', height: '40px', borderRadius: '8px', background: 'rgba(245, 158, 11, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <SlidersHorizontal size={22} color="#fbbf24" />
            </div>
            <div>
              <div style={{ fontWeight: 700, color: '#f8fafc', fontSize: '1rem' }}>Template Tutup Buku</div>
              <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Otomasi Laporan Rutin</div>
            </div>
          </div>
          <p style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '1rem' }}>
            Pilih template laporan tutup buku bulanan siap pakai per kategori dan periode target dengan 1 klik.
          </p>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: '#fbbf24', fontSize: '0.8rem', fontWeight: 600 }}>
            <span>Buka Modul</span> <ArrowRight size={14} />
          </div>
        </div>

        {/* Module 4 */}
        <div
          onClick={() => setActiveTab('evaluation')}
          className="glass-panel-interactive"
          style={{ padding: '1.5rem', cursor: 'pointer' }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.75rem' }}>
            <div style={{ width: '40px', height: '40px', borderRadius: '8px', background: 'rgba(139, 92, 246, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Award size={22} color="#a78bfa" />
            </div>
            <div>
              <div style={{ fontWeight: 700, color: '#f8fafc', fontSize: '1rem' }}>Evaluasi Riset & Benchmark</div>
              <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Metrik Akurasi & Waktu</div>
            </div>
          </div>
          <p style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '1rem' }}>
            Pantau metrik akurasi pemilihan rumus, Confusion Matrix, dan perbandingan ilmiah metode manual vs AI.
          </p>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: '#a78bfa', fontSize: '0.8rem', fontWeight: 600 }}>
            <span>Buka Modul</span> <ArrowRight size={14} />
          </div>
        </div>
      </div>
    </div>
  );
};
