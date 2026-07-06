<template>
  <div class="not-found">
    <h1>404</h1>
    <p>Page not found.</p>
    <router-link to="/">Go home</router-link>
  </div>
</template>

<style scoped>
.not-found {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}
</style>
