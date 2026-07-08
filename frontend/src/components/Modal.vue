<script setup>
import { onBeforeUnmount, onMounted } from "vue";

const props = defineProps({
  title: { type: String, default: "" },
  wide: { type: Boolean, default: false },
});

const emit = defineEmits(["close"]);

function onKeydown(e) {
  if (e.key === "Escape") emit("close");
}

onMounted(() => document.addEventListener("keydown", onKeydown));
onBeforeUnmount(() => document.removeEventListener("keydown", onKeydown));
</script>

<template>
  <Teleport to="body">
    <div class="modal-overlay" @click.self="emit('close')">
      <div class="modal-panel" :class="{ wide }" role="dialog" aria-modal="true">
        <div class="modal-header">
          <h2 class="modal-title">{{ title }}</h2>
          <button type="button" class="modal-close" aria-label="Close" @click="emit('close')">✕</button>
        </div>
        <div class="modal-body">
          <slot />
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  z-index: 100;
}

.modal-panel {
  width: 100%;
  max-width: 420px;
  max-height: calc(100vh - 2rem);
  overflow-y: auto;
  background: var(--color-surface);
  border-radius: var(--radius);
  border-top: 3px solid var(--color-primary);
  border-image: var(--gradient-primary) 1;
  box-shadow: var(--shadow-hover);
}

.modal-panel.wide {
  max-width: 560px;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 1.1rem 1.25rem;
  border-bottom: 1px solid var(--color-border);
}

.modal-title {
  font-size: 1.05rem;
  margin: 0;
}

.modal-close {
  flex-shrink: 0;
  background: transparent;
  color: var(--color-text-muted);
  border: none;
  padding: 0.2rem 0.5rem;
  font-size: 1rem;
  line-height: 1;
}

.modal-close:hover {
  background: rgba(255, 255, 255, 0.06);
  color: var(--color-text);
}

.modal-body {
  padding: 1.25rem;
}

@media (max-width: 480px) {
  .modal-overlay {
    padding: 0;
    align-items: flex-end;
  }

  .modal-panel {
    max-width: none;
    width: 100%;
    max-height: 90vh;
    border-radius: var(--radius) var(--radius) 0 0;
  }
}
</style>
