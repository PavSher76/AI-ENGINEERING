import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import keycloak, { keycloakUtils } from './keycloak.ts';
import environment from '../config/environment.ts';

// API base URL
const API_BASE_URL = environment.api.baseUrl;

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config: AxiosRequestConfig) => {
    // Добавляем токен авторизации если пользователь аутентифицирован
    if (keycloak.authenticated && keycloak.token) {
      config.headers = {
        ...config.headers,
        Authorization: `Bearer ${keycloak.token}`,
      };
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle token refresh
api.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  async (error) => {
    const originalRequest = error.config;

    // Обрабатываем ошибки авторизации
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        // Пытаемся обновить токен
        const refreshed = await keycloakUtils.updateToken(30);
        if (refreshed && keycloak.token) {
          originalRequest.headers.Authorization = `Bearer ${keycloak.token}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        console.error('Ошибка обновления токена:', refreshError);
        // Если не удалось обновить токен, перенаправляем на страницу входа
        keycloakUtils.logout();
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

// API service classes
export class RAGService {
  static async searchDocuments(query: string, collectionId?: string, projectId?: string) {
    const response = await api.post('/rag/documents/search', {
      query,
      collection_id: collectionId,
      project_id: projectId,
      limit: 10,
      threshold: 0.7,
    });
    return response.data;
  }

  static async getCollections(projectId?: string, collectionType?: string) {
    const params = new URLSearchParams();
    if (projectId) params.append('project_id', projectId);
    if (collectionType) params.append('collection_type', collectionType);
    
    const response = await api.get(`/rag/collections?${params}`);
    return response.data;
  }

  static async uploadDocument(file: File, collectionId?: string, projectId?: string) {
    const formData = new FormData();
    formData.append('file', file);
    if (collectionId) formData.append('collection_id', collectionId);
    if (projectId) formData.append('project_id', projectId);

    const response = await api.post('/rag/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }
}

export class AINkService {
  static async chat(request: {
    query: string;
    sessionId?: string;
    model?: string;
    temperature?: number;
    maxTokens?: number;
    collectionId?: string;
    projectId?: string;
  }) {
    const response = await api.post('/ollama-service/chat', request);
    return response.data;
  }

  static async performCalculation(request: {
    calculationType: string;
    inputData: Record<string, any>;
    parameters?: Record<string, any>;
    model?: string;
    projectId?: string;
  }) {
    const response = await api.post('/ollama-service/calculate', request);
    return response.data;
  }

  static async analyzeProject(request: {
    analysisType: string;
    projectId: string;
    documentTypes?: string[];
    standards?: string[];
    model?: string;
  }) {
    const response = await api.post('/ollama-service/analyze', request);
    return response.data;
  }

  static async generateReport(request: {
    reportType: string;
    projectId: string;
    template?: string;
    sections?: string[];
    includeDocuments?: boolean;
    model?: string;
  }) {
    const response = await api.post('/ollama-service/generate-report', request);
    return response.data;
  }

  static async getAvailableModels() {
    const response = await api.get('/ollama-service/models');
    return response.data;
  }
}

export class ChatService {
  static async getChatHistory(sessionId: string, limit = 50) {
    const response = await api.get(`/chat/history/${sessionId}?limit=${limit}`);
    return response.data;
  }

  static async createChatSession(title?: string, projectId?: string) {
    const response = await api.post('/chat/sessions', {
      title,
      project_id: projectId,
    });
    return response.data;
  }

  static async getChatSessions(limit = 20) {
    const response = await api.get(`/chat/sessions?limit=${limit}`);
    return response.data;
  }
}

export class DocumentService {
  static async getDocuments(projectId?: string, collectionId?: string, documentType?: string) {
    const params = new URLSearchParams();
    if (projectId) params.append('project_id', projectId);
    if (collectionId) params.append('collection_id', collectionId);
    if (documentType) params.append('document_type', documentType);
    
    const response = await api.get(`/document/documents?${params}`);
    return response.data;
  }

  static async getDocument(documentId: string) {
    const response = await api.get(`/document/documents/${documentId}`);
    return response.data;
  }

  static async deleteDocument(documentId: string) {
    const response = await api.delete(`/document/documents/${documentId}`);
    return response.data;
  }
}

export class CalculationService {
  static async getCalculationHistory(projectId?: string, limit = 20) {
    const params = new URLSearchParams();
    if (projectId) params.append('project_id', projectId);
    params.append('limit', limit.toString());
    
    const response = await api.get(`/calculation/history?${params}`);
    return response.data;
  }

  static async getCalculation(calculationId: string) {
    const response = await api.get(`/calculation/calculations/${calculationId}`);
    return response.data;
  }
}

export class AnalyticsService {
  static async getProjectAnalytics(projectId: string) {
    const response = await api.get(`/analytics/projects/${projectId}`);
    return response.data;
  }

  static async getComplianceAnalysis(projectId: string, standards?: string[]) {
    const response = await api.post('/analytics/compliance', {
      project_id: projectId,
      standards,
    });
    return response.data;
  }

  static async getTechnicalAnalysis(projectId: string) {
    const response = await api.post('/analytics/technical', {
      project_id: projectId,
    });
    return response.data;
  }
}

export class ReportService {
  static async getReportHistory(projectId?: string, limit = 20) {
    const params = new URLSearchParams();
    if (projectId) params.append('project_id', projectId);
    params.append('limit', limit.toString());
    
    const response = await api.get(`/report/history?${params}`);
    return response.data;
  }

  static async getReport(reportId: string) {
    const response = await api.get(`/report/reports/${reportId}`);
    return response.data;
  }

  static async downloadReport(reportId: string) {
    const response = await api.get(`/report/reports/${reportId}/download`, {
      responseType: 'blob',
    });
    return response.data;
  }
}

export default api;
