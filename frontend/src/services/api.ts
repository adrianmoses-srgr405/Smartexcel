import axios from 'axios';
import {
  Dataset,
  AnalysisResult,
  FormulaKnowledgeItem,
  EvaluationSummary,
} from '../types';

const API_BASE_URL = 'http://localhost:8000/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const api = {
  // Datasets
  uploadDataset: async (file: File): Promise<Dataset> => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await apiClient.post<Dataset>('/datasets/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },

  listDatasets: async (): Promise<Dataset[]> => {
    const res = await apiClient.get<Dataset[]>('/datasets');
    return res.data;
  },

  getDatasetDetail: async (datasetId: string): Promise<Dataset> => {
    const res = await apiClient.get<Dataset>(`/datasets/${datasetId}`);
    return res.data;
  },

  switchSheet: async (datasetId: string, sheetName: string): Promise<Dataset> => {
    const res = await apiClient.post<Dataset>(`/datasets/${datasetId}/switch-sheet`, {
      sheet_name: sheetName,
    });
    return res.data;
  },

  deleteDataset: async (datasetId: string): Promise<void> => {
    await apiClient.delete(`/datasets/${datasetId}`);
  },

  // Query & Analysis
  analyzeQuery: async (datasetId: string, query: string): Promise<AnalysisResult> => {
    const res = await apiClient.post<AnalysisResult>('/query/analyze', {
      dataset_id: datasetId,
      query: query,
    });
    return res.data;
  },

  // Formulas
  getKnowledgeBase: async (): Promise<FormulaKnowledgeItem[]> => {
    const res = await apiClient.get<FormulaKnowledgeItem[]>('/formulas/knowledge-base');
    return res.data;
  },

  trainModel: async (): Promise<{ status: string; message: string; classes: string[]; features_count: number }> => {
    const res = await apiClient.post('/formulas/train');
    return res.data;
  },

  // Reports
  exportReport: async (analysisId: string, payload: any): Promise<{ message: string; file_name: string; download_url: string }> => {
    const res = await apiClient.post(`/reports/export/${analysisId}`, payload);
    return res.data;
  },

  // Evaluation
  getEvaluationMetrics: async (): Promise<EvaluationSummary> => {
    const res = await apiClient.get<EvaluationSummary>('/evaluation/metrics');
    return res.data;
  },

  submitEvaluation: async (payload: {
    analysis_id: string;
    expected_formula?: string;
    is_formula_correct?: boolean;
    manual_time_seconds?: number;
    notes?: string;
  }): Promise<void> => {
    await apiClient.post('/evaluation/submit', payload);
  },

  // Templates
  getTemplates: async (): Promise<any[]> => {
    const res = await apiClient.get('/templates');
    return res.data;
  },
};
