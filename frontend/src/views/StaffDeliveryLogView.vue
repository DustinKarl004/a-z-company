<script setup>
import { computed, onMounted, ref } from "vue";
import { ApiError } from "../api/client";
import { listBranches } from "../api/branches";
import { listStockItems } from "../api/stockItems";
import { listStockDeliveries, updateStockDelivery } from "../api/stockDeliveries";
import Icon from "../components/Icon.vue";
import LoadingState from "../components/LoadingState.vue";

const RETENTION_DAYS = 3;

function toDateStr(d) {
  return d.toISOString().slice(0, 10);
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

const savingIds = ref(new Set());
const groupSaving = ref(new Set());
const actionError = ref("");

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
  dayList.map((day) => ({
    ...day,
    count: (needsByDay.value[day.value] || []).filter((n) => !n.is_delivered).length,
  }))
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

const pendingCount = computed(() =>
  Object.values(needsByDay.value).reduce(
    (sum, list) => sum + list.filter((n) => !n.is_delivered).length,
    0
  )
);

async function refresh() {
  loading.value = true;
  error.value = "";
  try {
    const [branchList, itemList, ...results] = await Promise.all([
      listBranches(),
      listStockItems(),
      ...dayList.map((day) => listStockDeliveries({ date: day.value, is_short: true })),
    ]);
    branches.value = branchList;
    stockItems.value = itemList;
    needsByDay.value = Object.fromEntries(dayList.map((day, i) => [day.value, results[i]]));
  } catch (e) {
    error.value = e instanceof ApiError ? e.detail || "Could not load needs" : "Could not load needs";
  } finally {
    loading.value = false;
  }
}

function groupKey(day, branchId) {
  return `${day}:${branchId}`;
}

function isGroupAllDelivered(group) {
  return group.items.length > 0 && group.items.every((n) => n.is_delivered);
}

async function toggleNeed(need) {
  actionError.value = "";
  savingIds.value.add(need.id);
  try {
    await updateStockDelivery(need.id, { is_delivered: !need.is_delivered });
    await refresh();
  } catch (e) {
    actionError.value = e instanceof ApiError ? e.detail || "Could not update" : "Could not update";
  } finally {
    savingIds.value.delete(need.id);
  }
}

async function toggleGroup(day, group) {
  const key = groupKey(day, group.branchId);
  actionError.value = "";
  const target = !isGroupAllDelivered(group);
  const toUpdate = group.items.filter((n) => n.is_delivered !== target);
  if (!toUpdate.length) return;
  groupSaving.value.add(key);
  try {
    await Promise.all(toUpdate.map((n) => updateStockDelivery(n.id, { is_delivered: target })));
    await refresh();
  } catch (e) {
    actionError.value = e instanceof ApiError ? e.detail || "Could not update" : "Could not update";
  } finally {
    groupSaving.value.delete(key);
  }
}

onMounted(refresh);
</script>

<template>
  <div class="page-header">
    <div>
      <h1>Delivery needs</h1>
      <p class="page-subtitle">Items flagged "Need Deliver" by staff. Check off once delivered.</p>
    </div>
  </div>

  <div class="summary-strip">
    <div class="summary-total">
      <span class="summary-total-value">{{ pendingCount }}</span>
      <span class="summary-total-label">pending delivery</span>
    </div>
    <div class="summary-pills">
      <span v-for="day in dayCounts" :key="day.value" class="summary-pill" :class="{ dim: !day.count }">
        {{ day.label }}
        <strong>{{ day.count }}</strong>
      </span>
    </div>
  </div>

  <p v-if="error" class="error-message top-error">{{ error }}</p>
  <p v-if="actionError" class="error-message top-error">{{ actionError }}</p>
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
              <span class="count-chip">
                <Icon name="count" :size="14" /> {{ group.items.filter((n) => !n.is_delivered).length }} pending
              </span>
            </div>

            <label class="check-all">
              <input
                type="checkbox"
                :checked="isGroupAllDelivered(group)"
                :disabled="groupSaving.has(groupKey(day.value, group.branchId))"
                @change="toggleGroup(day.value, group)"
              />
              Check all
            </label>

            <ul class="need-items">
              <li
                v-for="n in group.items"
                :key="n.id"
                class="need-item"
                :class="{ delivered: n.is_delivered }"
              >
                <label class="need-checkbox">
                  <input
                    type="checkbox"
                    :checked="n.is_delivered"
                    :disabled="savingIds.has(n.id)"
                    @change="toggleNeed(n)"
                  />
                  <span class="item-name">{{ itemName(n.item_id) }}</span>
                </label>
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

.page-header h1 {
  font-size: 1.5rem;
  margin-bottom: 0.35rem;
}

.page-subtitle {
  color: var(--color-text-muted);
  margin: 0;
}

.top-error {
  text-align: center;
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

.count-chip {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  background: var(--color-primary-soft);
  color: var(--color-primary);
  font-size: 0.78rem;
  font-weight: 600;
  padding: 0.25rem 0.7rem;
  border-radius: 999px;
  white-space: nowrap;
}

.check-all {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--color-text-muted);
  padding-bottom: 0.6rem;
  margin-bottom: 0.4rem;
  border-bottom: 1px dashed var(--color-border);
  cursor: pointer;
}

.check-all input {
  width: 16px;
  height: 16px;
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
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.6rem 0.1rem;
  border-bottom: 1px solid var(--color-border);
  transition: padding-left 0.15s ease;
}

.need-item:last-child {
  border-bottom: none;
}

.need-item.delivered {
  opacity: 0.65;
}

.need-checkbox {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  cursor: pointer;
  min-width: 0;
}

.need-checkbox input {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
}

.item-name {
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
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--color-danger);
  background: var(--color-danger-soft, rgba(255, 45, 77, 0.12));
  padding: 0.2rem 0.55rem;
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
}
</style>
