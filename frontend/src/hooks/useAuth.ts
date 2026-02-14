import { useMutation } from "@tanstack/react-query";
import { useNavigate } from "react-router";
import { authService } from "@/services/auth";
import type { LoginRequest, RegisterRequest } from "@/services/auth";
import { useAuthStore } from "@/store/auth-store";

export function useLogin() {
  const navigate = useNavigate();
  const login = useAuthStore((state) => state.login);

  return useMutation({
    mutationFn: (data: LoginRequest) => authService.login(data),
    onSuccess: (response) => {
      login(response.user);
      navigate("/");
    },
  });
}

export function useRegister() {
  const navigate = useNavigate();
  const login = useAuthStore((state) => state.login);

  return useMutation({
    mutationFn: (data: RegisterRequest) => authService.register(data),
    onSuccess: (response) => {
      login(response.user);
      navigate("/");
    },
  });
}
