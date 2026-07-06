import { apiFetch } from "./client";

export function listStockCounts(params = {}) {
  const query = new URLSearchParams(params).toString();
  return apiFetch(`/stock-counts${query ? `?${query}` : ""}`);
}

export function createStockCount({ itemId, quantityRemaining }) {
  return apiFetch("/stock-counts", {
    method: "POST",
    body: { item_id: itemId, quantity_remaining: quantityRemaining },
  });
}

export function updateStockCount(id, payload) {
  return apiFetch(`/stock-counts/${id}`, { method: "PATCH", body: payload });
}
