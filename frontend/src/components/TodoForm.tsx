import { useState, type FormEvent } from "react";

interface Props {
  onAdd: (title: string) => Promise<void>;
}

export function TodoForm({ onAdd }: Props) {
  const [title, setTitle] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const trimmed = title.trim();
    if (!trimmed) return;

    setSubmitting(true);
    try {
      await onAdd(trimmed);
      setTitle("");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form className="todo-form" onSubmit={handleSubmit}>
      <input
        type="text"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        placeholder="新しいTODOを入力..."
        disabled={submitting}
      />
      <button type="submit" disabled={submitting || !title.trim()}>
        追加
      </button>
    </form>
  );
}
