<script setup>
import { onMounted, ref } from "vue";
import { createStockItem, listStockItems } from "../api/stockItems";
import { ApiError } from "../api/client";

const items = ref([]);
const form = ref({ name: "", unit: "" });
const error = ref("");
const submitting = ref(false);
const loading = ref(true);

async function refresh() {
  loading.value = true;
  items.value = await listStockItems();
  loading.value = false;
}

async function onSubmit() {
  error.value = "";
  submitting.value = true;
  try {
    await createStockItem(form.value);
    form.value = { name: "", unit: "" };
    await refresh();
  } catch (e) {
    error.value = e instanceof ApiError ? e.detail || "Could not create item" : "Could not create item";
  } finally {
    submitting.value = false;
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
          <input id="item-unit" v-model="form.unit" required placeholder="e.g. kg" />
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
          </tr>
        </thead>
        <tbody>
          <tr v-for="i in items" :key="i.id">
            <td class="primary-cell">{{ i.name }}</td>
            <td>{{ i.unit }}</td>
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
