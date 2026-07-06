import { apiFetch } from "./client";

export function listExpenses(params = {}) {
  const query = new URLSearchParams(params).toString();
  return apiFetch(`/expenses${query ? `?${query}` : ""}`);
}

export function createExpense({ branchId, description, amount }) {
  return apiFetch("/expenses", {
    method: "POST",
    body: { branch_id: branchId, description, amount },
  });
}
