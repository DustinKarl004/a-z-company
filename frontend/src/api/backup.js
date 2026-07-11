import { apiFetch } from "./client";

export function getBackupConfig() {
  return apiFetch("/backup/config");
}

export function listBackupRuns() {
  return apiFetch("/backup/runs");
}

export function triggerBackup(date) {
  return apiFetch("/backup/run", { method: "POST", body: date ? { date } : {} });
}

export function deleteBackupRun(id, password) {
  return apiFetch(`/backup/runs/${id}`, { method: "DELETE", body: { password } });
}
