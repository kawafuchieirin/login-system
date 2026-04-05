import axios from "axios";
import type { Todo, TodoListResponse, TokenResponse, User } from "../types";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8080",
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
