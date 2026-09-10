import React, { useState, useEffect } from 'react';
import {
  BookOpen,
  Search,
  Filter,
  Code2,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  Sparkles,
} from 'lucide-react';
import { FormulaKnowledgeItem } from '../types';
import { api } from '../services/api';

export const FormulaKBPage: React.FC = () => {
  const [formulas, setFormulas] = useState<FormulaKnowledgeItem[]>([]);
  const [searchFilter, setSearchFilter] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('ALL');
  const [isLoading, setIsLoading] = useState(true);
  const [isTraining, setIsTraining] = useState(false);
  const [trainStatus, setTrainStatus] = useState<string | null>(null);

  const handleRetrain = async () => {
    setIsTraining(true);
    setTrainStatus(null);
    try {
      const res = await api.trainModel();
      const numClasses = res.classes?.length || (res as any).training_run?.classes?.length || 18;
      const acc = (res as any).accuracy != null ? `(Akurasi: ${((res as any).accuracy * 100).toFixed(1)}%)` : '';
      setTrainStatus(`Berhasil! ${res.message} ${numClasses} formula dipelajari ${acc}`.trim());
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || 'Gagal melatih model AI.';
      setTrainStatus(`Gagal: ${msg}`);
    } finally {
      setIsTraining(false);
    }
  };

  useEffect(() => {
    const fetchKB = async () => {
      try {
        const data = await api.getKnowledgeBase();
        setFormulas(data);
      } catch (err) {
        console.error('Failed to load formula knowledge base', err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchKB();
  }, []);

  const categories = ['ALL', 'Aggregation', 'Statistical', 'Lookup', 'Modeling'];

  const filteredFormulas = formulas.filter((f) => {
    const matchCat = selectedCategory === 'ALL' || f.category === selectedCategory;
    const matchSearch =
      f.name.toLowerCase().includes(searchFilter.toLowerCase()) ||
      f.description.toLowerCase().includes(searchFilter.toLowerCase()) ||
      f.keywords.some((k) => k.toLowerCase().includes(searchFilter.toLowerCase()));
    return matchCat && matchSearch;
  });

  return (
    <div className="content-body animate-fade-in">
      {/* Header */}
      <div style={{ marginBottom: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 style={{ fontSize: '1.6rem', fontWeight: 800, color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <BookOpen size={28} color="#10b981" />
            Formula Knowledge Base & Decision Matrix
          </h1>
          <p style={{ color: '#94a3b8', fontSize: '0.9rem', marginTop: '0.25rem' }}>
            Daftar aturan rumus Excel yang dapat dikembangkan secara modular untuk menunjang Deterministic Decision Engine.
          </p>
        </div>

        <button
          onClick={handleRetrain}
          disabled={isTraining}
          className="btn btn-primary"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.6rem 1.2rem',
            borderRadius: '8px',
            background: 'linear-gradient(135deg, #10b981, #059669)',
            boxShadow: '0 4px 12px rgba(16, 185, 129, 0.25)',
            cursor: isTraining ? 'not-allowed' : 'pointer',
            opacity: isTraining ? 0.7 : 1,
          }}
        >
          <Sparkles size={16} className={isTraining ? 'animate-spin' : ''} />
          {isTraining ? 'Melatih Model AI...' : 'Latih Ulang Model AI'}
        </button>
      </div>

      {trainStatus && (
        <div style={{
          padding: '0.75rem 1rem',
          borderRadius: '8px',
          marginBottom: '1.25rem',
          background: trainStatus.includes('Berhasil') ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
          border: `1px solid ${trainStatus.includes('Berhasil') ? 'rgba(16, 185, 129, 0.4)' : 'rgba(239, 68, 68, 0.4)'}`,
          color: trainStatus.includes('Berhasil') ? '#34d399' : '#f87171',
          fontSize: '0.85rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
        }}>
          {trainStatus.startsWith('Berhasil') ? <CheckCircle2 size={16} /> : <AlertCircle size={16} />}
          {trainStatus}
        </div>
      )}

      {/* Filter & Search Bar */}
      <div className="glass-panel" style={{
        padding: '1rem 1.25rem',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '1rem',
        marginBottom: '1.5rem'
      }}>
        {/* Category Pills */}
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className="btn"
              style={{
                padding: '0.35rem 0.85rem',
                fontSize: '0.8rem',
                background: selectedCategory === cat ? '#10b981' : 'rgba(255, 255, 255, 0.05)',
                color: selectedCategory === cat ? '#ffffff' : '#94a3b8',
                borderRadius: '999px',
                border: '1px solid rgba(255, 255, 255, 0.08)'
              }}
            >
              {cat}
            </button>
          ))}
        </div>

        {/* Search */}
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
            placeholder="Cari formula atau kata kunci..."
            value={searchFilter}
            onChange={(e) => setSearchFilter(e.target.value)}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#f8fafc',
              fontSize: '0.8rem',
              outline: 'none',
              width: '220px'
            }}
          />
        </div>
      </div>

      {/* Grid of Formulas */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(380px, 1fr))',
        gap: '1.25rem'
      }}>
        {filteredFormulas.map((f) => (
          <div key={f.id} className="glass-panel-interactive" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span className="badge badge-formula" style={{ fontSize: '0.85rem', padding: '0.3rem 0.65rem' }}>
                  {f.name}
                </span>
                <span className="badge badge-categorical" style={{ fontSize: '0.7rem' }}>
                  {f.category}
                </span>
              </div>
              <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
                Min: {f.min_filters} Filter | Max: {f.max_filters} Filter
              </span>
            </div>

            <p style={{ fontSize: '0.85rem', color: '#cbd5e1', marginBottom: '1rem', flex: 1 }}>
              {f.description}
            </p>

            <div style={{ marginBottom: '0.75rem' }}>
              <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginBottom: '0.3rem', fontWeight: 600 }}>
                Syntax Template:
              </div>
              <div className="formula-code" style={{ fontSize: '0.8rem', padding: '0.5rem 0.75rem' }}>
                {f.syntax_template}
              </div>
            </div>

            {/* Keywords */}
            <div>
              <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginBottom: '0.3rem', fontWeight: 600 }}>
                Kata Kunci Pemicu Intent:
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.3rem' }}>
                {f.keywords.map((kw, i) => (
                  <span key={i} style={{
                    background: 'rgba(255, 255, 255, 0.05)',
                    color: '#94a3b8',
                    padding: '0.15rem 0.45rem',
                    borderRadius: '4px',
                    fontSize: '0.7rem'
                  }}>
                    {kw}
                  </span>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
