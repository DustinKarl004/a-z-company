<script setup>
import { computed, onMounted, reactive, ref, watch } from "vue";
import * as XLSX from "xlsx-js-style";
import { listBranches } from "../api/branches";
import { ApiError } from "../api/client";
import { createExpense, listExpenses } from "../api/expenses";
import { createTotalSale, listSales, updateTotalSale } from "../api/sales";
import { listStockItems } from "../api/stockItems";
import { createStockCount, listStockCounts, updateStockCount } from "../api/stockCounts";
import { createStockDelivery, listStockDeliveries, updateStockDelivery } from "../api/stockDeliveries";
import CustomSelect from "../components/CustomSelect.vue";
import Icon from "../components/Icon.vue";
import LoadingState from "../components/LoadingState.vue";

const today = new Date().toISOString().slice(0, 10);

const branches = ref([]);
const selectedDate = ref(today);
const selectedBranchId = ref("");

const expenses = ref([]);
const sales = ref([]);
const loading = ref(true);
const error = ref("");

const stockItems = ref([]);
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
const salesRows = reactive({});

function billRowFor(branchId) {
  if (!billRows[branchId]) {
    billRows[branchId] = { id: null, amount: "", saving: false, saved: false, error: "", editing: false };
  }
  return billRows[branchId];
}

function salesRowFor(branchId) {
  if (!salesRows[branchId]) {
    salesRows[branchId] = { id: null, amount: "", saving: false, saved: false, error: "", editing: false };
  }
  return salesRows[branchId];
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

async function saveSales(branchId) {
  const row = salesRowFor(branchId);
  row.error = "";
  if (row.amount === "" || Number.isNaN(Number(row.amount))) return;
  row.saving = true;
  try {
    let result;
    if (row.id) {
      result = await updateTotalSale(row.id, Number(row.amount));
    } else {
      result = await createTotalSale({ branchId, date: selectedDate.value, amount: Number(row.amount) });
    }
    row.id = result.id;
    row.editing = false;
    const idx = sales.value.findIndex((s) => s.branch_id === branchId && s.item_id === null);
    if (idx !== -1) {
      sales.value[idx] = result;
    } else {
      sales.value.push(result);
    }
    flashSaved(row);
  } catch (e) {
    row.error = e instanceof ApiError ? e.detail || "Could not save" : "Could not save";
  } finally {
    row.saving = false;
  }
}

const dateRegex = /^\d{4}-\d{2}-\d{2}$/;

async function refresh() {
  if (!dateRegex.test(selectedDate.value)) return;
  loading.value = true;
  error.value = "";
  const params = { date: selectedDate.value };
  if (selectedBranchId.value) params.branch_id = selectedBranchId.value;
  try {
    [expenses.value, sales.value] = await Promise.all([listExpenses(params), listSales(params)]);
    for (const b of branches.value) {
      const bill = billRowFor(b.id);
      bill.id = null;
      bill.amount = "";
      const salesRow = salesRowFor(b.id);
      salesRow.id = null;
      salesRow.amount = "";
    }
    for (const e of expenses.value) {
      const row = billRowFor(e.branch_id);
      row.id = e.id;
      row.amount = String(e.amount);
    }
    for (const s of sales.value) {
      if (s.item_id !== null) continue;
      const row = salesRowFor(s.branch_id);
      row.id = s.id;
      row.amount = String(s.amount);
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

const stockRows = reactive({});

function stockRowKey(branchId, itemId) {
  return `${branchId}|${itemId}`;
}

function stockRowFor(branchId, itemId) {
  const key = stockRowKey(branchId, itemId);
  if (!stockRows[key]) {
    stockRows[key] = {
      branchId,
      itemId,
      itemName: "—",
      price: 0,
      opening: 0,
      delivery: "",
      deliveryId: null,
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
  return stockRows[key];
}

async function refreshStockExpense() {
  if (!dateRegex.test(selectedDate.value)) return;
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

  for (const key of Object.keys(stockRows)) {
    delete stockRows[key];
  }

  const openingMap = new Map(closingYesterday.map((c) => [`${c.branch_id}|${c.item_id}`, c.quantity_remaining]));
  const deliveryMap = new Map();
  for (const d of deliveriesToday) {
    const key = `${d.branch_id}|${d.item_id}`;
    if (!deliveryMap.has(key)) {
      deliveryMap.set(key, { id: d.id, total: 0 });
    }
    deliveryMap.get(key).total += d.quantity_delivered;
  }
  const closingMap = new Map(closingToday.map((c) => [`${c.branch_id}|${c.item_id}`, c]));

  const relevantBranches = selectedBranchId.value
    ? branches.value.filter((b) => b.id === selectedBranchId.value)
    : branches.value;

  for (const branch of relevantBranches) {
    for (const item of items) {
      const key = stockRowKey(branch.id, item.id);
      const row = stockRowFor(branch.id, item.id);
      row.itemName = item.name;
      row.price = item.price || 0;
      row.opening = openingMap.get(key) || 0;
      const delivery = deliveryMap.get(key);
      row.delivery = delivery ? String(delivery.total) : "";
      row.deliveryId = delivery ? delivery.id : null;
      const closing = closingMap.get(key);
      row.closing = closing ? String(closing.quantity_remaining) : "";
      row.closingId = closing ? closing.id : null;
    }
  }

  stockExpenseLoading.value = false;
}

async function saveStockDelivery(branchId, itemId) {
  const row = stockRowFor(branchId, itemId);
  row.deliveryError = "";
  if (row.delivery === "" || Number.isNaN(Number(row.delivery))) return;
  row.deliverySaving = true;
  try {
    if (row.deliveryId) {
      await updateStockDelivery(row.deliveryId, { quantity_delivered: Number(row.delivery) });
    } else {
      const created = await createStockDelivery({
        branchId,
        itemId,
        quantityDelivered: Number(row.delivery),
        date: selectedDate.value,
      });
      row.deliveryId = created.id;
    }
    row.deliverySaved = true;
    setTimeout(() => {
      row.deliverySaved = false;
    }, 1500);
  } catch (e) {
    row.deliveryError = e instanceof ApiError ? e.detail || "Could not save" : "Could not save";
  } finally {
    row.deliverySaving = false;
  }
}

async function saveStockClosing(branchId, itemId) {
  const row = stockRowFor(branchId, itemId);
  row.closingError = "";
  if (row.closing === "" || Number.isNaN(Number(row.closing))) return;
  row.closingSaving = true;
  try {
    if (row.closingId) {
      await updateStockCount(row.closingId, { quantity_remaining: Number(row.closing) });
    } else {
      const created = await createStockCount({
        branchId,
        itemId,
        quantityRemaining: Number(row.closing),
        date: selectedDate.value,
      });
      row.closingId = created.id;
    }
    row.closingSaved = true;
    setTimeout(() => {
      row.closingSaved = false;
    }, 1500);
  } catch (e) {
    row.closingError = e instanceof ApiError ? e.detail || "Could not save" : "Could not save";
  } finally {
    row.closingSaving = false;
  }
}

function useOpeningAsClosing(branchId, itemId) {
  const row = stockRowFor(branchId, itemId);
  row.closing = String(row.opening ?? 0);
  saveStockClosing(branchId, itemId);
}

const stockExpenseRows = computed(() =>
  Object.values(stockRows).map((row) => {
    const opening = Number(row.opening) || 0;
    const delivery = row.delivery === "" ? 0 : Number(row.delivery) || 0;
    const hasClosing = row.closing !== "" && !Number.isNaN(Number(row.closing));
    const closing = hasClosing ? Number(row.closing) : null;
    const used = hasClosing ? opening + delivery - closing : null;
    const expense = hasClosing ? used * row.price : null;
    return {
      key: stockRowKey(row.branchId, row.itemId),
      branchId: row.branchId,
      itemId: row.itemId,
      itemName: row.itemName,
      opening,
      delivery,
      closing,
      hasClosing,
      price: row.price,
      used,
      expense,
      row,
    };
  })
);

const stockExpenseTotal = computed(() => stockExpenseRows.value.reduce((sum, r) => sum + (r.expense || 0), 0));
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
    return ((av ?? 0) - (bv ?? 0)) * dir;
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
    total: rows.reduce((sum, r) => sum + (r.expense || 0), 0),
  }));
});


const exportBranchSummaries = computed(() => {
  const relevantBranches = selectedBranchId.value
    ? branches.value.filter((b) => b.id === selectedBranchId.value)
    : branches.value;
  return relevantBranches.map((b) => {
    const sales = Number(salesRowFor(b.id).amount) || 0;
    const bills = Number(billRowFor(b.id).amount) || 0;
    const stockExpense = stockExpenseByBranch.value.find((g) => g.branchId === b.id)?.total || 0;
    const totalExpense = bills + stockExpense;
    return {
      branchName: b.name,
      sales,
      bills,
      stockExpense,
      totalExpense,
      profit: sales - totalExpense,
    };
  });
});

const EXPORT_COLS = 7;

const borderThin = { style: "thin", color: { rgb: "FF999999" } };
const allBorders = { top: borderThin, bottom: borderThin, left: borderThin, right: borderThin };

const titleStyle = {
  font: { bold: true, sz: 13 },
  fill: { fgColor: { rgb: "FFFFA733" } },
  alignment: { vertical: "center", horizontal: "left" },
  border: allBorders,
};
const titleTotalStyle = {
  font: { bold: true, sz: 13 },
  fill: { fgColor: { rgb: "FFFFA733" } },
  alignment: { vertical: "center", horizontal: "right" },
  border: allBorders,
};
const headerStyle = {
  font: { bold: true, color: { rgb: "FFCC0000" } },
  fill: { fgColor: { rgb: "FFFFF200" } },
  alignment: { vertical: "center", horizontal: "center" },
  border: allBorders,
};
const cellStyle = { border: allBorders, alignment: { vertical: "center" } };
const cellStyleRight = { border: allBorders, alignment: { vertical: "center", horizontal: "right" } };
const totalLabelStyle = {
  font: { bold: true },
  fill: { fgColor: { rgb: "FFFFF200" } },
  border: allBorders,
  alignment: { vertical: "center" },
};
const totalValueStyle = {
  font: { bold: true },
  fill: { fgColor: { rgb: "FFFFF200" } },
  border: allBorders,
  alignment: { vertical: "center", horizontal: "right" },
};

const RED = "FFFF4D4D";
const GREEN = "FF1B7A43";

function cellStyleColored(color) {
  return { border: allBorders, alignment: { vertical: "center", horizontal: "right" }, font: { color: { rgb: color } } };
}
function totalValueStyleColored(color) {
  return { ...totalValueStyle, font: { ...totalValueStyle.font, color: { rgb: color } } };
}

function cell(v, style) {
  return { v, s: style, t: typeof v === "number" ? "n" : "s" };
}

function setCell(sheet, r, c, v, style) {
  sheet[XLSX.utils.encode_cell({ r, c })] = cell(v, style);
}

const BRANCHES_PER_ROW = 2;
const GAP_COLS = 1;
const BLOCK_WIDTH = EXPORT_COLS + GAP_COLS;

function writeBranchBlock(sheet, merges, group, rowOffset, colOffset) {
  let r = rowOffset;

  setCell(sheet, r, colOffset, group.name, titleStyle);
  for (let c = 1; c < EXPORT_COLS - 1; c++) setCell(sheet, r, colOffset + c, "", titleStyle);
  setCell(sheet, r, colOffset + EXPORT_COLS - 1, peso(group.total), titleTotalStyle);
  merges.push({ s: { r, c: colOffset }, e: { r, c: colOffset + EXPORT_COLS - 2 } });
  r++;

  ["Item", "Opening", "Delivery", "Price", "Closing", "Used", "Expense"].forEach((h, i) =>
    setCell(sheet, r, colOffset + i, h, headerStyle)
  );
  r++;

  for (const row of group.rows) {
    setCell(sheet, r, colOffset, row.itemName, cellStyle);
    setCell(sheet, r, colOffset + 1, row.opening, cellStyleRight);
    setCell(sheet, r, colOffset + 2, row.delivery, cellStyleRight);
    setCell(sheet, r, colOffset + 3, peso(row.price), cellStyleRight);
    setCell(sheet, r, colOffset + 4, row.hasClosing ? row.closing : "—", cellStyleRight);
    const usedStyle = row.hasClosing && row.used < 0 ? cellStyleColored(RED) : row.hasClosing && row.used > 0 ? cellStyleColored(GREEN) : cellStyleRight;
    setCell(sheet, r, colOffset + 5, row.hasClosing ? row.used : "—", usedStyle);
    const expenseStyle = row.hasClosing && row.expense < 0 ? cellStyleColored(RED) : cellStyleRight;
    setCell(sheet, r, colOffset + 6, row.hasClosing ? peso(row.expense) : "—", expenseStyle);
    r++;
  }

  setCell(sheet, r, colOffset, "TOTAL EXPENSES", totalLabelStyle);
  for (let c = 1; c < EXPORT_COLS - 1; c++) setCell(sheet, r, colOffset + c, "", totalLabelStyle);
  setCell(sheet, r, colOffset + EXPORT_COLS - 1, peso(group.total), totalValueStyle);
  merges.push({ s: { r, c: colOffset }, e: { r, c: colOffset + EXPORT_COLS - 2 } });
  r++;

  return r - rowOffset;
}

function exportToExcel() {
  const sheet = {};
  const merges = [];
  let rowOffset = 0;
  let maxCol = 0;

  const groups = stockExpenseByBranch.value;
  for (let i = 0; i < groups.length; i += BRANCHES_PER_ROW) {
    const chunk = groups.slice(i, i + BRANCHES_PER_ROW);
    let chunkHeight = 0;
    chunk.forEach((group, idx) => {
      const colOffset = idx * BLOCK_WIDTH;
      const height = writeBranchBlock(sheet, merges, group, rowOffset, colOffset);
      chunkHeight = Math.max(chunkHeight, height);
      maxCol = Math.max(maxCol, colOffset + EXPORT_COLS - 1);
    });
    rowOffset += chunkHeight + 1;
  }

  const summaryStartRow = rowOffset;
  setCell(sheet, rowOffset, 0, `Daily Sales & Bills — ${selectedDate.value}`, titleStyle);
  for (let c = 1; c < EXPORT_COLS; c++) setCell(sheet, rowOffset, c, "", titleStyle);
  merges.push({ s: { r: summaryStartRow, c: 0 }, e: { r: summaryStartRow, c: EXPORT_COLS - 1 } });
  rowOffset++;

  ["Branch", "Sales", "Daily Bills", "Stock Expense", "Total Expense", "Profit", ""].forEach((h, i) =>
    setCell(sheet, rowOffset, i, h, headerStyle)
  );
  rowOffset++;

  for (const row of exportBranchSummaries.value) {
    setCell(sheet, rowOffset, 0, row.branchName, cellStyle);
    setCell(sheet, rowOffset, 1, peso(row.sales), cellStyleRight);
    setCell(sheet, rowOffset, 2, peso(row.bills), cellStyleRight);
    setCell(sheet, rowOffset, 3, peso(row.stockExpense), cellStyleRight);
    setCell(sheet, rowOffset, 4, peso(row.totalExpense), cellStyleRight);
    setCell(sheet, rowOffset, 5, peso(row.profit), cellStyleColored(row.profit >= 0 ? GREEN : RED));
    setCell(sheet, rowOffset, 6, "", cellStyle);
    rowOffset++;
  }

  setCell(sheet, rowOffset, 0, "TOTAL", totalLabelStyle);
  setCell(sheet, rowOffset, 1, peso(totalSales.value), totalValueStyle);
  setCell(sheet, rowOffset, 2, peso(totalBills.value), totalValueStyle);
  setCell(sheet, rowOffset, 3, peso(stockExpenseTotal.value), totalValueStyle);
  setCell(sheet, rowOffset, 4, peso(grandTotalExpense.value), totalValueStyle);
  setCell(sheet, rowOffset, 5, peso(dailyProfit.value), totalValueStyleColored(dailyProfit.value >= 0 ? GREEN : RED));
  setCell(sheet, rowOffset, 6, "", totalLabelStyle);

  sheet["!ref"] = XLSX.utils.encode_range({ s: { r: 0, c: 0 }, e: { r: rowOffset, c: Math.max(maxCol, EXPORT_COLS - 1) } });
  sheet["!merges"] = merges;

  const colWidths = [];
  const numGroupCols = Math.min(groups.length, BRANCHES_PER_ROW);
  for (let g = 0; g < Math.max(numGroupCols, 1); g++) {
    colWidths.push({ wch: 18 }, { wch: 10 }, { wch: 10 }, { wch: 12 }, { wch: 10 }, { wch: 10 }, { wch: 12 });
    if (g < numGroupCols - 1) colWidths.push({ wch: 3 });
  }
  sheet["!cols"] = colWidths;

  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, sheet, "Expenses");
  XLSX.writeFile(workbook, `Expenses_${selectedDate.value}.xlsx`);
}

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
      <p class="page-subtitle">Daily sales, bills, and daily profit</p>
    </div>
    <div class="header-filters">
      <button type="button" class="secondary export-excel-btn" @click="exportToExcel">
        <Icon name="download" :size="14" />
        Export Excel
      </button>
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

    <LoadingState v-if="stockExpenseLoading" label="Loading stock expense..." />
    <div v-else-if="!stockExpenseByBranch.length" class="empty-state">
      <p>No stock items or branches set up yet.</p>
    </div>
    <div v-else class="branch-groups">
      <div v-for="group in stockExpenseByBranch" :key="group.branchId" class="branch-group">
        <div class="branch-group-header">
          <h3 class="branch-group-name">{{ group.name }}</h3>
          <span class="branch-group-total">
            {{ peso(group.total + (Number(billRowFor(group.branchId).amount) || 0)) }}
          </span>

          <div class="daily-bills-inline">
            <span class="daily-bills-title">Sales</span>

            <template v-if="!salesRowFor(group.branchId).id || salesRowFor(group.branchId).editing">
              <span class="unit-label">₱</span>
              <input
                type="number"
                inputmode="decimal"
                min="0"
                step="any"
                class="value-input"
                :class="{ saved: salesRowFor(group.branchId).saved }"
                placeholder="0"
                v-model="salesRowFor(group.branchId).amount"
                @blur="saveSales(group.branchId)"
                @keyup.enter="($event.target).blur()"
              />
              <span v-if="salesRowFor(group.branchId).saving" class="save-status">Saving...</span>
            </template>
            <template v-else>
              <button
                type="button"
                class="edit-bill-btn"
                title="Edit sales"
                aria-label="Edit sales"
                @click="salesRowFor(group.branchId).editing = true"
              >
                <Icon name="edit" :size="12" />
              </button>
            </template>
          </div>
          <p v-if="salesRowFor(group.branchId).error" class="row-error">{{ salesRowFor(group.branchId).error }}</p>

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
                <td>
                  <input
                    type="number"
                    inputmode="decimal"
                    min="0"
                    step="any"
                    class="value-input table-input"
                    :class="{ saved: row.row.deliverySaved }"
                    placeholder="0"
                    v-model="row.row.delivery"
                    @blur="saveStockDelivery(row.branchId, row.itemId)"
                    @keyup.enter="($event.target).blur()"
                  />
                  <span v-if="row.row.deliverySaving" class="save-status">Saving...</span>
                  <p v-if="row.row.deliveryError" class="row-error">{{ row.row.deliveryError }}</p>
                </td>
                <td>
                  <div class="closing-input-row">
                    <input
                      type="number"
                      inputmode="decimal"
                      min="0"
                      step="any"
                      class="value-input table-input"
                      :class="{ saved: row.row.closingSaved }"
                      placeholder="0"
                      v-model="row.row.closing"
                      @blur="saveStockClosing(row.branchId, row.itemId)"
                      @keyup.enter="($event.target).blur()"
                    />
                    <button
                      type="button"
                      class="same-as-opening-btn"
                      title="Same as opening"
                      aria-label="Set closing same as opening"
                      @click="useOpeningAsClosing(row.branchId, row.itemId)"
                    >
                      <Icon name="equal" :size="14" />
                    </button>
                  </div>
                  <span v-if="row.row.closingSaving" class="save-status">Saving...</span>
                  <p v-if="row.row.closingError" class="row-error">{{ row.row.closingError }}</p>
                </td>
                <td>{{ peso(row.price) }}</td>
                <td :class="{ negative: row.hasClosing && row.used < 0, positive: row.hasClosing && row.used > 0 }">
                  {{ row.hasClosing ? row.used : "—" }}
                </td>
                <td :class="{ negative: row.hasClosing && row.expense < 0 }">
                  {{ row.hasClosing ? peso(row.expense) : "—" }}
                </td>
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

.export-excel-btn {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  white-space: nowrap;
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

.table-input {
  width: 90px;
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
  width: 30px;
  height: 30px;
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
