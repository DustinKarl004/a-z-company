import { apiFetch } from "./client";

export function getMe() {
  return apiFetch("/me");
}

export function updateMyBranch(branchId) {
  return apiFetch("/me/branch", { method: "PATCH", body: { branch_id: branchId } });
}

export function changeMyPassword(currentPassword, newPassword) {
  return apiFetch("/me/password", {
    method: "POST",
    body: { current_password: currentPassword, new_password: newPassword },
  });
}
