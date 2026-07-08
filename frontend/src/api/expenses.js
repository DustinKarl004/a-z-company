import { apiFetch, buildQuery } from "./client";

export function listExpenses(params = {}) {
  return apiFetch(`/expenses${buildQuery(params)}`);
}

export function createExpense({ branchId, date, description, amount }) {
  return apiFetch("/expenses", {
    method: "POST",
    body: { branch_id: branchId, date, description, amount },
  });
}

export function deleteExpense(id, password) {
  return apiFetch(`/expenses/${id}`, { method: "DELETE", body: { password } });
}
