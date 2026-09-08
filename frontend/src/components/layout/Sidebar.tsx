import React from 'react';
import {
  LayoutDashboard,
  UploadCloud,
  FileSpreadsheet,
  Binary,
  Sparkles,
  BookOpen,
  FileCheck2,
  SlidersHorizontal,
  ActivitySquare,
  Building2,
} from 'lucide-react';

export type NavTab =
  | 'dashboard'
  | 'upload_preview'
  | 'profiling'
  | 'ai_query'
  | 'formula_kb'
  | 'templates'
  | 'simulation'
  | 'evaluation';

interface SidebarProps {
  activeTab: NavTab;
  setActiveTab: (tab: NavTab) => void;
  datasetCount: number;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  setActiveTab,
  datasetCount,
}) => {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard & KPI', icon: LayoutDashboard },
    { id: 'upload_preview', label: 'Upload & Preview Data', icon: UploadCloud, badge: datasetCount > 0 ? `${datasetCount}` : undefined },
    { id: 'profiling', label: 'Data Profiling', icon: Binary },
    { id: 'ai_query', label: 'AI Natural Language Query', icon: Sparkles, highlight: true },
    { id: 'formula_kb', label: 'Formula Knowledge Base', icon: BookOpen },
    { id: 'templates', label: 'Template Tutup Buku', icon: FileCheck2 },
    { id: 'simulation', label: 'What-If Simulation', icon: SlidersHorizontal },
    { id: 'evaluation', label: 'Research & Evaluation', icon: ActivitySquare },
  ];

  return (
    <aside style={{
      width: '280px',
      background: '#0d1322',
      borderRight: '1px solid rgba(255, 255, 255, 0.08)',
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      flexShrink: 0
    }}>
      {/* Brand Header */}
      <div style={{
        padding: '1.5rem 1.25rem',
        borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
        display: 'flex',
        alignItems: 'center',
        gap: '0.75rem'
      }}>
        <div style={{
          width: '40px',
          height: '40px',
          borderRadius: '10px',
          background: 'linear-gradient(135deg, #10b981, #059669)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 4px 12px rgba(16, 185, 129, 0.35)'
        }}>
          <Building2 size={22} color="#ffffff" />
        </div>
        <div>
          <div style={{ fontWeight: 800, fontSize: '1rem', letterSpacing: '-0.02em', color: '#ffffff' }}>
            SMART EXCEL
          </div>
          <div style={{ fontSize: '0.7rem', color: '#10b981', fontWeight: 600, letterSpacing: '0.05em' }}>
            PTPN AI MODELING
          </div>
        </div>
      </div>

      {/* Navigation List */}
      <nav style={{ flex: 1, padding: '1rem 0.75rem', overflowY: 'auto' }}>
        <div style={{ fontSize: '0.675rem', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.08em', padding: '0.5rem 0.75rem 0.5rem' }}>
          Menu Utama
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id as NavTab)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.75rem',
                  padding: '0.7rem 0.85rem',
                  borderRadius: '10px',
                  border: isActive ? '1px solid rgba(16, 185, 129, 0.4)' : '1px solid transparent',
                  background: isActive
                    ? 'rgba(16, 185, 129, 0.12)'
                    : item.highlight
                    ? 'rgba(59, 130, 246, 0.06)'
                    : 'transparent',
                  color: isActive ? '#34d399' : '#94a3b8',
                  fontWeight: isActive ? 600 : 500,
                  fontSize: '0.85rem',
                  cursor: 'pointer',
                  textAlign: 'left',
                  transition: 'all 0.18s ease',
                  width: '100%',
                }}
              >
                <Icon size={18} color={isActive ? '#34d399' : item.highlight ? '#60a5fa' : '#94a3b8'} />
                <span style={{ flex: 1 }}>{item.label}</span>
                {item.badge && (
                  <span style={{
                    background: '#10b981',
                    color: '#ffffff',
                    fontSize: '0.7rem',
                    fontWeight: 700,
                    padding: '0.1rem 0.45rem',
                    borderRadius: '999px'
                  }}>
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </nav>

      {/* Footer Info */}
      <div style={{
        padding: '1.25rem',
        borderTop: '1px solid rgba(255, 255, 255, 0.08)',
        background: 'rgba(0, 0, 0, 0.2)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <div style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            background: '#10b981',
            boxShadow: '0 0 8px #10b981'
          }} />
          <span style={{ fontSize: '0.75rem', color: '#94a3b8', fontWeight: 500 }}>
            Deterministic Engine Active
          </span>
        </div>
        <div style={{ fontSize: '0.7rem', color: '#64748b', marginTop: '0.25rem' }}>
          PTPN Internship Project v1.0
        </div>
      </div>
    </aside>
  );
};
