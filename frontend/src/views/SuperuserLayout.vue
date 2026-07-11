<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";
import ConfirmModal from "../components/ConfirmModal.vue";

const auth = useAuthStore();
const router = useRouter();

const showLogoutConfirm = ref(false);

function onLogout() {
  auth.logout();
  router.push({ name: "login" });
}
</script>

<template>
  <div class="superuser-shell">
    <header class="superuser-topbar">
      <div class="brand">
        <img src="/logo.png" alt="" class="brand-logo" />
        <div class="brand-text">
          <span class="brand-name">Z.A. Company</span>
          <span class="brand-subtitle">Superuser</span>
        </div>
      </div>

      <button type="button" class="logout-btn" @click="showLogoutConfirm = true">
        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
          <polyline points="16 17 21 12 16 7" />
          <line x1="21" y1="12" x2="9" y2="12" />
        </svg>
        Log out
      </button>
    </header>

    <ConfirmModal
      :open="showLogoutConfirm"
      title="Log out?"
      message="Are you sure you want to log out?"
      confirm-label="Log Out"
      variant="danger"
      @confirm="onLogout"
      @cancel="showLogoutConfirm = false"
    />

    <main class="superuser-content">
      <router-view />
    </main>
  </div>
</template>

<style scoped>
.superuser-shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.superuser-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  position: sticky;
  top: 0;
  background: var(--glass-bg);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  border-bottom: 1px solid rgba(255, 84, 112, 0.2);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.35);
  padding: 0.85rem 1.25rem;
  z-index: 50;
}

.brand {
  display: flex;
  align-items: center;
  gap: 0.7rem;
  color: #fff;
}

.brand-logo {
  width: 32px;
  height: 32px;
  border-radius: 8px;
}

.brand-text {
  display: flex;
  flex-direction: column;
  line-height: 1.2;
}

.brand-name {
  font-weight: 700;
  font-size: 0.95rem;
}

.brand-subtitle {
  font-size: 0.7rem;
  font-weight: 500;
  color: var(--color-accent);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.logout-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.35);
  padding: 0.5rem 1rem;
  font-size: 0.9rem;
  font-weight: 600;
  flex-shrink: 0;
}

.logout-btn:hover {
  background: var(--color-danger);
  border-color: var(--color-danger);
}

.superuser-content {
  flex: 1;
  padding: 2rem 1.5rem;
  max-width: 1100px;
  margin: 0 auto;
  width: 100%;
}

@media (max-width: 720px) {
  .superuser-content {
    padding: 1.25rem 1rem;
  }

  .brand-subtitle {
    display: none;
  }
}
</style>
