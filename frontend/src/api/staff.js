import { apiFetch } from "./client";

export function listStaff() {
  return apiFetch("/staff");
}

export function createStaff({ name, email, password, branchId }) {
  return apiFetch("/staff", {
    method: "POST",
    body: { name, email, password, branch_id: branchId },
  });
}

export function updateStaff(id, payload) {
  return apiFetch(`/staff/${id}`, { method: "PATCH", body: payload });
}
