<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";
import * as XLSX from "xlsx-js-style";
import { listBranches } from "../api/branches";
import { ApiError } from "../api/client";
import { createExpense, deleteExpense, deleteMonthData, listExpenses } from "../api/expenses";
import { createTotalSale, deleteSale, listSales, updateTotalSale } from "../api/sales";
import { listStockItems } from "../api/stockItems";
import { createStockCount, deleteStockCount, listStockCounts, updateStockCount } from "../api/stockCounts";
import {
  createStockDelivery,
  deleteStockDelivery,
  listStockDeliveries,
  updateStockDelivery,
} from "../api/stockDeliveries";
import ConfirmDeleteModal from "../components/ConfirmDeleteModal.vue";
import ConfirmModal from "../components/ConfirmModal.vue";
import CustomSelect from "../components/CustomSelect.vue";
import Icon from "../components/Icon.vue";
import LoadingState from "../components/LoadingState.vue";
import Modal from "../components/Modal.vue";
import { fetchBusinessToday, toLocalISO, todayLocalISO } from "../utils/date";

const today = todayLocalISO();
console.log("[AdminExpenses] device-guessed today (before server sync):", today);

const branches = ref([]);
const selectedDate = ref(today);
const selectedBranchId = ref("");
// The real "today" per the server (Asia/Manila) — used to tell apart clearing
// today's locked-in bill (must stay explicitly "no bill", never resurrected
// by carry-forward) from clearing a future preview day (should fall back to
// showing the preview again, so it's fully deleted instead).
const serverToday = ref(today);

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
  return `₱${Number(amount || 0).toLocaleString("en-PH", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

// Guards against floating-point noise (e.g. 10.7 + 5.3 - 3.85 === 12.150000000000002)
// from leaking into displayed quantities/amounts.
function round2(n) {
  return Math.round((n + Number.EPSILON) * 100) / 100;
}

const totalSales = computed(() => sales.value.reduce((sum, s) => sum + (Number(s.amount) || 0), 0));
const totalBills = computed(() =>
  expenses.value.reduce((sum, e) => (e.is_projected ? sum : sum + (Number(e.amount) || 0)), 0)
);

// A future date is just a preview (nothing saved yet) — inputs are disabled
// so nobody can accidentally lock in a value for a day that hasn't arrived.
const isFutureDate = computed(() => selectedDate.value > serverToday.value);

const billRows = reactive({});
const salesRows = reactive({});

function billRowFor(branchId) {
  if (!billRows[branchId]) {
    billRows[branchId] = {
      id: null,
      amount: "",
      saving: false,
      saved: false,
      error: "",
      editing: false,
      carriedForward: false,
      projected: false,
    };
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
  if (Number.isNaN(Number(row.amount)) && row.amount !== "") return;
  if (row.amount === "" && !row.id) {
    row.editing = false;
    flashSaved(row);
    return;
  }
  row.saving = true;
  try {
    if (row.amount === "" && selectedDate.value !== serverToday.value) {
      // Not today — no carry-forward resurrection risk here, so fully delete
      // instead of nulling, then re-fetch so a future date falls back to
      // showing its preview again instead of staying blank.
      await deleteExpense(row.id);
      row.editing = false;
      await refresh();
      flashSaved(billRowFor(branchId));
      return;
    }
    const amount = row.amount === "" ? null : Number(row.amount);
    const result = await createExpense({
      branchId,
      date: selectedDate.value,
      description: "Daily bills",
      amount,
    });
    row.id = result.id;
    row.carriedForward = false;
    row.projected = false;
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
  if (Number.isNaN(Number(row.amount))) return;
  row.saving = true;
  try {
    if (row.amount === "") {
      if (row.id) {
        await deleteSale(row.id);
        const idx = sales.value.findIndex((s) => s.branch_id === branchId && s.item_id === null);
        if (idx !== -1) sales.value.splice(idx, 1);
      }
      row.id = null;
      row.editing = false;
      flashSaved(row);
      return;
    }
    const amount = Number(row.amount);
    let result;
    if (row.id) {
      result = await updateTotalSale(row.id, amount);
    } else {
      result = await createTotalSale({ branchId, date: selectedDate.value, amount });
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
  console.log("[AdminExpenses] refresh() fetching expenses/sales with params:", params);
  try {
    [expenses.value, sales.value] = await Promise.all([listExpenses(params), listSales(params)]);
    console.log(
      "[AdminExpenses] expenses received:",
      expenses.value.map((e) => ({
        branch_id: e.branch_id,
        amount: e.amount,
        is_carried_forward: e.is_carried_forward,
        is_projected: e.is_projected,
      }))
    );
    for (const b of branches.value) {
      const bill = billRowFor(b.id);
      bill.id = null;
      bill.amount = "";
      bill.carriedForward = false;
      bill.projected = false;
      const salesRow = salesRowFor(b.id);
      salesRow.id = null;
      salesRow.amount = "";
    }
    for (const e of expenses.value) {
      const row = billRowFor(e.branch_id);
      row.id = e.is_projected ? null : e.id;
      row.amount = e.amount === null ? "" : String(e.amount);
      row.carriedForward = !!e.is_carried_forward;
      row.projected = !!e.is_projected;
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
      unit: "",
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
      if (item.branch_ids && item.branch_ids.length && !item.branch_ids.includes(branch.id)) continue;
      const key = stockRowKey(branch.id, item.id);
      const row = stockRowFor(branch.id, item.id);
      row.itemName = item.name;
      row.unit = item.unit || "";
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
  if (Number.isNaN(Number(row.delivery))) return;
  row.deliverySaving = true;
  try {
    if (row.delivery === "") {
      if (row.deliveryId) {
        await deleteStockDelivery(row.deliveryId);
        row.deliveryId = null;
      }
    } else {
      const quantity = Number(row.delivery);
      if (row.deliveryId) {
        await updateStockDelivery(row.deliveryId, { quantity_delivered: quantity });
      } else {
        const created = await createStockDelivery({
          branchId,
          itemId,
          quantityDelivered: quantity,
          date: selectedDate.value,
        });
        row.deliveryId = created.id;
      }
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
  if (Number.isNaN(Number(row.closing))) return;
  row.closingSaving = true;
  try {
    if (row.closing === "") {
      if (row.closingId) {
        await deleteStockCount(row.closingId);
        row.closingId = null;
      }
    } else {
      const quantity = Number(row.closing);
      if (row.closingId) {
        await updateStockCount(row.closingId, { quantity_remaining: quantity });
      } else {
        const created = await createStockCount({
          branchId,
          itemId,
          quantityRemaining: quantity,
          date: selectedDate.value,
        });
        row.closingId = created.id;
      }
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
    const used = hasClosing ? round2(opening + delivery - closing) : null;
    const expense = hasClosing ? round2(used * row.price) : null;
    return {
      key: stockRowKey(row.branchId, row.itemId),
      branchId: row.branchId,
      itemId: row.itemId,
      itemName: row.itemName,
      unit: row.unit,
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

const stockExpenseTotal = computed(() =>
  round2(stockExpenseRows.value.reduce((sum, r) => sum + (r.expense || 0), 0))
);
const grandTotalExpense = computed(() => round2(stockExpenseTotal.value + totalBills.value));
const dailyProfit = computed(() => round2(totalSales.value - grandTotalExpense.value));

const COLLAPSED_BRANCHES_KEY = "za-admin-expenses-collapsed-branches";

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
  return [...groups.entries()].map(([branchId, rows]) => {
    const total = round2(rows.reduce((sum, r) => sum + (r.expense || 0), 0));
    const sales = Number(salesRowFor(branchId).amount) || 0;
    const bills = billRowFor(branchId).projected ? 0 : Number(billRowFor(branchId).amount) || 0;
    return {
      branchId,
      name: branchName(branchId),
      rows: sortRows(rows),
      total,
      grandTotal: round2(sales - (total + bills)),
    };
  });
});


const exportBranchSummaries = computed(() => {
  const relevantBranches = selectedBranchId.value
    ? branches.value.filter((b) => b.id === selectedBranchId.value)
    : branches.value;
  return relevantBranches.map((b) => {
    const sales = Number(salesRowFor(b.id).amount) || 0;
    const bills = billRowFor(b.id).projected ? 0 : Number(billRowFor(b.id).amount) || 0;
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

function cell(v, style, link) {
  const c = { v, s: style, t: typeof v === "number" ? "n" : "s" };
  if (link) c.l = { Target: link };
  return c;
}

function setCell(sheet, r, c, v, style, link) {
  sheet[XLSX.utils.encode_cell({ r, c })] = cell(v, style, link);
}

const linkCellStyle = {
  border: allBorders,
  alignment: { vertical: "center" },
  font: { color: { rgb: "FF1155CC" }, underline: true, bold: true },
};

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
    setCell(sheet, r, colOffset, row.unit ? `${row.itemName} ${row.unit}` : row.itemName, cellStyle);
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

const showExportConfirm = ref(false);
const exporting = ref(false);

const now = new Date();
const exportYear = now.getFullYear();
const exportMonth = now.getMonth();
const exportMonthLabel = now.toLocaleString("en-US", { month: "long", year: "numeric" });
const exportDaysInMonth = new Date(exportYear, exportMonth + 1, 0).getDate();

function monthValue(y, m) {
  return `${y}-${String(m + 1).padStart(2, "0")}`;
}

function monthLabel(value) {
  const [y, m] = value.split("-").map(Number);
  return new Date(y, m - 1, 1).toLocaleString("en-US", { month: "long", year: "numeric" });
}

const MONTH_ABBR = Array.from({ length: 12 }, (_, i) =>
  new Date(2000, i, 1).toLocaleString("en-US", { month: "short" })
);

const showDeleteMonthPanel = ref(false);
const deleteMonthPanelRoot = ref(null);
const selectedDeleteMonths = ref([]);
const calendarYear = ref(exportYear);

const isCurrentOrFutureCalendarYear = computed(() => calendarYear.value >= exportYear);

function isCalendarMonthDisabled(monthIndex) {
  return calendarYear.value > exportYear || (calendarYear.value === exportYear && monthIndex >= exportMonth);
}

function isCalendarMonthSelected(monthIndex) {
  return selectedDeleteMonths.value.includes(monthValue(calendarYear.value, monthIndex));
}

function toggleCalendarMonth(monthIndex) {
  if (isCalendarMonthDisabled(monthIndex)) return;
  const value = monthValue(calendarYear.value, monthIndex);
  const idx = selectedDeleteMonths.value.indexOf(value);
  if (idx >= 0) selectedDeleteMonths.value.splice(idx, 1);
  else selectedDeleteMonths.value.push(value);
}

function goToPrevCalendarYear() {
  calendarYear.value -= 1;
}

function goToNextCalendarYear() {
  if (!isCurrentOrFutureCalendarYear.value) calendarYear.value += 1;
}

const selectedDeleteMonthsLabel = computed(() => {
  if (!selectedDeleteMonths.value.length) return "Select months";
  if (selectedDeleteMonths.value.length === 1) return monthLabel(selectedDeleteMonths.value[0]);
  return `${selectedDeleteMonths.value.length} months selected`;
});

const selectedDeleteMonthsListLabel = computed(() =>
  selectedDeleteMonths.value.map(monthLabel).join(", ")
);

function toggleDeleteMonthPanel() {
  showDeleteMonthPanel.value = !showDeleteMonthPanel.value;
}

function onDeleteMonthPanelClickOutside(e) {
  if (deleteMonthPanelRoot.value?.contains(e.target)) return;
  showDeleteMonthPanel.value = false;
}

watch(showDeleteMonthPanel, (isOpen) => {
  if (isOpen) document.addEventListener("mousedown", onDeleteMonthPanelClickOutside);
  else document.removeEventListener("mousedown", onDeleteMonthPanelClickOutside);
});

onBeforeUnmount(() => {
  document.removeEventListener("mousedown", onDeleteMonthPanelClickOutside);
});

const showDeleteOldMonthModal = ref(false);
const deletingOldMonth = ref(false);
const deleteOldMonthError = ref("");

function openDeleteOldMonthModal() {
  if (!selectedDeleteMonths.value.length) return;
  deleteOldMonthError.value = "";
  showDeleteMonthPanel.value = false;
  showDeleteOldMonthModal.value = true;
}

function cancelDeleteOldMonth() {
  if (deletingOldMonth.value) return;
  showDeleteOldMonthModal.value = false;
}

async function confirmDeleteOldMonth(password) {
  deletingOldMonth.value = true;
  deleteOldMonthError.value = "";
  try {
    for (const value of selectedDeleteMonths.value) {
      const [year, month] = value.split("-").map(Number);
      await deleteMonthData(year, month, password);
    }
    selectedDeleteMonths.value = [];
    showDeleteOldMonthModal.value = false;
    await Promise.all([refresh(), refreshStockExpense()]);
  } catch (e) {
    deleteOldMonthError.value =
      e instanceof ApiError ? e.detail || "Could not delete month data" : "Could not delete month data";
  } finally {
    deletingOldMonth.value = false;
  }
}

async function fetchDayReport(dateStr, items) {
  const params = { date: dateStr };
  const openingParams = { date: previousDay(dateStr) };
  if (selectedBranchId.value) {
    params.branch_id = selectedBranchId.value;
    openingParams.branch_id = selectedBranchId.value;
  }

  const [expensesRes, salesRes, closingToday, closingYesterday, deliveriesToday] = await Promise.all([
    listExpenses(params),
    listSales(params),
    listStockCounts(params),
    listStockCounts(openingParams),
    listStockDeliveries(params),
  ]);

  const openingMap = new Map(closingYesterday.map((c) => [`${c.branch_id}|${c.item_id}`, c.quantity_remaining]));
  const deliveryMap = new Map();
  for (const d of deliveriesToday) {
    const key = `${d.branch_id}|${d.item_id}`;
    deliveryMap.set(key, (deliveryMap.get(key) || 0) + d.quantity_delivered);
  }
  const closingMap = new Map(closingToday.map((c) => [`${c.branch_id}|${c.item_id}`, c.quantity_remaining]));
  const billsMap = new Map(expensesRes.map((e) => [e.branch_id, e.amount]));
  const salesMap = new Map(salesRes.filter((s) => s.item_id === null).map((s) => [s.branch_id, s.amount]));

  const relevantBranches = selectedBranchId.value
    ? branches.value.filter((b) => b.id === selectedBranchId.value)
    : branches.value;

  const groups = relevantBranches.map((b) => {
    const rows = items
      .filter((item) => !item.branch_ids || !item.branch_ids.length || item.branch_ids.includes(b.id))
      .map((item) => {
        const key = `${b.id}|${item.id}`;
        const opening = openingMap.get(key) || 0;
        const delivery = deliveryMap.get(key) || 0;
        const closingRaw = closingMap.get(key);
        const hasClosing = closingRaw !== undefined;
        const closing = hasClosing ? closingRaw : null;
        const used = hasClosing ? round2(opening + delivery - closing) : null;
        const expense = hasClosing ? round2(used * (item.price || 0)) : null;
        return {
          itemName: item.name,
          unit: item.unit || "",
          opening,
          delivery,
          price: item.price || 0,
          closing,
          hasClosing,
          used,
          expense,
        };
      });
    const total = round2(rows.reduce((sum, r) => sum + (r.expense || 0), 0));
    return { branchId: b.id, name: b.name, rows, total };
  });

  const summaries = relevantBranches.map((b) => {
    const sales = Number(salesMap.get(b.id)) || 0;
    const bills = Number(billsMap.get(b.id)) || 0;
    const stockExpense = groups.find((g) => g.branchId === b.id)?.total || 0;
    const totalExpense = round2(bills + stockExpense);
    return { branchName: b.name, sales, bills, stockExpense, totalExpense, profit: round2(sales - totalExpense) };
  });

  const totals = summaries.reduce(
    (acc, r) => ({
      sales: round2(acc.sales + r.sales),
      bills: round2(acc.bills + r.bills),
      stockExpense: round2(acc.stockExpense + r.stockExpense),
      totalExpense: round2(acc.totalExpense + r.totalExpense),
      profit: round2(acc.profit + r.profit),
    }),
    { sales: 0, bills: 0, stockExpense: 0, totalExpense: 0, profit: 0 }
  );

  return { groups, summaries, totals };
}

function buildDaySheet(dateStr, { groups, summaries, totals }) {
  const sheet = {};
  const merges = [];
  let rowOffset = 0;
  let maxCol = 0;

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
  setCell(sheet, rowOffset, 0, `Daily Sales & Bills — ${dateStr}`, titleStyle);
  for (let c = 1; c < EXPORT_COLS; c++) setCell(sheet, rowOffset, c, "", titleStyle);
  merges.push({ s: { r: summaryStartRow, c: 0 }, e: { r: summaryStartRow, c: EXPORT_COLS - 1 } });
  rowOffset++;

  ["Branch", "Sales", "Daily Bills", "Stock Expense", "Total Expense", "Profit", ""].forEach((h, i) =>
    setCell(sheet, rowOffset, i, h, headerStyle)
  );
  rowOffset++;

  for (const row of summaries) {
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
  setCell(sheet, rowOffset, 1, peso(totals.sales), totalValueStyle);
  setCell(sheet, rowOffset, 2, peso(totals.bills), totalValueStyle);
  setCell(sheet, rowOffset, 3, peso(totals.stockExpense), totalValueStyle);
  setCell(sheet, rowOffset, 4, peso(totals.totalExpense), totalValueStyle);
  setCell(sheet, rowOffset, 5, peso(totals.profit), totalValueStyleColored(totals.profit >= 0 ? GREEN : RED));
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

  return sheet;
}

function buildSummarySheet(dayResults, monthLabel) {
  const sheet = {};
  const cols = 6;
  let r = 0;

  setCell(sheet, r, 0, `${monthLabel} — Daily Summary (click a date to jump to its sheet)`, titleStyle);
  for (let c = 1; c < cols; c++) setCell(sheet, r, c, "", titleStyle);
  const merges = [{ s: { r, c: 0 }, e: { r, c: cols - 1 } }];
  r++;

  ["Date", "Sales", "Daily Bills", "Stock Expense", "Total Expense", "Profit"].forEach((h, i) =>
    setCell(sheet, r, i, h, headerStyle)
  );
  r++;

  const monthTotals = { sales: 0, bills: 0, stockExpense: 0, totalExpense: 0, profit: 0 };
  for (const day of dayResults) {
    setCell(sheet, r, 0, day.tabName, linkCellStyle, `#'${day.tabName}'!A1`);
    setCell(sheet, r, 1, peso(day.totals.sales), cellStyleRight);
    setCell(sheet, r, 2, peso(day.totals.bills), cellStyleRight);
    setCell(sheet, r, 3, peso(day.totals.stockExpense), cellStyleRight);
    setCell(sheet, r, 4, peso(day.totals.totalExpense), cellStyleRight);
    setCell(sheet, r, 5, peso(day.totals.profit), cellStyleColored(day.totals.profit >= 0 ? GREEN : RED));
    monthTotals.sales = round2(monthTotals.sales + day.totals.sales);
    monthTotals.bills = round2(monthTotals.bills + day.totals.bills);
    monthTotals.stockExpense = round2(monthTotals.stockExpense + day.totals.stockExpense);
    monthTotals.totalExpense = round2(monthTotals.totalExpense + day.totals.totalExpense);
    monthTotals.profit = round2(monthTotals.profit + day.totals.profit);
    r++;
  }

  setCell(sheet, r, 0, "MONTH TOTAL", totalLabelStyle);
  setCell(sheet, r, 1, peso(monthTotals.sales), totalValueStyle);
  setCell(sheet, r, 2, peso(monthTotals.bills), totalValueStyle);
  setCell(sheet, r, 3, peso(monthTotals.stockExpense), totalValueStyle);
  setCell(sheet, r, 4, peso(monthTotals.totalExpense), totalValueStyle);
  setCell(sheet, r, 5, peso(monthTotals.profit), totalValueStyleColored(monthTotals.profit >= 0 ? GREEN : RED));

  sheet["!ref"] = XLSX.utils.encode_range({ s: { r: 0, c: 0 }, e: { r, c: cols - 1 } });
  sheet["!merges"] = merges;
  sheet["!cols"] = [{ wch: 14 }, { wch: 12 }, { wch: 12 }, { wch: 14 }, { wch: 14 }, { wch: 12 }];

  return sheet;
}

function confirmExportToExcel() {
  exportToExcel();
  showExportConfirm.value = false;
}

const exportProgress = reactive({ current: 0, total: exportDaysInMonth });

async function exportToExcel() {
  exporting.value = true;
  exportProgress.current = 0;
  exportProgress.total = exportDaysInMonth;
  try {
    const items = stockItems.value.length ? stockItems.value : await listStockItems();
    const workbook = XLSX.utils.book_new();
    const dayResults = [];

    for (let day = 1; day <= exportDaysInMonth; day++) {
      const dateStr = `${exportYear}-${String(exportMonth + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
      const report = await fetchDayReport(dateStr, items);
      const sheet = buildDaySheet(dateStr, report);
      const tabName = new Date(`${dateStr}T00:00:00Z`).toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        timeZone: "UTC",
      });
      XLSX.utils.book_append_sheet(workbook, sheet, tabName);
      dayResults.push({ dateStr, tabName, totals: report.totals });
      exportProgress.current = day;
    }

    const summarySheet = buildSummarySheet(dayResults, exportMonthLabel);
    XLSX.utils.book_append_sheet(workbook, summarySheet, "Summary");
    const summaryIdx = workbook.SheetNames.indexOf("Summary");
    workbook.SheetNames.splice(summaryIdx, 1);
    workbook.SheetNames.unshift("Summary");

    workbook.Workbook = { WBView: [{ activeTab: 0, tabRatio: 700 }] };

    XLSX.writeFile(workbook, `Expenses_${exportMonthLabel.replace(" ", "_")}.xlsx`);
  } finally {
    exporting.value = false;
  }
}

onMounted(async () => {
  branches.value = await listBranches();

  // The backend (Asia/Manila) is the source of truth for "what day is it" —
  // this avoids relying on the device's own clock/timezone, which is what
  // was silently breaking the daily-bills carry-forward (it only kicks in
  // when the requested date exactly matches the server's business day).
  const wasOnToday = selectedDate.value === today;
  const { date: serverToday } = await fetchBusinessToday();
  const serverTodayISO = toLocalISO(serverToday);
  console.log("[AdminExpenses] server business-day today:", serverTodayISO);
  serverToday.value = serverTodayISO;
  if (wasOnToday && serverTodayISO !== selectedDate.value) {
    console.log(
      "[AdminExpenses] correcting selectedDate from device guess to server date:",
      selectedDate.value,
      "->",
      serverTodayISO
    );
    selectedDate.value = serverTodayISO;
  }

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
      <button
        type="button"
        class="secondary export-excel-btn"
        :disabled="exporting"
        @click="showExportConfirm = true"
      >
        <Icon name="download" :size="14" />
        {{ exporting ? "Exporting..." : "Export Excel" }}
      </button>
      <div class="delete-month-group" ref="deleteMonthPanelRoot">
        <button type="button" class="secondary month-multiselect-trigger" @click="toggleDeleteMonthPanel">
          <span>{{ selectedDeleteMonthsLabel }}</span>
          <svg class="chevron" width="12" height="8" viewBox="0 0 12 8" fill="none">
            <path d="M1 1.5L6 6.5L11 1.5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </button>
        <button
          type="button"
          class="secondary danger-outline"
          :disabled="!selectedDeleteMonths.length"
          @click="openDeleteOldMonthModal"
        >
          <Icon name="trash" :size="14" />
          Delete
        </button>

        <div v-if="showDeleteMonthPanel" class="month-calendar-panel">
          <div class="month-calendar-header">
            <button type="button" class="month-calendar-nav" @click="goToPrevCalendarYear">
              <svg width="10" height="10" viewBox="0 0 12 12" fill="none">
                <path d="M8 1L3 6L8 11" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
            </button>
            <span class="month-calendar-year">{{ calendarYear }}</span>
            <button
              type="button"
              class="month-calendar-nav"
              :disabled="isCurrentOrFutureCalendarYear"
              @click="goToNextCalendarYear"
            >
              <svg width="10" height="10" viewBox="0 0 12 12" fill="none">
                <path d="M4 1L9 6L4 11" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
            </button>
          </div>
          <div class="month-calendar-grid">
            <button
              v-for="(abbr, idx) in MONTH_ABBR"
              :key="idx"
              type="button"
              class="month-calendar-cell"
              :class="{ selected: isCalendarMonthSelected(idx) }"
              :disabled="isCalendarMonthDisabled(idx)"
              @click="toggleCalendarMonth(idx)"
            >
              {{ abbr }}
            </button>
          </div>
        </div>
      </div>
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
    <div class="card stat-card">
      <span class="stat-label">Daily bills</span>
      <span class="stat-value">{{ peso(totalBills) }}</span>
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
          <h3 class="branch-group-name">{{ group.name }}</h3>
          <div class="daily-bills-inline">
            <span class="daily-bills-title">Stock expense</span>
            <span class="branch-group-total">{{ peso(group.total) }}</span>
          </div>

          <div class="daily-bills-inline">
            <span class="daily-bills-title">Sales</span>

            <template v-if="!salesRowFor(group.branchId).id || salesRowFor(group.branchId).editing">
              <div class="daily-bills-value-row">
                <span class="unit-label">₱</span>
                <input
                  type="number"
                  inputmode="decimal"
                  min="0"
                  step="any"
                  class="value-input"
                  :class="{ saved: salesRowFor(group.branchId).saved }"
                  placeholder="0"
                  :disabled="isFutureDate"
                  v-model="salesRowFor(group.branchId).amount"
                  @blur="saveSales(group.branchId)"
                  @keyup.enter="($event.target).blur()"
                />
                <span v-if="salesRowFor(group.branchId).saving" class="save-status">Saving...</span>
              </div>
            </template>
            <template v-else>
              <div class="daily-bills-value-row">
                <span class="daily-bills-value">{{ peso(Number(salesRowFor(group.branchId).amount) || 0) }}</span>
                <button
                  type="button"
                  class="edit-bill-btn"
                  title="Edit sales"
                  aria-label="Edit sales"
                  :disabled="isFutureDate"
                  @click="salesRowFor(group.branchId).editing = true"
                >
                  <Icon name="edit" :size="12" />
                </button>
              </div>
            </template>
          </div>
          <p v-if="salesRowFor(group.branchId).error" class="row-error">{{ salesRowFor(group.branchId).error }}</p>

          <div class="daily-bills-inline">
            <span class="daily-bills-title">Daily bills</span>

            <template v-if="!billRowFor(group.branchId).id || billRowFor(group.branchId).editing">
              <div class="daily-bills-value-row">
                <span class="unit-label">₱</span>
                <input
                  type="number"
                  inputmode="decimal"
                  min="0"
                  step="any"
                  class="value-input"
                  :class="{ saved: billRowFor(group.branchId).saved }"
                  placeholder="0"
                  :disabled="isFutureDate"
                  v-model="billRowFor(group.branchId).amount"
                  @blur="saveBill(group.branchId)"
                  @keyup.enter="($event.target).blur()"
                />
                <span v-if="billRowFor(group.branchId).saving" class="save-status">Saving...</span>
                <span v-else-if="billRowFor(group.branchId).projected" class="save-status carried-badge"
                  >preview — not yet saved</span
                >
              </div>
            </template>
            <template v-else>
              <div class="daily-bills-value-row">
                <span class="daily-bills-value">{{
                  billRowFor(group.branchId).amount === "" ? "—" : peso(Number(billRowFor(group.branchId).amount))
                }}</span>
                <span v-if="billRowFor(group.branchId).carriedForward" class="save-status carried-badge"
                  >carried from yesterday</span
                >
                <button
                  type="button"
                  class="edit-bill-btn"
                  title="Edit daily bills"
                  aria-label="Edit daily bills"
                  :disabled="isFutureDate"
                  @click="billRowFor(group.branchId).editing = true"
                >
                  <Icon name="edit" :size="12" />
                </button>
              </div>
            </template>
          </div>

          <div class="daily-bills-inline">
            <span class="daily-bills-title">Grand total</span>
            <span
              class="branch-group-total"
              :class="{ 'total-negative': group.grandTotal < 0, 'total-positive': group.grandTotal >= 0 }"
            >
              {{ group.grandTotal >= 0 ? "+" : "" }}{{ peso(group.grandTotal) }}
            </span>
          </div>
        </div>
        <p v-if="billRowFor(group.branchId).error" class="row-error">{{ billRowFor(group.branchId).error }}</p>
        <div v-show="!isBranchCollapsed(group.branchId)" class="table-scroll">
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
                <td>{{ row.itemName }} <span v-if="row.unit" class="item-unit">{{ row.unit }}</span></td>
                <td>{{ row.opening }}</td>
                <td>
                  <input
                    type="number"
                    inputmode="decimal"
                    min="0"
                    step="any"
                    class="value-input table-input"
                    :class="{ saved: row.row.deliverySaved }"
                    :disabled="isFutureDate"
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
                      :disabled="isFutureDate"
                      v-model="row.row.closing"
                      @blur="saveStockClosing(row.branchId, row.itemId)"
                      @keyup.enter="($event.target).blur()"
                    />
                    <button
                      type="button"
                      class="same-as-opening-btn"
                      title="Same as opening"
                      aria-label="Set closing same as opening"
                      :disabled="isFutureDate"
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

  <ConfirmModal
    :open="showExportConfirm"
    title="Export to Excel?"
    :message="`This will download the ${exportMonthLabel} expenses report as an Excel file, with one sheet per day.`"
    confirm-label="Export"
    @confirm="confirmExportToExcel"
    @cancel="showExportConfirm = false"
  />

  <ConfirmDeleteModal
    :open="showDeleteOldMonthModal"
    title="Delete old month data?"
    :message="`This will permanently delete all stock (opening, delivery, closing), expenses, sales, and daily billing/profit data for ${selectedDeleteMonthsListLabel}, except each month's last day closing count (kept as the next month's opening). This cannot be undone.`"
    confirm-label="Delete"
    loading-label="Deleting..."
    :loading="deletingOldMonth"
    :error="deleteOldMonthError"
    @confirm="confirmDeleteOldMonth"
    @cancel="cancelDeleteOldMonth"
  />

  <Modal v-if="exporting" title="Exporting Excel" @close="() => {}">
    <div class="export-progress">
      <span class="loading-spinner" aria-hidden="true"></span>
      <p class="export-progress-label">
        Exporting {{ exportMonthLabel }}… day {{ exportProgress.current }} of {{ exportProgress.total }}
      </p>
      <div class="export-progress-bar">
        <div
          class="export-progress-fill"
          :style="{ width: `${(exportProgress.current / exportProgress.total) * 100}%` }"
        ></div>
      </div>
      <p class="export-progress-hint">Please keep this page open until the download starts.</p>
    </div>
  </Modal>
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

.delete-month-group {
  position: relative;
  display: flex;
  align-items: stretch;
}

.month-multiselect-trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  min-width: 150px;
  font-family: inherit;
  font-size: 0.95rem;
  border-radius: var(--radius) 0 0 var(--radius);
  border-right: none;
}

.month-multiselect-trigger .chevron {
  flex-shrink: 0;
  color: var(--color-text-muted);
}

.delete-month-group > button.danger-outline {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  white-space: nowrap;
  border-radius: 0 var(--radius) var(--radius) 0;
}

.month-calendar-panel {
  position: absolute;
  z-index: 200;
  top: calc(100% + 6px);
  left: 0;
  width: 220px;
  padding: 0.6rem;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 10px;
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.45);
}

.month-calendar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.5rem;
}

.month-calendar-year {
  font-weight: 700;
  font-size: 0.95rem;
}

.month-calendar-nav {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  padding: 0;
  border: 1px solid var(--color-border);
  border-radius: 7px;
  background: transparent;
  color: var(--color-text);
}

.month-calendar-nav:hover:not(:disabled) {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.month-calendar-nav:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.month-calendar-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.4rem;
}

.month-calendar-cell {
  padding: 0.55rem 0;
  border: 1px solid var(--color-border);
  border-radius: 7px;
  background: transparent;
  color: var(--color-text);
  font-size: 0.85rem;
  cursor: pointer;
}

.month-calendar-cell:hover:not(:disabled):not(.selected) {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.month-calendar-cell.selected {
  background: var(--color-danger);
  border-color: var(--color-danger);
  color: #fff;
}

.month-calendar-cell.selected:hover:not(:disabled) {
  opacity: 0.85;
}

.month-calendar-cell:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.danger-outline {
  color: var(--color-danger);
  border-color: var(--color-danger);
}

.danger-outline:hover {
  background: var(--color-danger);
  color: #fff;
}

.top-error {
  text-align: center;
}

.stat-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
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
}

.branch-collapse-btn:hover {
  border-color: var(--color-text-muted);
}

.branch-collapse-btn .icon {
  transition: transform 0.15s ease;
  transform: rotate(90deg);
}

.branch-collapse-btn.collapsed .icon {
  transform: rotate(0deg);
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
  flex-direction: column;
  align-items: flex-start;
  gap: 0.2rem;
}

.daily-bills-value-row {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.daily-bills-value {
  font-weight: 600;
  color: var(--color-text);
}

.branch-group-total {
  font-weight: 700;
  color: var(--color-primary);
}

.branch-group-total.total-positive {
  color: var(--color-success, #2e7d32);
}

.branch-group-total.total-negative {
  color: var(--color-danger);
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

.item-unit {
  color: var(--color-danger);
  font-size: 0.8em;
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

.value-input:disabled,
.edit-bill-btn:disabled,
.same-as-opening-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
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

.carried-badge {
  font-style: italic;
}

@media (max-width: 560px) {
  .stat-row {
    grid-template-columns: 1fr;
  }
}

.export-progress {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.85rem;
  padding: 0.5rem 0 0.75rem;
  text-align: center;
}

.export-progress .loading-spinner {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 3px solid var(--color-border);
  border-top-color: var(--color-primary);
  animation: export-progress-spin 0.7s linear infinite;
}

.export-progress-label {
  margin: 0;
  font-weight: 600;
  color: var(--color-text);
  font-size: 0.95rem;
}

.export-progress-bar {
  width: 100%;
  max-width: 280px;
  height: 8px;
  border-radius: 999px;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  overflow: hidden;
}

.export-progress-fill {
  height: 100%;
  background: var(--gradient-primary, var(--color-primary));
  transition: width 0.2s ease;
}

.export-progress-hint {
  margin: 0;
  font-size: 0.8rem;
  color: var(--color-text-muted);
}

@keyframes export-progress-spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
