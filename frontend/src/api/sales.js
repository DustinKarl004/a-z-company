import { apiFetch } from "./client";

export function listSales(params = {}) {
  const query = new URLSearchParams(params).toString();
  return apiFetch(`/sales${query ? `?${query}` : ""}`);
}

export function createSale({ itemId, quantitySold }) {
  return apiFetch("/sales", {
    method: "POST",
    body: { item_id: itemId, quantity_sold: quantitySold },
  });
}

export function updateSale(id, quantitySold) {
  return apiFetch(`/sales/${id}`, { method: "PATCH", body: { quantity_sold: quantitySold } });
}

export function createTotalSale({ date, amount }) {
  return apiFetch("/sales", {
    method: "POST",
    body: { date, amount },
  });
}

export function updateTotalSale(id, amount) {
  return apiFetch(`/sales/${id}`, { method: "PATCH", body: { amount } });
}
