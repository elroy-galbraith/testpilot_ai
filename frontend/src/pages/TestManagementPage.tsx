import React, { useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  CircularProgress,
  Alert,
  TextField,
  InputAdornment,
} from '@mui/material';
import { Visibility, Refresh } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useApi } from '../hooks/useApi';
import { apiService } from '../services/api';
import { TestCase } from '../types/api';
import RealTimeStatusChip from '../components/RealTimeStatusChip';

const TestManagementPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = React.useState('');
  const [filteredTests, setFilteredTests] = React.useState<TestCase[]>([]);
  
  const { data: tests, loading, error, execute: fetchTests } = useApi(apiService.getTestCases);

  useEffect(() => {
    fetchTests();
  }, [fetchTests]);

  useEffect(() => {
    if (tests) {
      const filtered = tests.filter(test =>
        test.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        test.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
        test.framework.toLowerCase().includes(searchTerm.toLowerCase())
      );
      setFilteredTests(filtered);
    }
  }, [tests, searchTerm]);

  const getStatusColor = (status: string) => {
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

  const handleRefresh = () => {
    fetchTests();
  };

  const handleViewTest = (testId: string) => {
    navigate(`/tests/${testId}`);
  };

  if (loading && !tests) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        Error loading tests: {error.detail}
      </Alert>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          Test Management
        </Typography>
        <IconButton onClick={handleRefresh} disabled={loading}>
          <Refresh />
        </IconButton>
      </Box>

      <TextField
        fullWidth
        variant="outlined"
        placeholder="Search tests by title, description, or framework..."
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
        sx={{ mb: 3 }}
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              {loading && <CircularProgress size={20} />}
            </InputAdornment>
          ),
        }}
      />

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Title</TableCell>
              <TableCell>Framework</TableCell>
              <TableCell>Language</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Created</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredTests.map((test) => (
              <TableRow key={test.id} hover>
                <TableCell>
                  <Typography variant="subtitle2">{test.title}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    {test.description}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Chip label={test.framework} size="small" />
                </TableCell>
                <TableCell>
                  <Chip label={test.language} size="small" variant="outlined" />
                </TableCell>
                <TableCell>
                  <RealTimeStatusChip 
                    testCaseId={test.id}
                    initialStatus={test.status}
                  />
                </TableCell>
                <TableCell>
                  {new Date(test.createdAt).toLocaleDateString()}
                </TableCell>
                <TableCell>
                  <IconButton 
                    onClick={() => handleViewTest(test.id)}
                    size="small"
                  >
                    <Visibility />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {filteredTests.length === 0 && !loading && (
        <Box textAlign="center" py={4}>
          <Typography variant="body1" color="text.secondary">
            {searchTerm ? 'No tests match your search criteria.' : 'No tests found.'}
          </Typography>
        </Box>
      )}
    </Box>
  );
};

export default TestManagementPage; 