export interface User {
  user_id: string;
  email: string;
  created_at: string;
}

export interface Todo {
  todo_id: string;
  title: string;
  completed: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface TodoListResponse {
  todos: Todo[];
}

export interface PasskeyCredential {
  credential_id: string;
  created_at: string;
}

export interface PasskeyCredentialListResponse {
  credentials: PasskeyCredential[];
}
