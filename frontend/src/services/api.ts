import axios from "axios";
import type {
  PasskeyCredentialListResponse,
  Todo,
  TodoListResponse,
  TokenResponse,
  User,
} from "../types";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "http://localhost:8080",
});

// Attach token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auto logout on 401
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("token");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authApi = {
  register: (email: string, password: string) =>
    api.post<User>("/api/v1/auth/register", { email, password }),

  login: (email: string, password: string) =>
    api.post<TokenResponse>("/api/v1/auth/login", { email, password }),

  logout: () => api.post("/api/v1/auth/logout"),

  me: () => api.get<User>("/api/v1/auth/me"),
};

// Todo API
export const todoApi = {
  list: () => api.get<TodoListResponse>("/api/v1/todos"),

  create: (title: string) =>
    api.post<Todo>("/api/v1/todos", { title }),

  update: (todoId: string, data: { title?: string; completed?: boolean }) =>
    api.patch<Todo>(`/api/v1/todos/${todoId}`, data),

  delete: (todoId: string) => api.delete(`/api/v1/todos/${todoId}`),
};

// Passkey API
export const passkeyApi = {
  getRegistrationOptions: () =>
    api.post<Record<string, unknown>>("/api/v1/passkey/register/options"),

  verifyRegistration: (credential: Record<string, unknown>) =>
    api.post("/api/v1/passkey/register/verify", { credential }),

  getAuthenticationOptions: (email?: string) =>
    api.post<Record<string, unknown>>("/api/v1/passkey/authenticate/options", {
      email: email || null,
    }),

  verifyAuthentication: (credential: Record<string, unknown>) =>
    api.post<TokenResponse>("/api/v1/passkey/authenticate/verify", {
      credential,
    }),

  listCredentials: () =>
    api.get<PasskeyCredentialListResponse>("/api/v1/passkey/credentials"),

  deleteCredential: (credentialId: string) =>
    api.delete(`/api/v1/passkey/credentials/${credentialId}`),
};
