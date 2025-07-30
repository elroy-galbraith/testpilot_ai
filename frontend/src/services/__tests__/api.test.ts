import axios from 'axios';
import { apiService } from '../api';
import { GenerateRequest, ExecuteRequest, FeedbackRequest } from '../../types/api';

// Mock axios
jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

describe('ApiService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Reset the singleton instance
    (apiService as any).client = mockedAxios.create();
  });

  describe('generateTest', () => {
    it('should successfully generate a test', async () => {
      const mockResponse = {
        data: {
          testCaseId: 'test-123',
          code: 'console.log("test");',
          message: 'Test generated successfully'
        }
      };

      mockedAxios.post.mockResolvedValueOnce(mockResponse);

      const request: GenerateRequest = {
        spec: 'Test the login functionality',
        framework: 'playwright',
        language: 'javascript'
      };

      const result = await apiService.generateTest(request);

      expect(mockedAxios.post).toHaveBeenCalledWith(
        '/api/v1/generate',
        request
      );
      expect(result).toEqual(mockResponse.data);
    });

    it('should handle API errors', async () => {
      const mockError = {
        response: {
          data: {
            detail: 'Invalid specification',
            status_code: 400
          },
          status: 400
        }
      };

      mockedAxios.post.mockRejectedValueOnce(mockError);

      const request: GenerateRequest = {
        spec: '',
        framework: 'playwright'
      };

      await expect(apiService.generateTest(request)).rejects.toEqual({
        detail: 'Invalid specification',
        status_code: 400
      });
    });
  });

  describe('executeTest', () => {
    it('should successfully execute a test', async () => {
      const mockResponse = {
        data: {
          executionId: 'exec-123',
          status: 'pending',
          message: 'Test execution started'
        }
      };

      mockedAxios.post.mockResolvedValueOnce(mockResponse);

      const request: ExecuteRequest = {
        testCaseId: 'test-123',
        baseUrl: 'http://localhost:3000'
      };

      const result = await apiService.executeTest(request);

      expect(mockedAxios.post).toHaveBeenCalledWith(
        '/api/v1/execute',
        request
      );
      expect(result).toEqual(mockResponse.data);
    });
  });

  describe('getExecutionResult', () => {
    it('should successfully get execution results', async () => {
      const mockResponse = {
        data: {
          id: 'exec-123',
          testCaseId: 'test-123',
          status: 'completed',
          logs: 'Test passed successfully',
          screenshotUrl: 'http://example.com/screenshot.png',
          duration: 5.2,
          createdAt: '2023-01-01T00:00:00Z',
          updatedAt: '2023-01-01T00:00:05Z'
        }
      };

      mockedAxios.get.mockResolvedValueOnce(mockResponse);

      const result = await apiService.getExecutionResult('exec-123');

      expect(mockedAxios.get).toHaveBeenCalledWith(
        '/api/v1/results/exec-123'
      );
      expect(result).toEqual(mockResponse.data);
    });
  });

  describe('submitFeedback', () => {
    it('should successfully submit feedback', async () => {
      const mockResponse = {
        data: {
          id: 'feedback-123',
          message: 'Feedback submitted successfully'
        }
      };

      mockedAxios.post.mockResolvedValueOnce(mockResponse);

      const request: FeedbackRequest = {
        testCaseId: 'test-123',
        executionId: 'exec-123',
        rating: 5,
        comments: 'Great test execution!',
        metadata: {
          category: 'functionality',
          priority: 'high'
        }
      };

      const result = await apiService.submitFeedback(request);

      expect(mockedAxios.post).toHaveBeenCalledWith(
        '/api/v1/feedback',
        request
      );
      expect(result).toEqual(mockResponse.data);
    });
  });

  describe('getTestCases', () => {
    it('should successfully get test cases', async () => {
      const mockResponse = {
        data: [
          {
            id: 'test-1',
            title: 'Login Test',
            description: 'Test user login functionality',
            code: 'console.log("login test");',
            framework: 'playwright',
            language: 'javascript',
            status: 'completed',
            createdAt: '2023-01-01T00:00:00Z',
            updatedAt: '2023-01-01T00:00:00Z'
          }
        ]
      };

      mockedAxios.get.mockResolvedValueOnce(mockResponse);

      const result = await apiService.getTestCases();

      expect(mockedAxios.get).toHaveBeenCalledWith(
        '/api/v1/test-cases'
      );
      expect(result).toEqual(mockResponse.data);
    });
  });

  describe('getTestCase', () => {
    it('should successfully get a specific test case', async () => {
      const mockResponse = {
        data: {
          id: 'test-1',
          title: 'Login Test',
          description: 'Test user login functionality',
          code: 'console.log("login test");',
          framework: 'playwright',
          language: 'javascript',
          status: 'completed',
          createdAt: '2023-01-01T00:00:00Z',
          updatedAt: '2023-01-01T00:00:00Z'
        }
      };

      mockedAxios.get.mockResolvedValueOnce(mockResponse);

      const result = await apiService.getTestCase('test-1');

      expect(mockedAxios.get).toHaveBeenCalledWith(
        '/api/v1/test-cases/test-1'
      );
      expect(result).toEqual(mockResponse.data);
    });
  });

  describe('healthCheck', () => {
    it('should successfully perform health check', async () => {
      const mockResponse = {
        data: {
          status: 'healthy'
        }
      };

      mockedAxios.get.mockResolvedValueOnce(mockResponse);

      const result = await apiService.healthCheck();

      expect(mockedAxios.get).toHaveBeenCalledWith(
        '/health'
      );
      expect(result).toEqual(mockResponse.data);
    });
  });
}); 