import type { Todo } from "../types";

interface Props {
  todo: Todo;
  onToggle: (todoId: string, completed: boolean) => void;
  onDelete: (todoId: string) => void;
}

export function TodoItem({ todo, onToggle, onDelete }: Props) {
  return (
    <li className="todo-item">
      <label className="todo-label">
        <input
          type="checkbox"
          checked={todo.completed}
          onChange={() => onToggle(todo.todo_id, todo.completed)}
        />
        <span className={todo.completed ? "completed" : ""}>{todo.title}</span>
      </label>
      <button
        className="delete-button"
        onClick={() => onDelete(todo.todo_id)}
        aria-label="削除"
      >
        ✕
      </button>
    </li>
  );
}
