import React, { useEffect, useState } from 'react';
import { Chip, ChipProps } from '@mui/material';
import { useApi } from '../hooks/useApi';
import { apiService } from '../services/api';
import { ExecutionResult } from '../types/api';

interface RealTimeStatusChipProps {
  testCaseId: string;
  initialStatus: string;
  onStatusChange?: (status: string) => void;
}

const RealTimeStatusChip: React.FC<RealTimeStatusChipProps> = ({
  testCaseId,
  initialStatus,
  onStatusChange,
}) => {
  const [status, setStatus] = useState(initialStatus);
  const [lastExecutionId, setLastExecutionId] = useState<string | null>(null);

  const { execute: getTestCases } = useApi(apiService.getTestCases);
  const { execute: getExecutionResult } = useApi(apiService.getExecutionResult);

  // Poll for status updates every 5 seconds
  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        // Get latest test cases to check for new executions
        const testCases = await getTestCases();
        const currentTestCase = testCases?.find(tc => tc.id === testCaseId);
        
        if (currentTestCase && currentTestCase.status !== status) {
          setStatus(currentTestCase.status);
          onStatusChange?.(currentTestCase.status);
        }
      } catch (error) {
        console.error('Error polling for status updates:', error);
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [testCaseId, status, getTestCases, onStatusChange]);

  const getStatusColor = (): ChipProps['color'] => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'running':
        return 'warning';
      case 'failed':
        return 'error';
      default:
        return 'default';
    }
  };

  return (
    <Chip 
      label={status} 
      color={getStatusColor()}
      size="small"
    />
  );
};

export default RealTimeStatusChip; 