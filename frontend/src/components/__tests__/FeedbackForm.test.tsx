import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import FeedbackForm from '../FeedbackForm';
import { apiService } from '../../services/api';

// Mock the API service
jest.mock('../../services/api');
const mockedApiService = apiService as jest.Mocked<typeof apiService>;

// Mock the useApi hook
jest.mock('../../hooks/useApi', () => ({
  useApi: jest.fn(() => ({
    execute: jest.fn(),
    loading: false,
    error: null,
  })),
}));

const theme = createTheme();

const renderWithTheme = (component: React.ReactElement) => {
  return render(
    <ThemeProvider theme={theme}>
      {component}
    </ThemeProvider>
  );
};

describe('FeedbackForm', () => {
  const defaultProps = {
    testCaseId: 'test-123',
    executionId: 'exec-123',
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders feedback form with all fields', () => {
    renderWithTheme(<FeedbackForm {...defaultProps} />);

    expect(screen.getByText('Submit Feedback')).toBeInTheDocument();
    expect(screen.getByText('How would you rate this test execution?')).toBeInTheDocument();
    expect(screen.getByLabelText('Comments')).toBeInTheDocument();
    expect(screen.getByLabelText('Category')).toBeInTheDocument();
    expect(screen.getByLabelText('Priority')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Submit Feedback' })).toBeInTheDocument();
  });

  it('shows validation errors for empty form submission', async () => {
    const user = userEvent.setup();
    renderWithTheme(<FeedbackForm {...defaultProps} />);

    const submitButton = screen.getByRole('button', { name: 'Submit Feedback' });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Rating is required')).toBeInTheDocument();
      expect(screen.getByText('Comments are required')).toBeInTheDocument();
      expect(screen.getByText('Category is required')).toBeInTheDocument();
      expect(screen.getByText('Priority is required')).toBeInTheDocument();
    });
  });

  it('shows validation error for short comments', async () => {
    const user = userEvent.setup();
    renderWithTheme(<FeedbackForm {...defaultProps} />);

    const commentsField = screen.getByLabelText('Comments');
    await user.type(commentsField, 'Short');

    const submitButton = screen.getByRole('button', { name: 'Submit Feedback' });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Comments must be at least 10 characters')).toBeInTheDocument();
    });
  });

  it('allows selecting rating', async () => {
    const user = userEvent.setup();
    renderWithTheme(<FeedbackForm {...defaultProps} />);

    const ratingStars = screen.getAllByRole('radio');
    await user.click(ratingStars[4]); // Click 5th star (rating 5)

    expect(ratingStars[4]).toBeChecked();
  });

  it('allows selecting category and priority', async () => {
    const user = userEvent.setup();
    renderWithTheme(<FeedbackForm {...defaultProps} />);

    // Select category
    const categorySelect = screen.getByLabelText('Category');
    await user.click(categorySelect);
    const functionalityOption = screen.getByText('Functionality');
    await user.click(functionalityOption);

    // Select priority
    const prioritySelect = screen.getByLabelText('Priority');
    await user.click(prioritySelect);
    const highOption = screen.getByText('High');
    await user.click(highOption);

    expect(categorySelect).toHaveValue('functionality');
    expect(prioritySelect).toHaveValue('high');
  });

  it('submits form with valid data', async () => {
    const user = userEvent.setup();
    const mockSubmitFeedback = jest.fn().mockResolvedValue({
      id: 'feedback-123',
      message: 'Feedback submitted successfully'
    });

    // Mock the useApi hook to return our mock function
    const { useApi } = require('../../hooks/useApi');
    useApi.mockReturnValue({
      execute: mockSubmitFeedback,
      loading: false,
      error: null,
    });

    renderWithTheme(<FeedbackForm {...defaultProps} />);

    // Fill out the form
    const ratingStars = screen.getAllByRole('radio');
    await user.click(ratingStars[4]); // Rating 5

    const commentsField = screen.getByLabelText('Comments');
    await user.type(commentsField, 'This is a very detailed comment about the test execution.');

    const categorySelect = screen.getByLabelText('Category');
    await user.click(categorySelect);
    await user.click(screen.getByText('Functionality'));

    const prioritySelect = screen.getByLabelText('Priority');
    await user.click(prioritySelect);
    await user.click(screen.getByText('High'));

    // Submit the form
    const submitButton = screen.getByRole('button', { name: 'Submit Feedback' });
    await user.click(submitButton);

    await waitFor(() => {
      expect(mockSubmitFeedback).toHaveBeenCalledWith({
        testCaseId: 'test-123',
        executionId: 'exec-123',
        rating: 5,
        comments: 'This is a very detailed comment about the test execution.',
        metadata: {
          category: 'functionality',
          priority: 'high',
        },
      });
    });
  });

  it('shows success message after successful submission', async () => {
    const user = userEvent.setup();
    const mockSubmitFeedback = jest.fn().mockResolvedValue({
      id: 'feedback-123',
      message: 'Feedback submitted successfully'
    });

    const { useApi } = require('../../hooks/useApi');
    useApi.mockReturnValue({
      execute: mockSubmitFeedback,
      loading: false,
      error: null,
    });

    renderWithTheme(<FeedbackForm {...defaultProps} />);

    // Fill out the form
    const ratingStars = screen.getAllByRole('radio');
    await user.click(ratingStars[4]);

    const commentsField = screen.getByLabelText('Comments');
    await user.type(commentsField, 'This is a very detailed comment about the test execution.');

    const categorySelect = screen.getByLabelText('Category');
    await user.click(categorySelect);
    await user.click(screen.getByText('Functionality'));

    const prioritySelect = screen.getByLabelText('Priority');
    await user.click(prioritySelect);
    await user.click(screen.getByText('High'));

    // Submit the form
    const submitButton = screen.getByRole('button', { name: 'Submit Feedback' });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Thank you for your feedback! Your submission has been recorded.')).toBeInTheDocument();
    });
  });

  it('shows loading state during submission', async () => {
    const { useApi } = require('../../hooks/useApi');
    useApi.mockReturnValue({
      execute: jest.fn(),
      loading: true,
      error: null,
    });

    renderWithTheme(<FeedbackForm {...defaultProps} />);

    expect(screen.getByRole('button', { name: 'Submitting...' })).toBeInTheDocument();
  });

  it('shows error message when submission fails', async () => {
    const { useApi } = require('../../hooks/useApi');
    useApi.mockReturnValue({
      execute: jest.fn(),
      loading: false,
      error: {
        detail: 'Failed to submit feedback',
        status_code: 500,
      },
    });

    renderWithTheme(<FeedbackForm {...defaultProps} />);

    expect(screen.getByText('Error submitting feedback: Failed to submit feedback')).toBeInTheDocument();
  });
}); 