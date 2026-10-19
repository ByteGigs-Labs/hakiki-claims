import axios from "axios";

export const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

const AUTH_PATH = "/v1/auth/";

export const http = axios.create({
  baseURL: API_URL,
  withCredentials: true,
  timeout: 20000,
});

http.interceptors.response.use(undefined, (failure) => {
  const url: string = failure?.config?.url ?? "";
  if (failure?.response?.status === 401 && !url.startsWith(AUTH_PATH) && window.location.pathname !== "/login") {
    window.location.assign("/login");
  }
  return Promise.reject(failure);
});
