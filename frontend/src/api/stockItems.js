import { apiFetch } from "./client";

export function listStockItems(branchId) {
  return apiFetch(branchId ? `/stock-items?branch_id=${branchId}` : "/stock-items");
}

export function createStockItem({ name, unit, price, category, branchIds }) {
  return apiFetch("/stock-items", {
    method: "POST",
    body: { name, unit, price, category, branch_ids: branchIds || [] },
  });
}

export function updateStockItem(id, { name, unit, price, category, branchIds }) {
  return apiFetch(`/stock-items/${id}`, {
    method: "PATCH",
    body: { name, unit, price, category, branch_ids: branchIds || [] },
  });
}

export function deleteStockItem(id, password) {
  return apiFetch(`/stock-items/${id}`, { method: "DELETE", body: { password } });
}
