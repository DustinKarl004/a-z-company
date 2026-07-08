<script setup>
import { onMounted, ref } from "vue";
import QRCode from "qrcode";
import { disableTotp, enableTotp, getTotpStatus, setupTotp } from "../api/settings";
import { ApiError } from "../api/client";
import Modal from "../components/Modal.vue";
import ConfirmDeleteModal from "../components/ConfirmDeleteModal.vue";
import LoadingState from "../components/LoadingState.vue";

const loading = ref(true);
const enabled = ref(false);

const showSetupModal = ref(false);
const settingUp = ref(false);
const setupError = ref("");
const setupSecret = ref("");
const qrDataUrl = ref("");
const confirmCode = ref("");
const confirming = ref(false);
const backupCodes = ref([]);

const showDisableModal = ref(false);
const disabling = ref(false);
const disableError = ref("");

async function refresh() {
  loading.value = true;
  const status = await getTotpStatus();
  enabled.value = status.enabled;
  loading.value = false;
}

async function openSetupModal() {
  setupError.value = "";
  confirmCode.value = "";
  backupCodes.value = [];
  settingUp.value = true;
  showSetupModal.value = true;
  try {
    const { secret, otpauth_uri } = await setupTotp();
    setupSecret.value = secret;
    qrDataUrl.value = await QRCode.toDataURL(otpauth_uri);
  } catch (e) {
    setupError.value = e instanceof ApiError ? e.detail || "Could not start 2FA setup" : "Could not start 2FA setup";
  } finally {
    settingUp.value = false;
  }
}

async function closeSetupModal() {
  showSetupModal.value = false;
  if (backupCodes.value.length) await refresh();
}

async function confirmSetup() {
  setupError.value = "";
  confirming.value = true;
  try {
    const result = await enableTotp(setupSecret.value, confirmCode.value);
    backupCodes.value = result.backup_codes;
  } catch (e) {
    setupError.value = e instanceof ApiError ? e.detail || "Invalid code" : "Invalid code";
  } finally {
    confirming.value = false;
  }
}

function downloadBackupCodes() {
  const text = [
    "Z.A. Company - two-factor authentication backup codes",
    "Each code can be used once to sign in if you lose access to your authenticator app.",
    "",
    ...backupCodes.value,
  ].join("\n");
  const blob = new Blob([text], { type: "text/plain" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "za-company-backup-codes.txt";
  link.click();
  URL.revokeObjectURL(url);
}

async function finishSetup() {
  showSetupModal.value = false;
  await refresh();
}

function openDisableModal() {
  disableError.value = "";
  showDisableModal.value = true;
}

function cancelDisable() {
  showDisableModal.value = false;
}

async function confirmDisable(password) {
  disableError.value = "";
  disabling.value = true;
  try {
    await disableTotp(password);
    showDisableModal.value = false;
    await refresh();
  } catch (e) {
    disableError.value = e instanceof ApiError ? e.detail || "Could not turn off 2FA" : "Could not turn off 2FA";
  } finally {
    disabling.value = false;
  }
}

onMounted(refresh);
</script>

<template>
  <div>
    <div class="page-header">
      <div>
        <h1>Settings</h1>
        <p class="page-subtitle">Manage security options for your admin account.</p>
      </div>
    </div>

    <div v-if="loading" class="card state-card">
      <LoadingState label="Loading settings..." />
    </div>

    <div v-else class="card totp-card">
      <div class="totp-info">
        <h2>Two-factor authentication</h2>
        <p class="totp-desc">
          Add an extra layer of protection to your account by requiring a code from an authenticator app
          (like Google Authenticator or Authy) every time you sign in.
        </p>
        <span class="status-chip" :class="enabled ? 'status-on' : 'status-off'">
          {{ enabled ? "Enabled" : "Disabled" }}
        </span>
      </div>
      <div class="totp-actions">
        <button v-if="!enabled" type="button" @click="openSetupModal">Enable 2FA</button>
        <button v-else type="button" class="secondary danger" @click="openDisableModal">Disable 2FA</button>
      </div>
    </div>

    <Modal
      v-if="showSetupModal"
      :title="backupCodes.length ? 'Save your backup codes' : 'Set up two-factor authentication'"
      @close="closeSetupModal"
    >
      <LoadingState v-if="settingUp" label="Preparing setup..." />

      <div v-else-if="backupCodes.length">
        <p class="modal-step">
          Two-factor authentication is now on. Save these one-time backup codes somewhere safe — each one
          can be used to sign in if you ever lose access to your authenticator app.
        </p>
        <div class="backup-codes">
          <code v-for="code in backupCodes" :key="code">{{ code }}</code>
        </div>
        <div class="modal-actions">
          <button type="button" class="secondary" @click="downloadBackupCodes">Download codes</button>
          <button type="button" @click="finishSetup">Done</button>
        </div>
      </div>

      <form v-else @submit.prevent="confirmSetup">
        <p class="modal-step">1. Scan this QR code with your authenticator app.</p>
        <div class="qr-wrap">
          <img v-if="qrDataUrl" :src="qrDataUrl" alt="Scan this QR code with your authenticator app" />
        </div>
        <p class="modal-step">Can't scan it? Enter this key manually instead:</p>
        <code class="manual-secret">{{ setupSecret }}</code>

        <p class="modal-step">2. Enter the 6-digit code from the app to confirm.</p>
        <div class="field">
          <label for="totp-code">Authenticator code</label>
          <input
            id="totp-code"
            v-model="confirmCode"
            required
            inputmode="numeric"
            autocomplete="one-time-code"
            maxlength="6"
            placeholder="123456"
            autofocus
          />
        </div>

        <p v-if="setupError" class="error-message">{{ setupError }}</p>

        <div class="modal-actions">
          <button type="button" class="secondary" :disabled="confirming" @click="closeSetupModal">Cancel</button>
          <button type="submit" :disabled="confirming || !confirmCode">
            {{ confirming ? "Confirming..." : "Confirm and enable" }}
          </button>
        </div>
      </form>
    </Modal>

    <ConfirmDeleteModal
      :open="showDisableModal"
      title="Turn off two-factor authentication?"
      message="You'll only need your password to sign in after this. Enter your password to confirm."
      confirm-label="Disable 2FA"
      loading-label="Disabling..."
      :loading="disabling"
      :error="disableError"
      @confirm="confirmDisable"
      @cancel="cancelDisable"
    />
  </div>
</template>

<style scoped>
.page-header {
  margin-bottom: 1.75rem;
}

.page-header h1 {
  font-size: 1.6rem;
  margin-bottom: 0.35rem;
}

.page-subtitle {
  color: var(--color-text-muted);
  margin: 0;
}

.card {
  margin-bottom: 1.5rem;
}

.state-card {
  padding: 0;
}

.totp-card {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1.5rem;
  background: var(--color-surface);
  border-radius: var(--radius);
  border-top: 3px solid var(--color-primary);
  box-shadow: var(--shadow);
  padding: 1.75rem;
}

.totp-info h2 {
  font-size: 1.1rem;
  margin-bottom: 0.5rem;
}

.totp-desc {
  color: var(--color-text-muted);
  max-width: 480px;
  margin: 0 0 0.85rem;
}

.status-chip {
  display: inline-block;
  font-size: 0.85rem;
  font-weight: 600;
  padding: 0.3rem 0.8rem;
  border-radius: 999px;
}

.status-on {
  background: rgba(46, 160, 67, 0.15);
  color: #2ea043;
}

.status-off {
  background: var(--color-primary-soft);
  color: var(--color-text-muted);
}

.totp-actions {
  flex-shrink: 0;
}

.totp-actions .danger {
  color: var(--color-danger);
  border-color: var(--color-danger);
}

.totp-actions .danger:hover {
  background: rgba(255, 77, 77, 0.1);
}

.modal-step {
  font-size: 0.9rem;
  margin: 0 0 0.6rem;
}

.backup-codes {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.5rem;
  background: var(--color-primary-soft);
  border-radius: 8px;
  padding: 1rem;
  margin: 0.75rem 0 1.25rem;
}

.backup-codes code {
  text-align: center;
  letter-spacing: 0.03em;
  padding: 0.3rem 0;
}

.qr-wrap {
  display: flex;
  justify-content: center;
  margin-bottom: 1rem;
}

.qr-wrap img {
  width: 200px;
  height: 200px;
  border-radius: 8px;
}

.manual-secret {
  display: block;
  text-align: center;
  background: var(--color-primary-soft);
  border-radius: 8px;
  padding: 0.6rem;
  margin-bottom: 1.25rem;
  letter-spacing: 0.05em;
  word-break: break-all;
}

.field {
  margin-bottom: 1.1rem;
}

.field input {
  width: 100%;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.6rem;
  margin-top: 0.25rem;
}

@media (max-width: 560px) {
  .totp-card {
    flex-direction: column;
  }

  .totp-actions {
    width: 100%;
  }

  .totp-actions button {
    width: 100%;
  }
}

@media (max-width: 480px) {
  .qr-wrap img {
    width: 160px;
    height: 160px;
  }

  .backup-codes {
    grid-template-columns: 1fr;
  }

  .modal-actions {
    flex-direction: column-reverse;
  }

  .modal-actions button {
    width: 100%;
  }
}
</style>
