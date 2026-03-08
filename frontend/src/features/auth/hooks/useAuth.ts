import { useMutation } from "@tanstack/react-query";
import { useNavigate } from "react-router";
import { authService } from "@/features/auth/api/auth.service";
import type { LoginRequest, RegisterRequest } from "@/features/auth/api/auth.service";
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
