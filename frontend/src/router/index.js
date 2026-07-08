import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "../stores/auth";
import LoginView from "../views/LoginView.vue";
import AdminLayout from "../views/AdminLayout.vue";
import AdminDashboardView from "../views/AdminDashboardView.vue";
import AdminBranchesView from "../views/AdminBranchesView.vue";
import AdminStaffView from "../views/AdminStaffView.vue";
import AdminStockItemsView from "../views/AdminStockItemsView.vue";
import AdminExpensesView from "../views/AdminExpensesView.vue";
import AdminNeedsView from "../views/AdminNeedsView.vue";
import AdminSettingsView from "../views/AdminSettingsView.vue";
import StaffLayout from "../views/StaffLayout.vue";
import StaffDeliveriesView from "../views/StaffDeliveriesView.vue";
import StaffDeliveryLogView from "../views/StaffDeliveryLogView.vue";
import NotFoundView from "../views/NotFoundView.vue";

function defaultStaffRoute(auth) {
  if (!auth.staffRoles.includes("staff") && auth.staffRoles.includes("delivery")) {
    return { name: "staff-delivery-log" };
  }
  return { name: "staff-deliveries" };
}

const routes = [
  { path: "/login", name: "login", component: LoginView, meta: { guestOnly: true } },
  {
    path: "/admin",
    component: AdminLayout,
    meta: { requiresRole: "admin" },
    children: [
      { path: "", redirect: { name: "admin-dashboard" } },
      { path: "dashboard", name: "admin-dashboard", component: AdminDashboardView },
      { path: "branches", name: "admin-branches", component: AdminBranchesView },
      { path: "staff", name: "admin-staff", component: AdminStaffView },
      { path: "stock-items", name: "admin-stock-items", component: AdminStockItemsView },
      { path: "expenses", name: "admin-expenses", component: AdminExpensesView },
      { path: "needs", name: "admin-needs", component: AdminNeedsView },
      { path: "settings", name: "admin-settings", component: AdminSettingsView },
    ],
  },
  {
    path: "/staff",
    component: StaffLayout,
    meta: { requiresRole: "staff" },
    children: [
      { path: "", redirect: () => defaultStaffRoute(useAuthStore()) },
      {
        path: "deliveries",
        name: "staff-deliveries",
        component: StaffDeliveriesView,
        meta: { requiresStaffRole: "staff" },
      },
      {
        path: "delivery-log",
        name: "staff-delivery-log",
        component: StaffDeliveryLogView,
        meta: { requiresStaffRole: "delivery" },
      },
    ],
  },
  { path: "/", redirect: "/login" },
  { path: "/:pathMatch(.*)*", name: "not-found", component: NotFoundView },
];

export const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to) => {
  const auth = useAuthStore();

  if (to.meta.guestOnly && auth.isAuthenticated) {
    return auth.role === "admin" ? { name: "admin-dashboard" } : defaultStaffRoute(auth);
  }

  if (to.meta.requiresRole) {
    if (!auth.isAuthenticated) {
      return { name: "login" };
    }
    if (auth.role !== to.meta.requiresRole) {
      return auth.role === "admin" ? { name: "admin-dashboard" } : defaultStaffRoute(auth);
    }
  }

  if (to.meta.requiresStaffRole && !auth.staffRoles.includes(to.meta.requiresStaffRole)) {
    return defaultStaffRoute(auth);
  }

  return true;
});
