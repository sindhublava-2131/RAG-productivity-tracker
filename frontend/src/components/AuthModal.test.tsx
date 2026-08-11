import { describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { AuthModal } from './AuthModal';
import { AuthService } from '../services/api';

vi.mock('../services/api', () => ({
  AuthService: {
    login: vi.fn(),
    register: vi.fn(),
  },
}));

const mockedAuthService = vi.mocked(AuthService);

const testUser = { id: 1, name: 'Test', email: 'test@dev.io', created_at: '2026-01-01T00:00:00Z' };

describe('AuthModal', () => {
  const baseProps = {
    isOpen: true,
    onClose: vi.fn(),
    onSuccess: vi.fn(),
  };

  it('renders null when closed', () => {
    const { container } = render(<AuthModal {...baseProps} isOpen={false} />);
    expect(container).toBeEmptyDOMElement();
  });

  it('calls onSuccess with the user after a successful login', async () => {
    mockedAuthService.login.mockResolvedValue({ access_token: 'token123', user: testUser } as never);

    const onSuccess = vi.fn();
    const onClose = vi.fn();
    render(<AuthModal isOpen onClose={onClose} onSuccess={onSuccess} />);

    fireEvent.change(screen.getByLabelText(/Email Address/i), { target: { value: 'test@dev.io' } });
    fireEvent.change(screen.getByLabelText(/Password/i), { target: { value: 'password123' } });
    fireEvent.click(screen.getByText('Sign In 🌸'));

    await waitFor(() => {
      expect(mockedAuthService.login).toHaveBeenCalledWith('test@dev.io', 'password123');
      expect(onSuccess).toHaveBeenCalledWith(testUser);
      expect(onClose).toHaveBeenCalled();
    });
  });

  it('displays the error message when login fails', async () => {
    mockedAuthService.login.mockRejectedValue(new Error('Incorrect email or password.'));

    render(<AuthModal {...baseProps} />);

    fireEvent.change(screen.getByLabelText(/Email Address/i), { target: { value: 'bad@dev.io' } });
    fireEvent.change(screen.getByLabelText(/Password/i), { target: { value: 'wrongpass' } });
    fireEvent.click(screen.getByText('Sign In 🌸'));

    await waitFor(() => {
      expect(screen.getByText('Incorrect email or password.')).toBeInTheDocument();
    });
  });

  it('toggles to the register form and calls register', async () => {
    mockedAuthService.register.mockResolvedValue({ access_token: 'token123', user: testUser } as never);

    render(<AuthModal {...baseProps} />);

    fireEvent.click(screen.getByText('Sign Up'));
    expect(screen.getByText('Create Account 🚀')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText(/Your Name/i), { target: { value: 'Test' } });
    fireEvent.change(screen.getByLabelText(/Email Address/i), { target: { value: 'test@dev.io' } });
    fireEvent.change(screen.getByLabelText(/Password/i), { target: { value: 'password123' } });
    fireEvent.click(screen.getByText('Create Account 🚀'));

    await waitFor(() => {
      expect(mockedAuthService.register).toHaveBeenCalledWith('Test', 'test@dev.io', 'password123');
    });
  });
});
