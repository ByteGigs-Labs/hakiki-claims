import type { AuthProvider } from "@refinedev/core";
import { http } from "../lib/http";
import type { Identity } from "../types";

export const authProvider: AuthProvider = {
  login: async ({ email, password }) => {
    try {
      await http.post("/v1/auth/login", { email, password });
      return { success: true, redirectTo: "/" };
    } catch (failure) {
      const status = (failure as { response?: { status?: number } }).response?.status;
      return {
        success: false,
        error: {
          name: "Sign in failed",
          message:
            status === 429
              ? "Too many attempts. Wait a few minutes and try again."
              : "Invalid email or password",
        },
      };
    }
  },

  logout: async () => {
    await http.post("/v1/auth/logout").catch(() => undefined);
    return { success: true, redirectTo: "/login" };
  },

  check: async () => {
    try {
      await http.get("/v1/auth/me");
      return { authenticated: true };
    } catch {
      return { authenticated: false, redirectTo: "/login" };
    }
  },

  getIdentity: async () => {
    try {
      return (await http.get<Identity>("/v1/auth/me")).data;
    } catch {
      return null;
    }
  },

  onError: async (error) => {
    if ((error as { response?: { status?: number } })?.response?.status === 401) {
      return { logout: true, redirectTo: "/login" };
    }
    return { error };
  },
};
