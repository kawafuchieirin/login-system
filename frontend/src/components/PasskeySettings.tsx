import { useCallback, useEffect, useState } from "react";
import { startRegistration } from "@simplewebauthn/browser";
import type { PublicKeyCredentialCreationOptionsJSON } from "@simplewebauthn/browser";
import { passkeyApi } from "../services/api";
import type { PasskeyCredential } from "../types";

export function PasskeySettings() {
  const [credentials, setCredentials] = useState<PasskeyCredential[]>([]);
  const [loading, setLoading] = useState(true);
  const [registering, setRegistering] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const fetchCredentials = useCallback(async () => {
    try {
      const res = await passkeyApi.listCredentials();
      setCredentials(res.data.credentials ?? []);
    } catch {
      setError("パスキーの取得に失敗しました");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCredentials();
  }, [fetchCredentials]);

  const handleRegister = async () => {
    setError("");
    setSuccess("");
    setRegistering(true);
    try {
      const optionsRes = await passkeyApi.getRegistrationOptions();
      const options = optionsRes.data;

      const credential = await startRegistration({
        optionsJSON:
          options as unknown as PublicKeyCredentialCreationOptionsJSON,
      });

      await passkeyApi.verifyRegistration(
        credential as unknown as Record<string, unknown>
      );

      setSuccess("パスキーを登録しました");
      await fetchCredentials();
    } catch (e) {
      if (e instanceof Error && e.name === "NotAllowedError") {
        setError("パスキーの登録がキャンセルされました");
      } else {
        setError("パスキーの登録に失敗しました");
      }
    } finally {
      setRegistering(false);
    }
  };

  const handleDelete = async (credentialId: string) => {
    setError("");
    setSuccess("");
    try {
      await passkeyApi.deleteCredential(credentialId);
      setCredentials((prev) =>
        prev.filter((c) => c.credential_id !== credentialId)
      );
      setSuccess("パスキーを削除しました");
    } catch {
      setError("パスキーの削除に失敗しました");
    }
  };

  return (
    <div className="passkey-settings">
      <h2>パスキー設定</h2>
      {error && <p className="error">{error}</p>}
      {success && <p className="success">{success}</p>}

      <button
        onClick={handleRegister}
        disabled={registering}
        className="passkey-register-button"
      >
        {registering ? "登録中..." : "パスキーを追加"}
      </button>

      {loading ? (
        <p className="loading">読み込み中...</p>
      ) : credentials.length === 0 ? (
        <p className="empty">登録済みのパスキーはありません</p>
      ) : (
        <ul className="passkey-list">
          {credentials.map((cred) => (
            <li key={cred.credential_id} className="passkey-item">
              <div className="passkey-info">
                <span className="passkey-id">
                  {cred.credential_id.slice(0, 16)}...
                </span>
                <span className="passkey-date">
                  {new Date(cred.created_at).toLocaleDateString("ja-JP")}
                </span>
              </div>
              <button
                onClick={() => handleDelete(cred.credential_id)}
                className="passkey-delete-button"
              >
                削除
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
