import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router";
import { authService } from "@/features/auth/api/auth.service";
import type {
  ChangePasswordRequest,
  LoginRequest,
  PasswordResetConfirmRequest,
  PasswordResetRequest,
  RegisterRequest,
  UpdateProfileRequest,
} from "@/features/auth/api/auth.service";
import { useAuthStore } from "@/features/auth/store/auth-store";

function resolveRedirectDestination(redirectTo?: string | null): string {
  return redirectTo && redirectTo.startsWith("/") ? redirectTo : "/";
}

export function useLogin(redirectTo?: string | null) {
  const navigate = useNavigate();
  const login = useAuthStore((state) => state.login);

  return useMutation({
    mutationFn: (data: LoginRequest) => authService.login(data),
    onSuccess: (response) => {
      login(response.user);
      navigate(resolveRedirectDestination(redirectTo), { replace: true });
    },
  });
}

export function useRegister(redirectTo?: string | null) {
  const navigate = useNavigate();
  const login = useAuthStore((state) => state.login);

  return useMutation({
    mutationFn: (data: RegisterRequest) => authService.register(data),
    onSuccess: (response) => {
      login(response.user);
      navigate(resolveRedirectDestination(redirectTo), { replace: true });
    },
  });
}


export function useSendVerificationEmail() {
  return useMutation({
    mutationFn: () => authService.sendVerificationEmail(),
  });
}

export function useRequestPasswordReset() {
  return useMutation({
    mutationFn: (data: PasswordResetRequest) => authService.requestPasswordReset(data),
  });
}

export function useConfirmPasswordReset() {
  return useMutation({
    mutationFn: (data: PasswordResetConfirmRequest) => authService.confirmPasswordReset(data),
  });
}

export function useUpdateProfile() {
  const login = useAuthStore((state) => state.login);

  return useMutation({
    mutationFn: (patch: UpdateProfileRequest) => authService.updateProfile(patch),
    onSuccess: (updatedUser) => {
      login(updatedUser);
    },
  });
}

export function useChangePassword() {
  return useMutation({
    mutationFn: (data: ChangePasswordRequest) => authService.changePassword(data),
  });
}

export function useUploadAvatar() {
  const login = useAuthStore((state) => state.login);

  return useMutation({
    mutationFn: (file: File) => authService.uploadAvatar(file),
    onSuccess: (updatedUser) => {
      login(updatedUser);
    },
  });
}

export function useDeleteAvatar() {
  const login = useAuthStore((state) => state.login);

  return useMutation({
    mutationFn: () => authService.deleteAvatar(),
    onSuccess: (updatedUser) => {
      login(updatedUser);
    },
  });
}

export function useAiPreferences() {
  return useQuery({
    queryKey: ["ai-preferences"],
    queryFn: () => authService.getAiPreferences(),
  });
}

export function useUpdateAiPreferences() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { auto_approve: Record<string, boolean> }) =>
      authService.updateAiPreferences(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ai-preferences"] });
    },
  });
}
