<script setup>
import { computed, ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";
import Icon from "../components/Icon.vue";
import ConfirmModal from "../components/ConfirmModal.vue";

const auth = useAuthStore();
const router = useRouter();

// "delivery" staff always get two tabs (Delivery + Stock Records) even when
// it's their only role, so tab visibility can't just check role count.
const showTabs = computed(() => auth.staffRoles.length > 1 || auth.staffRoles.includes("delivery"));

const showLogoutConfirm = ref(false);

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

    <nav v-if="showTabs" class="staff-tabs">
      <router-link
        v-if="auth.staffRoles.includes('staff')"
        :to="{ name: 'staff-deliveries' }"
        class="staff-tab"
        active-class="active"
      >
        <Icon name="stock" :size="16" /><span>Daily Stock</span>
      </router-link>
      <router-link
        v-if="auth.staffRoles.includes('delivery')"
        :to="{ name: 'staff-delivery-log' }"
        class="staff-tab"
        active-class="active"
      >
        <Icon name="truck" :size="16" /><span>Delivery</span>
      </router-link>
      <router-link
        v-if="auth.staffRoles.includes('delivery')"
        :to="{ name: 'staff-stock-records' }"
        class="staff-tab"
        active-class="active"
      >
        <Icon name="list" :size="16" /><span>Stock Records</span>
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
  gap: 0;
  padding: 0.75rem 1.5rem 0;
  max-width: 1100px;
  margin: 0 auto;
  width: 100%;
  border-bottom: 1px solid var(--color-border);
}

.staff-tab {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.6rem 1.1rem;
  margin-bottom: -1px;
  border-radius: 0;
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--color-text-muted);
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  text-decoration: none;
}

.staff-tab:hover:not(.active) {
  color: var(--color-text);
}

.staff-tab.active {
  color: var(--color-primary);
  background: var(--color-primary-soft);
  border-bottom-color: var(--color-primary);
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
    /* Leave room for the fixed bottom tab bar below, plus the device's
       home-indicator safe area, so content never sits underneath it. */
    padding-bottom: calc(1.25rem + 64px + env(safe-area-inset-bottom));
  }

  .brand-subtitle {
    display: none;
  }

  .staff-tabs {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    max-width: none;
    margin: 0;
    gap: 0;
    padding: 0.4rem 0.5rem calc(0.4rem + env(safe-area-inset-bottom));
    background: var(--glass-bg);
    backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);
    border-top: 1px solid rgba(255, 84, 112, 0.2);
    border-bottom: none;
    box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.35);
    z-index: 50;
  }

  .staff-tab {
    flex: 1;
    flex-direction: column;
    justify-content: center;
    gap: 0.2rem;
    text-align: center;
    padding: 0.5rem 0.4rem;
    margin-bottom: 0;
    border-radius: 10px;
    border: none;
    border-bottom: none;
    background: transparent;
    font-size: 0.7rem;
  }

  .staff-tab.active {
    color: #fff;
    background: var(--gradient-primary);
  }
}
</style>
