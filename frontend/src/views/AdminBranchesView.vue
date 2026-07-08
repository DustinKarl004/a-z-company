<script setup>
import { onMounted, ref } from "vue";
import { createBranch, deleteBranch, listBranches, updateBranch } from "../api/branches";
import { ApiError } from "../api/client";
import Modal from "../components/Modal.vue";
import ConfirmDeleteModal from "../components/ConfirmDeleteModal.vue";
import Icon from "../components/Icon.vue";
import LoadingState from "../components/LoadingState.vue";

const branches = ref([]);
const name = ref("");
const error = ref("");
const submitting = ref(false);
const loading = ref(true);
const showAddModal = ref(false);

const editingId = ref(null);
const editName = ref("");
const editError = ref("");
const savingEdit = ref(false);

const deletingId = ref(null);
const deleteError = ref("");
const deleteTarget = ref(null);
const deleteModalError = ref("");
const deleting = ref(false);

async function refresh() {
  loading.value = true;
  branches.value = await listBranches();
  loading.value = false;
}

function openAddModal() {
  name.value = "";
  error.value = "";
  showAddModal.value = true;
}

function closeAddModal() {
  showAddModal.value = false;
}

async function onSubmit() {
  error.value = "";
  submitting.value = true;
  try {
    await createBranch(name.value);
    name.value = "";
    showAddModal.value = false;
    await refresh();
  } catch (e) {
    error.value = e instanceof ApiError ? e.detail || "Could not create branch" : "Could not create branch";
  } finally {
    submitting.value = false;
  }
}

function initials(branchName) {
  return branchName
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0].toUpperCase())
    .join("");
}

function startEdit(branch) {
  deleteError.value = "";
  editingId.value = branch.id;
  editName.value = branch.name;
  editError.value = "";
}

function cancelEdit() {
  editingId.value = null;
  editError.value = "";
}

async function saveEdit(branch) {
  editError.value = "";
  savingEdit.value = true;
  try {
    await updateBranch(branch.id, editName.value);
    editingId.value = null;
    await refresh();
  } catch (e) {
    editError.value = e instanceof ApiError ? e.detail || "Could not rename branch" : "Could not rename branch";
  } finally {
    savingEdit.value = false;
  }
}

function onDelete(branch) {
  deleteError.value = "";
  deleteModalError.value = "";
  deleteTarget.value = branch;
}

function cancelDelete() {
  deleteTarget.value = null;
}

async function confirmDelete(password) {
  const branch = deleteTarget.value;
  deleteModalError.value = "";
  deleting.value = true;
  deletingId.value = branch.id;
  try {
    await deleteBranch(branch.id, password);
    deleteTarget.value = null;
    await refresh();
  } catch (e) {
    deleteModalError.value =
      e instanceof ApiError ? e.detail || "Could not delete branch" : "Could not delete branch";
  } finally {
    deleting.value = false;
    deletingId.value = null;
  }
}

onMounted(refresh);
</script>

<template>
  <div>
    <div class="page-header">
      <div>
        <h1>Branches</h1>
        <p class="page-subtitle">Every branch that can have its own staff and daily records.</p>
      </div>
      <div class="header-actions">
        <span class="count-chip"><Icon name="count" :size="14" /> {{ branches.length }} {{ branches.length === 1 ? "branch" : "branches" }}</span>
        <button type="button" class="btn-icon" @click="openAddModal"><Icon name="plus" :size="16" /> Add branch</button>
      </div>
    </div>

    <Modal v-if="showAddModal" title="Add a branch" @close="closeAddModal">
      <form @submit.prevent="onSubmit">
        <div class="field">
          <label for="branch-name">Branch name</label>
          <input id="branch-name" v-model="name" required placeholder="e.g. Quezon City" autofocus />
        </div>
        <p v-if="error" class="error-message">{{ error }}</p>
        <div class="modal-actions">
          <button type="button" class="secondary cancel" :disabled="submitting" @click="closeAddModal">Cancel</button>
          <button type="submit" :disabled="submitting">{{ submitting ? "Adding..." : "Add branch" }}</button>
        </div>
      </form>
    </Modal>

    <ConfirmDeleteModal
      :open="!!deleteTarget"
      :title="`Delete &quot;${deleteTarget?.name}&quot;?`"
      message="This cannot be undone."
      :loading="deleting"
      :error="deleteModalError"
      @confirm="confirmDelete"
      @cancel="cancelDelete"
    />

    <p v-if="deleteError" class="error-message top-error">{{ deleteError }}</p>

    <div v-if="loading" class="card state-card">
      <LoadingState label="Loading branches..." />
    </div>

    <div v-else-if="!branches.length" class="card state-card">
      <div class="empty-state">
        <p>No branches yet.</p>
        <p class="empty-hint">Add your first branch above to start assigning staff to it.</p>
      </div>
    </div>

    <div v-else class="branch-grid">
      <div v-for="b in branches" :key="b.id" class="branch-card">
        <template v-if="editingId === b.id">
          <div class="branch-card-icon">{{ initials(editName || b.name) }}</div>
          <div class="edit-field">
            <input v-model="editName" required placeholder="Branch name" @keyup.enter="saveEdit(b)" @keyup.escape="cancelEdit" />
            <p v-if="editError" class="error-message">{{ editError }}</p>
          </div>
          <div class="branch-card-actions">
            <button class="secondary cancel" :disabled="savingEdit" @click="cancelEdit">Cancel</button>
            <button :disabled="savingEdit || !editName.trim()" @click="saveEdit(b)">
              {{ savingEdit ? "Saving..." : "Save" }}
            </button>
          </div>
        </template>
        <template v-else>
          <div class="branch-card-icon">{{ initials(b.name) }}</div>
          <div class="branch-card-body">
            <div class="branch-card-name">{{ b.name }}</div>
            <div class="branch-card-meta">Added {{ new Date(b.created_at).toLocaleDateString() }}</div>
          </div>
          <div class="branch-card-actions">
            <button class="secondary edit btn-icon" @click="startEdit(b)"><Icon name="edit" :size="14" /> Edit</button>
            <button
              class="secondary danger btn-icon"
              :disabled="deletingId === b.id"
              @click="onDelete(b)"
            >
              <Icon name="trash" :size="14" /> {{ deletingId === b.id ? "Deleting..." : "Delete" }}
            </button>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
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

.header-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-shrink: 0;
}

.count-chip {
  flex-shrink: 0;
  background: var(--color-primary-soft);
  color: var(--color-primary);
  font-size: 0.85rem;
  font-weight: 600;
  padding: 0.35rem 0.85rem;
  border-radius: 999px;
  white-space: nowrap;
}

.card {
  margin-bottom: 1.5rem;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.6rem;
  margin-top: 0.25rem;
}

.top-error {
  margin: -0.75rem 0 1.25rem;
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
  margin-top: 0.35rem;
}

.branch-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 0.85rem;
}

.branch-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 0.85rem;
  background: var(--color-surface);
  border-radius: var(--radius);
  border-top: 3px solid var(--color-primary);
  border-image: var(--gradient-primary) 1;
  box-shadow: var(--shadow);
  padding: 1.5rem 1.25rem;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.branch-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-hover);
}

.branch-card-icon {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background: var(--gradient-primary);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.1rem;
  font-weight: 700;
  flex-shrink: 0;
}

.branch-card-body {
  min-width: 0;
}

.branch-card-name {
  font-weight: 600;
  font-size: 1.05rem;
  color: var(--color-text);
  word-break: break-word;
}

.branch-card-meta {
  font-size: 0.8rem;
  color: var(--color-text-muted);
  margin-top: 0.2rem;
}

.branch-card-actions {
  display: flex;
  gap: 0.5rem;
  width: 100%;
}

.branch-card-actions button {
  flex: 1;
  font-size: 0.85rem;
  padding: 0.45rem 0.6rem;
}

.branch-card-actions .edit {
  border-color: #fff;
}

.cancel {
  border-color: #fff;
}

.branch-card-actions .danger {
  color: var(--color-danger);
  border-color: var(--color-danger);
}

.branch-card-actions .danger:hover {
  background: rgba(255, 77, 77, 0.1);
}

.edit-field {
  width: 100%;
}

.edit-field input {
  width: 100%;
  text-align: center;
}

.edit-field .error-message {
  text-align: center;
}

@media (max-width: 560px) {
  .page-header {
    flex-direction: column;
    align-items: stretch;
  }

  .header-actions {
    justify-content: space-between;
  }

  .branch-grid {
    grid-template-columns: 1fr 1fr;
    gap: 0.6rem;
  }

  .branch-card {
    padding: 1.1rem 0.85rem;
    gap: 0.6rem;
  }

  .branch-card-actions {
    flex-direction: column;
  }
}

@media (max-width: 360px) {
  .branch-grid {
    grid-template-columns: 1fr;
  }
}
</style>
