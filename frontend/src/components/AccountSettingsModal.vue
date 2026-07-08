<script setup>
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { ApiError } from "../api/client";
import { listBranches } from "../api/branches";
import { changeMyPassword, getMe, updateMyBranch } from "../api/me";
import { useAuthStore } from "../stores/auth";
import CustomSelect from "./CustomSelect.vue";
import Modal from "./Modal.vue";

const emit = defineEmits(["close"]);

const auth = useAuthStore();
const router = useRouter();

const loading = ref(true);
const me = ref(null);
const branches = ref([]);
const branchOptions = computed(() => branches.value.map((b) => ({ label: b.name, value: b.id })));
const canEditBranch = computed(() => !!me.value?.roles?.includes("staff"));

const branchDraft = ref("");
const branchSaving = ref(false);
const branchError = ref("");
const branchSaved = ref(false);

const passwordForm = ref({ currentPassword: "", newPassword: "", confirmPassword: "" });
const passwordSaving = ref(false);
const passwordError = ref("");

const showPassword = ref({ current: false, new: false, confirm: false });

async function refresh() {
  loading.value = true;
  const [meData, branchList] = await Promise.all([getMe(), listBranches()]);
  me.value = meData;
  branches.value = branchList;
  branchDraft.value = meData.branch_id || "";
  loading.value = false;
}

async function saveBranch() {
  branchError.value = "";
  branchSaving.value = true;
  try {
    const { access_token } = await updateMyBranch(branchDraft.value);
    auth.setToken(access_token);
    me.value.branch_id = branchDraft.value;
    branchSaved.value = true;
    setTimeout(() => {
      branchSaved.value = false;
    }, 1500);
  } catch (e) {
    branchError.value = e instanceof ApiError ? e.detail || "Could not update branch" : "Could not update branch";
  } finally {
    branchSaving.value = false;
  }
}

async function savePassword() {
  passwordError.value = "";
  if (passwordForm.value.newPassword !== passwordForm.value.confirmPassword) {
    passwordError.value = "New passwords do not match.";
    return;
  }
  passwordSaving.value = true;
  try {
    await changeMyPassword(passwordForm.value.currentPassword, passwordForm.value.newPassword);
    auth.logout();
    router.push({ name: "login" });
  } catch (e) {
    passwordError.value = e instanceof ApiError ? e.detail || "Could not change password" : "Could not change password";
    passwordSaving.value = false;
  }
}

onMounted(refresh);
</script>

<template>
  <Modal title="Account settings" @close="emit('close')">
    <div v-if="loading" class="loading-row">Loading...</div>
    <template v-else>
      <section v-if="canEditBranch" class="settings-section">
        <h3>Branch</h3>
        <div class="field">
          <label for="account-branch">Assigned branch</label>
          <CustomSelect id="account-branch" v-model="branchDraft" :options="branchOptions" placeholder="Select a branch" />
        </div>
        <p v-if="branchError" class="error-message">{{ branchError }}</p>
        <div class="section-actions">
          <button
            type="button"
            :disabled="branchSaving || !branchDraft || branchDraft === me.branch_id"
            @click="saveBranch"
          >
            {{ branchSaving ? "Saving..." : branchSaved ? "Saved" : "Save branch" }}
          </button>
        </div>
        <p class="section-hint">Takes effect right away, no need to log out.</p>
      </section>

      <section class="settings-section">
        <h3>Change password</h3>
        <p class="section-hint section-hint-lead">You'll be signed out after changing your password — log back in with the new one.</p>
        <form @submit.prevent="savePassword">
          <div class="field">
            <label for="account-current-password">Current password</label>
            <div class="inpw">
              <input
                id="account-current-password"
                v-model="passwordForm.currentPassword"
                :type="showPassword.current ? 'text' : 'password'"
                required
                autocomplete="current-password"
              />
              <button
                type="button"
                class="tpw"
                :aria-label="showPassword.current ? 'Hide password' : 'Show password'"
                @click="showPassword.current = !showPassword.current"
              >
                <svg v-if="showPassword.current" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
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
          <div class="field">
            <label for="account-new-password">New password</label>
            <div class="inpw">
              <input
                id="account-new-password"
                v-model="passwordForm.newPassword"
                :type="showPassword.new ? 'text' : 'password'"
                required
                minlength="8"
                placeholder="At least 8 characters"
                autocomplete="new-password"
              />
              <button
                type="button"
                class="tpw"
                :aria-label="showPassword.new ? 'Hide password' : 'Show password'"
                @click="showPassword.new = !showPassword.new"
              >
                <svg v-if="showPassword.new" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
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
          <div class="field">
            <label for="account-confirm-password">Confirm new password</label>
            <div class="inpw">
              <input
                id="account-confirm-password"
                v-model="passwordForm.confirmPassword"
                :type="showPassword.confirm ? 'text' : 'password'"
                required
                autocomplete="new-password"
              />
              <button
                type="button"
                class="tpw"
                :aria-label="showPassword.confirm ? 'Hide password' : 'Show password'"
                @click="showPassword.confirm = !showPassword.confirm"
              >
                <svg v-if="showPassword.confirm" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
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
          <p v-if="passwordError" class="error-message">{{ passwordError }}</p>
          <div class="section-actions">
            <button type="submit" :disabled="passwordSaving">
              {{ passwordSaving ? "Saving..." : "Change password" }}
            </button>
          </div>
        </form>
      </section>
    </template>
  </Modal>
</template>

<style scoped>
.loading-row {
  padding: 1rem 0;
  color: var(--color-text-muted);
}

.settings-section {
  margin-bottom: 1.5rem;
}

.settings-section:last-child {
  margin-bottom: 0;
}

.settings-section h3 {
  font-size: 0.95rem;
  margin-bottom: 0.75rem;
}

.field {
  margin-bottom: 0.85rem;
}

.field input {
  width: 100%;
}

.inpw {
  position: relative;
}

.inpw input {
  padding-right: 2.75rem;
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

.section-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 0.5rem;
}

.section-hint {
  font-size: 0.78rem;
  color: var(--color-text-muted);
  margin-top: 0.6rem;
}

.section-hint.section-hint-lead {
  margin-top: -0.35rem;
  margin-bottom: 0.85rem;
}
</style>
