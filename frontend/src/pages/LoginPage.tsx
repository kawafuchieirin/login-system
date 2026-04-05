import { useState, type FormEvent } from "react";
import { Link, Navigate } from "react-router-dom";
import { browserSupportsWebAuthn } from "@simplewebauthn/browser";
import { useAuth } from "../hooks/useAuth";

export function LoginPage() {
  const { login, loginWithPasskey, token } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  if (token) return <Navigate to="/" replace />;

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await login(email, password);
    } catch {
      setError("メールアドレスまたはパスワードが正しくありません");
    } finally {
      setSubmitting(false);
    }
  };

  const handlePasskeyLogin = async () => {
    setError("");
    setSubmitting(true);
    try {
      await loginWithPasskey(email || undefined);
    } catch (e) {
      if (e instanceof Error && e.name === "NotAllowedError") {
        setError("パスキー認証がキャンセルされました");
      } else {
        setError("パスキー認証に失敗しました");
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="auth-page">
      <h1>ログイン</h1>
      <form onSubmit={handleSubmit}>
        {error && <p className="error">{error}</p>}
        <div className="form-group">
          <label htmlFor="email">メールアドレス</label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="password">パスワード</label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>
        <button type="submit" disabled={submitting}>
          {submitting ? "ログイン中..." : "ログイン"}
        </button>
      </form>

      {browserSupportsWebAuthn() && (
        <div className="passkey-login">
          <div className="divider">
            <span>または</span>
          </div>
          <button
            onClick={handlePasskeyLogin}
            disabled={submitting}
            className="passkey-button"
          >
            パスキーでログイン
          </button>
        </div>
      )}

      <p className="auth-link">
        アカウントをお持ちでない方は <Link to="/register">新規登録</Link>
      </p>
    </div>
  );
}
