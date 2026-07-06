import { apiFetch } from "./client";

export function getOverview() {
  return apiFetch("/dashboard/overview");
}

export function getMonthly(year, month) {
  return apiFetch(`/dashboard/monthly?year=${year}&month=${month}`);
}
