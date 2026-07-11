export function defaultStaffRoute(auth) {
  if (!auth.staffRoles.includes("staff") && auth.staffRoles.includes("delivery")) {
    return { name: "staff-delivery-log" };
  }
  return { name: "staff-deliveries" };
}

export function defaultRouteForRole(auth) {
  if (auth.role === "admin") return { name: "admin-dashboard" };
  if (auth.role === "superuser") return { name: "superuser-backups" };
  return defaultStaffRoute(auth);
}
