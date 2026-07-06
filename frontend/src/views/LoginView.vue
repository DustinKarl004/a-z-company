<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";
import { ApiError } from "../api/client";

const email = ref("");
const password = ref("");
const error = ref("");
const loading = ref(false);

const auth = useAuthStore();
const router = useRouter();

async function onSubmit() {
  error.value = "";
  loading.value = true;
  try {
    await auth.login(email.value, password.value);
    router.push(auth.role === "admin" ? { name: "admin-branches" } : { name: "staff-home" });
  } catch (e) {
    error.value = e instanceof ApiError ? e.detail || "Login failed" : "Login failed";
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="login-page">
    <form class="card login-card" @submit.prevent="onSubmit">
      <h1>Z.A. Company</h1>
      <p class="subtitle">Sign in to continue</p>

      <div class="field">
        <label for="email">Email</label>
        <input id="email" v-model="email" type="email" required autocomplete="username" />
      </div>

      <div class="field">
        <label for="password">Password</label>
        <input id="password" v-model="password" type="password" required autocomplete="current-password" />
      </div>

      <button type="submit" :disabled="loading">{{ loading ? "Signing in..." : "Sign in" }}</button>

      <p v-if="error" class="error-message">{{ error }}</p>
    </form>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-dark));
}

.login-card {
  width: 320px;
}

.subtitle {
  color: var(--color-text-muted);
  margin: -0.5rem 0 1.5rem;
}

button {
  width: 100%;
}
</style>
