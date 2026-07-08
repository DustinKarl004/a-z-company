import { apiFetch, buildQuery } from "./client";

export function listSales(params = {}) {
  return apiFetch(`/sales${buildQuery(params)}`);
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

export function createTotalSale({ branchId, date, amount }) {
  return apiFetch("/sales", {
    method: "POST",
    body: { branch_id: branchId, date, amount },
  });
}

export function updateTotalSale(id, amount) {
  return apiFetch(`/sales/${id}`, { method: "PATCH", body: { amount } });
}
