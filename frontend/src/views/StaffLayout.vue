<script setup>
import { computed, ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";
import AccountSettingsModal from "../components/AccountSettingsModal.vue";
import Icon from "../components/Icon.vue";

const auth = useAuthStore();
const router = useRouter();

const showTabs = computed(() => auth.staffRoles.length > 1);
const showSettings = ref(false);

function onLogout() {
  auth.logout();
  router.push({ name: "login" });
}
</script>

<template>
  <div class="staff-shell">
    <header class="staff-topbar">
      <div class="brand">
        <img src="/logo.png" alt="" class="brand-logo" />
        <div class="brand-text">
          <span class="brand-name">Z.A. Company</span>
          <span class="brand-subtitle">Staff Portal</span>
        </div>
      </div>

      <div class="header-actions">
        <button type="button" class="settings-btn" aria-label="Account settings" @click="showSettings = true">
          <Icon name="settings" :size="16" />
        </button>
        <button type="button" class="logout-btn" @click="onLogout">
          <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
            <polyline points="16 17 21 12 16 7" />
            <line x1="21" y1="12" x2="9" y2="12" />
          </svg>
          Log out
        </button>
      </div>
    </header>

    <AccountSettingsModal v-if="showSettings" @close="showSettings = false" />

    <nav v-if="showTabs" class="staff-tabs">
      <router-link
        v-if="auth.staffRoles.includes('staff')"
        :to="{ name: 'staff-deliveries' }"
        class="staff-tab"
        active-class="active"
      >
        Daily Stock
      </router-link>
      <router-link
        v-if="auth.staffRoles.includes('delivery')"
        :to="{ name: 'staff-delivery-log' }"
        class="staff-tab"
        active-class="active"
      >
        Delivery
      </router-link>
    </nav>

    <main class="staff-content">
      <router-view />
    </main>
  </div>
</template>

<style scoped>
.staff-shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.staff-topbar {
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

.header-actions {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  flex-shrink: 0;
}

.settings-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.35);
  border-radius: 999px;
  padding: 0;
  flex-shrink: 0;
}

.settings-btn:hover {
  background: rgba(255, 255, 255, 0.2);
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

.staff-tabs {
  display: flex;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem 0;
  max-width: 1100px;
  margin: 0 auto;
  width: 100%;
}

.staff-tab {
  padding: 0.5rem 1rem;
  border-radius: 999px;
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--color-text-muted);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
}

.staff-tab.active {
  color: #fff;
  background: var(--gradient-primary);
  border-color: transparent;
}

.staff-content {
  flex: 1;
  padding: 2rem 1.5rem;
  max-width: 1100px;
  margin: 0 auto;
  width: 100%;
}

@media (max-width: 720px) {
  .staff-content {
    padding: 1.25rem 1rem;
  }

  .brand-subtitle {
    display: none;
  }
}
</style>
