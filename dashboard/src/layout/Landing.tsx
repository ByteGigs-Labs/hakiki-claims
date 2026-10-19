import { useGetIdentity } from "@refinedev/core";
import { Navigate } from "react-router";
import type { Identity } from "../types";

export function Landing() {
  const { data: identity, isLoading } = useGetIdentity<Identity>();
  if (isLoading) return null;
  return <Navigate to={identity?.role === "clerk" ? "/check" : "/overview"} replace />;
}
