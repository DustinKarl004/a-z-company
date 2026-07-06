<script setup>
import { onMounted, ref } from "vue";
import { createStockItem, listStockItems, updateStockItem } from "../api/stockItems";
import { ApiError } from "../api/client";

const UNIT_OPTIONS = ["kg", "g", "L", "mL", "pcs", "servings", "pack", "box", "sack", "bottle"];

const items = ref([]);
const form = ref({ name: "", unit: "", price: "" });
const error = ref("");
const submitting = ref(false);
const loading = ref(true);
const editingId = ref(null);
const editingUnit = ref("");
const editingPrice = ref("");
const savingEdit = ref(false);

async function refresh() {
  loading.value = true;
  items.value = await listStockItems();
  loading.value = false;
}

async function onSubmit() {
  error.value = "";
  submitting.value = true;
  try {
    await createStockItem({ ...form.value, price: Number(form.value.price) });
    form.value = { name: "", unit: "", price: "" };
    await refresh();
  } catch (e) {
    error.value = e instanceof ApiError ? e.detail || "Could not create item" : "Could not create item";
  } finally {
    submitting.value = false;
  }
}

function startEdit(item) {
  editingId.value = item.id;
  editingUnit.value = item.unit;
  editingPrice.value = item.price;
}

function cancelEdit() {
  editingId.value = null;
}

async function saveEdit(item) {
  error.value = "";
  savingEdit.value = true;
  try {
    await updateStockItem(item.id, { unit: editingUnit.value, price: Number(editingPrice.value) });
    editingId.value = null;
    await refresh();
  } catch (e) {
    error.value = e instanceof ApiError ? e.detail || "Could not update item" : "Could not update item";
  } finally {
    savingEdit.value = false;
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
      <span class="count-chip">{{ items.length }} {{ items.length === 1 ? "item" : "items" }}</span>
    </div>

    <form class="card new-item" @submit.prevent="onSubmit">
      <h2 class="card-title">Add an item</h2>
      <div class="new-item-row">
        <div class="field">
          <label for="item-name">Item name</label>
          <input id="item-name" v-model="form.name" required placeholder="e.g. Rice" />
        </div>
        <div class="field unit-field">
          <label for="item-unit">Unit</label>
          <select id="item-unit" v-model="form.unit" required>
            <option disabled value="">Select a unit</option>
            <option v-for="u in UNIT_OPTIONS" :key="u" :value="u">{{ u }}</option>
          </select>
        </div>
        <div class="field unit-field">
          <label for="item-price">Price (₱)</label>
          <input id="item-price" v-model="form.price" type="number" min="0" step="any" required placeholder="e.g. 250" />
        </div>
        <button type="submit" :disabled="submitting">{{ submitting ? "Adding..." : "Add item" }}</button>
      </div>
      <p v-if="error" class="error-message">{{ error }}</p>
    </form>

    <div class="card table-card">
      <table v-if="!loading && items.length">
        <thead>
          <tr>
            <th>Name</th>
            <th>Unit</th>
            <th>Price</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="i in items" :key="i.id">
            <td class="primary-cell">{{ i.name }}</td>
            <td>
              <select v-if="editingId === i.id" v-model="editingUnit" class="unit-edit-select">
                <option v-for="u in UNIT_OPTIONS" :key="u" :value="u">{{ u }}</option>
              </select>
              <span v-else>{{ i.unit }}</span>
            </td>
            <td>
              <input
                v-if="editingId === i.id"
                v-model="editingPrice"
                type="number"
                min="0"
                step="any"
                class="price-edit-input"
              />
              <span v-else>₱{{ i.price.toFixed(2) }}</span>
            </td>
            <td>
              <template v-if="editingId === i.id">
                <button type="button" :disabled="savingEdit" @click="saveEdit(i)">Save</button>
                <button type="button" class="secondary" @click="cancelEdit">Cancel</button>
              </template>
              <button v-else type="button" class="secondary" @click="startEdit(i)">Edit</button>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-else-if="loading" class="state-message">Loading items...</p>
      <div v-else class="empty-state">
        <p>No stock items yet.</p>
        <p class="empty-hint">Add your first item above so staff can start logging against it.</p>
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

.count-chip {
  flex-shrink: 0;
  background: rgba(15, 110, 110, 0.1);
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

.card-title {
  font-size: 1.05rem;
  margin-bottom: 1rem;
}

.new-item-row {
  display: flex;
  align-items: flex-end;
  gap: 1rem;
}

.new-item-row .field {
  flex: 1;
  margin-bottom: 0;
}

.new-item-row .unit-field {
  flex: 0 0 140px;
}

.table-card {
  padding: 0;
  overflow: hidden;
}

.table-card table {
  margin: 0;
}

.table-card th,
.table-card td {
  padding: 0.85rem 1.5rem;
}

.table-card tbody tr:hover {
  background: var(--color-bg);
}

.primary-cell {
  font-weight: 600;
  color: var(--color-primary-dark);
}

.state-message {
  padding: 2rem 1.5rem;
  text-align: center;
  color: var(--color-text-muted);
  margin: 0;
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

.price-edit-input {
  width: 100px;
}

.unit-edit-select {
  width: 110px;
}

.secondary {
  background: transparent;
  color: var(--color-primary);
}

@media (max-width: 560px) {
  .new-item-row {
    flex-direction: column;
    align-items: stretch;
  }

  .new-item-row .unit-field {
    flex: 1;
  }
}
</style>
