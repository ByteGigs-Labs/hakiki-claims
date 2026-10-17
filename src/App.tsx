import { Authenticated, Refine } from "@refinedev/core";
import {
  AuthPage, ErrorComponent, ThemedLayout, useNotificationProvider,
} from "@refinedev/antd";
import routerProvider, {
  CatchAllNavigate, NavigateToResource,
} from "@refinedev/react-router";
import dataProvider from "@refinedev/simple-rest";
import { BrowserRouter, Outlet, Route, Routes } from "react-router";
import { App as AntdApp } from "antd";
import "@refinedev/antd/dist/reset.css";

import { API_URL, http } from "./lib/http";
import { authProvider } from "./providers/authProvider";
import { CheckClaimPage } from "./pages/check";
import { ClaimList } from "./pages/claims/list";

export default function App() {
  return (
    <BrowserRouter>
      <AntdApp>
        <Refine
          // Same axios instance, so list requests carry the session cookie.
          dataProvider={dataProvider(`${API_URL}/v1`, http)}
          authProvider={authProvider}
          routerProvider={routerProvider}
          notificationProvider={useNotificationProvider}
          resources={[
            { name: "check", list: "/check", meta: { label: "Check claim" } },
            { name: "claims", list: "/claims", meta: { label: "Claims history" } },
          ]}
          options={{ syncWithLocation: true, disableTelemetry: true }}
        >
          <Routes>
            <Route
              element={
                <Authenticated key="app" fallback={<CatchAllNavigate to="/login" />}>
                  <ThemedLayout Title={() => <strong>Hakiki</strong>}>
                    <Outlet />
                  </ThemedLayout>
                </Authenticated>
              }
            >
              <Route index element={<NavigateToResource resource="check" />} />
              <Route path="/check" element={<CheckClaimPage />} />
              <Route path="/claims" element={<ClaimList />} />
            </Route>

            <Route
              element={
                <Authenticated key="auth" fallback={<Outlet />}>
                  <NavigateToResource />
                </Authenticated>
              }
            >
              <Route
                path="/login"
                element={
                  <AuthPage
                    type="login"
                    title={<strong>Hakiki</strong>}
                    rememberMe={false}
                    registerLink={false}
                    forgotPasswordLink={false}
                  />
                }
              />
            </Route>

            <Route path="*" element={<ErrorComponent />} />
          </Routes>
        </Refine>
      </AntdApp>
    </BrowserRouter>
  );
}
