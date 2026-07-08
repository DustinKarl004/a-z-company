<script setup>
defineProps({
  label: { type: String, default: "Loading..." },
});
</script>

<template>
  <div class="loading-state">
    <span class="loading-spinner" aria-hidden="true"></span>
    <span class="loading-label">{{ label }}</span>
  </div>
</template>

<style scoped>
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 2.5rem 1.5rem;
  color: var(--color-text-muted);
}

.loading-spinner {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 3px solid var(--color-border);
  border-top-color: var(--color-primary);
  animation: loading-spin 0.7s linear infinite;
}

.loading-label {
  font-size: 0.85rem;
  font-weight: 600;
}

@keyframes loading-spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
