import { apiFetch } from "./client";

export function listSales(params = {}) {
  const query = new URLSearchParams(params).toString();
  return apiFetch(`/sales${query ? `?${query}` : ""}`);
}

export function createSale({ itemId, quantitySold, amount }) {
  return apiFetch("/sales", {
    method: "POST",
    body: { item_id: itemId, quantity_sold: quantitySold, amount },
  });
}

export function updateSale(id, payload) {
  return apiFetch(`/sales/${id}`, { method: "PATCH", body: payload });
}
