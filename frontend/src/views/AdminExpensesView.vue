<script setup>
import { computed, onMounted, reactive, ref, watch } from "vue";
import { listBranches } from "../api/branches";
import { ApiError } from "../api/client";
import { createExpense, listExpenses } from "../api/expenses";
import { listSales } from "../api/sales";
import { listStockItems } from "../api/stockItems";
import { listStockCounts } from "../api/stockCounts";
import { listStockDeliveries } from "../api/stockDeliveries";
import CustomSelect from "../components/CustomSelect.vue";
import Icon from "../components/Icon.vue";

const today = new Date().toISOString().slice(0, 10);

const branches = ref([]);
const selectedDate = ref(today);
const selectedBranchId = ref("");

const expenses = ref([]);
const sales = ref([]);
const loading = ref(true);
const error = ref("");

const stockItems = ref([]);
const stockExpenseRows = ref([]);
const stockExpenseLoading = ref(true);

const branchOptions = computed(() => [
  { label: "All branches", value: "" },
  ...branches.value.map((b) => ({ label: b.name, value: b.id })),
]);

function branchName(id) {
  return branches.value.find((b) => b.id === id)?.name || "—";
}

function peso(amount) {
  return `₱${amount.toLocaleString("en-PH", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

const totalSales = computed(() => sales.value.reduce((sum, s) => sum + s.amount, 0));
const totalBills = computed(() => expenses.value.reduce((sum, e) => sum + e.amount, 0));

const billRows = reactive({});

function billRowFor(branchId) {
  if (!billRows[branchId]) {
    billRows[branchId] = { id: null, amount: "", saving: false, saved: false, error: "", editing: false };
  }
  return billRows[branchId];
}

function flashSaved(row) {
  row.saved = true;
  setTimeout(() => {
    row.saved = false;
  }, 1500);
}

async function saveBill(branchId) {
  const row = billRowFor(branchId);
  row.error = "";
  if (row.amount === "" || Number.isNaN(Number(row.amount))) return;
  row.saving = true;
  try {
    const result = await createExpense({
      branchId,
      date: selectedDate.value,
      description: "Daily bills",
      amount: Number(row.amount),
    });
    row.id = result.id;
    row.editing = false;
    const idx = expenses.value.findIndex((e) => e.branch_id === branchId);
    if (idx !== -1) {
      expenses.value[idx] = result;
    } else {
      expenses.value.push(result);
    }
    flashSaved(row);
  } catch (e) {
    row.error = e instanceof ApiError ? e.detail || "Could not save" : "Could not save";
  } finally {
    row.saving = false;
  }
}

async function refresh() {
  loading.value = true;
  error.value = "";
  const params = { date: selectedDate.value };
  if (selectedBranchId.value) params.branch_id = selectedBranchId.value;
  try {
    [expenses.value, sales.value] = await Promise.all([listExpenses(params), listSales(params)]);
    for (const b of branches.value) {
      const row = billRowFor(b.id);
      row.id = null;
      row.amount = "";
    }
    for (const e of expenses.value) {
      const row = billRowFor(e.branch_id);
      row.id = e.id;
      row.amount = String(e.amount);
    }
  } catch (e) {
    error.value = e instanceof ApiError ? e.detail || "Could not load data" : "Could not load data";
  } finally {
    loading.value = false;
  }
}

function previousDay(dateStr) {
  const d = new Date(`${dateStr}T00:00:00Z`);
  return new Date(d.getTime() - 24 * 60 * 60 * 1000).toISOString().slice(0, 10);
}

async function refreshStockExpense() {
  stockExpenseLoading.value = true;
  const params = { date: selectedDate.value };
  const openingParams = { date: previousDay(selectedDate.value) };
  if (selectedBranchId.value) {
    params.branch_id = selectedBranchId.value;
    openingParams.branch_id = selectedBranchId.value;
  }

  const [items, closingToday, closingYesterday, deliveriesToday] = await Promise.all([
    listStockItems(),
    listStockCounts(params),
    listStockCounts(openingParams),
    listStockDeliveries(params),
  ]);
  stockItems.value = items;

  const openingMap = new Map(closingYesterday.map((c) => [`${c.branch_id}|${c.item_id}`, c.quantity_remaining]));
  const deliveryTotals = new Map();
  for (const d of deliveriesToday) {
    const key = `${d.branch_id}|${d.item_id}`;
    deliveryTotals.set(key, (deliveryTotals.get(key) || 0) + d.quantity_delivered);
  }
  const itemsById = new Map(items.map((i) => [i.id, i]));

  stockExpenseRows.value = closingToday
    .map((c) => {
      const key = `${c.branch_id}|${c.item_id}`;
      const item = itemsById.get(c.item_id);
      const opening = openingMap.get(key) || 0;
      const delivery = deliveryTotals.get(key) || 0;
      const closing = c.quantity_remaining;
      const used = opening + delivery - closing;
      const price = item?.price || 0;
      return {
        key: c.id,
        branchId: c.branch_id,
        itemName: item?.name || "—",
        opening,
        delivery,
        closing,
        price,
        used,
        expense: used * price,
      };
    })
    .sort((a, b) => branchName(a.branchId).localeCompare(branchName(b.branchId)) || a.itemName.localeCompare(b.itemName));

  stockExpenseLoading.value = false;
}

const stockExpenseTotal = computed(() => stockExpenseRows.value.reduce((sum, r) => sum + r.expense, 0));
const grandTotalExpense = computed(() => stockExpenseTotal.value + totalBills.value);
const dailyProfit = computed(() => totalSales.value - grandTotalExpense.value);

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
    return (av - bv) * dir;
  });
}

const stockExpenseByBranch = computed(() => {
  const groups = new Map();
  for (const row of stockExpenseRows.value) {
    if (!groups.has(row.branchId)) groups.set(row.branchId, []);
    groups.get(row.branchId).push(row);
  }
  return [...groups.entries()].map(([branchId, rows]) => ({
    branchId,
    name: branchName(branchId),
    rows: sortRows(rows),
    total: rows.reduce((sum, r) => sum + r.expense, 0),
  }));
});


onMounted(async () => {
  branches.value = await listBranches();
  await Promise.all([refresh(), refreshStockExpense()]);
});

watch([selectedDate, selectedBranchId], () => {
  refresh();
  refreshStockExpense();
});
</script>

<template>
  <div class="page-header">
    <div>
      <h1>Expenses</h1>
      <p class="page-subtitle">Daily sales, bills, and net profit per branch.</p>
    </div>
    <div class="header-filters">
      <input v-model="selectedDate" type="date" />
      <CustomSelect v-model="selectedBranchId" :options="branchOptions" placeholder="All branches" />
    </div>
  </div>

  <p v-if="error" class="error-message top-error">{{ error }}</p>

  <div class="stat-row">
    <div class="card stat-card">
      <span class="stat-label">Sales</span>
      <span class="stat-value">{{ peso(totalSales) }}</span>
    </div>
    <div class="card stat-card">
      <span class="stat-label">Total expense (incl. bills)</span>
      <span class="stat-value">{{ peso(grandTotalExpense) }}</span>
    </div>
    <div class="card stat-card" :class="{ 'stat-card-alert': dailyProfit < 0, 'stat-card-positive': dailyProfit >= 0 }">
      <span class="stat-label">Daily Profit</span>
      <span class="stat-value">{{ dailyProfit >= 0 ? "+" : "" }}{{ peso(dailyProfit) }}</span>
    </div>
  </div>

  <section class="card stock-expense-section">
    <div class="stock-expense-header">
      <h2 class="card-title">Stock expense</h2>
    </div>

    <p v-if="stockExpenseLoading" class="state-message">Loading...</p>
    <div v-else-if="!stockExpenseByBranch.length" class="empty-state">
      <p>No closing counts logged for this day yet.</p>
    </div>
    <div v-else class="branch-groups">
      <div v-for="group in stockExpenseByBranch" :key="group.branchId" class="branch-group">
        <div class="branch-group-header">
          <h3 class="branch-group-name">{{ group.name }}</h3>
          <span class="branch-group-total">
            {{ peso(group.total + (Number(billRowFor(group.branchId).amount) || 0)) }}
          </span>

          <div class="daily-bills-inline">
            <span class="daily-bills-title">Daily bills</span>

            <template v-if="!billRowFor(group.branchId).id || billRowFor(group.branchId).editing">
              <span class="unit-label">₱</span>
              <input
                type="number"
                inputmode="decimal"
                min="0"
                step="any"
                class="value-input"
                :class="{ saved: billRowFor(group.branchId).saved }"
                placeholder="0"
                v-model="billRowFor(group.branchId).amount"
                @blur="saveBill(group.branchId)"
                @keyup.enter="($event.target).blur()"
              />
              <span v-if="billRowFor(group.branchId).saving" class="save-status">Saving...</span>
            </template>
            <template v-else>
              <button
                type="button"
                class="edit-bill-btn"
                title="Edit daily bills"
                aria-label="Edit daily bills"
                @click="billRowFor(group.branchId).editing = true"
              >
                <Icon name="edit" :size="12" />
              </button>
            </template>
          </div>
        </div>
        <p v-if="billRowFor(group.branchId).error" class="row-error">{{ billRowFor(group.branchId).error }}</p>
        <div class="table-scroll">
          <table class="stock-expense-table">
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
                <th class="sortable" @click="toggleSort('price')">
                  Price <span v-if="sortKey === 'price'" class="sort-arrow">{{ sortDir === "asc" ? "▲" : "▼" }}</span>
                </th>
                <th class="sortable" @click="toggleSort('used')">
                  Used <span v-if="sortKey === 'used'" class="sort-arrow">{{ sortDir === "asc" ? "▲" : "▼" }}</span>
                </th>
                <th class="sortable" @click="toggleSort('expense')">
                  Expense <span v-if="sortKey === 'expense'" class="sort-arrow">{{ sortDir === "asc" ? "▲" : "▼" }}</span>
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in group.rows" :key="row.key">
                <td>{{ row.itemName }}</td>
                <td>{{ row.opening }}</td>
                <td>{{ row.delivery }}</td>
                <td>{{ row.closing }}</td>
                <td>{{ peso(row.price) }}</td>
                <td :class="{ negative: row.used < 0, positive: row.used > 0 }">{{ row.used }}</td>
                <td :class="{ negative: row.expense < 0 }">{{ peso(row.expense) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1.75rem;
  flex-wrap: wrap;
}

.page-header h1 {
  font-size: 1.5rem;
  margin-bottom: 0.35rem;
}

.page-subtitle {
  color: var(--color-text-muted);
  margin: 0;
}

.header-filters {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  flex-wrap: wrap;
}

.header-filters input[type="date"] {
  width: auto;
}

.top-error {
  text-align: center;
}

.stat-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  box-shadow: var(--shadow);
  padding: 1.5rem;
}

.stat-card {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.stat-label {
  font-size: 0.75rem;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.stat-value {
  font-family: "SFMono-Regular", Consolas, monospace;
  font-size: 1.6rem;
  font-weight: 700;
  color: var(--color-text);
}

.stat-card-alert .stat-value {
  color: var(--color-danger);
}

.stat-card-positive .stat-value {
  color: var(--color-success, #2e7d32);
}

.card-title {
  font-size: 0.95rem;
  margin-bottom: 1.1rem;
  color: var(--color-text);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}


.state-message {
  text-align: center;
  color: var(--color-text-muted);
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

.row-error {
  color: var(--color-danger);
  font-size: 0.8rem;
  margin: 0.4rem 0 0;
}

.stock-expense-section {
  margin-bottom: 1.25rem;
}

.stock-expense-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1.1rem;
}

.stock-expense-header .card-title {
  margin-bottom: 0;
}

.stock-expense-total {
  font-size: 1.2rem;
}

.branch-groups {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.branch-group-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
  margin-bottom: 0.6rem;
}

.branch-group-name {
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--color-text);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin: 0 auto 0 0;
}

.daily-bills-inline {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.branch-group-total {
  font-weight: 700;
  color: var(--color-primary);
}

.table-scroll {
  overflow-x: auto;
}

.stock-expense-table {
  width: 100%;
  min-width: 520px;
  border-collapse: collapse;
  font-size: 0.88rem;
}

.stock-expense-table th {
  text-align: left;
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--color-text);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 0.65rem 0.75rem;
  background: var(--color-bg);
  border-bottom: 2px solid var(--color-border);
  white-space: nowrap;
}

.stock-expense-table th.sortable {
  cursor: pointer;
  user-select: none;
}

.stock-expense-table th.sortable:hover {
  color: var(--color-primary);
}

.sort-arrow {
  font-size: 0.65rem;
  margin-left: 0.2rem;
}

.stock-expense-table td {
  padding: 0.55rem 0.75rem;
  border-bottom: 1px solid var(--color-border);
  color: var(--color-text);
  white-space: nowrap;
}

.stock-expense-table td.positive {
  color: var(--color-success, #2e7d32);
}

.stock-expense-table td.negative {
  color: var(--color-danger);
}

.daily-bills-title {
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.edit-bill-btn {
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
}

.edit-bill-btn:hover {
  border-color: var(--color-text-muted);
}

.unit-label {
  font-size: 0.9rem;
  color: var(--color-text-muted);
}

.value-input {
  width: 140px;
  font-weight: 600;
  transition: border-color 0.3s;
}

.value-input.saved {
  border-color: var(--color-success, #2e7d32);
}

.save-status {
  font-size: 0.8rem;
  color: var(--color-text-muted);
}

@media (max-width: 560px) {
  .stat-row {
    grid-template-columns: 1fr;
  }
}
</style>
