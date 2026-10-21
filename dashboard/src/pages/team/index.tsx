import { useGetIdentity } from "@refinedev/core";
import { useState, type FormEvent } from "react";
import { Icon } from "../../components/Icon";
import { useAsync } from "../../hooks/useAsync";
import { createUser, errorMessage, fetchUsers, updateUser } from "../../lib/api";
import { formatDate } from "../../lib/format";
import type { Identity, ManagedUser, Role } from "../../types";
import "./team.css";

const ROLES: { value: Role; label: string }[] = [
  { value: "clerk", label: "Billing clerk" },
  { value: "finance_manager", label: "Finance manager" },
  { value: "admin", label: "Admin" },
];

const BLANK = { name: "", email: "", role: "clerk" as Role, password: "" };

export function TeamPage() {
  const { data: identity } = useGetIdentity<Identity>();
  const { data: users, error, loading, reload } = useAsync(fetchUsers, []);
  const [form, setForm] = useState(BLANK);
  const [problem, setProblem] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const add = async (event: FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setProblem(null);
    try {
      await createUser(form);
      setForm(BLANK);
      reload();
    } catch (failure) {
      setProblem(errorMessage(failure, "The user could not be added."));
    } finally {
      setBusy(false);
    }
  };

  const change = async (user: ManagedUser, patch: { role?: Role; is_active?: boolean }) => {
    setProblem(null);
    try {
      await updateUser(user.id, patch);
      reload();
    } catch (failure) {
      setProblem(errorMessage(failure, "The change could not be saved."));
    }
  };

  return (
    <div className="page team">
      <header className="page__header reveal">
        <p className="eyebrow">Your facility</p>
        <h1>Team</h1>
        <p>Add the people who check claims, choose what each can see, and switch off access when someone leaves.</p>
      </header>

      <form className="team__add surface reveal" style={{ "--i": 1 } as React.CSSProperties} onSubmit={add}>
        <h2>Add a person</h2>
        <div className="team__fields">
          <label className="field">
            <span className="field__label">Full name</span>
            <input className="input" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required maxLength={120} autoComplete="off" />
          </label>
          <label className="field">
            <span className="field__label">Email</span>
            <input className="input" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required maxLength={254} autoComplete="off" />
          </label>
          <label className="field">
            <span className="field__label">Role</span>
            <select className="input" value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value as Role })}>
              {ROLES.map((role) => (
                <option key={role.value} value={role.value}>
                  {role.label}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span className="field__label">First password</span>
            <input className="input" type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required minLength={10} maxLength={256} autoComplete="new-password" />
            <span className="field__hint">At least 10 characters. They can change it after signing in.</span>
          </label>
        </div>
        <button type="submit" className="btn btn--solid" disabled={busy}>
          {busy ? <span className="spinner" /> : <Icon name="plus" size={18} />}
          Add person
        </button>
      </form>

      {problem && (
        <p className="form-error" role="alert">
          <Icon name="alert" size={16} /> {problem}
        </p>
      )}

      <section className="team__list reveal" style={{ "--i": 2 } as React.CSSProperties} aria-label="People">
        {loading && <div className="skeleton" style={{ height: 220 }} />}
        {error != null && <p className="form-error" role="alert">The team could not be loaded.</p>}
        <ul>
          {users?.map((user) => {
            const self = user.id === identity?.id;
            return (
              <li key={user.id} className={`team__person surface${user.is_active ? "" : " team__person--off"}`}>
                <span className="team__who">
                  <strong>{user.name}</strong>
                  <small>{user.email}</small>
                  <small>Added {formatDate(user.created_at)}</small>
                </span>
                <label className="team__role">
                  <span className="field__label">Role</span>
                  <select
                    className="input"
                    value={user.role}
                    disabled={self}
                    onChange={(e) => change(user, { role: e.target.value as Role })}
                  >
                    {ROLES.map((role) => (
                      <option key={role.value} value={role.value}>
                        {role.label}
                      </option>
                    ))}
                  </select>
                </label>
                <span className="team__state">{user.is_active ? "Active" : "Switched off"}</span>
                <button
                  type="button"
                  className="btn btn--soft btn--small"
                  disabled={self}
                  title={self ? "You cannot switch off your own access" : undefined}
                  onClick={() => change(user, { is_active: !user.is_active })}
                >
                  {user.is_active ? "Switch off" : "Switch on"}
                </button>
              </li>
            );
          })}
        </ul>
      </section>
    </div>
  );
}
