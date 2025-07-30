import { test, expect } from '@playwright/test';

test.describe('TestPilot AI Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the dashboard
    await page.goto('http://localhost:3000');
  });

  test('should display test management page', async ({ page }) => {
    // Check that the main page loads
    await expect(page.getByRole('heading', { name: 'Test Management' })).toBeVisible();
    
    // Check that the header is present
    await expect(page.getByRole('banner')).toBeVisible();
    await expect(page.getByText('TestPilot AI')).toBeVisible();
    
    // Check that the search field is present
    await expect(page.getByPlaceholder('Search tests by title, description, or framework...')).toBeVisible();
  });

  test('should display test cases table', async ({ page }) => {
    // Mock API response for test cases
    await page.route('**/api/v1/test-cases', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
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
          },
          {
            id: 'test-2',
            title: 'Registration Test',
            description: 'Test user registration flow',
            code: 'console.log("registration test");',
            framework: 'playwright',
            language: 'javascript',
            status: 'pending',
            createdAt: '2023-01-01T00:00:00Z',
            updatedAt: '2023-01-01T00:00:00Z'
          }
        ])
      });
    });

    // Reload page to trigger API call
    await page.reload();

    // Check that test cases are displayed
    await expect(page.getByText('Login Test')).toBeVisible();
    await expect(page.getByText('Registration Test')).toBeVisible();
    
    // Check that status chips are displayed
    await expect(page.getByText('completed')).toBeVisible();
    await expect(page.getByText('pending')).toBeVisible();
  });

  test('should navigate to test detail page', async ({ page }) => {
    // Mock API responses
    await page.route('**/api/v1/test-cases', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
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
        ])
      });
    });

    await page.route('**/api/v1/test-cases/test-1', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'test-1',
          title: 'Login Test',
          description: 'Test user login functionality',
          code: 'console.log("login test");',
          framework: 'playwright',
          language: 'javascript',
          status: 'completed',
          createdAt: '2023-01-01T00:00:00Z',
          updatedAt: '2023-01-01T00:00:00Z'
        })
      });
    });

    // Reload page to trigger API call
    await page.reload();

    // Click on the view button for the first test
    await page.getByRole('button', { name: 'View' }).first().click();

    // Check that we're on the test detail page
    await expect(page.getByText('Login Test')).toBeVisible();
    await expect(page.getByText('Test Information')).toBeVisible();
    await expect(page.getByText('Test Code')).toBeVisible();
  });

  test('should execute test and show results', async ({ page }) => {
    // Mock API responses
    await page.route('**/api/v1/test-cases/test-1', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'test-1',
          title: 'Login Test',
          description: 'Test user login functionality',
          code: 'console.log("login test");',
          framework: 'playwright',
          language: 'javascript',
          status: 'pending',
          createdAt: '2023-01-01T00:00:00Z',
          updatedAt: '2023-01-01T00:00:00Z'
        })
      });
    });

    await page.route('**/api/v1/execute', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          executionId: 'exec-123',
          status: 'pending',
          message: 'Test execution started'
        })
      });
    });

    await page.route('**/api/v1/results/exec-123', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'exec-123',
          testCaseId: 'test-1',
          status: 'completed',
          logs: 'Test passed successfully',
          screenshotUrl: 'http://example.com/screenshot.png',
          duration: 5.2,
          createdAt: '2023-01-01T00:00:00Z',
          updatedAt: '2023-01-01T00:00:05Z'
        })
      });
    });

    // Navigate to test detail page
    await page.goto('http://localhost:3000/tests/test-1');

    // Click execute button
    await page.getByRole('button', { name: 'Execute Test' }).click();

    // Check that execution results are displayed
    await expect(page.getByText('Execution Results')).toBeVisible();
    await expect(page.getByText('completed')).toBeVisible();
    await expect(page.getByText('Test passed successfully')).toBeVisible();
  });

  test('should submit feedback', async ({ page }) => {
    // Mock API responses
    await page.route('**/api/v1/test-cases/test-1', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'test-1',
          title: 'Login Test',
          description: 'Test user login functionality',
          code: 'console.log("login test");',
          framework: 'playwright',
          language: 'javascript',
          status: 'completed',
          createdAt: '2023-01-01T00:00:00Z',
          updatedAt: '2023-01-01T00:00:00Z'
        })
      });
    });

    await page.route('**/api/v1/results/exec-123', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'exec-123',
          testCaseId: 'test-1',
          status: 'completed',
          logs: 'Test passed successfully',
          createdAt: '2023-01-01T00:00:00Z',
          updatedAt: '2023-01-01T00:00:05Z'
        })
      });
    });

    await page.route('**/api/v1/feedback', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'feedback-123',
          message: 'Feedback submitted successfully'
        })
      });
    });

    // Navigate to test detail page with execution results
    await page.goto('http://localhost:3000/tests/test-1');

    // Wait for execution results to be displayed
    await expect(page.getByText('Execution Results')).toBeVisible();

    // Fill out feedback form
    await page.getByRole('radio', { name: '5 Stars' }).click();
    await page.getByLabelText('Comments').fill('This is a very detailed comment about the test execution.');
    
    await page.getByLabelText('Category').click();
    await page.getByText('Functionality').click();
    
    await page.getByLabelText('Priority').click();
    await page.getByText('High').click();

    // Submit feedback
    await page.getByRole('button', { name: 'Submit Feedback' }).click();

    // Check success message
    await expect(page.getByText('Thank you for your feedback! Your submission has been recorded.')).toBeVisible();
  });

  test('should search and filter tests', async ({ page }) => {
    // Mock API response
    await page.route('**/api/v1/test-cases', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
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
          },
          {
            id: 'test-2',
            title: 'API Test',
            description: 'Test API endpoints',
            code: 'console.log("api test");',
            framework: 'playwright',
            language: 'javascript',
            status: 'pending',
            createdAt: '2023-01-01T00:00:00Z',
            updatedAt: '2023-01-01T00:00:00Z'
          }
        ])
      });
    });

    // Reload page to trigger API call
    await page.reload();

    // Search for "Login"
    await page.getByPlaceholder('Search tests by title, description, or framework...').fill('Login');

    // Check that only Login Test is visible
    await expect(page.getByText('Login Test')).toBeVisible();
    await expect(page.getByText('API Test')).not.toBeVisible();

    // Clear search
    await page.getByPlaceholder('Search tests by title, description, or framework...').clear();

    // Check that both tests are visible again
    await expect(page.getByText('Login Test')).toBeVisible();
    await expect(page.getByText('API Test')).toBeVisible();
  });
}); 