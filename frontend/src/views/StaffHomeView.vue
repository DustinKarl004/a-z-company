<script setup>
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";
import { ApiError } from "../api/client";
import { listStockItems } from "../api/stockItems";
import { createStockDelivery, listStockDeliveries } from "../api/stockDeliveries";
import { createStockCount, listStockCounts } from "../api/stockCounts";
import { createSale, listSales } from "../api/sales";

const auth = useAuthStore();
const router = useRouter();

const today = new Date().toISOString().slice(0, 10);
const todayLabel = new Date().toLocaleDateString(undefined, {
  weekday: "long",
  month: "long",
  day: "numeric",
});

const stockItems = ref([]);
const deliveries = ref([]);
const counts = ref([]);
const sales = ref([]);
const loading = ref(true);
const error = ref("");

const deliveryForm = ref({ itemId: "", quantityDelivered: "", isShort: false });
const countForm = ref({ itemId: "", quantityRemaining: "" });
const saleForm = ref({ itemId: "", quantitySold: "", amount: "" });

const submitting = ref({ delivery: false, count: false, sale: false });

function itemName(id) {
  return stockItems.value.find((i) => i.id === id)?.name || "—";
}

function itemUnit(id) {
  return stockItems.value.find((i) => i.id === id)?.unit || "";
}

async function refresh() {
  loading.value = true;
  [stockItems.value, deliveries.value, counts.value, sales.value] = await Promise.all([
    listStockItems(),
    listStockDeliveries({ date: today }),
    listStockCounts({ date: today }),
    listSales({ date: today }),
  ]);
  loading.value = false;
}

async function submitDelivery() {
  error.value = "";
  submitting.value.delivery = true;
  try {
    await createStockDelivery({
      itemId: deliveryForm.value.itemId,
      quantityDelivered: Number(deliveryForm.value.quantityDelivered),
      isShort: deliveryForm.value.isShort,
    });
    deliveryForm.value = { itemId: "", quantityDelivered: "", isShort: false };
    await refresh();
  } catch (e) {
    error.value = e instanceof ApiError ? e.detail || "Could not log delivery" : "Could not log delivery";
  } finally {
    submitting.value.delivery = false;
  }
}

async function submitCount() {
  error.value = "";
  submitting.value.count = true;
  try {
    await createStockCount({
      itemId: countForm.value.itemId,
      quantityRemaining: Number(countForm.value.quantityRemaining),
    });
    countForm.value = { itemId: "", quantityRemaining: "" };
    await refresh();
  } catch (e) {
    error.value = e instanceof ApiError ? e.detail || "Could not log count" : "Could not log count";
  } finally {
    submitting.value.count = false;
  }
}

async function submitSale() {
  error.value = "";
  submitting.value.sale = true;
  try {
    await createSale({
      itemId: saleForm.value.itemId,
      quantitySold: Number(saleForm.value.quantitySold),
      amount: Number(saleForm.value.amount),
    });
    saleForm.value = { itemId: "", quantitySold: "", amount: "" };
    await refresh();
  } catch (e) {
    error.value = e instanceof ApiError ? e.detail || "Could not log sale" : "Could not log sale";
  } finally {
    submitting.value.sale = false;
  }
}

const totalSalesToday = computed(() => sales.value.reduce((sum, s) => sum + s.amount, 0));

function onLogout() {
  auth.logout();
  router.push({ name: "login" });
}

onMounted(refresh);
</script>

<template>
  <div class="staff-shell">
    <header class="staff-nav">
      <div class="nav-inner">
        <div class="brand">
          <img src="/logo.svg" alt="" class="brand-logo" />
          <span>Z.A. Company</span>
        </div>
        <button class="logout-btn" @click="onLogout">Log out</button>
      </div>
    </header>

    <main class="staff-content">
      <div class="page-header">
        <h1>Today's entries</h1>
        <p class="page-subtitle">{{ todayLabel }} — you can edit anything logged today until midnight.</p>
      </div>

      <p v-if="error" class="error-message top-error">{{ error }}</p>
      <p v-if="loading" class="state-message">Loading...</p>

      <template v-else>
        <section class="card entry-section">
          <h2 class="card-title">Stock delivery</h2>
          <form class="entry-form" @submit.prevent="submitDelivery">
            <select v-model="deliveryForm.itemId" required>
              <option disabled value="">Select an item</option>
              <option v-for="i in stockItems" :key="i.id" :value="i.id">{{ i.name }} ({{ i.unit }})</option>
            </select>
            <input v-model="deliveryForm.quantityDelivered" type="number" min="0" step="any" placeholder="Quantity delivered" required />
            <label class="checkbox-field">
              <input v-model="deliveryForm.isShort" type="checkbox" />
              Delivery was short / not enough
            </label>
            <button type="submit" :disabled="submitting.delivery">
              {{ submitting.delivery ? "Saving..." : "Log delivery" }}
            </button>
          </form>

          <ul class="entry-list" v-if="deliveries.length">
            <li v-for="d in deliveries" :key="d.id">
              <span>{{ itemName(d.item_id) }}</span>
              <span>{{ d.quantity_delivered }} {{ itemUnit(d.item_id) }}</span>
              <span v-if="d.is_short" class="badge inactive">Short</span>
            </li>
          </ul>
          <p v-else class="empty-hint">No deliveries logged yet today.</p>
        </section>

        <section class="card entry-section">
          <h2 class="card-title">End-of-day stock count</h2>
          <form class="entry-form" @submit.prevent="submitCount">
            <select v-model="countForm.itemId" required>
              <option disabled value="">Select an item</option>
              <option v-for="i in stockItems" :key="i.id" :value="i.id">{{ i.name }} ({{ i.unit }})</option>
            </select>
            <input v-model="countForm.quantityRemaining" type="number" min="0" step="any" placeholder="Quantity remaining" required />
            <button type="submit" :disabled="submitting.count">
              {{ submitting.count ? "Saving..." : "Log count" }}
            </button>
          </form>

          <ul class="entry-list" v-if="counts.length">
            <li v-for="c in counts" :key="c.id">
              <span>{{ itemName(c.item_id) }}</span>
              <span>{{ c.quantity_remaining }} {{ itemUnit(c.item_id) }}</span>
            </li>
          </ul>
          <p v-else class="empty-hint">No stock count logged yet today.</p>
        </section>

        <section class="card entry-section">
          <h2 class="card-title">Sales</h2>
          <form class="entry-form" @submit.prevent="submitSale">
            <select v-model="saleForm.itemId" required>
              <option disabled value="">Select an item</option>
              <option v-for="i in stockItems" :key="i.id" :value="i.id">{{ i.name }} ({{ i.unit }})</option>
            </select>
            <input v-model="saleForm.quantitySold" type="number" min="0" step="any" placeholder="Quantity sold" required />
            <input v-model="saleForm.amount" type="number" min="0" step="any" placeholder="Amount (₱)" required />
            <button type="submit" :disabled="submitting.sale">
              {{ submitting.sale ? "Saving..." : "Log sale" }}
            </button>
          </form>

          <ul class="entry-list" v-if="sales.length">
            <li v-for="s in sales" :key="s.id">
              <span>{{ itemName(s.item_id) }}</span>
              <span>{{ s.quantity_sold }} {{ itemUnit(s.item_id) }} — ₱{{ s.amount.toFixed(2) }}</span>
            </li>
          </ul>
          <p v-else class="empty-hint">No sales logged yet today.</p>
          <p v-if="sales.length" class="sales-total">Total sales today: ₱{{ totalSalesToday.toFixed(2) }}</p>
        </section>
      </template>
    </main>
  </div>
</template>

<style scoped>
.staff-shell {
  min-height: 100vh;
}

.staff-nav {
  background: var(--color-primary-dark);
  border-bottom: 3px solid var(--color-accent);
}

.nav-inner {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.85rem 2rem;
  max-width: 720px;
  margin: 0 auto;
}

.brand {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  font-weight: 700;
  color: #fff;
  margin-right: auto;
}

.brand-logo {
  width: 30px;
  height: 30px;
}

.logout-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.35);
  padding: 0.5rem 1rem;
  font-size: 0.9rem;
  font-weight: 600;
}

.logout-btn:hover {
  background: var(--color-danger);
  border-color: var(--color-danger);
}

.staff-content {
  padding: 2rem 1.5rem;
  max-width: 720px;
  margin: 0 auto;
}

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

.state-message {
  text-align: center;
  color: var(--color-text-muted);
}

.top-error {
  text-align: center;
}

.entry-section {
  margin-bottom: 1.5rem;
}

.card-title {
  font-size: 1.05rem;
  margin-bottom: 1rem;
}

.entry-form {
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  gap: 0.75rem;
  align-items: center;
  margin-bottom: 1.25rem;
}

.entry-form select,
.entry-form input[type="number"] {
  width: 100%;
}

.checkbox-field {
  grid-column: 1 / -1;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
  color: var(--color-text);
  margin: 0;
}

.checkbox-field input {
  width: auto;
}

.entry-form button {
  grid-column: 1 / -1;
  width: fit-content;
}

.entry-list {
  list-style: none;
  margin: 0;
  padding: 0;
  border-top: 1px solid var(--color-border);
}

.entry-list li {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.6rem 0;
  border-bottom: 1px solid var(--color-border);
  font-size: 0.92rem;
}

.entry-list li span:first-child {
  font-weight: 600;
  color: var(--color-primary-dark);
  flex: 1;
}

.empty-hint {
  color: var(--color-text-muted);
  font-size: 0.9rem;
  margin: 0;
}

.sales-total {
  margin: 0.75rem 0 0;
  font-weight: 700;
  color: var(--color-primary-dark);
  text-align: right;
}

@media (max-width: 560px) {
  .entry-form {
    grid-template-columns: 1fr;
  }
}
</style>
