import type {
  AuditStatus,
  Batch,
  BatchRow,
  ApiKeySummary,
  Citation,
  CreatedApiKey,
  CheckResult,
  ClaimInput,
  Language,
  ManagedUser,
  Narration,
  NewUser,
  Overview,
  ReferenceData,
  Role,
  Verdict,
} from "../types";
import { http } from "./http";

export const checkClaim = async (claim: ClaimInput) =>
  (await http.post<CheckResult>("/v1/claims/check", claim)).data;

export const explainCheck = async (traceHash: string, language: Language) =>
  (
    await http.get<Narration>(`/v1/claims/${encodeURIComponent(traceHash)}/explanation`, {
      params: { lang: language },
    })
  ).data;

export const fetchStoredCheck = async (traceHash: string) =>
  (await http.get<CheckResult>(`/v1/audit/entries/${encodeURIComponent(traceHash)}`)).data;

export const verifyChain = async () => (await http.get<AuditStatus>("/v1/audit/verify")).data;

export const fetchCitation = async (rule: string) =>
  (await http.get<Citation>(`/v1/citations/${rule}`)).data;

let referenceRequest: Promise<ReferenceData> | undefined;

export const fetchReference = () => {
  referenceRequest ??= http.get<ReferenceData>("/v1/reference").then(
    (response) => response.data,
    (failure) => {
      referenceRequest = undefined;
      throw failure;
    },
  );
  return referenceRequest;
};

export const uploadBatch = async (file: File, onProgress: (fraction: number) => void) => {
  const body = new FormData();
  body.append("file", file);
  const response = await http.post<Batch>("/v1/claims/batch", body, {
    onUploadProgress: (event) => onProgress(event.total ? event.loaded / event.total : 0),
  });
  return response.data;
};

export const fetchBatch = async (id: string) => (await http.get<Batch>(`/v1/claims/batch/${id}`)).data;

export const fetchRecentBatches = async (limit = 5) =>
  (await http.get<Batch[]>("/v1/claims/batch", { params: { limit } })).data;

export const fetchBatchRows = async (
  id: string,
  options: { verdict?: Verdict; start: number; end: number },
) => {
  const response = await http.get<BatchRow[]>(`/v1/claims/batch/${id}/rows`, {
    params: { verdict: options.verdict, _start: options.start, _end: options.end },
  });
  return { rows: response.data, total: Number(response.headers["x-total-count"] ?? 0) };
};

export const downloadTemplate = async () => {
  const response = await http.get<string>("/v1/claims/batch/template", { responseType: "text" });
  const url = URL.createObjectURL(new Blob([response.data], { type: "text/csv" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = "hakiki-claims-template.csv";
  link.click();
  URL.revokeObjectURL(url);
};

export const errorMessage = (error: unknown, fallback: string) => {
  const body = (error as { response?: { data?: { error?: { message?: string } } } }).response?.data;
  return body?.error?.message ?? fallback;
};

export const fetchOverview = async (days: number) =>
  (await http.get<Overview>("/v1/reports/overview", { params: { days } })).data;

export const fetchUsers = async () => (await http.get<ManagedUser[]>("/v1/users")).data;

export const createUser = async (user: NewUser) => (await http.post<ManagedUser>("/v1/users", user)).data;

export const updateUser = async (id: string, change: { role?: Role; is_active?: boolean }) =>
  (await http.patch<ManagedUser>(`/v1/users/${id}`, change)).data;

export const fetchApiKeys = async () => (await http.get<ApiKeySummary[]>("/v1/api-keys")).data;

export const createApiKey = async (name: string) =>
  (await http.post<CreatedApiKey>("/v1/api-keys", { name })).data;

export const revokeApiKey = async (id: string) => {
  await http.delete(`/v1/api-keys/${id}`);
};

export const changePassword = async (currentPassword: string, newPassword: string) => {
  await http.post("/v1/auth/password", { current_password: currentPassword, new_password: newPassword });
};
