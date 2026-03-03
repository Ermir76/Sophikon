// Public API for the `auth` feature
export { default as LoginPage } from './pages/LoginPage';
export { default as RegisterPage } from './pages/RegisterPage';
export { default as VerifyEmailPage } from './pages/VerifyEmailPage';

export { useLogin, useRegister, useSendVerificationEmail } from './hooks/useAuth';
export { useAuthStore } from './store/auth-store';
export { authService } from './api/auth.service';
