import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Rating,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  CircularProgress,
} from '@mui/material';
import { useForm, Controller } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import * as yup from 'yup';
import { useApi } from '../hooks/useApi';
import { apiService } from '../services/api';
import { FeedbackRequest } from '../types/api';

interface FeedbackFormProps {
  testCaseId: string;
  executionId: string;
}

const feedbackSchema = yup.object({
  rating: yup.number().required('Rating is required').min(1).max(5),
  comments: yup.string().required('Comments are required').min(10, 'Comments must be at least 10 characters'),
  metadata: yup.object({
    category: yup.string().required('Category is required'),
    priority: yup.string().required('Priority is required'),
  }),
}).required();

type FeedbackFormData = yup.InferType<typeof feedbackSchema>;

const FeedbackForm: React.FC<FeedbackFormProps> = ({ testCaseId, executionId }) => {
  const [isSubmitted, setIsSubmitted] = useState(false);
  
  const { execute: submitFeedback, loading, error } = useApi(apiService.submitFeedback);

  const {
    control,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<FeedbackFormData>({
    resolver: yupResolver(feedbackSchema),
    defaultValues: {
      rating: 0,
      comments: '',
      metadata: {
        category: '',
        priority: '',
      },
    },
  });

  const onSubmit = async (data: FeedbackFormData) => {
    const feedbackRequest: FeedbackRequest = {
      testCaseId,
      executionId,
      rating: data.rating,
      comments: data.comments,
      metadata: data.metadata,
    };

    const result = await submitFeedback(feedbackRequest);
    if (result) {
      setIsSubmitted(true);
      reset();
    }
  };

  if (isSubmitted) {
    return (
      <Card>
        <CardContent>
          <Alert severity="success">
            Thank you for your feedback! Your submission has been recorded.
          </Alert>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Submit Feedback
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Help us improve by providing feedback on this test execution.
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            Error submitting feedback: {error.detail}
          </Alert>
        )}

        <Box component="form" onSubmit={handleSubmit(onSubmit)}>
          <Box mb={3}>
            <Typography component="legend" gutterBottom>
              How would you rate this test execution?
            </Typography>
            <Controller
              name="rating"
              control={control}
              render={({ field }) => (
                <Rating
                  {...field}
                  size="large"
                  onChange={(_, value) => field.onChange(value)}
                />
              )}
            />
            {errors.rating && (
              <Typography color="error" variant="caption">
                {errors.rating.message}
              </Typography>
            )}
          </Box>

          <Box mb={3}>
            <Controller
              name="comments"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  label="Comments"
                  multiline
                  rows={4}
                  fullWidth
                  error={!!errors.comments}
                  helperText={errors.comments?.message}
                  placeholder="Please provide detailed feedback about the test execution, including any issues you noticed or suggestions for improvement..."
                />
              )}
            />
          </Box>

          <Box mb={3}>
            <Controller
              name="metadata.category"
              control={control}
              render={({ field }) => (
                <FormControl fullWidth error={!!errors.metadata?.category}>
                  <InputLabel>Category</InputLabel>
                  <Select {...field} label="Category">
                    <MenuItem value="functionality">Functionality</MenuItem>
                    <MenuItem value="performance">Performance</MenuItem>
                    <MenuItem value="ui_ux">UI/UX</MenuItem>
                    <MenuItem value="accessibility">Accessibility</MenuItem>
                    <MenuItem value="security">Security</MenuItem>
                    <MenuItem value="other">Other</MenuItem>
                  </Select>
                </FormControl>
              )}
            />
            {errors.metadata?.category && (
              <Typography color="error" variant="caption">
                {errors.metadata.category.message}
              </Typography>
            )}
          </Box>

          <Box mb={3}>
            <Controller
              name="metadata.priority"
              control={control}
              render={({ field }) => (
                <FormControl fullWidth error={!!errors.metadata?.priority}>
                  <InputLabel>Priority</InputLabel>
                  <Select {...field} label="Priority">
                    <MenuItem value="low">Low</MenuItem>
                    <MenuItem value="medium">Medium</MenuItem>
                    <MenuItem value="high">High</MenuItem>
                    <MenuItem value="critical">Critical</MenuItem>
                  </Select>
                </FormControl>
              )}
            />
            {errors.metadata?.priority && (
              <Typography color="error" variant="caption">
                {errors.metadata.priority.message}
              </Typography>
            )}
          </Box>

          <Button
            type="submit"
            variant="contained"
            disabled={loading}
            startIcon={loading ? <CircularProgress size={20} /> : null}
          >
            {loading ? 'Submitting...' : 'Submit Feedback'}
          </Button>
        </Box>
      </CardContent>
    </Card>
  );
};

export default FeedbackForm; 