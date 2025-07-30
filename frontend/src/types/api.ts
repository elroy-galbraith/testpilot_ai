export interface TestCase {
  id: string;
  title: string;
  description: string;
  code: string;
  framework: string;
  language: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  createdAt: string;
  updatedAt: string;
}

export interface ExecutionResult {
  id: string;
  testCaseId: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  logs: string;
  screenshotUrl?: string;
  logUrl?: string;
  duration?: number;
  error?: string;
  createdAt: string;
  updatedAt: string;
}

export interface GenerateRequest {
  spec: string;
  framework: 'playwright' | 'english';
  language?: 'javascript' | 'python';
}

export interface GenerateResponse {
  testCaseId: string;
  code: string;
  message: string;
}

export interface ExecuteRequest {
  testCaseId: string;
  baseUrl?: string;
}

export interface ExecuteResponse {
  executionId: string;
  status: string;
  message: string;
}

export interface FeedbackRequest {
  testCaseId: string;
  executionId: string;
  rating: number;
  comments: string;
  metadata?: Record<string, any>;
}

export interface FeedbackResponse {
  id: string;
  message: string;
}

export interface ApiError {
  detail: string;
  status_code: number;
} 