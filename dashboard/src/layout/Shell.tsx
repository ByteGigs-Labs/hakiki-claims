import { useGetIdentity, useLogout } from "@refinedev/core";
import { Suspense } from "react";
import { NavLink, Outlet, useLocation } from "react-router";
import { Icon, type IconName } from "../components/Icon";
import { Logo } from "../components/Logo";
import type { Identity } from "../types";
import "./shell.css";

const NAV: { to: string; label: string; icon: IconName }[] = [
  { to: "/check", label: "Check claim", icon: "shield" },
  { to: "/batch", label: "Batch check", icon: "upload" },
  { to: "/claims", label: "Claims history", icon: "history" },
];

export function Shell() {
  const { data: identity } = useGetIdentity<Identity>();
  const { mutate: logout } = useLogout();
  const location = useLocation();
  const active = Math.max(
    NAV.findIndex((item) => location.pathname.startsWith(item.to)),
    0,
  );

  return (
    <div className="shell">
      <aside className="rail glass">
        <NavLink to="/" className="rail__brand" aria-label="Hakiki home">
          <Logo />
        </NavLink>
        <nav className="rail__nav" style={{ "--active": active, "--count": NAV.length } as React.CSSProperties}>
          <span className="rail__pill" aria-hidden="true" />
          {NAV.map((item) => (
            <NavLink key={item.to} to={item.to} className="rail__link">
              <Icon name={item.icon} size={20} />
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="rail__user">
          <div className="rail__who">
            <span className="rail__avatar" aria-hidden="true">
              {(identity?.name ?? "?").slice(0, 1)}
            </span>
            <span className="rail__names">
              <strong>{identity?.name ?? "…"}</strong>
              <small>{identity?.facility}</small>
            </span>
          </div>
          <button type="button" className="btn btn--ghost" onClick={() => logout()} aria-label="Sign out">
            <Icon name="out" size={18} />
            <span>Sign out</span>
          </button>
        </div>
      </aside>
      <main className="shell__main" key={location.pathname}>
        <Suspense fallback={<div className="page"><div className="skeleton" style={{ height: 420 }} /></div>}>
          <Outlet />
        </Suspense>
      </main>
    </div>
  );
}
