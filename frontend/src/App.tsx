import React, { useState, useEffect, Component, ErrorInfo, ReactNode } from 'react';
import { Sidebar, NavTab } from './components/layout/Sidebar';
import { Navbar } from './components/layout/Navbar';
import { DashboardPage } from './pages/DashboardPage';
import { UploadPreviewPage } from './pages/UploadPreviewPage';
import { ProfilingPage } from './pages/ProfilingPage';
import { AIQueryPage } from './pages/AIQueryPage';
import { FormulaKBPage } from './pages/FormulaKBPage';
import { TemplatesPage } from './pages/TemplatesPage';
import { SimulationPage } from './pages/SimulationPage';
import { EvaluationPage } from './pages/EvaluationPage';
import { Dataset } from './types';
import { api } from './services/api';

interface ErrorBoundaryProps {
  children: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  errorText: string;
}

class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, errorText: '' };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, errorText: error.message || 'Terjadi kesalahan pada tampilan UI.' };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '3rem', textAlign: 'center', color: '#f8fafc' }}>
          <div className="glass-panel" style={{ padding: '2rem', maxWidth: '600px', margin: '0 auto', border: '1px solid rgba(239, 68, 68, 0.4)' }}>
            <h3 style={{ color: '#ef4444', marginBottom: '0.8rem' }}>⚠️ Terjadi Kendala Tampilan</h3>
            <p style={{ color: '#94a3b8', fontSize: '0.9rem', marginBottom: '1.25rem' }}>{this.state.errorText}</p>
            <button
              onClick={() => {
                this.setState({ hasError: false, errorText: '' });
                window.location.reload();
              }}
              className="btn btn-primary"
            >
              Muat Ulang Halaman
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}


export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<NavTab>('dashboard');
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedDataset, setSelectedDataset] = useState<Dataset | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Initial Data Fetching
  useEffect(() => {
    const fetchDatasets = async () => {
      try {
        const list = await api.listDatasets();
        setDatasets(list);
        if (list.length > 0) {
          // Fetch full detail for the first dataset
          const detail = await api.getDatasetDetail(list[0].id);
          setSelectedDataset(detail);
        }
      } catch (err) {
        console.error('Failed to initialize datasets', err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchDatasets();
  }, []);

  const handleSelectDataset = async (ds: Dataset) => {
    try {
      const detail = await api.getDatasetDetail(ds.id);
      setSelectedDataset(detail);
    } catch (err) {
      setSelectedDataset(ds);
    }
  };

  const handleDatasetUploaded = (newDs: Dataset) => {
    setDatasets((prev) => [newDs, ...prev]);
    setSelectedDataset(newDs);
    setActiveTab('upload_preview');
  };

  const handleDatasetUpdated = (updatedDs: Dataset) => {
    setDatasets((prev) => prev.map((d) => (d.id === updatedDs.id ? updatedDs : d)));
    setSelectedDataset(updatedDs);
  };

  const handleDatasetDeleted = (deletedId: string) => {
    const updated = datasets.filter((d) => d.id !== deletedId);
    setDatasets(updated);
    if (selectedDataset?.id === deletedId) {
      setSelectedDataset(updated.length > 0 ? updated[0] : null);
    }
  };

  const handleApplyTemplateQuery = (queryText: string) => {
    setActiveTab('ai_query');
    // Handled in AIQueryPage
  };

  return (
    <div className="app-container">
      {/* Sidebar Navigation */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        datasetCount={datasets.length}
      />

      {/* Main Container */}
      <div className="main-content">
        {/* Top Navbar */}
        <Navbar
          datasets={datasets}
          selectedDataset={selectedDataset}
          onSelectDataset={handleSelectDataset}
          onUploadClick={() => setActiveTab('upload_preview')}
        />

        {/* Dynamic Page Content with Error Boundary */}
        <ErrorBoundary>
          {activeTab === 'dashboard' && (
            <DashboardPage
              datasets={datasets}
              selectedDataset={selectedDataset}
              setActiveTab={setActiveTab}
            />
          )}

          {activeTab === 'upload_preview' && (
            <UploadPreviewPage
              datasets={datasets}
              selectedDataset={selectedDataset}
              onSelectDataset={handleSelectDataset}
              onDatasetUploaded={handleDatasetUploaded}
              onDatasetDeleted={handleDatasetDeleted}
              onDatasetUpdated={handleDatasetUpdated}
            />
          )}

          {activeTab === 'profiling' && (
            <ProfilingPage selectedDataset={selectedDataset} />
          )}

          {activeTab === 'ai_query' && (
            <AIQueryPage selectedDataset={selectedDataset} />
          )}

          {activeTab === 'formula_kb' && <FormulaKBPage />}

          {activeTab === 'templates' && (
            <TemplatesPage
              selectedDataset={selectedDataset}
              onApplyTemplateQuery={handleApplyTemplateQuery}
            />
          )}

          {activeTab === 'simulation' && (
            <SimulationPage selectedDataset={selectedDataset} />
          )}

          {activeTab === 'evaluation' && <EvaluationPage />}
        </ErrorBoundary>
      </div>
    </div>
  );
};

export default App;
