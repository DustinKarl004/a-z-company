import { apiFetch } from "./client";

export function listStockItems() {
  return apiFetch("/stock-items");
}

export function createStockItem({ name, unit }) {
  return apiFetch("/stock-items", { method: "POST", body: { name, unit } });
}
