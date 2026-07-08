import { apiFetch, buildQuery } from "./client";

export function listStockDeliveries(params = {}) {
  return apiFetch(`/stock-deliveries${buildQuery(params)}`);
}

export function createStockDelivery({ branchId, itemId, quantityDelivered, isShort, date }) {
  return apiFetch("/stock-deliveries", {
    method: "POST",
    body: { branch_id: branchId, item_id: itemId, quantity_delivered: quantityDelivered, is_short: isShort, date },
  });
}

export function updateStockDelivery(id, payload) {
  return apiFetch(`/stock-deliveries/${id}`, { method: "PATCH", body: payload });
}
