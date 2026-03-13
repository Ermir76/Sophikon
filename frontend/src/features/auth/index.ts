// Public API for the `auth` feature
export { default as LoginPage } from './pages/LoginPage';
export { default as RegisterPage } from './pages/RegisterPage';
export { default as VerifyEmailPage } from './pages/VerifyEmailPage';
export { default as ForgotPasswordPage } from './pages/ForgotPasswordPage';
export { default as ResetPasswordPage } from './pages/ResetPasswordPage';
export { default as ProfilePage } from './pages/ProfilePage';

export {
  useLogin,
  useRegister,
  useSendVerificationEmail,
  useRequestPasswordReset,
  useConfirmPasswordReset,
  useUpdateProfile,
  useChangePassword,
  useUploadAvatar,
  useDeleteAvatar,
} from './hooks/useAuth';
export { useAuthStore } from './store/auth-store';
export { authService } from './api/auth.service';
