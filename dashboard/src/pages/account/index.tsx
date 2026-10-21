import { useState, type FormEvent } from "react";
import { Icon } from "../../components/Icon";
import { changePassword, errorMessage } from "../../lib/api";
import "../team/team.css";

export function AccountPage() {
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [problem, setProblem] = useState<string | null>(null);
  const [done, setDone] = useState(false);
  const [busy, setBusy] = useState(false);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setProblem(null);
    setDone(false);
    try {
      await changePassword(current, next);
      setCurrent("");
      setNext("");
      setDone(true);
    } catch (failure) {
      setProblem(errorMessage(failure, "The password could not be changed."));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="page team">
      <header className="page__header reveal">
        <p className="eyebrow">Your account</p>
        <h1>Password</h1>
        <p>Changing it signs you out everywhere else.</p>
      </header>
      <form className="team__add surface reveal" style={{ "--i": 1 } as React.CSSProperties} onSubmit={submit}>
        <label className="field">
          <span className="field__label">Current password</span>
          <input className="input" type="password" value={current} onChange={(e) => setCurrent(e.target.value)} required maxLength={256} autoComplete="current-password" />
        </label>
        <label className="field">
          <span className="field__label">New password</span>
          <input className="input" type="password" value={next} onChange={(e) => setNext(e.target.value)} required minLength={10} maxLength={256} autoComplete="new-password" />
          <span className="field__hint">At least 10 characters.</span>
        </label>
        <button type="submit" className="btn btn--solid" disabled={busy}>
          {busy ? <span className="spinner" /> : <Icon name="shield" size={18} />}
          Change password
        </button>
      </form>
      {problem && (
        <p className="form-error" role="alert">
          <Icon name="alert" size={16} /> {problem}
        </p>
      )}
      {done && (
        <p className="form-error" role="status">
          <Icon name="check" size={16} /> Your password has been changed.
        </p>
      )}
    </div>
  );
}
