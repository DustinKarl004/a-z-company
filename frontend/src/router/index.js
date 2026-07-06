import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "../stores/auth";
import LoginView from "../views/LoginView.vue";
import AdminLayout from "../views/AdminLayout.vue";
import AdminBranchesView from "../views/AdminBranchesView.vue";
import AdminStaffView from "../views/AdminStaffView.vue";
import StaffHomeView from "../views/StaffHomeView.vue";
import NotFoundView from "../views/NotFoundView.vue";

const routes = [
  { path: "/login", name: "login", component: LoginView, meta: { guestOnly: true } },
  {
    path: "/admin",
    component: AdminLayout,
    meta: { requiresRole: "admin" },
    children: [
      { path: "", redirect: { name: "admin-branches" } },
      { path: "branches", name: "admin-branches", component: AdminBranchesView },
      { path: "staff", name: "admin-staff", component: AdminStaffView },
    ],
  },
  {
    path: "/staff",
    name: "staff-home",
    component: StaffHomeView,
    meta: { requiresRole: "staff" },
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
    return auth.role === "admin" ? { name: "admin-branches" } : { name: "staff-home" };
  }

  if (to.meta.requiresRole) {
    if (!auth.isAuthenticated) {
      return { name: "login" };
    }
    if (auth.role !== to.meta.requiresRole) {
      return auth.role === "admin" ? { name: "admin-branches" } : { name: "staff-home" };
    }
  }

  return true;
});
