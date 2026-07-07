<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import { ApiError } from "../api/client";
import { listStockItems } from "../api/stockItems";
import { createStockDelivery, listStockDeliveries, updateStockDelivery } from "../api/stockDeliveries";
import { createStockCount, listStockCounts, updateStockCount } from "../api/stockCounts";
import { createTotalSale, listSales, updateTotalSale } from "../api/sales";
import { useAuthStore } from "../stores/auth";
import Icon from "../components/Icon.vue";

const auth = useAuthStore();

const today = new Date().toISOString().slice(0, 10);
const yesterday = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString().slice(0, 10);
const todayLabel = new Date().toLocaleDateString(undefined, {
  weekday: "long",
  month: "long",
  day: "numeric",
});

const categoryOrder = [
  "Meats",
  "Side Dishes / Banchan",
  "Rice & Staples",
  "Sauces & Condiments",
  "Drinks",
  "Consumables/Supplies",
];

function categoryRank(category) {
  if (!category) return categoryOrder.length;
  const idx = categoryOrder.findIndex((c) => c.toLowerCase() === category.toLowerCase());
  return idx === -1 ? categoryOrder.length : idx;
}

const stockItems = ref([]);
const loading = ref(true);
const error = ref("");
const search = ref("");

const totalSale = reactive({ id: null, amount: "", saving: false, saved: false, error: "", editing: false });

function peso(amount) {
  return `₱${amount.toLocaleString("en-PH", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

// itemId -> row state
const rows = reactive({});

function rowFor(itemId) {
  if (!rows[itemId]) {
    rows[itemId] = {
      opening: null,
      delivery: "",
      deliveryId: null,
      isShort: false,
      deliverySaving: false,
      deliverySaved: false,
      deliveryError: "",
      closing: "",
      closingId: null,
      closingSaving: false,
      closingSaved: false,
      closingError: "",
    };
  }
  return rows[itemId];
}

const sortedItems = computed(() =>
  stockItems.value
    .slice()
    .sort((a, b) => {
      const rankDiff = categoryRank(a.category) - categoryRank(b.category);
      return rankDiff !== 0 ? rankDiff : a.name.localeCompare(b.name);
    })
);

const filteredItems = computed(() => {
  const term = search.value.trim().toLowerCase();
  if (!term) return sortedItems.value;
  return sortedItems.value.filter((i) => i.name.toLowerCase().includes(term));
});

const loggedTodayCount = computed(
  () => Object.values(rows).filter((r) => r.deliveryId || r.closingId).length
);

function kilogramUsed(itemId) {
  const r = rows[itemId];
  if (!r) return null;
  if (r.delivery === "" || r.closing === "") return null;
  const opening = Number(r.opening) || 0;
  const delivery = Number(r.delivery);
  const closing = Number(r.closing);
  if (Number.isNaN(delivery) || Number.isNaN(closing)) return null;
  return opening + delivery - closing;
}

function isComplete(itemId) {
  return kilogramUsed(itemId) !== null;
}

async function refresh() {
  loading.value = true;
  error.value = "";
  const [items, todayDeliveries, todayCounts, openingCounts, todaySales] = await Promise.all([
    listStockItems(),
    listStockDeliveries({ date: today }),
    listStockCounts({ date: today }),
    listStockCounts({ date: yesterday }),
    listSales({ date: today }),
  ]);
  stockItems.value = items;

  const openingByItem = new Map(openingCounts.map((c) => [c.item_id, c.quantity_remaining]));

  for (const item of items) {
    const r = rowFor(item.id);
    r.opening = openingByItem.has(item.id) ? openingByItem.get(item.id) : 0;
  }
  for (const d of todayDeliveries) {
    const r = rowFor(d.item_id);
    r.delivery = String(d.quantity_delivered);
    r.deliveryId = d.id;
    r.isShort = d.is_short;
  }
  for (const c of todayCounts) {
    const r = rowFor(c.item_id);
    r.closing = String(c.quantity_remaining);
    r.closingId = c.id;
  }

  const existingTotalSale = todaySales.find((s) => s.item_id === null);
  totalSale.id = existingTotalSale?.id || null;
  totalSale.amount = existingTotalSale ? String(existingTotalSale.amount) : "";

  loading.value = false;
}

function flashSaved(r, field) {
  r[`${field}Saved`] = true;
  setTimeout(() => {
    r[`${field}Saved`] = false;
  }, 1500);
}

async function saveTotalSale() {
  totalSale.error = "";
  if (totalSale.amount === "" || Number.isNaN(Number(totalSale.amount))) return;
  totalSale.saving = true;
  try {
    if (totalSale.id) {
      await updateTotalSale(totalSale.id, Number(totalSale.amount));
    } else {
      const created = await createTotalSale({ date: today, amount: Number(totalSale.amount) });
      totalSale.id = created.id;
    }
    totalSale.editing = false;
    totalSale.saved = true;
    setTimeout(() => {
      totalSale.saved = false;
    }, 1500);
  } catch (e) {
    totalSale.error = e instanceof ApiError ? e.detail || "Could not save" : "Could not save";
  } finally {
    totalSale.saving = false;
  }
}

async function saveDelivery(itemId) {
  const r = rowFor(itemId);
  r.deliveryError = "";
  if (r.delivery === "" || Number.isNaN(Number(r.delivery))) return;
  r.deliverySaving = true;
  try {
    if (r.deliveryId) {
      await updateStockDelivery(r.deliveryId, {
        quantity_delivered: Number(r.delivery),
        is_short: r.isShort,
      });
    } else {
      const created = await createStockDelivery({
        itemId,
        quantityDelivered: Number(r.delivery),
        isShort: r.isShort,
      });
      r.deliveryId = created.id;
    }
    flashSaved(r, "delivery");
  } catch (e) {
    r.deliveryError = e instanceof ApiError ? e.detail || "Could not save" : "Could not save";
  } finally {
    r.deliverySaving = false;
  }
}

async function saveClosing(itemId) {
  const r = rowFor(itemId);
  r.closingError = "";
  if (r.closing === "" || Number.isNaN(Number(r.closing))) return;
  r.closingSaving = true;
  try {
    if (r.closingId) {
      await updateStockCount(r.closingId, { quantity_remaining: Number(r.closing) });
    } else {
      const created = await createStockCount({ itemId, quantityRemaining: Number(r.closing) });
      r.closingId = created.id;
    }
    flashSaved(r, "closing");
  } catch (e) {
    r.closingError = e instanceof ApiError ? e.detail || "Could not save" : "Could not save";
  } finally {
    r.closingSaving = false;
  }
}

function useOpeningAsClosing(itemId) {
  const r = rowFor(itemId);
  r.closing = String(r.opening ?? 0);
  saveClosing(itemId);
}

onMounted(refresh);
</script>

<template>
  <div class="page-header top-header">
    <div>
      <h1>Daily stock</h1>
      <p class="page-subtitle">
        {{ todayLabel }}
        <span v-if="auth.branchName" class="branch-chip">{{ auth.branchName }}</span>
      </p>
    </div>
    <span v-if="!loading" class="count-chip"><Icon name="count" :size="14" /> {{ loggedTodayCount }} logged today</span>
  </div>

  <p v-if="error" class="error-message top-error">{{ error }}</p>
  <p v-if="loading" class="state-message">Loading...</p>

  <template v-else>
    <div class="card total-sale-card">
      <div class="total-sale-row">
        <div class="total-sale-group">
          <span class="total-sale-label">Total Daily Sales</span>

          <div v-if="!totalSale.id || totalSale.editing" class="total-sale-input-row">
            <span class="unit-label">₱</span>
            <input
              type="number"
              inputmode="decimal"
              min="0"
              step="any"
              class="value-input"
              :class="{ saved: totalSale.saved }"
              placeholder="0"
              v-model="totalSale.amount"
              @blur="saveTotalSale"
              @keyup.enter="($event.target).blur()"
            />
            <span v-if="totalSale.saving" class="save-status">Saving...</span>
          </div>
          <div v-else class="total-sale-input-row">
            <span class="total-sale-value">{{ peso(Number(totalSale.amount)) }}</span>
            <button
              type="button"
              class="edit-bill-btn"
              title="Edit total daily sales"
              aria-label="Edit total daily sales"
              @click="totalSale.editing = true"
            >
              <Icon name="edit" :size="12" />
            </button>
          </div>
        </div>

        <div v-if="stockItems.length" class="search-input">
          <Icon name="search" :size="15" class="search-icon" />
          <input v-model="search" placeholder="Search items" />
          <button v-if="search" type="button" class="search-clear" aria-label="Clear search" @click="search = ''">
            <Icon name="x" :size="13" />
          </button>
        </div>
      </div>
      <p v-if="totalSale.error" class="row-error">{{ totalSale.error }}</p>
    </div>

    <div v-if="!filteredItems.length" class="card state-card">
      <div class="empty-state">
        <p>No items match your search.</p>
      </div>
    </div>

    <div v-else class="stock-list">
      <div v-for="item in filteredItems" :key="item.id" class="stock-row">
        <div class="row-main">
          <span class="item-name">{{ item.name }}</span>
          <span v-if="item.category" class="category-chip">{{ item.category }}</span>
        </div>

        <div class="row-values">
          <div class="value-group">
            <span class="value-label">Opening</span>
            <span class="value-text muted">{{ rowFor(item.id).opening }}</span>
          </div>

          <div class="value-group">
            <span class="value-label">Delivery</span>
            <input
              type="number"
              inputmode="decimal"
              min="0"
              step="any"
              class="value-input"
              :class="{ saved: rowFor(item.id).deliverySaved }"
              placeholder="0"
              v-model="rowFor(item.id).delivery"
              @blur="saveDelivery(item.id)"
              @keyup.enter="($event.target).blur()"
            />
          </div>

          <div class="value-group">
            <span class="value-label">Closing</span>
            <div class="closing-input-row">
              <input
                type="number"
                inputmode="decimal"
                min="0"
                step="any"
                class="value-input"
                :class="{ saved: rowFor(item.id).closingSaved }"
                placeholder="0"
                v-model="rowFor(item.id).closing"
                @blur="saveClosing(item.id)"
                @keyup.enter="($event.target).blur()"
              />
              <button
                type="button"
                class="same-as-opening-btn"
                title="Same as opening"
                aria-label="Set closing same as opening"
                @click="useOpeningAsClosing(item.id)"
              >
                <Icon name="equal" :size="14" />
              </button>
            </div>
          </div>

          <div class="value-group result">
            <span class="value-label">Used</span>
            <span
              v-if="isComplete(item.id)"
              class="value-text"
              :class="{ negative: kilogramUsed(item.id) < 0, positive: kilogramUsed(item.id) > 0 }"
            >{{ kilogramUsed(item.id) }}</span>
            <span v-else class="value-text muted">—</span>
          </div>
        </div>

        <label class="short-toggle">
          <input type="checkbox" v-model="rowFor(item.id).isShort" @change="saveDelivery(item.id)" />
          Need Deliver
        </label>

        <p v-if="rowFor(item.id).deliveryError" class="row-error">{{ rowFor(item.id).deliveryError }}</p>
        <p v-if="rowFor(item.id).closingError" class="row-error">{{ rowFor(item.id).closingError }}</p>
      </div>
    </div>
  </template>
</template>

<style scoped>
.top-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1.75rem;
}

.branch-chip {
  display: inline-block;
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  color: var(--color-primary);
  background: var(--color-primary-soft);
  border: 1px solid var(--color-primary);
  border-radius: 999px;
  padding: 0.2rem 0.6rem;
  margin-left: 0.5rem;
}

.page-header h1 {
  font-size: 1.5rem;
  margin-bottom: 0.35rem;
}

.page-subtitle {
  color: var(--color-text-muted);
  margin: 0;
}

.state-message {
  text-align: center;
  color: var(--color-text-muted);
}

.top-error {
  text-align: center;
}

.total-sale-card {
  padding: 0.85rem 1rem;
  margin-bottom: 1rem;
}

.total-sale-row {
  display: flex;
  align-items: center;
  gap: 1.25rem;
  flex-wrap: wrap;
}

.total-sale-group {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-shrink: 0;
}

.total-sale-label {
  font-weight: 700;
  color: var(--color-text);
}

.total-sale-input-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.total-sale-value {
  font-weight: 700;
  color: var(--color-text);
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

.save-status {
  font-size: 0.8rem;
  color: var(--color-text-muted);
}

.search-input {
  position: relative;
  display: flex;
  align-items: center;
  flex: 1 1 200px;
  min-width: 0;
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

.stock-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.stock-row {
  background: var(--color-surface);
  border-radius: var(--radius);
  border: 1px solid var(--color-border);
  padding: 0.85rem 1rem;
}

.row-main {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.6rem;
}

.item-name {
  font-weight: 600;
  color: var(--color-text);
}

.category-chip {
  flex-shrink: 0;
  background: var(--color-bg);
  color: var(--color-text-muted);
  font-size: 0.72rem;
  font-weight: 600;
  padding: 0.2rem 0.55rem;
  border-radius: 999px;
  border: 1px solid var(--color-border);
}

.row-values {
  display: flex;
  align-items: flex-end;
  gap: 1.25rem;
}

.value-group {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  min-width: 64px;
}

.value-label {
  font-size: 0.7rem;
  color: var(--color-text-muted);
  font-weight: 600;
}

.value-text {
  font-size: 1rem;
  font-weight: 700;
  color: var(--color-text);
  padding: 0.35rem 0;
}

.value-text.muted {
  color: var(--color-text-muted);
  font-weight: 500;
}

.value-input {
  width: 100%;
  font-weight: 600;
  transition: border-color 0.3s;
}

.value-input.saved {
  border-color: var(--color-success, #2e7d32);
}

.closing-input-row {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.same-as-opening-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  padding: 0;
  border-radius: 8px;
  border: 1px solid var(--color-border);
  background: var(--color-bg);
  color: var(--color-text-muted);
}

.same-as-opening-btn:hover {
  border-color: var(--color-text-muted);
}

.value-group.result .value-text {
  color: var(--color-primary);
}

.value-group.result .value-text.positive {
  color: var(--color-success, #2e7d32);
}

.value-group.result .value-text.negative {
  color: var(--color-danger);
}

.short-toggle {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.8rem;
  color: var(--color-text-muted);
  margin: 0.55rem 0 0;
}

.short-toggle input {
  width: 16px;
  height: 16px;
}

.row-error {
  color: var(--color-danger);
  font-size: 0.8rem;
  margin: 0.4rem 0 0;
}

@media (max-width: 520px) {
  .row-values {
    flex-wrap: wrap;
    gap: 0.85rem 1rem;
  }

  .value-group {
    min-width: 40%;
  }

  .total-sale-row {
    flex-direction: column;
    align-items: stretch;
  }

  .total-sale-group {
    justify-content: space-between;
  }

  .search-input {
    flex: 1 1 auto;
  }
}
</style>
