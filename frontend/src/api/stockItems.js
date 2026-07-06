import { apiFetch } from "./client";

export function listStockItems() {
  return apiFetch("/stock-items");
}

export function createStockItem({ name, unit, price }) {
  return apiFetch("/stock-items", { method: "POST", body: { name, unit, price } });
}

export function updateStockItem(id, { unit, price }) {
  return apiFetch(`/stock-items/${id}`, { method: "PATCH", body: { unit, price } });
}
