import { useState, type FormEvent } from "react";
import { Icon } from "../../components/Icon";
import { useAsync } from "../../hooks/useAsync";
import { createApiKey, errorMessage, fetchApiKeys, revokeApiKey } from "../../lib/api";
import { formatDateTime } from "../../lib/format";
import type { CreatedApiKey } from "../../types";
import "../team/team.css";
import "./keys.css";

export function KeysPage() {
  const { data: keys, error, loading, reload } = useAsync(fetchApiKeys, []);
  const [name, setName] = useState("");
  const [fresh, setFresh] = useState<CreatedApiKey | null>(null);
  const [copied, setCopied] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const create = async (event: FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setProblem(null);
    try {
      setFresh(await createApiKey(name));
      setCopied(false);
      setName("");
      reload();
    } catch (failure) {
      setProblem(errorMessage(failure, "The key could not be created."));
    } finally {
      setBusy(false);
    }
  };

  const revoke = async (id: string) => {
    setProblem(null);
    try {
      await revokeApiKey(id);
      reload();
    } catch (failure) {
      setProblem(errorMessage(failure, "The key could not be revoked."));
    }
  };

  const copy = async () => {
    if (!fresh) return;
    await navigator.clipboard.writeText(fresh.key);
    setCopied(true);
  };

  return (
    <div className="page team keys">
      <header className="page__header reveal">
        <p className="eyebrow">For billing systems and partners</p>
        <h1>API keys</h1>
        <p>
          A key lets a program check claims and upload batches for your facility. It cannot read your history or manage people. Send it as{" "}
          <code>Authorization: Bearer hk_…</code>.
        </p>
      </header>

      <form className="team__add surface reveal" style={{ "--i": 1 } as React.CSSProperties} onSubmit={create}>
        <h2>Create a key</h2>
        <label className="field">
          <span className="field__label">What will use it?</span>
          <input className="input" value={name} onChange={(e) => setName(e.target.value)} placeholder="Billing system" required maxLength={80} autoComplete="off" />
        </label>
        <button type="submit" className="btn btn--solid" disabled={busy}>
          {busy ? <span className="spinner" /> : <Icon name="key" size={18} />}
          Create key
        </button>
      </form>

      {fresh && (
        <section className="keys__fresh glass" role="status">
          <p className="eyebrow">Copy it now</p>
          <p>This is the only time the full key is shown. Hakiki keeps a fingerprint and cannot show it again.</p>
          <code className="keys__secret">{fresh.key}</code>
          <div className="keys__actions">
            <button type="button" className="btn btn--solid btn--small" onClick={copy}>
              <Icon name="copy" size={16} /> {copied ? "Copied" : "Copy key"}
            </button>
            <button type="button" className="btn btn--ghost btn--small" onClick={() => setFresh(null)}>
              I have saved it
            </button>
          </div>
        </section>
      )}

      {problem && (
        <p className="form-error" role="alert">
          <Icon name="alert" size={16} /> {problem}
        </p>
      )}

      <section className="team__list reveal" style={{ "--i": 2 } as React.CSSProperties} aria-label="Keys">
        {loading && <div className="skeleton" style={{ height: 160 }} />}
        {error != null && <p className="form-error" role="alert">The keys could not be loaded.</p>}
        {keys?.length === 0 && (
          <div className="empty">
            <Icon name="key" size={56} />
            <h2>No keys yet</h2>
            <p>Create one when a billing system needs to call Hakiki.</p>
          </div>
        )}
        <ul>
          {keys?.map((key) => (
            <li key={key.id} className={`keys__row surface${key.revoked_at ? " team__person--off" : ""}`}>
              <span className="team__who">
                <strong>{key.name}</strong>
                <small className="mono">hk_{key.prefix}…</small>
              </span>
              <span className="team__who">
                <small>Created {formatDateTime(key.created_at)}</small>
                <small>{key.last_used_at ? `Last used ${formatDateTime(key.last_used_at)}` : "Never used"}</small>
              </span>
              <span className="team__state">{key.revoked_at ? "Revoked" : "Active"}</span>
              <button type="button" className="btn btn--soft btn--small" disabled={key.revoked_at !== null} onClick={() => revoke(key.id)}>
                Revoke
              </button>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
