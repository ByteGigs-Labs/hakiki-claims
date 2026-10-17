import type { AuthProvider } from "@refinedev/core";
import { http } from "../lib/http";

export const authProvider: AuthProvider = {
  login: async ({ email, password }) => {
    try {
      await http.post("/v1/auth/login", { email, password });
      return { success: true, redirectTo: "/" };
    } catch {
      // Generic message: don't reveal whether the email exists.
      return {
        success: false,
        error: { name: "Login failed", message: "Invalid email or password" },
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
      const { data } = await http.get("/v1/auth/me");
      return data;
    } catch {
      return null;
    }
  },

  onError: async (error) => {
    if (error?.response?.status === 401) {
      return { logout: true, redirectTo: "/login" };
    }
    return { error };
  },
};
