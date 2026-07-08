<script setup>
import { computed, onMounted, ref } from "vue";
import { listBranches } from "../api/branches";
import { ApiError } from "../api/client";
import { listStockItems } from "../api/stockItems";
import { listStockDeliveries } from "../api/stockDeliveries";
import Icon from "../components/Icon.vue";
import LoadingState from "../components/LoadingState.vue";
import { toLocalISO } from "../utils/date";

const RETENTION_DAYS = 3;

function toDateStr(d) {
  return toLocalISO(d);
}

const dayList = Array.from({ length: RETENTION_DAYS }, (_, i) => {
  const dateStr = toDateStr(new Date(Date.now() - i * 24 * 60 * 60 * 1000));
  let label;
  if (i === 0) label = "Today";
  else if (i === 1) label = "1 day ago";
  else label = `${i} days ago`;
  return { value: dateStr, label };
});

const branches = ref([]);
const stockItems = ref([]);
const needsByDay = ref({});
const loading = ref(true);
const error = ref("");

function branchName(id) {
  return branches.value.find((b) => b.id === id)?.name || "—";
}

function itemName(id) {
  return stockItems.value.find((i) => i.id === id)?.name || "—";
}

function groupByBranch(needs) {
  const groups = new Map();
  for (const n of needs) {
    if (!groups.has(n.branch_id)) groups.set(n.branch_id, []);
    groups.get(n.branch_id).push(n);
  }
  return [...groups.entries()]
    .map(([branchId, items]) => ({ branchId, name: branchName(branchId), items }))
    .sort((a, b) => a.name.localeCompare(b.name));
}

const dayCounts = computed(() =>
  dayList.map((day) => ({ ...day, count: (needsByDay.value[day.value] || []).length }))
);

const daySections = computed(() =>
  dayList
    .map((day, i) => ({
      ...day,
      isOldest: i === dayList.length - 1,
      groups: groupByBranch(needsByDay.value[day.value] || []),
    }))
    .filter((day) => day.groups.length)
);

const totalNeeds = computed(() =>
  Object.values(needsByDay.value).reduce((sum, list) => sum + list.length, 0)
);

async function refresh() {
  loading.value = true;
  error.value = "";
  try {
    const results = await Promise.all(
      dayList.map((day) => listStockDeliveries({ date: day.value, is_short: true }))
    );
    needsByDay.value = Object.fromEntries(dayList.map((day, i) => [day.value, results[i]]));
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
</script>

<template>
  <div class="page-header">
    <div>
      <h1>Needs</h1>
      <p class="page-subtitle">Items flagged "Need Deliver" by staff, per branch.</p>
    </div>
  </div>

  <div class="summary-strip">
    <div class="summary-total">
      <span class="summary-total-value">{{ totalNeeds }}</span>
      <span class="summary-total-label">need{{ totalNeeds === 1 ? "s" : "" }} delivery</span>
    </div>
    <div class="summary-pills">
      <span v-for="day in dayCounts" :key="day.value" class="summary-pill" :class="{ dim: !day.count }">
        {{ day.label }}
        <strong>{{ day.count }}</strong>
      </span>
    </div>
    <p class="retention-note">
      <Icon name="clock" :size="12" />
      Flags auto-clear after {{ RETENTION_DAYS }} days
    </p>
  </div>

  <p v-if="error" class="error-message top-error">{{ error }}</p>
  <LoadingState v-if="loading" label="Loading needs..." />

  <template v-else>
    <div v-if="!daySections.length" class="card state-card">
      <div class="empty-state">
        <Icon name="check" :size="28" class="empty-icon" />
        <p>No branch needs a delivery right now.</p>
      </div>
    </div>

    <div v-else class="day-sections">
      <section v-for="day in daySections" :key="day.value" class="day-section">
        <div class="day-heading">
          <span class="day-dot" :class="{ today: day.value === dayList[0].value }"></span>
          <h2 class="day-label">{{ day.label }}</h2>
          <span v-if="day.isOldest" class="expiring-tag">
            <Icon name="clock" :size="11" />
            Expiring soon
          </span>
        </div>

        <div class="needs-list">
          <section v-for="group in day.groups" :key="group.branchId" class="card branch-card">
            <div class="branch-card-header">
              <h3 class="card-title branch-title">
                <Icon name="map-pin" :size="14" />
                {{ group.name }}
              </h3>
              <span class="count-chip"><Icon name="count" :size="14" /> {{ group.items.length }} needs delivery</span>
            </div>

            <ul class="need-items">
              <li v-for="n in group.items" :key="n.id" class="need-item" :class="{ delivered: n.is_delivered }">
                <Icon :name="n.is_delivered ? 'check' : 'alert'" :size="13" class="need-icon" />
                <span class="item-name">{{ itemName(n.item_id) }}</span>
                <span class="delivered-badge" :class="{ done: n.is_delivered }">
                  {{ n.is_delivered ? "Delivered" : "Pending" }}
                </span>
              </li>
            </ul>
          </section>
        </div>
      </section>
    </div>
  </template>
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

.summary-strip {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  flex-wrap: wrap;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  padding: 1rem 1.25rem;
  margin-bottom: 1.75rem;
}

.summary-total {
  display: flex;
  align-items: baseline;
  gap: 0.4rem;
  flex-shrink: 0;
}

.summary-total-value {
  font-family: "SFMono-Regular", Consolas, monospace;
  font-size: 1.6rem;
  font-weight: 700;
  color: var(--color-text);
}

.summary-total-label {
  font-size: 0.8rem;
  color: var(--color-text-muted);
  font-weight: 600;
}

.summary-pills {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.summary-pill {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: 999px;
  padding: 0.3rem 0.75rem;
  font-size: 0.78rem;
  color: var(--color-text-muted);
  font-weight: 600;
}

.summary-pill strong {
  color: var(--color-primary);
  font-family: "SFMono-Regular", Consolas, monospace;
}

.summary-pill.dim strong {
  color: var(--color-text-muted);
}

.retention-note {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  color: var(--color-text-muted);
  font-size: 0.78rem;
  margin: 0 0 0 auto;
  white-space: nowrap;
}

.day-sections {
  display: flex;
  flex-direction: column;
  gap: 1.75rem;
}

.day-section {
  padding-top: 1.5rem;
  border-top: 1px solid var(--color-border);
}

.day-section:first-child {
  padding-top: 0;
  border-top: none;
}

.day-heading {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  margin: 0 0 1rem;
}

.day-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-text-muted);
  flex-shrink: 0;
}

.day-dot.today {
  background: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-soft);
}

.day-label {
  font-size: 0.78rem;
  font-weight: 700;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin: 0;
}

.expiring-tag {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  background: var(--color-danger-soft, rgba(255, 45, 77, 0.12));
  color: var(--color-danger);
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: none;
  letter-spacing: normal;
  padding: 0.2rem 0.55rem;
  border-radius: 999px;
}

.state-card {
  padding: 0;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.6rem;
  padding: 3rem 1.5rem;
  text-align: center;
  color: var(--color-text-muted);
}

.empty-icon {
  color: var(--color-success, #2e7d32);
}

.empty-state p {
  margin: 0;
}

.needs-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1rem;
  align-items: start;
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
}

.need-item {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  padding: 0.6rem 0.1rem;
  border-bottom: 1px solid var(--color-border);
  transition: padding-left 0.15s ease;
}

.need-item:last-child {
  border-bottom: none;
}

.need-item:hover {
  padding-left: 0.4rem;
}

.need-item.delivered {
  opacity: 0.65;
}

.need-icon {
  flex-shrink: 0;
  color: var(--color-danger);
}

.need-item.delivered .need-icon {
  color: var(--color-success, #2e7d32);
}

.item-name {
  flex: 1;
  min-width: 0;
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--color-text);
  word-break: break-word;
}

.need-item.delivered .item-name {
  text-decoration: line-through;
}

.delivered-badge {
  flex-shrink: 0;
  font-size: 0.68rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--color-danger);
  background: var(--color-danger-soft, rgba(255, 45, 77, 0.12));
  padding: 0.2rem 0.5rem;
  border-radius: 999px;
}

.delivered-badge.done {
  color: var(--color-success, #2e7d32);
  background: rgba(46, 204, 143, 0.12);
}

@media (max-width: 640px) {
  .needs-list {
    grid-template-columns: 1fr;
  }

  .summary-strip {
    flex-direction: column;
    align-items: flex-start;
  }

  .retention-note {
    margin-left: 0;
  }
}
</style>
