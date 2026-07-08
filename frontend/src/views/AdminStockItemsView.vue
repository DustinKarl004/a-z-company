<script setup>
import { computed, onMounted, ref, watch } from "vue";
import {
  createStockItem,
  deleteStockItem,
  listStockItems,
  updateStockItem,
} from "../api/stockItems";
import { ApiError } from "../api/client";
import ConfirmDeleteModal from "../components/ConfirmDeleteModal.vue";
import CustomSelect from "../components/CustomSelect.vue";
import Modal from "../components/Modal.vue";
import Icon from "../components/Icon.vue";
import LoadingState from "../components/LoadingState.vue";

const unitOptions = ref(["kg", "g", "L", "mL", "pcs", "servings", "pack", "box", "sack", "bottle"]);
const categoryOptions = ref([
  "Meats",
  "Side Dishes / Banchan",
  "Rice & Staples",
  "Sauces & Condiments",
  "Drinks",
  "Consumables/Supplies",
]);

const items = ref([]);
const form = ref({ name: "", unit: "", price: "", category: "" });
const error = ref("");
const submitting = ref(false);
const loading = ref(true);
const showAddModal = ref(false);
const editingId = ref(null);
const editingName = ref("");
const editingUnit = ref("");
const editingPrice = ref("");
const editingCategory = ref("");
const editError = ref("");
const savingEdit = ref(false);
const deletingId = ref(null);
const deleteError = ref("");
const deleteTarget = ref(null);
const deleteModalError = ref("");
const deleting = ref(false);

const addingUnit = ref(false);
const newUnit = ref("");
const addingCategory = ref(false);
const newCategory = ref("");

const search = ref("");
const unitFilter = ref("");
const categoryFilter = ref("");

const selectionMode = ref(false);
const selectedIds = ref(new Set());
const showDeleteSelectedModal = ref(false);
const deleteSelectedError = ref("");
const deletingSelected = ref(false);

const pageSize = 12;
const currentPage = ref(1);

const hasActiveFilters = computed(() => !!(search.value.trim() || unitFilter.value || categoryFilter.value));

function clearFilters() {
  search.value = "";
  unitFilter.value = "";
  categoryFilter.value = "";
}

function categoryRank(category) {
  if (!category) return categoryOptions.value.length;
  const index = categoryOptions.value.findIndex((c) => c.toLowerCase() === category.toLowerCase());
  return index === -1 ? categoryOptions.value.length : index;
}

const filteredItems = computed(() => {
  const term = search.value.trim().toLowerCase();
  return items.value
    .filter((i) => {
      if (term && !i.name.toLowerCase().includes(term)) return false;
      if (unitFilter.value && i.unit !== unitFilter.value) return false;
      if (categoryFilter.value && i.category !== categoryFilter.value) return false;
      return true;
    })
    .slice()
    .sort((a, b) => {
      const rankDiff = categoryRank(a.category) - categoryRank(b.category);
      if (rankDiff !== 0) return rankDiff;
      return a.name.localeCompare(b.name);
    });
});

const totalPages = computed(() => Math.max(1, Math.ceil(filteredItems.value.length / pageSize)));

const pagedItems = computed(() => {
  const start = (currentPage.value - 1) * pageSize;
  return filteredItems.value.slice(start, start + pageSize);
});

watch(totalPages, (total) => {
  if (currentPage.value > total) currentPage.value = total;
});

watch([search, unitFilter, categoryFilter], () => {
  currentPage.value = 1;
});

function goToPage(page) {
  currentPage.value = Math.min(Math.max(page, 1), totalPages.value);
}

const unitFilterOptions = computed(() => [
  { label: "All units", value: "" },
  ...unitOptions.value.map((u) => ({ label: u, value: u })),
]);

const categoryFilterOptions = computed(() => [
  { label: "All categories", value: "" },
  ...categoryOptions.value.map((c) => ({ label: c, value: c })),
]);

function startAddUnit() {
  addingUnit.value = true;
  newUnit.value = "";
}

function cancelAddUnit() {
  addingUnit.value = false;
  newUnit.value = "";
}

function confirmAddUnit(setUnit) {
  const value = newUnit.value.trim();
  console.log("[stock-items] confirmAddUnit called with:", value);
  if (!value) {
    console.log("[stock-items] confirmAddUnit: empty value, cancelling");
    cancelAddUnit();
    return;
  }
  const existing = unitOptions.value.find((u) => u.toLowerCase() === value.toLowerCase());
  if (!existing) unitOptions.value.push(value);
  console.log("[stock-items] unitOptions after add:", [...unitOptions.value]);
  setUnit(existing || value);
  cancelAddUnit();
}

function startAddCategory() {
  addingCategory.value = true;
  newCategory.value = "";
}

function cancelAddCategory() {
  addingCategory.value = false;
  newCategory.value = "";
}

function confirmAddCategory(setCategory) {
  const value = newCategory.value.trim();
  if (!value) {
    cancelAddCategory();
    return;
  }
  const existing = categoryOptions.value.find((c) => c.toLowerCase() === value.toLowerCase());
  if (!existing) categoryOptions.value.push(value);
  setCategory(existing || value);
  cancelAddCategory();
}

async function refresh() {
  loading.value = true;
  console.log("[stock-items] refresh: fetching items...");
  items.value = await listStockItems();
  console.log("[stock-items] refresh: fetched items:", JSON.parse(JSON.stringify(items.value)));
  items.value.forEach((i) => {
    if (i.unit && !unitOptions.value.some((u) => u.toLowerCase() === i.unit.toLowerCase())) {
      unitOptions.value.push(i.unit);
    }
    if (i.category && !categoryOptions.value.some((c) => c.toLowerCase() === i.category.toLowerCase())) {
      categoryOptions.value.push(i.category);
    }
  });
  console.log("[stock-items] refresh: unitOptions after merge:", [...unitOptions.value]);
  loading.value = false;
}

function openAddModal() {
  form.value = { name: "", unit: "", price: "", category: "" };
  error.value = "";
  cancelAddUnit();
  cancelAddCategory();
  showAddModal.value = true;
}

function closeAddModal() {
  showAddModal.value = false;
  cancelAddUnit();
  cancelAddCategory();
}

async function onSubmit() {
  console.log("[stock-items] onSubmit fired with form:", { ...form.value });
  error.value = "";
  submitting.value = true;
  try {
    const created = await createStockItem({
      ...form.value,
      price: Number(form.value.price),
      category: form.value.category || null,
    });
    console.log("[stock-items] createStockItem response:", created);
    form.value = { name: "", unit: "", price: "", category: "" };
    showAddModal.value = false;
    await refresh();
  } catch (e) {
    console.error("[stock-items] createStockItem failed:", e);
    error.value = e instanceof ApiError ? e.detail || "Could not create item" : "Could not create item";
  } finally {
    submitting.value = false;
  }
}

function startEdit(item) {
  deleteError.value = "";
  editingId.value = item.id;
  editingName.value = item.name;
  editingUnit.value = item.unit;
  editingPrice.value = item.price;
  editingCategory.value = item.category || "";
  editError.value = "";
  cancelAddUnit();
  cancelAddCategory();
}

function cancelEdit() {
  editingId.value = null;
  editError.value = "";
  cancelAddUnit();
  cancelAddCategory();
}

async function saveEdit() {
  console.log("[stock-items] saveEdit fired with:", {
    id: editingId.value,
    name: editingName.value,
    unit: editingUnit.value,
    price: editingPrice.value,
    category: editingCategory.value,
  });
  editError.value = "";
  savingEdit.value = true;
  try {
    const updated = await updateStockItem(editingId.value, {
      name: editingName.value,
      unit: editingUnit.value,
      price: Number(editingPrice.value),
      category: editingCategory.value || null,
    });
    console.log("[stock-items] updateStockItem response:", updated);
    editingId.value = null;
    await refresh();
  } catch (e) {
    console.error("[stock-items] updateStockItem failed:", e);
    editError.value = e instanceof ApiError ? e.detail || "Could not update item" : "Could not update item";
  } finally {
    savingEdit.value = false;
  }
}

function onDelete(item) {
  deleteError.value = "";
  deleteModalError.value = "";
  deleteTarget.value = item;
}

function cancelDelete() {
  deleteTarget.value = null;
}

async function confirmDelete(password) {
  const item = deleteTarget.value;
  deleteModalError.value = "";
  deleting.value = true;
  deletingId.value = item.id;
  try {
    await deleteStockItem(item.id, password);
    deleteTarget.value = null;
    await refresh();
  } catch (e) {
    deleteModalError.value = e instanceof ApiError ? e.detail || "Could not delete item" : "Could not delete item";
  } finally {
    deleting.value = false;
    deletingId.value = null;
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

function selectAllVisible() {
  selectedIds.value = new Set(filteredItems.value.map((i) => i.id));
}

function clearSelection() {
  selectedIds.value = new Set();
}

function openDeleteSelectedModal() {
  deleteSelectedError.value = "";
  showDeleteSelectedModal.value = true;
}

function cancelDeleteSelected() {
  showDeleteSelectedModal.value = false;
}

async function confirmDeleteSelected(password) {
  deleteSelectedError.value = "";
  deletingSelected.value = true;
  try {
    for (const id of selectedIds.value) {
      await deleteStockItem(id, password);
    }
    showDeleteSelectedModal.value = false;
    selectionMode.value = false;
    selectedIds.value = new Set();
    await refresh();
  } catch (e) {
    deleteSelectedError.value =
      e instanceof ApiError ? e.detail || "Could not delete selected items" : "Could not delete selected items";
  } finally {
    deletingSelected.value = false;
  }
}

onMounted(refresh);
</script>

<template>
  <div>
    <div class="page-header">
      <div>
        <h1>Stock Items</h1>
        <p class="page-subtitle">The catalog of items staff can log deliveries, counts, and sales against.</p>
      </div>
      <div class="header-actions">
        <span class="count-chip"><Icon name="count" :size="14" /> {{ items.length }} {{ items.length === 1 ? "item" : "items" }}</span>
        <button
          v-if="items.length"
          type="button"
          class="secondary btn-icon"
          :class="{ active: selectionMode }"
          @click="toggleSelectionMode"
        >
          <Icon name="check" :size="16" /> {{ selectionMode ? "Cancel select" : "Select" }}
        </button>
        <button type="button" class="btn-icon" @click="openAddModal"><Icon name="plus" :size="16" /> Add item</button>
      </div>
    </div>

    <div v-if="selectionMode" class="selection-bar">
      <span class="selection-count">{{ selectedIds.size }} selected</span>
      <div class="selection-actions">
        <button type="button" class="secondary" @click="selectAllVisible">Select all</button>
        <button type="button" class="secondary" :disabled="!selectedIds.size" @click="clearSelection">Clear</button>
        <button
          type="button"
          class="secondary danger btn-icon"
          :disabled="!selectedIds.size"
          @click="openDeleteSelectedModal"
        >
          <Icon name="trash" :size="14" /> Delete selected ({{ selectedIds.size }})
        </button>
      </div>
    </div>

    <Modal v-if="showAddModal" title="Add an item" @close="closeAddModal">
      <form @submit.prevent="onSubmit">
        <div class="field">
          <label for="item-name">Item name</label>
          <input id="item-name" v-model="form.name" required placeholder="e.g. Rice" autofocus />
        </div>
        <div class="field">
          <label>Unit</label>
          <div class="unit-picker">
            <button
              v-for="u in unitOptions"
              :key="u"
              type="button"
              class="unit-pill"
              :class="{ active: form.unit === u }"
              @click="form.unit = u"
            >
              {{ u }}
            </button>
            <div v-if="addingUnit" class="unit-add">
              <input
                v-model="newUnit"
                placeholder="New unit"
                autofocus
                @keyup.enter="confirmAddUnit((v) => (form.unit = v))"
                @keyup.escape="cancelAddUnit"
              />
              <button type="button" class="unit-add-confirm" @click="confirmAddUnit((v) => (form.unit = v))">✓ Use</button>
              <button type="button" class="unit-add-cancel" @click="cancelAddUnit">✕</button>
            </div>
            <button v-else type="button" class="unit-pill unit-pill-add" @click="startAddUnit">+ Add unit</button>
          </div>
          <p v-if="addingUnit" class="unit-hint">This just selects the unit — click "Add item" below to save.</p>
        </div>
        <div class="field">
          <label>Category</label>
          <div class="unit-picker">
            <button
              v-for="c in categoryOptions"
              :key="c"
              type="button"
              class="unit-pill"
              :class="{ active: form.category === c }"
              @click="form.category = c"
            >
              {{ c }}
            </button>
            <div v-if="addingCategory" class="unit-add">
              <input
                v-model="newCategory"
                placeholder="New category"
                autofocus
                @keyup.enter="confirmAddCategory((v) => (form.category = v))"
                @keyup.escape="cancelAddCategory"
              />
              <button type="button" class="unit-add-confirm" @click="confirmAddCategory((v) => (form.category = v))">✓ Use</button>
              <button type="button" class="unit-add-cancel" @click="cancelAddCategory">✕</button>
            </div>
            <button v-else type="button" class="unit-pill unit-pill-add" @click="startAddCategory">+ Add category</button>
          </div>
        </div>
        <div class="field">
          <label for="item-price">Price (₱)</label>
          <input id="item-price" v-model="form.price" type="number" min="0" step="any" required placeholder="e.g. 250" />
        </div>
        <p v-if="error" class="error-message">{{ error }}</p>
        <div class="modal-actions">
          <button type="button" class="secondary cancel" :disabled="submitting" @click="closeAddModal">Cancel</button>
          <button
            type="submit"
            :disabled="submitting || !form.unit"
            @click="console.log('[stock-items] Add item button clicked, form:', { ...form })"
          >
            {{ submitting ? "Adding..." : "Add item" }}
          </button>
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

    <ConfirmDeleteModal
      :open="showDeleteSelectedModal"
      :title="`Delete ${selectedIds.size} selected ${selectedIds.size === 1 ? 'item' : 'items'}?`"
      message="This will permanently delete the selected stock items, along with all sales, delivery, and count records tied to them. This cannot be undone."
      confirm-label="Delete selected"
      loading-label="Deleting..."
      :loading="deletingSelected"
      :error="deleteSelectedError"
      @confirm="confirmDeleteSelected"
      @cancel="cancelDeleteSelected"
    />

    <div class="card filters-card">
      <div class="filters-head">
        <span class="filters-title"><Icon name="filter" :size="14" /> Filters</span>
        <button v-if="hasActiveFilters" type="button" class="clear-filters" @click="clearFilters">
          <Icon name="x" :size="12" /> Clear filters
        </button>
      </div>
      <div class="filters-grid">
        <div class="field search-field">
          <label for="item-search">Search</label>
          <div class="search-input">
            <Icon name="search" :size="15" class="search-icon" />
            <input id="item-search" v-model="search" placeholder="Search by item name" />
            <button v-if="search" type="button" class="search-clear" aria-label="Clear search" @click="search = ''">
              <Icon name="x" :size="13" />
            </button>
          </div>
        </div>
        <div class="field">
          <label for="item-unit-filter">Unit</label>
          <CustomSelect id="item-unit-filter" v-model="unitFilter" :options="unitFilterOptions" placeholder="All units" />
        </div>
        <div class="field">
          <label for="item-category-filter">Category</label>
          <CustomSelect
            id="item-category-filter"
            v-model="categoryFilter"
            :options="categoryFilterOptions"
            placeholder="All categories"
          />
        </div>
      </div>
    </div>

    <p v-if="deleteError" class="error-message top-error">{{ deleteError }}</p>

    <LoadingState v-if="loading" label="Loading items..." />
    <div v-else-if="!filteredItems.length" class="card state-card">
      <div class="empty-state">
        <template v-if="items.length">
          <p>No items match your filters.</p>
          <p class="empty-hint">Try clearing the search or filters above.</p>
        </template>
        <template v-else>
          <p>No stock items yet.</p>
          <p class="empty-hint">Add your first item above so staff can start logging against it.</p>
        </template>
      </div>
    </div>

    <template v-else>
      <div class="item-grid">
        <div
          v-for="i in pagedItems"
          :key="i.id"
          class="item-card"
          :class="{ selectable: selectionMode, selected: selectionMode && isSelected(i.id) }"
          @click="selectionMode && toggleSelectItem(i.id)"
        >
          <div class="item-card-top">
            <label v-if="selectionMode" class="item-checkbox" @click.stop>
              <input type="checkbox" :checked="isSelected(i.id)" @change="toggleSelectItem(i.id)" />
            </label>
            <div class="item-card-name">{{ i.name }}</div>
            <span class="unit-chip">{{ i.unit }}</span>
          </div>
          <span v-if="i.category" class="category-chip">{{ i.category }}</span>
          <div class="item-card-price">₱{{ i.price.toFixed(2) }}</div>
          <div v-if="!selectionMode" class="item-card-actions">
            <button type="button" class="secondary edit btn-icon" @click="startEdit(i)"><Icon name="edit" :size="14" /> Edit</button>
            <button
              type="button"
              class="secondary danger btn-icon"
              :disabled="deletingId === i.id"
              @click="onDelete(i)"
            >
              <Icon name="trash" :size="14" /> {{ deletingId === i.id ? "Deleting..." : "Delete" }}
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

    <Modal v-if="editingId" title="Edit item" @close="cancelEdit">
      <form @submit.prevent="saveEdit">
        <div class="field">
          <label for="edit-item-name">Item name</label>
          <input id="edit-item-name" v-model="editingName" required placeholder="Item name" autofocus />
        </div>
        <div class="field">
          <label>Unit</label>
          <div class="unit-picker">
            <button
              v-for="u in unitOptions"
              :key="u"
              type="button"
              class="unit-pill"
              :class="{ active: editingUnit === u }"
              @click="editingUnit = u"
            >
              {{ u }}
            </button>
            <div v-if="addingUnit" class="unit-add">
              <input
                v-model="newUnit"
                placeholder="New unit"
                autofocus
                @keyup.enter="confirmAddUnit((v) => (editingUnit = v))"
                @keyup.escape="cancelAddUnit"
              />
              <button type="button" class="unit-add-confirm" @click="confirmAddUnit((v) => (editingUnit = v))">✓ Use</button>
              <button type="button" class="unit-add-cancel" @click="cancelAddUnit">✕</button>
            </div>
            <button v-else type="button" class="unit-pill unit-pill-add" @click="startAddUnit">+ Add unit</button>
          </div>
          <p v-if="addingUnit" class="unit-hint">This just selects the unit — click "Save" below to save.</p>
        </div>
        <div class="field">
          <label>Category</label>
          <div class="unit-picker">
            <button
              v-for="c in categoryOptions"
              :key="c"
              type="button"
              class="unit-pill"
              :class="{ active: editingCategory === c }"
              @click="editingCategory = c"
            >
              {{ c }}
            </button>
            <div v-if="addingCategory" class="unit-add">
              <input
                v-model="newCategory"
                placeholder="New category"
                autofocus
                @keyup.enter="confirmAddCategory((v) => (editingCategory = v))"
                @keyup.escape="cancelAddCategory"
              />
              <button type="button" class="unit-add-confirm" @click="confirmAddCategory((v) => (editingCategory = v))">✓ Use</button>
              <button type="button" class="unit-add-cancel" @click="cancelAddCategory">✕</button>
            </div>
            <button v-else type="button" class="unit-pill unit-pill-add" @click="startAddCategory">+ Add category</button>
          </div>
        </div>
        <div class="field">
          <label for="edit-item-price">Price (₱)</label>
          <input id="edit-item-price" v-model="editingPrice" type="number" min="0" step="any" required />
        </div>
        <p v-if="editError" class="error-message">{{ editError }}</p>
        <div class="modal-actions">
          <button type="button" class="secondary cancel" :disabled="savingEdit" @click="cancelEdit">Cancel</button>
          <button
            type="submit"
            :disabled="savingEdit || !editingName.trim() || !editingUnit"
            @click="console.log('[stock-items] Save button clicked, editingUnit:', editingUnit)"
          >
            {{ savingEdit ? "Saving..." : "Save" }}
          </button>
        </div>
      </form>
    </Modal>
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

.header-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-shrink: 0;
}

.card {
  margin-bottom: 1.5rem;
}

.header-actions .secondary.active {
  background: var(--color-primary-soft);
  border-color: var(--color-primary);
  color: var(--color-primary);
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
  margin-bottom: 1.25rem;
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

.item-checkbox {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.item-checkbox input {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.item-card.selectable {
  cursor: pointer;
}

.item-card.selected {
  box-shadow: 0 0 0 2px var(--color-primary);
}

.unit-picker {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.unit-pill {
  padding: 0.4rem 0.9rem;
  border-radius: 999px;
  border: 1px solid var(--color-border);
  background: transparent;
  color: var(--color-text-muted);
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s ease, border-color 0.15s ease, color 0.15s ease;
}

.unit-pill:hover {
  border-color: var(--color-primary);
  color: var(--color-text);
}

.unit-pill.active {
  background: var(--gradient-primary);
  border-color: var(--color-primary);
  color: #fff;
}

.unit-pill-add {
  border-style: dashed;
  color: var(--color-primary);
}

.unit-pill-add:hover {
  background: var(--color-primary-soft);
}

.unit-hint {
  margin: 0.5rem 0 0;
  font-size: 0.8rem;
  color: var(--color-text-muted);
}

.unit-add {
  display: flex;
  align-items: center;
  gap: 0.35rem;
}

.unit-add input {
  width: 120px;
  padding: 0.4rem 0.6rem;
  font-size: 0.85rem;
  border-radius: 999px;
}

.unit-add-confirm {
  flex-shrink: 0;
  padding: 0.4rem 0.75rem;
  border-radius: 999px;
  background: var(--color-primary);
  color: #fff;
  font-size: 0.85rem;
  font-weight: 600;
}

.unit-add-cancel {
  flex-shrink: 0;
  width: 30px;
  height: 30px;
  padding: 0;
  border-radius: 50%;
  background: transparent;
  color: var(--color-text-muted);
}

.unit-add-cancel:hover {
  background: rgba(255, 255, 255, 0.06);
  color: var(--color-text);
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.6rem;
  margin-top: 0.25rem;
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
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  align-items: end;
}

.filters-grid .field {
  flex: 0 1 220px;
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

.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
  margin-top: 1.5rem;
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

.top-error {
  margin: -0.75rem 0 1.25rem;
}

.item-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 1rem;
}

.item-card {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
  background: var(--color-surface);
  border-radius: var(--radius);
  border-top: 3px solid var(--color-primary);
  border-image: var(--gradient-primary) 1;
  box-shadow: var(--shadow);
  padding: 1.25rem;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.item-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-hover);
}

.item-card-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.5rem;
}

.item-card-name {
  font-weight: 600;
  font-size: 1.05rem;
  color: var(--color-text);
  word-break: break-word;
}

.unit-chip {
  flex-shrink: 0;
  background: var(--color-primary-soft);
  color: var(--color-primary);
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.25rem 0.6rem;
  border-radius: 999px;
  white-space: nowrap;
}

.category-chip {
  align-self: flex-start;
  background: var(--color-bg);
  color: var(--color-text-muted);
  font-size: 0.72rem;
  font-weight: 600;
  padding: 0.2rem 0.55rem;
  border-radius: 999px;
  border: 1px solid var(--color-border);
}

.item-card-price {
  font-family: "SFMono-Regular", Consolas, monospace;
  font-size: 1.4rem;
  font-weight: 700;
  color: var(--color-text);
}

.item-card-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: auto;
}

.item-card-actions button {
  flex: 1;
  font-size: 0.85rem;
  padding: 0.45rem 0.6rem;
}

.item-card-actions .edit {
  border-color: #fff;
}

.cancel {
  border-color: #fff;
}

.item-card-actions .danger {
  color: var(--color-danger);
  border-color: var(--color-danger);
}

.item-card-actions .danger:hover {
  background: rgba(255, 77, 77, 0.1);
}

@media (max-width: 560px) {
  .page-header {
    flex-direction: column;
    align-items: stretch;
  }

  .header-actions {
    justify-content: space-between;
  }

  .item-grid {
    grid-template-columns: 1fr 1fr;
    gap: 0.75rem;
  }

  .filters-grid .field {
    flex-basis: 100%;
  }
}

@media (max-width: 400px) {
  .item-grid {
    grid-template-columns: 1fr;
  }
}
</style>
