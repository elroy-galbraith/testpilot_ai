import { renderHook, act } from '@testing-library/react';
import { useApi } from '../useApi';

// Mock function for testing
const mockApiFunction = jest.fn();

describe('useApi', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should initialize with default state', () => {
    const { result } = renderHook(() => useApi(mockApiFunction));

    expect(result.current.data).toBeNull();
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('should handle successful API calls', async () => {
    const mockData = { id: '1', name: 'Test' };
    mockApiFunction.mockResolvedValueOnce(mockData);

    const { result } = renderHook(() => useApi(mockApiFunction));

    await act(async () => {
      const response = await result.current.execute('param1', 'param2');
      expect(response).toEqual(mockData);
    });

    expect(result.current.data).toEqual(mockData);
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
    expect(mockApiFunction).toHaveBeenCalledWith('param1', 'param2');
  });

  it('should handle API errors', async () => {
    const mockError = {
      detail: 'API Error',
      status_code: 500
    };
    mockApiFunction.mockRejectedValueOnce(mockError);

    const { result } = renderHook(() => useApi(mockApiFunction));

    await act(async () => {
      const response = await result.current.execute();
      expect(response).toBeNull();
    });

    expect(result.current.data).toBeNull();
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toEqual(mockError);
  });

  it('should set loading state during API calls', async () => {
    let resolvePromise: (value: any) => void;
    const promise = new Promise((resolve) => {
      resolvePromise = resolve;
    });
    mockApiFunction.mockReturnValueOnce(promise);

    const { result } = renderHook(() => useApi(mockApiFunction));

    act(() => {
      result.current.execute();
    });

    expect(result.current.loading).toBe(true);

    await act(async () => {
      resolvePromise!({ id: '1' });
      await promise;
    });

    expect(result.current.loading).toBe(false);
  });

  it('should reset state when reset is called', async () => {
    const mockData = { id: '1' };
    mockApiFunction.mockResolvedValueOnce(mockData);

    const { result } = renderHook(() => useApi(mockApiFunction));

    await act(async () => {
      await result.current.execute();
    });

    expect(result.current.data).toEqual(mockData);

    act(() => {
      result.current.reset();
    });

    expect(result.current.data).toBeNull();
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('should clear error when starting a new request', async () => {
    const mockError = { detail: 'Error', status_code: 400 };
    mockApiFunction.mockRejectedValueOnce(mockError);

    const { result } = renderHook(() => useApi(mockApiFunction));

    // First call that fails
    await act(async () => {
      await result.current.execute();
    });

    expect(result.current.error).toEqual(mockError);

    // Second call that succeeds
    const mockData = { id: '1' };
    mockApiFunction.mockResolvedValueOnce(mockData);

    await act(async () => {
      await result.current.execute();
    });

    expect(result.current.error).toBeNull();
    expect(result.current.data).toEqual(mockData);
  });
}); 