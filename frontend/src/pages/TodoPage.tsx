import { PasskeySettings } from "../components/PasskeySettings";
import { TodoForm } from "../components/TodoForm";
import { TodoItem } from "../components/TodoItem";
import { useAuth } from "../hooks/useAuth";
import { useTodos } from "../hooks/useTodos";

export function TodoPage() {
  const { user, logout } = useAuth();
  const { todos, loading, addTodo, toggleTodo, deleteTodo } = useTodos();

  return (
    <div className="todo-page">
      <header className="todo-header">
        <h1>TODO</h1>
        <div className="user-info">
          <span>{user?.email}</span>
          <button onClick={logout} className="logout-button">
            ログアウト
          </button>
        </div>
      </header>

      <TodoForm onAdd={addTodo} />

      {loading ? (
        <p className="loading">読み込み中...</p>
      ) : todos.length === 0 ? (
        <p className="empty">TODOがありません。上のフォームから追加しましょう。</p>
      ) : (
        <ul className="todo-list">
          {todos.map((todo) => (
            <TodoItem
              key={todo.todo_id}
              todo={todo}
              onToggle={toggleTodo}
              onDelete={deleteTodo}
            />
          ))}
        </ul>
      )}

      <PasskeySettings />
    </div>
  );
}
