import React from 'react';
import { render, screen } from '@testing-library/react';
import App from '../App';

test('renders TestPilot AI heading', () => {
  render(<App />);
  const headingElement = screen.getByRole('heading', { name: /TestPilot AI/i });
  expect(headingElement).toBeInTheDocument();
}); 