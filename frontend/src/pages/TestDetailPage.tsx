import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Paper,
  Chip,
  Button,
  CircularProgress,
  Alert,
  Card,
  CardContent,
} from '@mui/material';
import { ArrowBack, PlayArrow, Save } from '@mui/icons-material';
import Editor from '@monaco-editor/react';
import { useApi } from '../hooks/useApi';
import { useRealTimeUpdates } from '../hooks/useRealTimeUpdates';
import { apiService } from '../services/api';

import FeedbackForm from '../components/FeedbackForm';

const TestDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [editedCode, setEditedCode] = useState<string>('');
  const [currentExecutionId, setCurrentExecutionId] = useState<string | null>(null);
  const [isExecuting, setIsExecuting] = useState(false);

  const { data: testCase, loading, error, execute: fetchTestCase } = useApi(apiService.getTestCase);
  const { execute: executeTest } = useApi(apiService.executeTest);
  
  // Real-time updates for execution results
  const { executionResult, isPolling } = useRealTimeUpdates(currentExecutionId, {
    enabled: !!currentExecutionId,
    interval: 2000,
  });

  useEffect(() => {
    if (id) {
      // Validate that ID is a number
      if (!/^\d+$/.test(id)) {
        console.error(`Invalid test case ID: "${id}". Expected a numeric ID.`);
        navigate('/tests'); // Redirect back to test list
        return;
      }
      fetchTestCase(id);
    }
  }, [id, fetchTestCase, navigate]);

  useEffect(() => {
    if (testCase) {
      setEditedCode(testCase.code);
    }
  }, [testCase]);

  const handleExecute = async () => {
    if (!testCase) return;

    setIsExecuting(true);
    try {
      const result = await executeTest({ testCaseId: testCase.id });
      if (result) {
        setCurrentExecutionId(result.executionId);
        setIsExecuting(false);
      }
    } catch (error) {
      console.error('Execution failed:', error);
      setIsExecuting(false);
    }
  };

  const handleSave = async () => {
    // TODO: Implement save functionality
    console.log('Saving edited code:', editedCode);
  };

  if (loading && !testCase) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        Error loading test: {error.detail}
      </Alert>
    );
  }

  if (!testCase) {
    return (
      <Alert severity="warning">
        Test case not found.
      </Alert>
    );
  }

  return (
    <Box>
      <Box display="flex" alignItems="center" mb={3}>
        <Button
          startIcon={<ArrowBack />}
          onClick={() => navigate('/tests')}
          sx={{ mr: 2 }}
        >
          Back to Tests
        </Button>
        <Typography variant="h4" component="h1">
          {testCase.title}
        </Typography>
      </Box>

      <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
        {/* Test Information */}
        <Box sx={{ flex: '1 1 300px', minWidth: 0 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Test Information
              </Typography>
              <Box mb={2}>
                <Typography variant="body2" color="text.secondary">
                  {testCase.description}
                </Typography>
              </Box>
              <Box display="flex" gap={1} mb={2}>
                <Chip label={testCase.framework} size="small" />
                <Chip label={testCase.language} size="small" variant="outlined" />
                <Chip 
                  label={testCase.status} 
                  color={testCase.status === 'completed' ? 'success' : 
                         testCase.status === 'running' ? 'warning' : 
                         testCase.status === 'failed' ? 'error' : 'default'}
                  size="small"
                />
              </Box>
              <Typography variant="body2" color="text.secondary">
                Created: {new Date(testCase.createdAt).toLocaleString()}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Updated: {new Date(testCase.updatedAt).toLocaleString()}
              </Typography>
            </CardContent>
          </Card>

          {/* Execution Controls */}
          <Card sx={{ mt: 2 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Actions
              </Typography>
              <Box display="flex" gap={1} flexDirection="column">
                <Button
                  variant="contained"
                  startIcon={<PlayArrow />}
                  onClick={handleExecute}
                  disabled={isExecuting || isPolling}
                  fullWidth
                >
                  {isExecuting ? 'Starting...' : isPolling ? 'Running...' : 'Execute Test'}
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<Save />}
                  onClick={handleSave}
                  fullWidth
                >
                  Save Changes
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Box>

        {/* Code Editor */}
        <Box sx={{ flex: '2 1 600px', minWidth: 0 }}>
          <Paper sx={{ height: '600px' }}>
            <Box p={2} borderBottom={1} borderColor="divider">
              <Typography variant="h6">
                Test Code
              </Typography>
            </Box>
            <Editor
              height="550px"
              language={testCase.language === 'javascript' ? 'javascript' : 'python'}
              value={editedCode}
              onChange={(value) => setEditedCode(value || '')}
              options={{
                minimap: { enabled: false },
                fontSize: 14,
                wordWrap: 'on',
                automaticLayout: true,
              }}
            />
          </Paper>
        </Box>

        {/* Execution Results */}
        {executionResult && (
          <Box sx={{ width: '100%' }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Execution Results
                </Typography>
                <Box display="flex" gap={1} mb={2}>
                  <Chip 
                    label={executionResult.status} 
                    color={executionResult.status === 'completed' ? 'success' : 
                           executionResult.status === 'failed' ? 'error' : 'warning'}
                    size="small"
                  />
                  {executionResult.duration && (
                    <Chip 
                      label={`${executionResult.duration}s`} 
                      size="small" 
                      variant="outlined"
                    />
                  )}
                </Box>
                
                {executionResult.logs && (
                  <Box mb={2}>
                    <Typography variant="subtitle2" gutterBottom>
                      Logs:
                    </Typography>
                    <Paper 
                      variant="outlined" 
                      sx={{ p: 2, backgroundColor: 'grey.50', fontFamily: 'monospace' }}
                    >
                      <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                        {executionResult.logs}
                      </pre>
                    </Paper>
                  </Box>
                )}

                {executionResult.error && (
                  <Box mb={2}>
                    <Typography variant="subtitle2" color="error" gutterBottom>
                      Error:
                    </Typography>
                    <Paper 
                      variant="outlined" 
                      sx={{ p: 2, backgroundColor: 'error.light', color: 'error.contrastText' }}
                    >
                      <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                        {executionResult.error}
                      </pre>
                    </Paper>
                  </Box>
                )}

                {executionResult.screenshotUrl && (
                  <Box mb={2}>
                    <Typography variant="subtitle2" gutterBottom>
                      Screenshot:
                    </Typography>
                    <img 
                      src={executionResult.screenshotUrl} 
                      alt="Test execution screenshot"
                      style={{ maxWidth: '100%', height: 'auto' }}
                    />
                  </Box>
                )}
              </CardContent>
            </Card>
          </Box>
        )}

        {/* Feedback Form */}
        {executionResult && (
          <Box sx={{ width: '100%' }}>
            <FeedbackForm 
              testCaseId={testCase.id}
              executionId={executionResult.id}
            />
          </Box>
        )}
      </Box>
    </Box>
  );
};

export default TestDetailPage; 