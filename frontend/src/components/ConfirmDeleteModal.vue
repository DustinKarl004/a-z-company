<script setup>
import { nextTick, ref, watch } from "vue";
import Modal from "./Modal.vue";

const props = defineProps({
  open: { type: Boolean, default: false },
  title: { type: String, default: "Delete this?" },
  message: { type: String, default: "This cannot be undone." },
  confirmLabel: { type: String, default: "Delete" },
  loadingLabel: { type: String, default: "Deleting..." },
  loading: { type: Boolean, default: false },
  error: { type: String, default: "" },
  passwordLabel: { type: String, default: "Enter your admin password to confirm" },
});

const emit = defineEmits(["confirm", "cancel"]);

const password = ref("");
const showPassword = ref(false);
const inputRef = ref(null);

watch(
  () => props.open,
  async (isOpen) => {
    if (isOpen) {
      password.value = "";
      showPassword.value = false;
      await nextTick();
      inputRef.value?.focus();
    }
  }
);

function onConfirm() {
  if (!password.value || props.loading) return;
  emit("confirm", password.value);
}

function onCancel() {
  if (props.loading) return;
  emit("cancel");
}
</script>

<template>
  <Modal v-if="open" :title="title" @close="onCancel">
    <p class="modal-message">{{ message }}</p>

    <div>
      <div class="field">
        <label for="confirm-delete-password">{{ passwordLabel }}</label>
        <div class="inpw">
          <input
            id="confirm-delete-password"
            ref="inputRef"
            v-model="password"
            :type="showPassword ? 'text' : 'password'"
            autocomplete="off"
            placeholder="••••••••"
            @keyup.enter="onConfirm"
          />
          <button
            type="button"
            class="tpw"
            :aria-label="showPassword ? 'Hide password' : 'Show password'"
            @click="showPassword = !showPassword"
          >
            <svg v-if="showPassword" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" />
              <line x1="1" y1="1" x2="23" y2="23" />
            </svg>
            <svg v-else width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
              <circle cx="12" cy="12" r="3" />
            </svg>
          </button>
        </div>
      </div>

      <p v-if="error" class="error-message">{{ error }}</p>

      <div class="modal-actions">
        <button type="button" class="secondary cancel" :disabled="loading" @click="onCancel">Cancel</button>
        <button type="button" class="danger" :disabled="loading || !password" @click="onConfirm">
          {{ loading ? loadingLabel : confirmLabel }}
        </button>
      </div>
    </div>
  </Modal>
</template>

<style scoped>
.modal-message {
  color: var(--color-text-muted);
  margin: 0 0 1.1rem;
}

.field {
  margin-bottom: 1rem;
}

.field label {
  display: block;
  font-size: 0.85rem;
  margin-bottom: 0.4rem;
}

.inpw {
  position: relative;
}

.inpw input {
  width: 100%;
  padding: 0.65rem 2.75rem 0.65rem 0.75rem;
}

.tpw {
  position: absolute;
  top: 50%;
  right: 0.35rem;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  background: transparent;
  color: var(--color-text-muted);
  border: none;
  border-radius: 6px;
  padding: 0;
}

.tpw:hover {
  background: var(--color-primary-soft);
  color: var(--color-primary);
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.6rem;
  margin-top: 1.25rem;
}

.modal-actions button {
  min-width: 100px;
}

.cancel {
  border-color: #fff;
}

.danger {
  background: var(--color-danger);
}

.danger:hover {
  background: var(--color-danger);
  opacity: 0.9;
}

.error-message {
  margin: -0.25rem 0 0;
}
</style>
