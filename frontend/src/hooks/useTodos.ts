import { useCallback, useEffect, useState } from "react";
import { todoApi } from "../services/api";
import type { Todo } from "../types";

export function useTodos() {
  const [todos, setTodos] = useState<Todo[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchTodos = useCallback(async () => {
    setLoading(true);
    try {
      const res = await todoApi.list();
      setTodos(res.data.todos);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTodos();
  }, [fetchTodos]);

  const addTodo = useCallback(
    async (title: string) => {
      const res = await todoApi.create(title);
      setTodos((prev) => [...prev, res.data]);
    },
    []
  );

  const toggleTodo = useCallback(
    async (todoId: string, completed: boolean) => {
      const res = await todoApi.update(todoId, { completed: !completed });
      setTodos((prev) =>
        prev.map((t) => (t.todo_id === todoId ? res.data : t))
      );
    },
    []
  );

  const deleteTodo = useCallback(
    async (todoId: string) => {
      await todoApi.delete(todoId);
      setTodos((prev) => prev.filter((t) => t.todo_id !== todoId));
    },
    []
  );

  return { todos, loading, addTodo, toggleTodo, deleteTodo, refetch: fetchTodos };
}
