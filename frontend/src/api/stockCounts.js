import { apiFetch, buildQuery } from "./client";

export function listStockCounts(params = {}) {
  return apiFetch(`/stock-counts${buildQuery(params)}`);
}

export function createStockCount({ branchId, itemId, quantityRemaining, date }) {
  return apiFetch("/stock-counts", {
    method: "POST",
    body: { branch_id: branchId, item_id: itemId, quantity_remaining: quantityRemaining, date },
  });
}

export function updateStockCount(id, payload) {
  return apiFetch(`/stock-counts/${id}`, { method: "PATCH", body: payload });
}
