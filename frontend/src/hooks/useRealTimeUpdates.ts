import { useEffect, useRef, useCallback } from 'react';
import { useApi } from './useApi';
import { apiService } from '../services/api';
import { ExecutionResult } from '../types/api';

interface UseRealTimeUpdatesOptions {
  enabled?: boolean;
  interval?: number;
  maxAttempts?: number;
}

export function useRealTimeUpdates(
  executionId: string | null,
  options: UseRealTimeUpdatesOptions = {}
) {
  const {
    enabled = true,
    interval = 2000,
    maxAttempts = 150, // 5 minutes max
  } = options;

  const attemptCount = useRef(0);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  
  const { data: executionResult, loading, error, execute: fetchResult } = useApi(apiService.getExecutionResult);

  const startPolling = useCallback(() => {
    if (!executionId || !enabled) return;

    const poll = async () => {
      if (attemptCount.current >= maxAttempts) {
        console.warn('Max polling attempts reached');
        return;
      }

      attemptCount.current++;
      const result = await fetchResult(executionId);
      
      // Stop polling if execution is complete or failed
      if (result && (result.status === 'completed' || result.status === 'failed')) {
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
      }
    };

    // Initial fetch
    poll();

    // Set up interval
    intervalRef.current = setInterval(poll, interval);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [executionId, enabled, interval, maxAttempts, fetchResult]);

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    attemptCount.current = 0;
  }, []);

  useEffect(() => {
    const cleanup = startPolling();
    return () => {
      cleanup?.();
      stopPolling();
    };
  }, [startPolling, stopPolling]);

  return {
    executionResult,
    loading,
    error,
    isPolling: !!intervalRef.current,
    stopPolling,
  };
} 