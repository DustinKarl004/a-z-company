<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import { deleteBackupRun, getBackupConfig, listBackupRuns, triggerBackup } from "../api/backup";
import { ApiError } from "../api/client";
import { fetchBusinessToday, parseLocalISO, toLocalISO } from "../utils/date";
import ConfirmDeleteModal from "../components/ConfirmDeleteModal.vue";
import Icon from "../components/Icon.vue";
import LoadingState from "../components/LoadingState.vue";
import Modal from "../components/Modal.vue";

const runs = ref([]);
const config = ref(null);
const loading = ref(true);
const error = ref("");
const running = ref(false);
const runError = ref("");
const backupDate = ref("");
const maxDate = ref("");
const showRunConfirm = ref(false);

const deleteTarget = ref(null);
const deleteError = ref("");
const deleting = ref(false);

const selectionMode = ref(false);
const selectedIds = ref(new Set());
const showDeleteSelectedModal = ref(false);
const deleteSelectedError = ref("");
const deletingSelected = ref(false);

const pageSize = 10;
const currentPage = ref(1);

let pollTimer = null;

async function refresh() {
  error.value = "";
  try {
    runs.value = await listBackupRuns();
  } catch (e) {
    error.value = e instanceof ApiError ? e.detail || "Could not load backup history" : "Could not load backup history";
  } finally {
    loading.value = false;
  }
}

async function loadConfig() {
  try {
    config.value = await getBackupConfig();
  } catch {
    config.value = null;
  }
}

const datesToGenerate = computed(() => {
  if (!backupDate.value) return [];
  const target = parseLocalISO(backupDate.value);
  const start = new Date(target.getFullYear(), target.getMonth(), 1);
  const dates = [];
  for (let d = new Date(start); d <= target; d.setDate(d.getDate() + 1)) {
    dates.push(d.toLocaleDateString(undefined, { month: "short", day: "numeric" }));
  }
  return dates;
});

const runConfirmMonthLabel = computed(() => {
  if (!backupDate.value) return "";
  return parseLocalISO(backupDate.value).toLocaleDateString(undefined, { month: "long", year: "numeric" });
});

function openRunConfirm() {
  runError.value = "";
  showRunConfirm.value = true;
}

function cancelRunConfirm() {
  if (running.value) return;
  showRunConfirm.value = false;
}

async function onRunNow() {
  running.value = true;
  runError.value = "";
  try {
    const run = await triggerBackup(backupDate.value || undefined);
    runs.value = [run, ...runs.value];
    showRunConfirm.value = false;
    if (run.status === "failure") {
      runError.value = run.error_message || "Backup failed";
    }
  } catch (e) {
    runError.value = e instanceof ApiError ? e.detail || "Could not run backup" : "Could not run backup";
  } finally {
    running.value = false;
  }
}

function formatDate(iso) {
  return new Date(iso).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
    timeZone: config.value?.app_timezone || "Asia/Manila",
  });
}

// Covers day 1 of that month through as_of_date — falls back to the run's
// own created_at date for older rows recorded before as_of_date existed.
function coverageLabel(run) {
  const asOf = run.as_of_date ? parseLocalISO(run.as_of_date) : new Date(run.created_at);
  const start = new Date(asOf.getFullYear(), asOf.getMonth(), 1);
  const days = asOf.getDate();
  const startLabel = start.toLocaleDateString(undefined, { month: "short", day: "numeric" });
  const endLabel = asOf.toLocaleDateString(undefined, { month: "short", day: "numeric" });
  return `${startLabel} – ${endLabel} (${days} ${days === 1 ? "day" : "days"})`;
}

function onDelete(run) {
  deleteError.value = "";
  deleteTarget.value = run;
}

function cancelDelete() {
  if (deleting.value) return;
  deleteTarget.value = null;
}

async function confirmDelete(password) {
  const run = deleteTarget.value;
  deleteError.value = "";
  deleting.value = true;
  try {
    await deleteBackupRun(run.id, password);
    runs.value = runs.value.filter((r) => r.id !== run.id);
    deleteTarget.value = null;
  } catch (e) {
    deleteError.value = e instanceof ApiError ? e.detail || "Could not delete backup history" : "Could not delete backup history";
  } finally {
    deleting.value = false;
  }
}

function toggleSelectionMode() {
  selectionMode.value = !selectionMode.value;
  selectedIds.value = new Set();
}

function toggleSelectItem(id) {
  const next = new Set(selectedIds.value);
  if (next.has(id)) next.delete(id);
  else next.add(id);
  selectedIds.value = next;
}

function isSelected(id) {
  return selectedIds.value.has(id);
}

function selectAllOnPage() {
  selectedIds.value = new Set([...selectedIds.value, ...pagedRuns.value.map((r) => r.id)]);
}

function clearSelection() {
  selectedIds.value = new Set();
}

function openDeleteSelectedModal() {
  deleteSelectedError.value = "";
  showDeleteSelectedModal.value = true;
}

function cancelDeleteSelected() {
  if (deletingSelected.value) return;
  showDeleteSelectedModal.value = false;
}

async function confirmDeleteSelected(password) {
  deleteSelectedError.value = "";
  deletingSelected.value = true;
  try {
    for (const id of selectedIds.value) {
      await deleteBackupRun(id, password);
    }
    runs.value = runs.value.filter((r) => !selectedIds.value.has(r.id));
    showDeleteSelectedModal.value = false;
    selectionMode.value = false;
    selectedIds.value = new Set();
  } catch (e) {
    deleteSelectedError.value =
      e instanceof ApiError ? e.detail || "Could not delete selected history" : "Could not delete selected history";
  } finally {
    deletingSelected.value = false;
  }
}

const totalPages = computed(() => Math.max(1, Math.ceil(runs.value.length / pageSize)));

const pagedRuns = computed(() => {
  const start = (currentPage.value - 1) * pageSize;
  return runs.value.slice(start, start + pageSize);
});

watch(totalPages, (total) => {
  if (currentPage.value > total) currentPage.value = total;
});

function goToPage(page) {
  currentPage.value = Math.min(Math.max(page, 1), totalPages.value);
}

// Filenames follow Backup_<Month>_<Year>.xlsx, deterministic from the run's
// as_of_date (falling back to created_at for older rows without one).
function fileName(run) {
  const d = run.as_of_date ? parseLocalISO(run.as_of_date) : new Date(run.created_at);
  const month = d.toLocaleString("en-US", { month: "long" });
  return `Backup_${month}_${d.getFullYear()}.xlsx`;
}

const nextRunLabel = computed(() => {
  if (!config.value) return "";
  if (!config.value.backup_enabled) return "Scheduled backups are currently disabled.";
  const { backup_hour_local, app_timezone } = config.value;
  const label = new Date(2000, 0, 1, backup_hour_local).toLocaleTimeString(undefined, {
    hour: "numeric",
    minute: "2-digit",
  });
  return `Runs automatically every day at ${label} (${app_timezone}).`;
});

onMounted(async () => {
  loading.value = true;
  const { date } = await fetchBusinessToday();
  backupDate.value = toLocalISO(date);
  maxDate.value = toLocalISO(date);
  await Promise.all([refresh(), loadConfig()]);
  pollTimer = setInterval(refresh, 60000);
});

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer);
});
</script>

<template>
  <div class="page-header">
    <div>
      <h1>Daily backups</h1>
      <p class="page-subtitle">One Excel workbook per month, backed up to Google Drive automatically every night.</p>
      <p v-if="nextRunLabel" class="next-run">
        <Icon name="clock" :size="13" />
        {{ nextRunLabel }}
      </p>
    </div>
    <div class="header-actions">
      <button type="button" class="secondary" :disabled="loading" @click="refresh">
        <Icon name="refresh" :size="14" />
        Refresh
      </button>
      <button
        v-if="runs.length"
        type="button"
        class="secondary"
        :class="{ active: selectionMode }"
        @click="toggleSelectionMode"
      >
        <Icon name="check" :size="14" /> {{ selectionMode ? "Cancel select" : "Select" }}
      </button>
      <div class="run-now-group">
        <input
          v-model="backupDate"
          type="date"
          :max="maxDate"
          :disabled="running"
          aria-label="Date to back up"
          title="Regenerates that date's whole month, from the 1st through this date"
        />
        <button type="button" :disabled="running || !backupDate" @click="openRunConfirm">
          <Icon name="download" :size="14" />
          {{ running ? "Running..." : "Run backup now" }}
        </button>
      </div>
    </div>
  </div>

  <div v-if="selectionMode" class="selection-bar">
    <span class="selection-count">{{ selectedIds.size }} selected</span>
    <div class="selection-actions">
      <button type="button" class="secondary" @click="selectAllOnPage">Select page</button>
      <button type="button" class="secondary" :disabled="!selectedIds.size" @click="clearSelection">Clear</button>
      <button type="button" class="danger" :disabled="!selectedIds.size" @click="openDeleteSelectedModal">
        <Icon name="trash" :size="14" /> Delete selected ({{ selectedIds.size }})
      </button>
    </div>
  </div>

  <p v-if="runError" class="error-message top-error">{{ runError }}</p>
  <p v-if="error" class="error-message top-error">{{ error }}</p>
  <LoadingState v-if="loading" label="Loading backup history..." />

  <div v-else-if="!runs.length" class="card state-card">
    <div class="empty-state">
      <p>No backups have run yet.</p>
      <p class="empty-hint">Click "Run backup now" to create the first one, or wait for tonight's scheduled run.</p>
    </div>
  </div>

  <div v-else class="run-list">
    <div
      v-for="run in pagedRuns"
      :key="run.id"
      class="card run-row"
      :class="{ selectable: selectionMode, selected: selectionMode && isSelected(run.id) }"
      @click="selectionMode && toggleSelectItem(run.id)"
    >
      <div class="run-main">
        <label v-if="selectionMode" class="run-checkbox" @click.stop>
          <input type="checkbox" :checked="isSelected(run.id)" @change="toggleSelectItem(run.id)" />
        </label>
        <span class="badge" :class="run.status === 'success' ? 'active' : 'inactive'">
          <Icon :name="run.status === 'success' ? 'check' : 'x'" :size="11" />
          {{ run.status }}
        </span>
        <span class="run-date">{{ formatDate(run.created_at) }}</span>
        <span class="run-trigger">{{ run.triggered_by === "manual" ? "Manual" : "Scheduled" }}</span>
        <button
          v-if="!selectionMode"
          type="button"
          class="secondary delete-btn"
          title="Delete this history entry"
          aria-label="Delete this history entry"
          @click.stop="onDelete(run)"
        >
          <Icon name="trash" :size="13" />
        </button>
      </div>

      <div class="run-details">
        <div class="run-field">
          <span class="run-label">File</span>
          <a v-if="run.drive_file_link" :href="run.drive_file_link" target="_blank" rel="noopener" class="run-file-link">
            {{ fileName(run) }}
          </a>
          <span v-else class="muted">{{ fileName(run) }}</span>
        </div>
        <div class="run-field">
          <span class="run-label">Covers</span>
          <span>{{ coverageLabel(run) }}</span>
        </div>
        <p v-if="run.error_message" class="run-error">{{ run.error_message }}</p>
      </div>
    </div>

    <div v-if="totalPages > 1" class="pagination">
      <button class="secondary" :disabled="currentPage === 1" @click="goToPage(currentPage - 1)">Prev</button>
      <button
        v-for="page in totalPages"
        :key="page"
        class="page-btn"
        :class="{ active: page === currentPage }"
        @click="goToPage(page)"
      >
        {{ page }}
      </button>
      <button class="secondary" :disabled="currentPage === totalPages" @click="goToPage(currentPage + 1)">Next</button>
    </div>
  </div>

  <ConfirmDeleteModal
    :open="!!deleteTarget"
    title="Delete this backup history entry?"
    message="This only removes the log entry — it does not delete the Excel file already uploaded to Google Drive."
    password-label="Enter your superuser password to confirm"
    confirm-label="Delete"
    loading-label="Deleting..."
    :loading="deleting"
    :error="deleteError"
    @confirm="confirmDelete"
    @cancel="cancelDelete"
  />

  <ConfirmDeleteModal
    :open="showDeleteSelectedModal"
    :title="`Delete ${selectedIds.size} selected ${selectedIds.size === 1 ? 'entry' : 'entries'}?`"
    message="This only removes the log entries — it does not delete the Excel files already uploaded to Google Drive."
    password-label="Enter your superuser password to confirm"
    confirm-label="Delete selected"
    loading-label="Deleting..."
    :loading="deletingSelected"
    :error="deleteSelectedError"
    @confirm="confirmDeleteSelected"
    @cancel="cancelDeleteSelected"
  />

  <Modal v-if="showRunConfirm" title="Run backup now?" @close="cancelRunConfirm">
    <p class="modal-message">
      This will create or update <strong>Backup_{{ runConfirmMonthLabel.replace(" ", "_") }}.xlsx</strong> in Drive,
      covering these days:
    </p>
    <div class="date-chips">
      <span v-for="d in datesToGenerate" :key="d" class="date-chip">{{ d }}</span>
    </div>
    <p v-if="runError" class="error-message">{{ runError }}</p>
    <div class="modal-actions">
      <button type="button" class="secondary cancel" :disabled="running" @click="cancelRunConfirm">Cancel</button>
      <button type="button" :disabled="running" @click="onRunNow">
        {{ running ? "Running..." : "Confirm & run" }}
      </button>
    </div>
  </Modal>
</template>

<style scoped>
.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
  margin-bottom: 1.75rem;
}

.page-header h1 {
  font-size: 1.5rem;
  margin-bottom: 0.35rem;
}

.page-subtitle {
  color: var(--color-text-muted);
  margin: 0;
  max-width: 48ch;
}

.next-run {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  color: var(--color-text-muted);
  font-size: 0.82rem;
  margin: 0.6rem 0 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  flex-shrink: 0;
  flex-wrap: wrap;
}

.run-now-group {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.run-now-group input[type="date"] {
  padding: 0.5rem 0.6rem;
}

.header-actions button.active {
  background: var(--color-primary-soft);
  color: var(--color-primary);
  border-color: var(--color-primary);
}

.selection-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  flex-wrap: wrap;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  padding: 0.75rem 1rem;
  margin-bottom: 1rem;
}

.selection-count {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--color-text-muted);
}

.selection-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.selection-actions .danger {
  background: var(--color-danger);
}

.selection-actions .danger:hover {
  opacity: 0.9;
}

.run-checkbox {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.run-checkbox input {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.run-row.selectable {
  cursor: pointer;
}

.run-row.selected {
  box-shadow: 0 0 0 2px var(--color-primary);
}

.top-error {
  text-align: center;
}

.state-card {
  padding: 0;
}

.empty-state {
  padding: 2.5rem 1.5rem;
  text-align: center;
}

.empty-state p {
  margin: 0;
}

.empty-hint {
  color: var(--color-text-muted);
  font-size: 0.9rem;
  margin-top: 0.35rem !important;
}

.run-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.run-row {
  padding: 1rem 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
}

.run-main {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.badge {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  text-transform: capitalize;
}

.run-date {
  font-weight: 600;
}

.run-trigger {
  color: var(--color-text-muted);
  font-size: 0.85rem;
}

.delete-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  padding: 0;
  margin-left: auto;
  flex-shrink: 0;
}

.delete-btn:hover {
  background: var(--color-danger);
  color: #fff;
  border-color: var(--color-danger);
}

.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
  margin-top: 0.5rem;
}

.page-btn {
  min-width: 34px;
  height: 34px;
  padding: 0 0.5rem;
  border-radius: 8px;
  background: transparent;
  color: var(--color-text-muted);
  font-weight: 600;
  font-size: 0.85rem;
}

.page-btn:hover {
  background: var(--color-bg);
}

.page-btn.active {
  background: var(--gradient-primary);
  color: #fff;
}

.run-details {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  padding-top: 0.5rem;
  border-top: 1px solid var(--color-border);
}

.run-field {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.88rem;
}

.run-label {
  color: var(--color-text-muted);
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-weight: 600;
  flex-shrink: 0;
}

.run-file-link {
  word-break: break-all;
}

.muted {
  color: var(--color-text-muted);
}

.run-error {
  color: var(--color-danger);
  font-size: 0.85rem;
  margin: 0;
}

.modal-message {
  color: var(--color-text-muted);
  margin: 0 0 1rem;
}

.date-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  max-height: 220px;
  overflow-y: auto;
  padding-bottom: 0.25rem;
  margin-bottom: 1rem;
}

.date-chip {
  display: inline-block;
  padding: 0.25rem 0.6rem;
  border-radius: 999px;
  background: var(--color-primary-soft);
  color: var(--color-primary);
  font-size: 0.8rem;
  font-weight: 600;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.6rem;
}

.modal-actions button {
  min-width: 100px;
}

.cancel {
  border-color: #fff;
}

@media (max-width: 700px) {
  .page-header {
    flex-direction: column;
    align-items: stretch;
  }

  .header-actions {
    justify-content: stretch;
    flex-direction: column;
    align-items: stretch;
  }

  .header-actions > button {
    width: 100%;
  }

  .run-now-group {
    flex-direction: column;
    align-items: stretch;
  }

  .run-now-group input[type="date"] {
    width: 100%;
  }

  .selection-bar {
    flex-direction: column;
    align-items: stretch;
  }

  .selection-actions {
    justify-content: space-between;
  }

  .selection-actions button {
    flex: 1;
  }

  .run-main {
    position: relative;
    padding-right: 2.25rem;
  }

  .delete-btn {
    position: absolute;
    top: 0;
    right: 0;
    margin-left: 0;
  }

  .pagination {
    flex-wrap: wrap;
  }
}
</style>
