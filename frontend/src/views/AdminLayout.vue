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
      <div class="brand">Z.A. Company</div>
      <nav>
        <router-link :to="{ name: 'admin-branches' }">Branches</router-link>
        <router-link :to="{ name: 'admin-staff' }">Staff</router-link>
      </nav>
      <button class="secondary" @click="onLogout">Log out</button>
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
  display: flex;
  align-items: center;
  gap: 1.5rem;
  padding: 1rem 1.5rem;
  background: var(--color-primary-dark);
  color: #fff;
}

.brand {
  font-weight: 700;
  margin-right: auto;
}

.admin-nav nav {
  display: flex;
  gap: 1rem;
}

.admin-nav a {
  color: rgba(255, 255, 255, 0.8);
  text-decoration: none;
  padding-bottom: 0.2rem;
  border-bottom: 2px solid transparent;
}

.admin-nav a.router-link-active {
  color: #fff;
  border-bottom-color: var(--color-accent);
}

.admin-content {
  padding: 2rem;
  max-width: 960px;
  margin: 0 auto;
}
</style>
