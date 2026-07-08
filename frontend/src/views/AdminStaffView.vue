<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { listBranches } from "../api/branches";
import { createStaff, deleteStaff, listStaff, updateStaff } from "../api/staff";
import { ApiError } from "../api/client";
import CustomSelect from "../components/CustomSelect.vue";
import ConfirmDeleteModal from "../components/ConfirmDeleteModal.vue";
import ConfirmModal from "../components/ConfirmModal.vue";
import Modal from "../components/Modal.vue";
import Icon from "../components/Icon.vue";
import LoadingState from "../components/LoadingState.vue";


const staff = ref([]);
const branches = ref([]);
const loading = ref(true);
const submitting = ref(false);
const error = ref("");
const showAddModal = ref(false);

const togglingId = ref(null);
const deletingId = ref(null);
const rowError = ref("");
const deleteTarget = ref(null);
const deleteModalError = ref("");
const deleting = ref(false);

const toggleTarget = ref(null);
const toggleModalError = ref("");
const toggling = ref(false);

const form = ref({ name: "", email: "", password: "", branchId: "", role: "staff" });
const showPassword = ref(false);

const roleOptions = [
  { value: "staff", label: "Staff", hint: "Daily stock, closing counts, and sales" },
  { value: "delivery", label: "Delivery", hint: "Logs incoming stock deliveries" },
];

const rolesTarget = ref(null);
const roleDraft = ref("staff");
const branchDraft = ref("");
const rolesModalError = ref("");
const savingRoles = ref(false);

function roleLabel(value) {
  return roleOptions.find((r) => r.value === value)?.label || value;
}

function openRolesModal(member) {
  rolesModalError.value = "";
  roleDraft.value = member.roles?.[0] || "staff";
  branchDraft.value = member.branch_id || "";
  rolesTarget.value = member;
}

function cancelRolesModal() {
  rolesTarget.value = null;
}

async function saveRoles() {
  rolesModalError.value = "";
  if (roleDraft.value === "staff" && !branchDraft.value) {
    rolesModalError.value = "Select a branch for the Staff role.";
    return;
  }
  savingRoles.value = true;
  try {
    const payload = { roles: [roleDraft.value] };
    if (roleDraft.value === "staff") payload.branch_id = branchDraft.value;
    await updateStaff(rolesTarget.value.id, payload);
    rolesTarget.value = null;
    await refresh();
  } catch (e) {
    rolesModalError.value = e instanceof ApiError ? e.detail || "Could not update roles" : "Could not update roles";
  } finally {
    savingRoles.value = false;
  }
}

const search = ref("");
const branchFilter = ref("");
const statusFilter = ref("");

const statusOptions = [
  { label: "All statuses", value: "" },
  { label: "Active", value: "active" },
  { label: "Inactive", value: "inactive" },
];

const pageSize = 10;
const currentPage = ref(1);

const activeCount = computed(() => staff.value.filter((s) => s.is_active).length);
const inactiveCount = computed(() => staff.value.length - activeCount.value);

const hasActiveFilters = computed(() => !!(search.value.trim() || branchFilter.value || statusFilter.value));

function clearFilters() {
  search.value = "";
  branchFilter.value = "";
  statusFilter.value = "";
}

const filteredStaff = computed(() => {
  const term = search.value.trim().toLowerCase();
  return staff.value.filter((s) => {
    if (term && !s.name.toLowerCase().includes(term) && !s.email.toLowerCase().includes(term)) return false;
    if (branchFilter.value && s.branch_id !== branchFilter.value) return false;
    if (statusFilter.value === "active" && !s.is_active) return false;
    if (statusFilter.value === "inactive" && s.is_active) return false;
    return true;
  });
});

const totalPages = computed(() => Math.max(1, Math.ceil(filteredStaff.value.length / pageSize)));

const pagedStaff = computed(() => {
  const start = (currentPage.value - 1) * pageSize;
  return filteredStaff.value.slice(start, start + pageSize);
});

watch(totalPages, (total) => {
  if (currentPage.value > total) currentPage.value = total;
});

watch([search, branchFilter, statusFilter], () => {
  currentPage.value = 1;
});

function goToPage(page) {
  currentPage.value = Math.min(Math.max(page, 1), totalPages.value);
}

const branchOptions = computed(() => branches.value.map((b) => ({ label: b.name, value: b.id })));
const branchFilterOptions = computed(() => [{ label: "All branches", value: "" }, ...branchOptions.value]);

function branchName(id) {
  if (!id) return "All branches";
  return branches.value.find((b) => b.id === id)?.name || "—";
}

function initials(name) {
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0].toUpperCase())
    .join("");
}

async function refresh() {
  loading.value = true;
  [staff.value, branches.value] = await Promise.all([listStaff(), listBranches()]);
  loading.value = false;
}

function openAddModal() {
  form.value = { name: "", email: "", password: "", branchId: "", role: "staff" };
  error.value = "";
  showAddModal.value = true;
}

function closeAddModal() {
  showAddModal.value = false;
}

async function onSubmit() {
  error.value = "";
  if (form.value.role === "staff" && !form.value.branchId) {
    error.value = "Select a branch for the Staff role.";
    return;
  }
  submitting.value = true;
  try {
    await createStaff({ ...form.value, roles: [form.value.role] });
    form.value = { name: "", email: "", password: "", branchId: "", role: "staff" };
    showAddModal.value = false;
    await refresh();
  } catch (e) {
    error.value = e instanceof ApiError ? e.detail || "Could not create staff" : "Could not create staff";
  } finally {
    submitting.value = false;
  }
}

function onToggleActive(member) {
  rowError.value = "";
  toggleModalError.value = "";
  toggleTarget.value = member;
}

function cancelToggle() {
  toggleTarget.value = null;
}

async function confirmToggle() {
  const member = toggleTarget.value;
  toggleModalError.value = "";
  toggling.value = true;
  togglingId.value = member.id;
  try {
    await updateStaff(member.id, { is_active: !member.is_active });
    toggleTarget.value = null;
    await refresh();
  } catch (e) {
    toggleModalError.value = e instanceof ApiError ? e.detail || "Could not update staff" : "Could not update staff";
  } finally {
    toggling.value = false;
    togglingId.value = null;
  }
}

function onDelete(member) {
  rowError.value = "";
  deleteModalError.value = "";
  deleteTarget.value = member;
}

function cancelDelete() {
  deleteTarget.value = null;
}

async function confirmDelete(password) {
  const member = deleteTarget.value;
  deleteModalError.value = "";
  deleting.value = true;
  deletingId.value = member.id;
  try {
    await deleteStaff(member.id, password);
    deleteTarget.value = null;
    await refresh();
  } catch (e) {
    deleteModalError.value = e instanceof ApiError ? e.detail || "Could not delete staff" : "Could not delete staff";
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
        <h1>Staff</h1>
        <p class="page-subtitle">Staff accounts, scoped to a single branch each.</p>
      </div>
      <div class="header-actions">
        <span class="count-chip"><Icon name="count" :size="14" /> {{ staff.length }} {{ staff.length === 1 ? "member" : "members" }}</span>
        <button type="button" class="btn-icon" @click="openAddModal"><Icon name="plus" :size="16" /> Add staff</button>
      </div>
    </div>

    <div class="card stats-bar">
      <div class="stat-item">
        <span class="stat-value">{{ staff.length }}</span>
        <span class="stat-label">Total staff</span>
      </div>
      <div class="stat-item">
        <span class="stat-value stat-active">{{ activeCount }}</span>
        <span class="stat-label">Active</span>
      </div>
      <div class="stat-item">
        <span class="stat-value" :class="{ 'stat-danger': inactiveCount > 0 }">{{ inactiveCount }}</span>
        <span class="stat-label">Inactive</span>
      </div>
      <div class="stat-item">
        <span class="stat-value">{{ branches.length }}</span>
        <span class="stat-label">Branches covered</span>
      </div>
    </div>

    <Modal v-if="showAddModal" title="Add a staff member" wide @close="closeAddModal">
      <form @submit.prevent="onSubmit">
        <div class="new-staff-grid">
          <div class="field">
            <label for="staff-name">Name</label>
            <input id="staff-name" v-model="form.name" required placeholder="Jane Dela Cruz" autofocus />
          </div>
          <div class="field">
            <label for="staff-email">Email</label>
            <input id="staff-email" v-model="form.email" type="email" required placeholder="jane@za-company.com" />
          </div>
          <div class="field">
            <label for="staff-password">Password</label>
            <div class="inpw">
              <input
                id="staff-password"
                v-model="form.password"
                :type="showPassword ? 'text' : 'password'"
                required
                minlength="8"
                placeholder="At least 8 characters"
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
          <div v-if="form.role === 'staff'" class="field">
            <label for="staff-branch">Branch</label>
            <CustomSelect id="staff-branch" v-model="form.branchId" :options="branchOptions" placeholder="Select a branch" />
          </div>
        </div>
        <div class="field roles-field">
          <label>Role</label>
          <div class="role-checkboxes">
            <label v-for="opt in roleOptions" :key="opt.value" class="role-checkbox">
              <input type="radio" name="staff-role" :value="opt.value" v-model="form.role" />
              <span class="role-checkbox-text">
                <span class="role-checkbox-label">{{ opt.label }}</span>
                <span class="role-checkbox-hint">{{ opt.hint }}</span>
              </span>
            </label>
          </div>
          <p v-if="form.role === 'delivery'" class="roles-note">Delivery staff can log deliveries for any branch — no branch is assigned.</p>
        </div>
        <p v-if="error" class="error-message">{{ error }}</p>
        <div class="modal-actions">
          <button type="button" class="secondary cancel" :disabled="submitting" @click="closeAddModal">Cancel</button>
          <button type="submit" :disabled="submitting">{{ submitting ? "Adding..." : "Add staff" }}</button>
        </div>
      </form>
    </Modal>

    <div class="card filters-card">
      <div class="filters-head">
        <span class="filters-title"><Icon name="filter" :size="14" /> Filters</span>
        <button v-if="hasActiveFilters" type="button" class="clear-filters" @click="clearFilters">
          <Icon name="x" :size="12" /> Clear filters
        </button>
      </div>
      <div class="filters-grid">
        <div class="field search-field">
          <label for="staff-search">Search</label>
          <div class="search-input">
            <Icon name="search" :size="15" class="search-icon" />
            <input id="staff-search" v-model="search" placeholder="Search by name or email" />
            <button v-if="search" type="button" class="search-clear" aria-label="Clear search" @click="search = ''">
              <Icon name="x" :size="13" />
            </button>
          </div>
        </div>
        <div class="field">
          <label for="staff-branch-filter">Branch</label>
          <CustomSelect id="staff-branch-filter" v-model="branchFilter" :options="branchFilterOptions" placeholder="All branches" />
        </div>
        <div class="field">
          <label for="staff-status-filter">Status</label>
          <CustomSelect id="staff-status-filter" v-model="statusFilter" :options="statusOptions" placeholder="All statuses" />
        </div>
      </div>
    </div>

    <Modal v-if="rolesTarget" :title="`Edit roles for &quot;${rolesTarget.name}&quot;`" @close="cancelRolesModal">
      <div class="role-checkboxes">
        <label v-for="opt in roleOptions" :key="opt.value" class="role-checkbox">
          <input type="radio" name="edit-staff-role" :value="opt.value" v-model="roleDraft" />
          <span class="role-checkbox-text">
            <span class="role-checkbox-label">{{ opt.label }}</span>
            <span class="role-checkbox-hint">{{ opt.hint }}</span>
          </span>
        </label>
      </div>
      <div v-if="roleDraft === 'staff'" class="field roles-branch-field">
        <label for="roles-branch">Branch</label>
        <CustomSelect id="roles-branch" v-model="branchDraft" :options="branchOptions" placeholder="Select a branch" />
      </div>
      <p v-else class="roles-note">Delivery staff can log deliveries for any branch — no branch is assigned.</p>
      <p v-if="rolesModalError" class="error-message">{{ rolesModalError }}</p>
      <div class="modal-actions">
        <button type="button" class="secondary cancel" :disabled="savingRoles" @click="cancelRolesModal">Cancel</button>
        <button type="button" :disabled="savingRoles" @click="saveRoles">{{ savingRoles ? "Saving..." : "Save roles" }}</button>
      </div>
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

    <ConfirmModal
      :open="!!toggleTarget"
      :title="toggleTarget?.is_active ? `Deactivate &quot;${toggleTarget?.name}&quot;?` : `Activate &quot;${toggleTarget?.name}&quot;?`"
      :message="
        toggleTarget?.is_active
          ? 'They will lose access to their account until reactivated.'
          : 'They will regain access to their account.'
      "
      :confirm-label="toggleTarget?.is_active ? 'Deactivate' : 'Activate'"
      loading-label="Saving..."
      :variant="toggleTarget?.is_active ? 'danger' : 'primary'"
      :loading="toggling"
      :error="toggleModalError"
      @confirm="confirmToggle"
      @cancel="cancelToggle"
    />

    <p v-if="rowError" class="error-message top-error">{{ rowError }}</p>

    <LoadingState v-if="loading" label="Loading staff..." />
    <div v-else-if="!filteredStaff.length" class="card state-card">
      <div class="empty-state">
        <template v-if="staff.length">
          <p>No staff match your filters.</p>
          <p class="empty-hint">Try clearing the search or filters above.</p>
        </template>
        <template v-else>
          <p>No staff yet.</p>
          <p class="empty-hint">Add a branch first, then create staff accounts for it above.</p>
        </template>
      </div>
    </div>

    <template v-else>
      <div class="staff-grid">
        <div v-for="s in pagedStaff" :key="s.id" class="staff-card">
          <div class="staff-card-top">
            <span class="avatar">{{ initials(s.name) }}</span>
            <span class="badge" :class="s.is_active ? 'active' : 'inactive'">
              {{ s.is_active ? "Active" : "Inactive" }}
            </span>
          </div>
          <div class="staff-card-body">
            <div class="staff-card-name">{{ s.name }}</div>
            <div class="staff-card-email">{{ s.email }}</div>
            <div class="staff-card-branch">
              <span class="branch-dot"></span>
              {{ branchName(s.branch_id) }}
            </div>
            <div class="staff-card-roles">
              <span v-for="r in s.roles" :key="r" class="role-chip">{{ roleLabel(r) }}</span>
              <button type="button" class="edit-roles-btn" aria-label="Edit role" @click="openRolesModal(s)">
                <Icon name="edit" :size="12" /> Edit role
              </button>
            </div>
          </div>
          <div class="staff-card-actions">
            <button
              class="secondary"
              :class="s.is_active ? 'toggle-off' : 'toggle-on'"
              :disabled="togglingId === s.id"
              @click="onToggleActive(s)"
            >
              {{ togglingId === s.id ? "Saving..." : s.is_active ? "Deactivate" : "Activate" }}
            </button>
            <button
              v-if="!s.is_active"
              class="secondary danger btn-icon"
              :disabled="deletingId === s.id"
              @click="onDelete(s)"
            >
              <Icon name="trash" :size="14" /> {{ deletingId === s.id ? "Deleting..." : "Delete" }}
            </button>
          </div>
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
    </template>
  </div>
</template>

<style scoped>
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

.stats-bar {
  display: flex;
  align-items: stretch;
  flex-wrap: wrap;
  gap: 1rem 0;
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  flex: 1 1 140px;
  padding: 0 1.25rem;
  border-left: 1px solid var(--color-border);
}

.stat-item:first-child {
  border-left: none;
  padding-left: 0;
}

.stat-label {
  font-size: 0.75rem;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.stat-value {
  font-family: "SFMono-Regular", Consolas, monospace;
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-text);
}

.stat-active {
  color: var(--color-success);
}

.stat-danger {
  color: var(--color-danger);
}

.card {
  margin-bottom: 1.5rem;
}

.cancel {
  border-color: #fff;
}

.card-title {
  font-size: 1.05rem;
  margin-bottom: 1rem;
}

.new-staff-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
  margin-bottom: 0.25rem;
}

@media (max-width: 480px) {
  .new-staff-grid {
    grid-template-columns: 1fr;
  }
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.6rem;
  margin-top: 0.25rem;
}

.roles-field {
  margin-bottom: 1rem;
}

.role-checkboxes {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.role-checkbox {
  display: flex;
  align-items: flex-start;
  gap: 0.6rem;
  padding: 0.6rem 0.75rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  cursor: pointer;
}

.role-checkbox input {
  margin-top: 0.2rem;
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

.role-checkbox-text {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
}

.roles-branch-field {
  margin-top: 0.75rem;
}

.roles-note {
  margin-top: 0.75rem;
  font-size: 0.82rem;
  color: var(--color-text-muted);
}

.role-checkbox-label {
  font-weight: 600;
  color: var(--color-text);
}

.role-checkbox-hint {
  font-size: 0.8rem;
  color: var(--color-text-muted);
}

.staff-card-roles {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin-top: 0.6rem;
}

.role-chip {
  background: var(--color-bg);
  color: var(--color-text-muted);
  font-size: 0.72rem;
  font-weight: 600;
  padding: 0.2rem 0.55rem;
  border-radius: 999px;
  border: 1px solid var(--color-border);
}

.edit-roles-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.2rem 0.6rem;
  margin-left: auto;
  border-radius: 999px;
  background: var(--color-bg);
  border: 1px solid #fff;
  color: var(--color-text-muted);
  font-size: 0.72rem;
  font-weight: 600;
}

.edit-roles-btn:hover {
  background: var(--color-primary-soft);
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.filters-card {
  padding: 1.1rem 1.25rem 1.25rem;
}

.filters-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  margin-bottom: 0.9rem;
}

.filters-title {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.78rem;
  font-weight: 700;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.clear-filters {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  background: none;
  border: none;
  padding: 0;
  color: var(--color-primary);
  font-size: 0.82rem;
  font-weight: 600;
}

.clear-filters:hover {
  color: var(--color-primary-hover);
  background: none;
}

.filters-grid {
  display: grid;
  grid-template-columns: minmax(220px, 2fr) 1fr 1fr;
  gap: 1rem;
  align-items: end;
}

.filters-grid .field {
  margin-bottom: 0;
}

.search-input {
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 0.65rem;
  color: var(--color-text-muted);
  pointer-events: none;
}

.search-input input {
  width: 100%;
  padding-left: 2.1rem;
  padding-right: 2.1rem;
}

.search-clear {
  position: absolute;
  right: 0.35rem;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  padding: 0;
  background: transparent;
  color: var(--color-text-muted);
  border-radius: 50%;
}

.search-clear:hover {
  background: var(--color-primary-soft);
  color: var(--color-primary);
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

.staff-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.staff-card {
  display: flex;
  flex-direction: column;
  gap: 0.9rem;
  background: var(--color-surface);
  border-radius: var(--radius);
  border-top: 3px solid var(--color-primary);
  border-image: var(--gradient-primary) 1;
  box-shadow: var(--shadow);
  padding: 1.25rem;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.staff-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-hover);
}

.staff-card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.avatar {
  flex-shrink: 0;
  width: 42px;
  height: 42px;
  border-radius: 50%;
  background: var(--gradient-primary);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.9rem;
  font-weight: 700;
}

.staff-card-body {
  min-width: 0;
}

.staff-card-name {
  font-weight: 600;
  font-size: 1.05rem;
  color: var(--color-text);
  word-break: break-word;
}

.staff-card-email {
  font-size: 0.85rem;
  color: var(--color-text-muted);
  margin-top: 0.15rem;
  word-break: break-word;
}

.staff-card-branch {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.85rem;
  color: var(--color-text);
  margin-top: 0.6rem;
}

.branch-dot {
  flex-shrink: 0;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-primary);
}

.staff-card-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: auto;
}

.staff-card-actions button {
  flex: 1;
  font-size: 0.85rem;
  padding: 0.45rem 0.6rem;
}

.staff-card-actions .danger {
  color: var(--color-danger);
  border-color: var(--color-danger);
}

.staff-card-actions .danger:hover {
  background: rgba(255, 77, 77, 0.1);
}

.toggle-on {
  color: var(--color-success);
  border-color: var(--color-success);
}

.toggle-on:hover {
  background: rgba(46, 204, 143, 0.12);
}

.toggle-off {
  color: #ffb020;
  border-color: #ffb020;
}

.toggle-off:hover {
  background: rgba(255, 176, 32, 0.12);
}

.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
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

@media (max-width: 900px) {
  .filters-grid {
    grid-template-columns: 1fr 1fr;
  }

  .search-field {
    grid-column: 1 / -1;
  }
}

@media (max-width: 640px) {
  .new-staff-grid {
    grid-template-columns: 1fr;
  }

  .filters-grid {
    grid-template-columns: 1fr;
  }

  .filters-head {
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .stat-item {
    flex-basis: calc(50% - 0.6rem);
  }

  .stat-item:nth-child(2) {
    border-left: none;
  }
}

@media (max-width: 480px) {
  .page-header {
    flex-direction: column;
    align-items: stretch;
  }

  .header-actions {
    justify-content: space-between;
  }

  .staff-grid {
    grid-template-columns: 1fr;
  }

  .stat-item {
    flex-basis: 100%;
    border-left: none;
    padding-left: 0;
  }
}
</style>
