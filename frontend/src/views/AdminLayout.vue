<script setup>
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";

const auth = useAuthStore();
const router = useRouter();

function onLogout() {
  auth.logout();
  router.push({ name: "login" });
}
</script>

<template>
  <div class="admin-shell">
    <header class="admin-nav">
      <div class="nav-inner">
        <div class="brand">
          <img src="/logo.svg" alt="" class="brand-logo" />
          <span>Z.A. Company</span>
        </div>

        <nav>
          <router-link :to="{ name: 'admin-dashboard' }">Dashboard</router-link>
          <router-link :to="{ name: 'admin-branches' }">Branches</router-link>
          <router-link :to="{ name: 'admin-staff' }">Staff</router-link>
          <router-link :to="{ name: 'admin-stock-items' }">Stock Items</router-link>
        </nav>

        <button class="logout-btn" @click="onLogout">
          <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
            <polyline points="16 17 21 12 16 7" />
            <line x1="21" y1="12" x2="9" y2="12" />
          </svg>
          Log out
        </button>
      </div>
    </header>

    <main class="admin-content">
      <router-view />
    </main>
  </div>
</template>

<style scoped>
.admin-shell {
  min-height: 100vh;
}

.admin-nav {
  background: var(--color-primary-dark);
  border-bottom: 3px solid var(--color-accent);
}

.nav-inner {
  display: flex;
  align-items: center;
  gap: 2rem;
  padding: 0.85rem 2rem;
  max-width: 1100px;
  margin: 0 auto;
}

.brand {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  font-weight: 700;
  color: #fff;
  margin-right: auto;
  letter-spacing: 0.01em;
}

.brand-logo {
  width: 30px;
  height: 30px;
}

.admin-nav nav {
  display: flex;
  gap: 0.4rem;
}

.admin-nav a {
  color: rgba(255, 255, 255, 0.75);
  text-decoration: none;
  padding: 0.45rem 0.9rem;
  border-radius: 999px;
  font-size: 0.92rem;
  font-weight: 500;
  transition: background 0.15s, color 0.15s;
}

.admin-nav a:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.08);
}

.admin-nav a.router-link-active {
  color: var(--color-primary-dark);
  background: var(--color-accent);
  font-weight: 600;
}

.logout-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.35);
  padding: 0.5rem 1rem;
  font-size: 0.9rem;
  font-weight: 600;
}

.logout-btn:hover {
  background: var(--color-danger);
  border-color: var(--color-danger);
}

.admin-content {
  padding: 2.5rem 2rem;
  max-width: 1100px;
  margin: 0 auto;
}

@media (max-width: 640px) {
  .nav-inner {
    flex-wrap: wrap;
    gap: 0.75rem;
    padding: 0.85rem 1rem;
  }

  .brand {
    margin-right: 0;
    flex: 1;
  }

  .admin-nav nav {
    order: 3;
    width: 100%;
  }

  .admin-content {
    padding: 1.5rem 1rem;
  }
}
</style>
