import axios from "axios";

export const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

// Session lives in an httpOnly cookie set by the API; nothing is stored in JS.
export const http = axios.create({
  baseURL: API_URL,
  withCredentials: true,
  timeout: 15000,
});
