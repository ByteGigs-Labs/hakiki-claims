import { Authenticated, Refine } from "@refinedev/core";
import routerProvider, { CatchAllNavigate, NavigateToResource } from "@refinedev/react-router";
import dataProvider from "@refinedev/simple-rest";
import { lazy } from "react";
import { BrowserRouter, Navigate, Outlet, Route, Routes } from "react-router";
import { Shell } from "./layout/Shell";
import { Landing } from "./layout/Landing";
import { API_URL, http } from "./lib/http";
import { LoginPage } from "./pages/login";
import { authProvider } from "./providers/authProvider";

const OverviewPage = lazy(() => import("./pages/overview").then((m) => ({ default: m.OverviewPage })));
const CheckClaimPage = lazy(() => import("./pages/check").then((m) => ({ default: m.CheckClaimPage })));
const BatchPage = lazy(() => import("./pages/batch").then((m) => ({ default: m.BatchPage })));
const ClaimList = lazy(() => import("./pages/claims/list").then((m) => ({ default: m.ClaimList })));


export default function App() {
  return (
    <BrowserRouter>
      <Refine
        dataProvider={dataProvider(`${API_URL}/v1`, http)}
        authProvider={authProvider}
        routerProvider={routerProvider}
        resources={[
          { name: "overview", list: "/overview", meta: { label: "Overview" } },
          { name: "check", list: "/check", meta: { label: "Check claim" } },
          { name: "batch", list: "/batch", meta: { label: "Batch check" } },
          { name: "claims", list: "/claims", meta: { label: "Claims history" } },
        ]}
        options={{ syncWithLocation: false, disableTelemetry: true }}
      >
        <Routes>
          <Route
            element={
              <Authenticated key="app" fallback={<CatchAllNavigate to="/login" />}>
                <Shell />
              </Authenticated>
            }
          >
            <Route index element={<Landing />} />
            <Route path="/overview" element={<OverviewPage />} />
            <Route path="/check" element={<CheckClaimPage />} />
            <Route path="/batch" element={<BatchPage />} />
            <Route path="/claims" element={<ClaimList />} />
          </Route>
          <Route
            element={
              <Authenticated key="guest" fallback={<Outlet />}>
                <NavigateToResource resource="check" />
              </Authenticated>
            }
          >
            <Route path="/login" element={<LoginPage />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Refine>
    </BrowserRouter>
  );
}
