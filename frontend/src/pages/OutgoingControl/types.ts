// Типы для Outgoing Control

export interface Document {
  id: string;
  title: string;
  content?: string;
  status: 'draft' | 'uploaded' | 'processing' | 'reviewed' | 'approved' | 'rejected' | 'needs_revision' | 'pending' | 'deleted';
  created_at: string;
  updated_at: string;
  file_path?: string;
  file_size?: number;
  file_type?: string;
  document_type?: string;
  extracted_text?: string;
  checks?: DocumentChecks;
  overall_score?: number;
  recommendations?: string;
  can_send?: boolean;
}

export interface DocumentChecks {
  spell_check?: CheckResult;
  style_analysis?: CheckResult;
  ethics_check?: CheckResult;
  terminology_check?: CheckResult;
  final_review?: CheckResult;
}

export interface CheckResult {
  status: 'pending' | 'running' | 'completed' | 'failed';
  score?: number;
  issues?: Issue[];
  suggestions?: string[];
  completed_at?: string;
}

export interface Issue {
  type: 'error' | 'warning' | 'suggestion';
  message: string;
  position?: {
    start: number;
    end: number;
  };
  severity: 'low' | 'medium' | 'high';
}

export interface ServiceStats {
  total_documents_processed: number;
  documents_approved: number;
  documents_rejected: number;
  documents_needing_revision: number;
  average_processing_time: number;
  most_common_issues: string[];
}

export interface ProcessingRequest {
  checks: {
    spell_check: boolean;
    style_analysis: boolean;
    ethics_check: boolean;
    terminology_check: boolean;
  };
  priority: 'low' | 'medium' | 'high';
}

export interface FinalReviewData {
  approved: boolean;
  comments?: string;
  reviewer_notes?: string;
}

// Реальные типы для результатов проверок из API
export interface SpellCheckResult {
  total_words: number;
  errors_found: number;
  suggestions: Array<{
    word: string;
    suggestions: string[];
    position: number;
  }>;
  corrected_text: string;
  confidence_score: number;
}

export interface StyleAnalysisResult {
  readability_score: number;
  formality_score: number;
  business_style_score: number;
  tone_analysis: {
    tone: string;
    confidence: number;
  };
  recommendations: string;
}

export interface EthicsCheckResult {
  ethics_score: number;
  violations_found: Array<{
    type: string;
    description: string;
    severity: string;
  }>;
  recommendations: string;
  is_approved: boolean;
}

export interface TerminologyCheckResult {
  terms_used: string[];
  incorrect_terms: Array<{
    term: string;
    position: number;
    issue: string;
  }>;
  suggestions: Array<{
    term: string;
    suggestion: string;
    confidence: number;
  }>;
  accuracy_score: number;
}
