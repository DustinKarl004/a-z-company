import { apiFetch } from "./client";

export function listBranches() {
  return apiFetch("/branches");
}

export function createBranch(name) {
  return apiFetch("/branches", { method: "POST", body: { name } });
}
