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
  },

  actions: {
    async login(email, password) {
      const { access_token } = await apiLogin(email, password);
      this.token = access_token;
      localStorage.setItem(STORAGE_KEY, access_token);
    },

    logout() {
      this.token = null;
      localStorage.removeItem(STORAGE_KEY);
    },
  },
});
