import { useGetIdentity, useLogout } from "@refinedev/core";
import { Suspense } from "react";
import { NavLink, Outlet, useLocation } from "react-router";
import { Icon, type IconName } from "../components/Icon";
import { Logo } from "../components/Logo";
import type { Identity } from "../types";
import "./shell.css";

const NAV: { to: string; label: string; icon: IconName; roles?: Identity["role"][] }[] = [
  { to: "/overview", label: "Overview", icon: "chart", roles: ["finance_manager", "admin"] },
  { to: "/check", label: "Check claim", icon: "shield" },
  { to: "/batch", label: "Batch check", icon: "upload" },
  { to: "/claims", label: "Claims history", icon: "history" },
  { to: "/team", label: "Team", icon: "users", roles: ["admin"] },
  { to: "/keys", label: "API keys", icon: "key", roles: ["admin"] },
  { to: "/account", label: "Password", icon: "shield" },
];

export function Shell() {
  const { data: identity } = useGetIdentity<Identity>();
  const { mutate: logout } = useLogout();
  const location = useLocation();
  const items = NAV.filter((item) => !item.roles || (identity && item.roles.includes(identity.role)));
  const active = Math.max(
    items.findIndex((item) => location.pathname.startsWith(item.to)),
    0,
  );

  return (
    <div className="shell">
      <aside className="rail glass">
        <NavLink to="/" className="rail__brand" aria-label="Hakiki home">
          <Logo />
        </NavLink>
        <nav className="rail__nav" style={{ "--active": active, "--count": items.length } as React.CSSProperties}>
          <span className="rail__pill" aria-hidden="true" />
          {items.map((item) => (
            <NavLink key={item.to} to={item.to} className="rail__link" aria-label={item.label}>
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
