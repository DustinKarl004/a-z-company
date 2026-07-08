import { defineStore } from "pinia";
import { login as apiLogin } from "../api/auth";
import { decodeJwtPayload } from "../utils/jwt";

const STORAGE_KEY = "za_company_token";

export const useAuthStore = defineStore("auth", {
  state: () => ({
    token: localStorage.getItem(STORAGE_KEY) || null,
  }),

  getters: {
    user(state) {
      return state.token ? decodeJwtPayload(state.token) : null;
    },
    isAuthenticated(state) {
      return !!state.token;
    },
    role() {
      return this.user?.role || null;
    },
    branchId() {
      return this.user?.branch_id || null;
    },
    branchName() {
      return this.user?.branch_name || null;
    },
    staffRoles() {
      const roles = this.user?.roles;
      return Array.isArray(roles) && roles.length ? roles : ["staff"];
    },
  },

  actions: {
    async login(email, password, totpCode) {
      const { access_token } = await apiLogin(email, password, totpCode);
      this.token = access_token;
      localStorage.setItem(STORAGE_KEY, access_token);
    },

    setToken(token) {
      this.token = token;
      localStorage.setItem(STORAGE_KEY, token);
    },

    logout() {
      this.token = null;
      localStorage.removeItem(STORAGE_KEY);
    },
  },
});
