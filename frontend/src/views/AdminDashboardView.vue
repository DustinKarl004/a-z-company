<script setup>
import { onMounted, ref } from "vue";
import { getMonthly, getOverview } from "../api/dashboard";

const overview = ref(null);
const monthly = ref(null);
const loading = ref(true);
const monthlyLoading = ref(false);

const now = new Date();
const selectedYear = ref(now.getFullYear());
const selectedMonth = ref(now.getMonth() + 1);

const monthNames = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

function peso(amount) {
  return `₱${amount.toFixed(2)}`;
}

async function loadOverview() {
  loading.value = true;
  overview.value = await getOverview();
  loading.value = false;
}

async function loadMonthly() {
  monthlyLoading.value = true;
  monthly.value = await getMonthly(selectedYear.value, selectedMonth.value);
  monthlyLoading.value = false;
}

onMounted(async () => {
  await loadOverview();
  await loadMonthly();
});
</script>

<template>
  <div>
    <div class="page-header">
      <div>
        <h1>Dashboard</h1>
        <p class="page-subtitle">{{ overview ? new Date(overview.date).toLocaleDateString(undefined, { weekday: "long", month: "long", day: "numeric" }) : "" }}</p>
      </div>
    </div>

    <p v-if="loading" class="state-message">Loading dashboard...</p>

    <template v-else-if="overview">
      <div class="stat-row">
        <div class="card stat-card">
          <span class="stat-label">Today's sales</span>
          <span class="stat-value">{{ peso(overview.total_sales) }}</span>
        </div>
        <div class="card stat-card">
          <span class="stat-label">Today's expenses</span>
          <span class="stat-value">{{ peso(overview.total_expenses) }}</span>
        </div>
        <div class="card stat-card" :class="overview.total_profit >= 0 ? 'stat-positive' : 'stat-negative'">
          <span class="stat-label">Today's profit</span>
          <span class="stat-value">{{ peso(overview.total_profit) }}</span>
        </div>
        <div class="card stat-card">
          <span class="stat-label">Branches / Staff</span>
          <span class="stat-value">{{ overview.branch_count }} / {{ overview.staff_count }}</span>
        </div>
      </div>

      <div class="card table-card">
        <h2 class="card-title">Per-branch — today</h2>
        <table v-if="overview.branches.length">
          <thead>
            <tr>
              <th>Branch</th>
              <th>Sales</th>
              <th>Expenses</th>
              <th>Profit</th>
              <th>Stock</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="b in overview.branches" :key="b.branch_id">
              <td class="primary-cell">{{ b.branch_name }}</td>
              <td>{{ peso(b.total_sales) }}</td>
              <td>{{ peso(b.total_expenses) }}</td>
              <td :class="b.profit >= 0 ? 'profit-positive' : 'profit-negative'">{{ peso(b.profit) }}</td>
              <td>
                <span v-if="b.has_shortfall" class="badge inactive">Shortfall</span>
                <span v-else class="badge active">OK</span>
              </td>
            </tr>
          </tbody>
        </table>
        <p v-else class="empty-hint">No branches yet.</p>
      </div>

      <div class="card table-card">
        <div class="monthly-header">
          <h2 class="card-title">Monthly rollup</h2>
          <div class="month-picker">
            <select v-model.number="selectedMonth" @change="loadMonthly">
              <option v-for="(name, i) in monthNames" :key="name" :value="i + 1">{{ name }}</option>
            </select>
            <input v-model.number="selectedYear" type="number" @change="loadMonthly" />
          </div>
        </div>

        <p v-if="monthlyLoading" class="state-message">Loading...</p>
        <template v-else-if="monthly">
          <table v-if="monthly.branches.length">
            <thead>
              <tr>
                <th>Branch</th>
                <th>Sales</th>
                <th>Expenses</th>
                <th>Profit</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="b in monthly.branches" :key="b.branch_id">
                <td class="primary-cell">{{ b.branch_name }}</td>
                <td>{{ peso(b.total_sales) }}</td>
                <td>{{ peso(b.total_expenses) }}</td>
                <td :class="b.profit >= 0 ? 'profit-positive' : 'profit-negative'">{{ peso(b.profit) }}</td>
              </tr>
            </tbody>
            <tfoot>
              <tr>
                <td class="primary-cell">All branches</td>
                <td>{{ peso(monthly.total_sales) }}</td>
                <td>{{ peso(monthly.total_expenses) }}</td>
                <td :class="monthly.total_profit >= 0 ? 'profit-positive' : 'profit-negative'">{{ peso(monthly.total_profit) }}</td>
              </tr>
            </tfoot>
          </table>
          <p v-else class="empty-hint">No branches yet.</p>
        </template>
      </div>
    </template>
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

.state-message {
  padding: 2rem 1.5rem;
  text-align: center;
  color: var(--color-text-muted);
}

.stat-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.stat-card {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.stat-label {
  font-size: 0.85rem;
  color: var(--color-text-muted);
}

.stat-value {
  font-size: 1.4rem;
  font-weight: 700;
  color: var(--color-primary-dark);
}

.stat-positive .stat-value {
  color: var(--color-success);
}

.stat-negative .stat-value {
  color: var(--color-danger);
}

.card {
  margin-bottom: 1.5rem;
}

.table-card {
  padding: 1.5rem;
}

.card-title {
  font-size: 1.05rem;
  margin-bottom: 1rem;
}

.primary-cell {
  font-weight: 600;
  color: var(--color-primary-dark);
}

.profit-positive {
  color: var(--color-success);
  font-weight: 600;
}

.profit-negative {
  color: var(--color-danger);
  font-weight: 600;
}

.empty-hint {
  color: var(--color-text-muted);
  font-size: 0.9rem;
}

.monthly-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1rem;
}

.monthly-header .card-title {
  margin-bottom: 0;
}

.month-picker {
  display: flex;
  gap: 0.5rem;
}

.month-picker input {
  width: 90px;
}

tfoot td {
  border-top: 2px solid var(--color-border);
  border-bottom: none;
  font-weight: 700;
}

@media (max-width: 860px) {
  .stat-row {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 500px) {
  .stat-row {
    grid-template-columns: 1fr;
  }

  .monthly-header {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
