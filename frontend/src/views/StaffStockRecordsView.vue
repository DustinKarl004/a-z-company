<script setup>
import { computed, onMounted, ref } from "vue";
import { ApiError } from "../api/client";
import { listBranches } from "../api/branches";
import { listStockItems } from "../api/stockItems";
import { listStockCounts } from "../api/stockCounts";
import { listStockDeliveries } from "../api/stockDeliveries";
import CustomSelect from "../components/CustomSelect.vue";
import Icon from "../components/Icon.vue";
import LoadingState from "../components/LoadingState.vue";
import { toLocalISO, fetchBusinessToday } from "../utils/date";

const branches = ref([]);
const loading = ref(true);
const error = ref("");
const yesterdayLabel = ref("");

const stockRows = ref([]);

// Guards against floating-point noise (e.g. 10.7 + 5.3 - 3.85 === 12.150000000000002)
// from leaking into displayed quantities.
function round2(n) {
  return Math.round((n + Number.EPSILON) * 100) / 100;
}

function branchName(id) {
  return branches.value.find((b) => b.id === id)?.name || "—";
}

const sortKey = ref("itemName");
const sortDir = ref("asc");

function toggleSort(key) {
  if (sortKey.value === key) {
    sortDir.value = sortDir.value === "asc" ? "desc" : "asc";
  } else {
    sortKey.value = key;
    sortDir.value = "asc";
  }
}

function sortRows(rows) {
  const dir = sortDir.value === "asc" ? 1 : -1;
  return rows.slice().sort((a, b) => {
    const av = a[sortKey.value];
    const bv = b[sortKey.value];
    if (typeof av === "string") return av.localeCompare(bv) * dir;
    return ((av ?? 0) - (bv ?? 0)) * dir;
  });
}

const COLLAPSED_BRANCHES_KEY = "za-staff-stock-records-collapsed-branches";

function loadCollapsedBranches() {
  try {
    const stored = JSON.parse(localStorage.getItem(COLLAPSED_BRANCHES_KEY));
    return new Set(Array.isArray(stored) ? stored : []);
  } catch {
    return new Set();
  }
}

const collapsedBranches = ref(loadCollapsedBranches());

function toggleBranchCollapse(branchId) {
  const next = new Set(collapsedBranches.value);
  if (next.has(branchId)) next.delete(branchId);
  else next.add(branchId);
  collapsedBranches.value = next;
  localStorage.setItem(COLLAPSED_BRANCHES_KEY, JSON.stringify([...next]));
}

function isBranchCollapsed(branchId) {
  return collapsedBranches.value.has(branchId);
}

const search = ref("");
const branchFilter = ref("");

const hasActiveFilters = computed(() => !!(search.value.trim() || branchFilter.value));

function clearFilters() {
  search.value = "";
  branchFilter.value = "";
}

const branchFilterOptions = computed(() => [
  { label: "All branches", value: "" },
  ...branches.value
    .slice()
    .sort((a, b) => a.name.localeCompare(b.name))
    .map((b) => ({ label: b.name, value: b.id })),
]);

const rowsByBranch = computed(() => {
  const term = search.value.trim().toLowerCase();
  const groups = new Map();
  for (const row of stockRows.value) {
    if (branchFilter.value && row.branchId !== branchFilter.value) continue;
    if (term && !row.itemName.toLowerCase().includes(term)) continue;
    if (!groups.has(row.branchId)) groups.set(row.branchId, []);
    groups.get(row.branchId).push(row);
  }
  return [...groups.entries()]
    .map(([branchId, rows]) => ({
      branchId,
      name: branchName(branchId),
      rows: sortRows(rows),
    }))
    .sort((a, b) => a.name.localeCompare(b.name));
});

async function refresh() {
  loading.value = true;
  error.value = "";
  try {
    const { date } = await fetchBusinessToday();
    const yesterday = new Date(date);
    yesterday.setDate(yesterday.getDate() - 1);
    const dayBeforeYesterday = new Date(date);
    dayBeforeYesterday.setDate(dayBeforeYesterday.getDate() - 2);

    const yesterdayStr = toLocalISO(yesterday);
    const dayBeforeStr = toLocalISO(dayBeforeYesterday);
    yesterdayLabel.value = yesterday.toLocaleDateString(undefined, { weekday: "long", month: "long", day: "numeric" });

    const [branchList, items, closingYesterday, closingDayBefore, deliveriesYesterday] = await Promise.all([
      listBranches(),
      listStockItems(),
      listStockCounts({ date: yesterdayStr }),
      listStockCounts({ date: dayBeforeStr }),
      listStockDeliveries({ date: yesterdayStr }),
    ]);
    branches.value = branchList;

    const openingMap = new Map(closingDayBefore.map((c) => [`${c.branch_id}|${c.item_id}`, c.quantity_remaining]));
    const closingMap = new Map(closingYesterday.map((c) => [`${c.branch_id}|${c.item_id}`, c.quantity_remaining]));
    const deliveryMap = new Map();
    for (const d of deliveriesYesterday) {
      const key = `${d.branch_id}|${d.item_id}`;
      deliveryMap.set(key, (deliveryMap.get(key) || 0) + d.quantity_delivered);
    }

    const rows = [];
    for (const branch of branchList) {
      for (const item of items) {
        if (item.branch_ids && item.branch_ids.length && !item.branch_ids.includes(branch.id)) continue;
        const key = `${branch.id}|${item.id}`;
        const opening = openingMap.get(key) || 0;
        const delivery = deliveryMap.get(key) || 0;
        const closingRaw = closingMap.get(key);
        const hasClosing = closingRaw !== undefined;
        const closing = hasClosing ? closingRaw : null;
        const used = hasClosing ? round2(opening + delivery - closing) : null;
        rows.push({
          branchId: branch.id,
          itemId: item.id,
          itemName: item.name,
          unit: item.unit || "",
          opening,
          delivery,
          closing,
          hasClosing,
          used,
        });
      }
    }
    stockRows.value = rows;
  } catch (e) {
    error.value = e instanceof ApiError ? e.detail || "Could not load stock records" : "Could not load stock records";
  } finally {
    loading.value = false;
  }
}

onMounted(refresh);
</script>

<template>
  <div class="page-header">
    <div>
      <h1>Stock records — Yesterday</h1>
      <p v-if="yesterdayLabel" class="page-subtitle date-note">{{ yesterdayLabel }}</p>
    </div>
  </div>

  <p v-if="error" class="error-message top-error">{{ error }}</p>
  <LoadingState v-if="loading" label="Loading stock records..." />

  <template v-else>
    <div v-if="stockRows.length" class="card filters-card">
      <div class="filters-head">
        <span class="filters-title"><Icon name="filter" :size="14" /> Filters</span>
        <button v-if="hasActiveFilters" type="button" class="clear-filters" @click="clearFilters">
          <Icon name="x" :size="12" /> Clear filters
        </button>
      </div>
      <div class="filters-grid">
        <div class="field search-field">
          <label for="stock-records-search">Search</label>
          <div class="search-input">
            <Icon name="search" :size="15" class="search-icon" />
            <input id="stock-records-search" v-model="search" placeholder="Search by item name" />
            <button v-if="search" type="button" class="search-clear" aria-label="Clear search" @click="search = ''">
              <Icon name="x" :size="13" />
            </button>
          </div>
        </div>
        <div class="field">
          <label for="stock-records-branch-filter">Branch</label>
          <CustomSelect
            id="stock-records-branch-filter"
            v-model="branchFilter"
            :options="branchFilterOptions"
            placeholder="All branches"
          />
        </div>
      </div>
    </div>

    <div v-if="!rowsByBranch.length" class="card state-card">
      <div class="empty-state">
        <template v-if="stockRows.length">
          <p>No stock records match your filters.</p>
          <p class="empty-hint">Try clearing the search or filter above.</p>
        </template>
        <template v-else>
          <p>No stock records found for yesterday.</p>
        </template>
      </div>
    </div>

    <div v-else class="branch-groups">
      <section v-for="group in rowsByBranch" :key="group.branchId" class="card branch-card">
        <div class="branch-card-header">
          <button
            type="button"
            class="branch-collapse-btn"
            :class="{ collapsed: isBranchCollapsed(group.branchId) }"
            :aria-expanded="!isBranchCollapsed(group.branchId)"
            :aria-label="isBranchCollapsed(group.branchId) ? 'Expand branch' : 'Collapse branch'"
            @click="toggleBranchCollapse(group.branchId)"
          >
            <Icon name="chevron-right" :size="16" />
          </button>
          <h3 class="card-title branch-title">
            <Icon name="map-pin" :size="14" />
            {{ group.name }}
          </h3>
        </div>

        <div v-show="!isBranchCollapsed(group.branchId)" class="table-scroll">
          <table class="stock-table">
            <thead>
              <tr>
                <th class="sortable" @click="toggleSort('itemName')">
                  Item <span v-if="sortKey === 'itemName'" class="sort-arrow">{{ sortDir === "asc" ? "▲" : "▼" }}</span>
                </th>
                <th class="sortable" @click="toggleSort('opening')">
                  Opening <span v-if="sortKey === 'opening'" class="sort-arrow">{{ sortDir === "asc" ? "▲" : "▼" }}</span>
                </th>
                <th class="sortable" @click="toggleSort('delivery')">
                  Delivery <span v-if="sortKey === 'delivery'" class="sort-arrow">{{ sortDir === "asc" ? "▲" : "▼" }}</span>
                </th>
                <th class="sortable" @click="toggleSort('closing')">
                  Closing <span v-if="sortKey === 'closing'" class="sort-arrow">{{ sortDir === "asc" ? "▲" : "▼" }}</span>
                </th>
                <th class="sortable" @click="toggleSort('used')">
                  Used <span v-if="sortKey === 'used'" class="sort-arrow">{{ sortDir === "asc" ? "▲" : "▼" }}</span>
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in group.rows" :key="row.itemId">
                <td data-label="Item">{{ row.itemName }} <span v-if="row.unit" class="item-unit">{{ row.unit }}</span></td>
                <td data-label="Opening">{{ row.opening }}</td>
                <td data-label="Delivery">{{ row.delivery }}</td>
                <td data-label="Closing">{{ row.hasClosing ? row.closing : "—" }}</td>
                <td
                  data-label="Used"
                  :class="{ negative: row.hasClosing && row.used < 0, positive: row.hasClosing && row.used > 0 }"
                >
                  {{ row.hasClosing ? row.used : "—" }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </div>
  </template>
</template>

<style scoped>
.page-header {
  margin-bottom: 1.75rem;
}

.page-header h1 {
  font-size: 1.5rem;
  margin-bottom: 0.35rem;
}

.page-subtitle {
  color: var(--color-text-muted);
  margin: 0;
}

.date-note {
  font-size: 0.8rem;
  opacity: 0.7;
  margin-top: 0.15rem;
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
  margin-top: 0.35rem;
}

.filters-card {
  padding: 1.1rem 1.25rem 1.25rem;
  margin-bottom: 1.25rem;
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

.branch-groups {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.branch-card {
  padding: 1.25rem;
}

.branch-card-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.branch-collapse-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  flex-shrink: 0;
  padding: 0;
  border-radius: 6px;
  border: 1px solid var(--color-border);
  background: var(--color-bg);
  color: var(--color-text-muted);
  transition: transform 0.15s ease;
}

.branch-collapse-btn:hover {
  border-color: var(--color-text-muted);
}

.branch-collapse-btn svg {
  transition: transform 0.15s ease;
  transform: rotate(90deg);
}

.branch-collapse-btn.collapsed svg {
  transform: rotate(0deg);
}

.branch-title {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  margin: 0;
}

.table-scroll {
  overflow-x: auto;
}

.stock-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
}

.stock-table th,
.stock-table td {
  padding: 0.55rem 0.75rem;
  text-align: left;
  border-bottom: 1px solid var(--color-border);
  white-space: nowrap;
}

.stock-table th {
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text);
  font-weight: 700;
  background: var(--color-bg);
  border-bottom: 2px solid var(--color-border);
}

.stock-table th.sortable {
  cursor: pointer;
  user-select: none;
}

.stock-table th.sortable:hover {
  color: var(--color-primary);
}

.sort-arrow {
  font-size: 0.65rem;
  margin-left: 0.2rem;
}

.stock-table tbody tr:last-child td {
  border-bottom: none;
}

.item-unit {
  color: var(--color-danger);
  font-size: 0.8em;
}

.stock-table td.negative {
  color: var(--color-danger);
  font-weight: 600;
}

.stock-table td.positive {
  color: var(--color-success, #2e7d32);
  font-weight: 600;
}

/* Below ~700px a wide table just forces sideways scrolling on a phone, so
   each row becomes its own stacked card instead — label/value pairs. */
@media (max-width: 700px) {
  .filters-grid .field {
    flex-basis: 100%;
  }

  .branch-card {
    padding: 1rem 0.85rem;
  }

  .table-scroll {
    overflow-x: visible;
  }

  .stock-table thead {
    display: none;
  }

  .stock-table,
  .stock-table tbody,
  .stock-table tr {
    display: block;
    width: 100%;
  }

  .stock-table tr {
    padding: 0.5rem 0;
    border-bottom: 1px solid var(--color-border);
  }

  .stock-table tbody tr:last-child {
    border-bottom: none;
  }

  .stock-table td {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.75rem;
    padding: 0.2rem 0;
    border-bottom: none;
    white-space: normal;
  }

  .stock-table td[data-label="Item"] {
    font-weight: 600;
    justify-content: flex-start;
    padding-bottom: 0.3rem;
  }

  .stock-table td:not([data-label="Item"])::before {
    content: attr(data-label);
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: var(--color-text-muted);
  }
}
</style>
