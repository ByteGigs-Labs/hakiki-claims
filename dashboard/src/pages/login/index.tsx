import { useLogin } from "@refinedev/core";
import { useState, type FormEvent } from "react";
import { GlassCube } from "../../components/GlassCube";
import { Icon } from "../../components/Icon";
import { Logo } from "../../components/Logo";
import "./login.css";

export function LoginPage() {
  const { mutate: login, isPending } = useLogin<{ email: string; password: string }>();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [failed, setFailed] = useState<string | null>(null);

  const submit = (event: FormEvent) => {
    event.preventDefault();
    setFailed(null);
    login(
      { email, password },
      { onSuccess: (data) => !data.success && setFailed(data.error?.message ?? "Invalid email or password") },
    );
  };

  return (
    <div className="login">
      <section className="login__story">
        <Logo />
        <div className="login__copy">
          <p className="eyebrow reveal">Glass box pre-audit for SHA claims</p>
          <h1 className="reveal" style={{ "--i": 1 } as React.CSSProperties}>
            See why a claim<br />
            <em>passes or fails</em><br />
            before SHA does.
          </h1>
          <p className="login__lede reveal" style={{ "--i": 2 } as React.CSSProperties}>
            Every verdict is a reproducible chain of cited rules. Nothing is guessed, and nothing is hidden.
          </p>
        </div>
        <GlassCube className="login__cube" />
      </section>

      <section className="login__panel">
        <form className="login__form glass reveal" style={{ "--i": 2 } as React.CSSProperties} onSubmit={submit}>
          <div>
            <p className="eyebrow">Welcome back</p>
            <h2>Sign in</h2>
          </div>
          <label className="field">
            <span className="field__label">Email</span>
            <input className="input" type="email" autoComplete="username" value={email} onChange={(e) => setEmail(e.target.value)} required maxLength={254} />
          </label>
          <label className="field">
            <span className="field__label">Password</span>
            <input className="input" type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} required maxLength={256} />
          </label>
          {failed && (
            <p className="login__error" role="alert">
              <Icon name="alert" size={16} /> {failed}
            </p>
          )}
          <button type="submit" className="btn btn--solid btn--block" disabled={isPending}>
            {isPending ? <span className="spinner" /> : <Icon name="arrow" size={18} />}
            {isPending ? "Signing in…" : "Continue"}
          </button>
          <p className="login__fine">Health data is pseudonymised before it is checked.</p>
        </form>
      </section>
    </div>
  );
}
