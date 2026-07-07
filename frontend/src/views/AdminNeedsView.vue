<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { listBranches } from "../api/branches";
import { ApiError } from "../api/client";
import { listStockItems } from "../api/stockItems";
import { listStockDeliveries } from "../api/stockDeliveries";
import Icon from "../components/Icon.vue";

const today = new Date().toISOString().slice(0, 10);

const branches = ref([]);
const stockItems = ref([]);
const needs = ref([]);
const selectedDate = ref(today);
const loading = ref(true);
const error = ref("");

const dateLabel = computed(() =>
  new Date(`${selectedDate.value}T00:00:00`).toLocaleDateString(undefined, {
    weekday: "long",
    month: "long",
    day: "numeric",
  })
);

function branchName(id) {
  return branches.value.find((b) => b.id === id)?.name || "—";
}

function itemName(id) {
  return stockItems.value.find((i) => i.id === id)?.name || "—";
}

function itemCategory(id) {
  return stockItems.value.find((i) => i.id === id)?.category || "";
}

const groupedByBranch = computed(() => {
  const groups = new Map();
  for (const n of needs.value) {
    if (!groups.has(n.branch_id)) groups.set(n.branch_id, []);
    groups.get(n.branch_id).push(n);
  }
  return [...groups.entries()]
    .map(([branchId, items]) => ({ branchId, name: branchName(branchId), items }))
    .sort((a, b) => a.name.localeCompare(b.name));
});

async function refresh() {
  loading.value = true;
  error.value = "";
  try {
    needs.value = await listStockDeliveries({ date: selectedDate.value, is_short: true });
  } catch (e) {
    error.value = e instanceof ApiError ? e.detail || "Could not load needs" : "Could not load needs";
  } finally {
    loading.value = false;
  }
}

onMounted(async () => {
  [branches.value, stockItems.value] = await Promise.all([listBranches(), listStockItems()]);
  await refresh();
});

watch(selectedDate, refresh);
</script>

<template>
  <div class="page-header">
    <div>
      <h1>Needs</h1>
      <p class="page-subtitle">Items flagged "Need Deliver" by staff, per branch — {{ dateLabel }}</p>
    </div>
    <div class="header-filters">
      <input v-model="selectedDate" type="date" />
    </div>
  </div>

  <p v-if="error" class="error-message top-error">{{ error }}</p>
  <p v-if="loading" class="state-message">Loading...</p>

  <template v-else>
    <div v-if="!groupedByBranch.length" class="card state-card">
      <div class="empty-state">
        <p>Walang branch na may kailangang i-deliver sa araw na ito.</p>
      </div>
    </div>

    <div v-else class="needs-list">
      <section v-for="group in groupedByBranch" :key="group.branchId" class="card branch-card">
        <div class="branch-card-header">
          <h2 class="card-title branch-title">{{ group.name }}</h2>
          <span class="count-chip"><Icon name="count" :size="14" /> {{ group.items.length }} needs delivery</span>
        </div>

        <ul class="need-items">
          <li v-for="n in group.items" :key="n.id" class="need-item">
            <div class="need-main">
              <span class="item-name">{{ itemName(n.item_id) }}</span>
              <span v-if="itemCategory(n.item_id)" class="category-chip">{{ itemCategory(n.item_id) }}</span>
            </div>
          </li>
        </ul>
      </section>
    </div>
  </template>
</template>

<style scoped>
.header-filters {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  flex-wrap: wrap;
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

.needs-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.branch-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  flex-wrap: wrap;
  margin-bottom: 1rem;
}

.branch-title {
  margin-bottom: 0;
}

.need-items {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.need-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  flex-wrap: wrap;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  padding: 0.65rem 0.85rem;
}

.need-main {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
  min-width: 0;
}

.item-name {
  font-weight: 600;
  color: var(--color-text);
}

.category-chip {
  flex-shrink: 0;
  background: var(--color-surface);
  color: var(--color-text-muted);
  font-size: 0.72rem;
  font-weight: 600;
  padding: 0.2rem 0.55rem;
  border-radius: 999px;
  border: 1px solid var(--color-border);
}

@media (max-width: 560px) {
  .header-filters {
    width: 100%;
  }

  .header-filters input {
    width: 100%;
  }
}
</style>
