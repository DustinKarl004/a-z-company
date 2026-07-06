import { apiFetch } from "./client";

export function listStockDeliveries(params = {}) {
  const query = new URLSearchParams(params).toString();
  return apiFetch(`/stock-deliveries${query ? `?${query}` : ""}`);
}

export function createStockDelivery({ itemId, quantityDelivered, isShort }) {
  return apiFetch("/stock-deliveries", {
    method: "POST",
    body: { item_id: itemId, quantity_delivered: quantityDelivered, is_short: isShort },
  });
}

export function updateStockDelivery(id, payload) {
  return apiFetch(`/stock-deliveries/${id}`, { method: "PATCH", body: payload });
}
