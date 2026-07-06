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
  <div class="staff-page">
    <div class="card">
      <h1>Z.A. Company</h1>
      <p>You're signed in. Daily stock and sales entry isn't available yet — check back soon.</p>
      <button class="secondary" @click="onLogout">Log out</button>
    </div>
  </div>
</template>

<style scoped>
.staff-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
}

.card {
  max-width: 420px;
  text-align: center;
}
</style>
