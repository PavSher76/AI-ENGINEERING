// User types
export interface User {
  id: string;
  username: string;
  email: string;
  firstName: string;
  lastName: string;
  roles: string[];
  permissions: string[];
}

// Project types
export interface Project {
  id: string;
  name: string;
  description: string;
  projectCode: string;
  status: 'active' | 'inactive' | 'archived';
  createdAt: string;
  updatedAt: string;
}

// Document types
export interface Document {
  id: string;
  title: string;
  description?: string;
  filePath?: string;
  fileSize?: number;
  mimeType?: string;
  documentType?: string;
  collectionId?: string;
  projectId?: string;
  version: string;
  status: string;
  metadata?: Record<string, any>;
  isProcessed: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface DocumentCollection {
  id: string;
  name: string;
  description?: string;
  collectionType: 'normative' | 'chat' | 'input_data' | 'project' | 'archive' | 'analogues';
  projectId?: string;
  documentsCount?: number;
  createdAt: string;
  updatedAt: string;
}

// Chat types
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  metadata?: Record<string, any>;
}

export interface ChatSession {
  id: string;
  sessionId: string;
  title?: string;
  modelUsed?: string;
  messageCount: number;
  createdAt: string;
  updatedAt: string;
}

export interface ChatRequest {
  query: string;
  sessionId?: string;
  model?: string;
  temperature?: number;
  maxTokens?: number;
  collectionId?: string;
  projectId?: string;
}

export interface ChatResponse {
  response: string;
  model: string;
  contextUsed: boolean;
  relevantDocuments: Document[];
  sessionId?: string;
  createdAt: string;
}

// Calculation types
export interface Calculation {
  id: string;
  name: string;
  description?: string;
  calculationType: string;
  inputData: Record<string, any>;
  resultData: Record<string, any>;
  status: 'pending' | 'completed' | 'failed';
  confidence: number;
  modelUsed?: string;
  projectId?: string;
  createdAt: string;
  updatedAt: string;
}

export interface CalculationRequest {
  calculationType: string;
  inputData: Record<string, any>;
  parameters?: Record<string, any>;
  model?: string;
  projectId?: string;
}

export interface CalculationResponse {
  result: Record<string, any>;
  calculationType: string;
  inputData: Record<string, any>;
  confidence: number;
  modelUsed: string;
  createdAt: string;
}

// Analysis types
export interface Analysis {
  id: string;
  name: string;
  analysisType: string;
  targetId?: string;
  targetType?: string;
  analysisData: Record<string, any>;
  insights: Record<string, any>;
  recommendations: Record<string, any>;
  complianceScore: number;
  modelUsed?: string;
  projectId?: string;
  createdAt: string;
  updatedAt: string;
}

export interface AnalysisRequest {
  analysisType: string;
  projectId: string;
  documentTypes?: string[];
  standards?: string[];
  model?: string;
}

export interface AnalysisResponse {
  projectId: string;
  analysisType: string;
  results: Record<string, any>;
  complianceScore: number;
  recommendations: string[];
  modelUsed: string;
  createdAt: string;
}

// Report types
export interface Report {
  id: string;
  name: string;
  reportType: string;
  content: string;
  sections: string[];
  wordCount: number;
  templateUsed?: string;
  modelUsed?: string;
  projectId?: string;
  createdAt: string;
  updatedAt: string;
}

export interface ReportRequest {
  reportType: string;
  projectId: string;
  template?: string;
  sections?: string[];
  includeDocuments?: boolean;
  model?: string;
}

export interface ReportResponse {
  projectId: string;
  reportType: string;
  content: string;
  sections: string[];
  wordCount: number;
  generatedAt: string;
}

// Model types
export interface ModelInfo {
  name: string;
  size: number;
  modifiedAt?: string;
  family: string;
  format: string;
}

// API Response types
export interface ApiResponse<T> {
  data: T;
  message?: string;
  success: boolean;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  limit: number;
  hasNext: boolean;
  hasPrev: boolean;
}

// Search types
export interface SearchRequest {
  query: string;
  collectionId?: string;
  projectId?: string;
  limit?: number;
  threshold?: number;
  documentTypes?: string[];
}

export interface SearchResponse {
  query: string;
  results: Document[];
  scores: number[];
  total: number;
  searchTime?: number;
}

// File upload types
export interface FileUpload {
  file: File;
  collectionId?: string;
  projectId?: string;
  metadata?: Record<string, any>;
}

export interface UploadProgress {
  loaded: number;
  total: number;
  percentage: number;
}

// Validation types
export interface ValidationResult {
  isValid: boolean;
  errors: string[];
  warnings: string[];
  score: number;
}

// Integration types
export interface IntegrationConfig {
  type: 'enovia' | '3dexperience';
  url: string;
  credentials: Record<string, string>;
  settings: Record<string, any>;
}

// Context types
export interface ContextData {
  sessionId: string;
  contextType: string;
  data: Record<string, any>;
  expiresAt?: string;
}

// Dashboard types
export interface DashboardStats {
  totalProjects: number;
  totalDocuments: number;
  totalCalculations: number;
  totalReports: number;
  activeChatSessions: number;
  recentActivity: ActivityItem[];
}

export interface ActivityItem {
  id: string;
  type: 'document_upload' | 'calculation' | 'chat' | 'report' | 'analysis';
  description: string;
  timestamp: string;
  userId: string;
  projectId?: string;
}

// Error types
export interface ApiError {
  message: string;
  code?: string;
  details?: Record<string, any>;
  timestamp: string;
}

// Form types
export interface FormField {
  name: string;
  label: string;
  type: 'text' | 'number' | 'email' | 'password' | 'select' | 'textarea' | 'file';
  required?: boolean;
  options?: { value: string; label: string }[];
  validation?: {
    min?: number;
    max?: number;
    pattern?: string;
    message?: string;
  };
}

export interface FormData {
  [key: string]: any;
}

// Notification types
export interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
}

// Settings types
export interface UserSettings {
  theme: 'light' | 'dark';
  language: string;
  notifications: {
    email: boolean;
    push: boolean;
    chat: boolean;
  };
  defaultModel: string;
  autoSave: boolean;
}

export interface SystemSettings {
  maxFileSize: number;
  allowedFileTypes: string[];
  defaultCollectionTypes: string[];
  supportedModels: string[];
}
