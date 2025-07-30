import axios, { AxiosInstance, AxiosResponse } from 'axios';
import {
  TestCase,
  ExecutionResult,
  GenerateRequest,
  GenerateResponse,
  ExecuteRequest,
  ExecuteResponse,
  FeedbackRequest,
  FeedbackResponse,
  ApiError
} from '../types/api';

class ApiService {
  private client: AxiosInstance;
  private baseURL: string;

  constructor() {
    this.baseURL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
    this.client = axios.create({
      baseURL: this.baseURL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.data) {
          return Promise.reject(error.response.data as ApiError);
        }
        return Promise.reject({
          detail: error.message || 'Network error',
          status_code: error.response?.status || 500,
        } as ApiError);
      }
    );
  }

  // Test Generation
  async generateTest(request: GenerateRequest): Promise<GenerateResponse> {
    const response: AxiosResponse<GenerateResponse> = await this.client.post(
      '/api/v1/generate',
      request
    );
    return response.data;
  }

  // Test Execution
  async executeTest(request: ExecuteRequest): Promise<ExecuteResponse> {
    const response: AxiosResponse<ExecuteResponse> = await this.client.post(
      '/api/v1/execute',
      request
    );
    return response.data;
  }

  // Get Execution Results
  async getExecutionResult(executionId: string): Promise<ExecutionResult> {
    const response: AxiosResponse<ExecutionResult> = await this.client.get(
      `/api/v1/results/${executionId}`
    );
    return response.data;
  }

  // Submit Feedback
  async submitFeedback(request: FeedbackRequest): Promise<FeedbackResponse> {
    const response: AxiosResponse<FeedbackResponse> = await this.client.post(
      '/api/v1/feedback',
      request
    );
    return response.data;
  }

  // Get Test Cases (for dashboard listing)
  async getTestCases(): Promise<TestCase[]> {
    const response: AxiosResponse<TestCase[]> = await this.client.get(
      '/api/v1/test-cases'
    );
    return response.data;
  }

  // Get Test Case by ID
  async getTestCase(id: string): Promise<TestCase> {
    const response: AxiosResponse<TestCase> = await this.client.get(
      `/api/v1/test-cases/${id}`
    );
    return response.data;
  }

  // Health Check
  async healthCheck(): Promise<{ status: string }> {
    const response: AxiosResponse<{ status: string }> = await this.client.get(
      '/health'
    );
    return response.data;
  }
}

// Export singleton instance
export const apiService = new ApiService();
export default apiService; 