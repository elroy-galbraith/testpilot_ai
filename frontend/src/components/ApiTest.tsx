import React, { useState } from 'react';
import { Box, Typography, Button } from '@mui/material';
import { apiService } from '../services/api';

const ApiTest: React.FC = () => {
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const testApi = async () => {
    setLoading(true);
    setError(null);
    try {
      console.log('Testing API directly...');
      const data = await apiService.getTestCases();
      console.log('API test successful:', data);
      setResult(data);
    } catch (err) {
      console.error('API test failed:', err);
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box p={2}>
      <Typography variant="h6">API Test Component</Typography>
      <Button onClick={testApi} disabled={loading} variant="contained" sx={{ mb: 2 }}>
        {loading ? 'Testing...' : 'Test API'}
      </Button>
      
      {error && (
        <Typography color="error" sx={{ mb: 2 }}>
          Error: {error}
        </Typography>
      )}
      
      {result && (
        <Box>
          <Typography variant="subtitle1">Result:</Typography>
          <pre style={{ background: '#f5f5f5', padding: '10px', borderRadius: '4px' }}>
            {JSON.stringify(result, null, 2)}
          </pre>
        </Box>
      )}
    </Box>
  );
};

export default ApiTest; 