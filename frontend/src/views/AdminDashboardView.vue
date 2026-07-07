<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { getMonthly, getOverview } from "../api/dashboard";
import MonthYearPicker from "../components/MonthYearPicker.vue";

const SERIES_COLORS = ["#ff2d4d", "#ff8a3d", "#ffe14d", "#4dd6ff", "#8a6bff", "#4dffb0", "#ff4dd2", "#c8c8c8"];
const BAR_COLOR = "#ff2d4d";

const overview = ref(null);
const monthly = ref(null);
const loading = ref(true);
const monthlyLoading = ref(false);

const now = new Date();
const selectedYear = ref(now.getFullYear());
const selectedMonth = ref(now.getMonth() + 1);

function peso(amount) {
  return `₱${amount.toLocaleString("en-PH", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function niceMax(value) {
  if (value <= 0) return 10;
  const magnitude = Math.pow(10, Math.floor(Math.log10(value)));
  const scaled = value / magnitude;
  const step = scaled <= 1 ? 1 : scaled <= 2 ? 2 : scaled <= 5 ? 5 : 10;
  return step * magnitude;
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

watch([selectedYear, selectedMonth], loadMonthly);

const alertCount = computed(() => overview.value?.branches.filter((b) => b.has_shortfall).length || 0);

// --- Bar chart: profit today by branch ---
const BAR_CHART_W = 600;
const BAR_CHART_H = 220;
const BAR_MARGIN = { top: 24, right: 16, bottom: 28, left: 16 };

const barChart = computed(() => {
  const branches = overview.value?.branches || [];
  const innerW = BAR_CHART_W - BAR_MARGIN.left - BAR_MARGIN.right;
  const innerH = BAR_CHART_H - BAR_MARGIN.top - BAR_MARGIN.bottom;
  const maxVal = niceMax(Math.max(...branches.map((b) => b.profit), 0));
  const bandWidth = branches.length ? innerW / branches.length : innerW;
  const barWidth = Math.min(40, bandWidth * 0.5);

  const bars = branches.map((b, i) => {
    const bandCenter = BAR_MARGIN.left + bandWidth * (i + 0.5);
    const barHeight = maxVal > 0 ? (Math.max(b.profit, 0) / maxVal) * innerH : 0;
    return {
      id: b.branch_id,
      name: b.branch_name,
      value: b.profit,
      hasShortfall: b.has_shortfall,
      x: bandCenter - barWidth / 2,
      y: BAR_MARGIN.top + innerH - barHeight,
      width: barWidth,
      height: barHeight,
      labelX: bandCenter,
      nameY: BAR_MARGIN.top + innerH + 18,
    };
  });

  return { bars, innerH, baselineY: BAR_MARGIN.top + innerH };
});

const hoveredBar = ref(null);

// --- Line chart: daily sales trend by branch ---
const LINE_CHART_W = 640;
const LINE_CHART_H = 260;
const LINE_MARGIN = { top: 16, right: 16, bottom: 28, left: 40 };

const lineChart = computed(() => {
  const daily = monthly.value?.daily || [];
  const branches = monthly.value?.branches || [];
  const innerW = LINE_CHART_W - LINE_MARGIN.left - LINE_MARGIN.right;
  const innerH = LINE_CHART_H - LINE_MARGIN.top - LINE_MARGIN.bottom;

  const maxVal = niceMax(
    Math.max(...daily.flatMap((d) => Object.values(d.branch_sales)), 0)
  );
  const n = daily.length;
  const xStep = n > 1 ? innerW / (n - 1) : 0;

  const xAt = (i) => LINE_MARGIN.left + xStep * i;
  const yAt = (v) => LINE_MARGIN.top + innerH - (maxVal > 0 ? (v / maxVal) * innerH : 0);

  const series = branches.map((b, si) => {
    const color = SERIES_COLORS[si % SERIES_COLORS.length];
    const points = daily.map((d, i) => ({ x: xAt(i), y: yAt(d.branch_sales[b.branch_id] || 0) }));
    const path = points.map((p, i) => `${i === 0 ? "M" : "L"}${p.x},${p.y}`).join(" ");
    return { id: b.branch_id, name: b.branch_name, color, points, path, total: b.total_sales };
  });

  const gridLines = [0, 0.25, 0.5, 0.75, 1].map((f) => {
    const value = maxVal * f;
    return { y: yAt(value), value };
  });

  const labelEvery = Math.max(1, Math.ceil(n / 8));
  const xLabels = daily
    .map((d, i) => ({ x: xAt(i), label: d.date.slice(8, 10), i }))
    .filter((l) => l.i % labelEvery === 0);

  return { series, gridLines, xLabels, innerH, xAt, dates: daily.map((d) => d.date) };
});

const hoverIndex = ref(null);
const lineChartEl = ref(null);

function onLineChartMove(evt) {
  const daily = monthly.value?.daily || [];
  if (!daily.length || !lineChartEl.value) return;
  const rect = lineChartEl.value.getBoundingClientRect();
  const scaleX = LINE_CHART_W / rect.width;
  const localX = (evt.clientX - rect.left) * scaleX;
  const innerW = LINE_CHART_W - LINE_MARGIN.left - LINE_MARGIN.right;
  const ratio = Math.min(1, Math.max(0, (localX - LINE_MARGIN.left) / innerW));
  hoverIndex.value = Math.round(ratio * (daily.length - 1));
}

function onLineChartLeave() {
  hoverIndex.value = null;
}

const hoverTooltip = computed(() => {
  if (hoverIndex.value === null || !monthly.value) return null;
  const point = monthly.value.daily[hoverIndex.value];
  if (!point) return null;
  const rows = lineChart.value.series.map((s) => ({
    name: s.name,
    color: s.color,
    value: point.branch_sales[s.id] || 0,
  }));
  return { date: point.date, x: lineChart.value.xAt(hoverIndex.value), rows };
});
</script>

<template>
  <div class="dash">
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
          <span class="stat-label">This month's sales</span>
          <span class="stat-value">{{ monthly ? peso(monthly.total_sales) : "—" }}</span>
        </div>
        <div class="card stat-card">
          <span class="stat-label">Branches</span>
          <span class="stat-value">{{ overview.branch_count }}</span>
        </div>
        <div class="card stat-card" :class="{ 'stat-card-alert': alertCount > 0 }">
          <span class="stat-label">Stock alerts</span>
          <span class="stat-value">{{ alertCount }}</span>
        </div>
      </div>

      <div class="card chart-card" v-if="overview.branches.length">
        <h2 class="card-title">Daily profit by branch</h2>
        <div class="chart-scroll">
          <svg
            class="bar-chart"
            :viewBox="`0 0 ${BAR_CHART_W} ${BAR_CHART_H}`"
            preserveAspectRatio="xMidYMid meet"
            role="img"
            aria-label="Bar chart of today's profit per branch"
          >
            <defs>
              <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" :stop-color="BAR_COLOR" stop-opacity="1" />
                <stop offset="100%" :stop-color="BAR_COLOR" stop-opacity="0.35" />
              </linearGradient>
            </defs>
            <line
              class="baseline"
              :x1="0"
              :x2="BAR_CHART_W"
              :y1="barChart.baselineY"
              :y2="barChart.baselineY"
            />
            <g v-for="bar in barChart.bars" :key="bar.id">
              <rect
                class="bar"
                :class="{ 'bar-hover': hoveredBar === bar.id }"
                :x="bar.x"
                :y="bar.y"
                :width="bar.width"
                :height="Math.max(bar.height, 1)"
                rx="4"
                fill="url(#barGradient)"
                tabindex="0"
                @pointerenter="hoveredBar = bar.id"
                @pointerleave="hoveredBar = null"
                @focus="hoveredBar = bar.id"
                @blur="hoveredBar = null"
              />
              <circle v-if="bar.hasShortfall" class="alert-dot" :cx="bar.x + bar.width / 2" :cy="bar.y - 16" r="3" />
              <text class="bar-value" :x="bar.labelX" :y="bar.y - 8" text-anchor="middle">
                {{ peso(bar.value) }}
              </text>
              <text class="bar-name" :x="bar.labelX" :y="bar.nameY" text-anchor="middle">
                {{ bar.name }}
              </text>
            </g>
          </svg>
        </div>
      </div>

      <div class="card chart-card">
        <div class="monthly-header">
          <h2 class="card-title">Monthly trend</h2>
          <MonthYearPicker v-model:year="selectedYear" v-model:month="selectedMonth" />
        </div>

        <p v-if="monthlyLoading" class="state-message">Loading...</p>
        <template v-else-if="monthly">
          <div v-if="monthly.daily?.length" class="monthly-body">
            <div class="line-chart-scroll">
              <div class="line-chart-wrap">
                <svg
                ref="lineChartEl"
                class="line-chart"
                :viewBox="`0 0 ${LINE_CHART_W} ${LINE_CHART_H}`"
                preserveAspectRatio="xMidYMid meet"
                role="img"
                aria-label="Line chart of daily sales this month per branch"
                @pointermove="onLineChartMove"
                @pointerleave="onLineChartLeave"
              >
                <line
                  v-for="(g, i) in lineChart.gridLines"
                  :key="i"
                  class="gridline"
                  :x1="LINE_MARGIN.left"
                  :x2="LINE_CHART_W - LINE_MARGIN.right"
                  :y1="g.y"
                  :y2="g.y"
                />
                <text
                  v-for="(g, i) in lineChart.gridLines"
                  :key="'gy' + i"
                  class="axis-label"
                  :x="LINE_MARGIN.left - 8"
                  :y="g.y + 3"
                  text-anchor="end"
                >
                  {{ Math.round(g.value).toLocaleString("en-PH") }}
                </text>
                <text
                  v-for="l in lineChart.xLabels"
                  :key="l.i"
                  class="axis-label"
                  :x="l.x"
                  :y="LINE_CHART_H - 8"
                  text-anchor="middle"
                >
                  {{ l.label }}
                </text>

                <path
                  v-for="s in lineChart.series"
                  :key="s.id"
                  class="series-line"
                  :d="s.path"
                  :stroke="s.color"
                  fill="none"
                />

                <g v-if="hoverTooltip">
                  <line
                    class="crosshair"
                    :x1="hoverTooltip.x"
                    :x2="hoverTooltip.x"
                    :y1="LINE_MARGIN.top"
                    :y2="LINE_CHART_H - LINE_MARGIN.bottom"
                  />
                  <circle
                    v-for="row in hoverTooltip.rows"
                    :key="row.name"
                    class="hover-dot"
                    :cx="hoverTooltip.x"
                    :cy="lineChart.series.find((s) => s.name === row.name).points[hoverIndex].y"
                    r="4"
                    :fill="row.color"
                  />
                </g>
              </svg>

              <div
                v-if="hoverTooltip"
                class="chart-tooltip"
                :style="{ left: `${(hoverTooltip.x / LINE_CHART_W) * 100}%` }"
              >
                <div class="tooltip-date">{{ hoverTooltip.date }}</div>
                <div v-for="row in hoverTooltip.rows" :key="row.name" class="tooltip-row">
                  <span class="tooltip-key" :style="{ background: row.color }"></span>
                  <span class="tooltip-name">{{ row.name }}</span>
                  <span class="tooltip-value">{{ peso(row.value) }}</span>
                </div>
              </div>
            </div>
            </div>

            <ul class="branch-totals">
              <li v-for="s in lineChart.series" :key="s.id">
                <span class="legend-swatch" :style="{ background: s.color }"></span>
                <span class="branch-totals-name">{{ s.name }}</span>
                <span class="branch-totals-value">{{ peso(s.total) }}</span>
              </li>
              <li class="branch-totals-all">
                <span class="branch-totals-name">All branches</span>
                <span class="branch-totals-value">{{ peso(monthly.total_sales) }}</span>
              </li>
            </ul>
          </div>
          <p v-else class="empty-hint">No sales recorded this month yet.</p>
        </template>
      </div>
    </template>
  </div>
</template>

<style scoped>
.dash {
  --dash-glow: rgba(255, 45, 77, 0.35);
}

.page-header {
  margin-bottom: 1.75rem;
  border-bottom: 1px solid var(--color-border);
}

.page-header h1 {
  font-size: 1.7rem;
  margin-bottom: 0.35rem;
  color: var(--color-text);
  letter-spacing: 0.02em;
}

.page-subtitle {
  color: var(--color-text-muted);
  margin: 0;
  font-family: "SFMono-Regular", Consolas, monospace;
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
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

.card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  box-shadow: var(--shadow);
  padding: 1.5rem;
  position: relative;
  overflow: hidden;
}

.card::before {
  content: "";
  position: absolute;
  inset: 0 0 auto 0;
  height: 2px;
  background: linear-gradient(90deg, var(--color-primary), transparent 70%);
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
  text-shadow: 0 0 18px var(--dash-glow);
}

.stat-card-alert .stat-value {
  color: var(--color-primary);
}

.chart-card {
  margin-bottom: 1.5rem;
}

.card-title {
  font-size: 0.95rem;
  margin-bottom: 1.25rem;
  color: var(--color-text);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.card-title::before {
  background: var(--color-primary);
  box-shadow: 0 0 8px var(--dash-glow);
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

.chart-scroll {
  overflow-x: auto;
}

.bar-chart {
  width: 100%;
  min-width: 480px;
  height: 220px;
  overflow: visible;
}

.baseline {
  stroke: var(--color-border);
  stroke-width: 1;
}

.bar {
  transition: opacity 0.15s ease, filter 0.15s ease;
  cursor: pointer;
  filter: drop-shadow(0 0 6px var(--dash-glow));
}

.bar-hover {
  opacity: 0.85;
  filter: drop-shadow(0 0 14px var(--dash-glow));
}

.alert-dot {
  fill: #ffb84d;
  filter: drop-shadow(0 0 4px rgba(255, 184, 77, 0.8));
}

.bar-value {
  font-family: "SFMono-Regular", Consolas, monospace;
  font-size: 12px;
  font-weight: 700;
  fill: var(--color-text);
}

.bar-name {
  font-size: 11px;
  fill: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.monthly-body {
  display: grid;
  grid-template-columns: 1fr 220px;
  gap: 1.5rem;
  align-items: start;
}

.line-chart-scroll {
  overflow-x: auto;
}

.line-chart-wrap {
  position: relative;
  min-width: 560px;
}

.line-chart {
  width: 100%;
  height: 260px;
  overflow: visible;
}

.gridline {
  stroke: var(--color-border);
  stroke-width: 1;
}

.axis-label {
  font-family: "SFMono-Regular", Consolas, monospace;
  font-size: 10px;
  fill: var(--color-text-muted);
}

.series-line {
  stroke-width: 2;
  stroke-linecap: round;
  stroke-linejoin: round;
  filter: drop-shadow(0 0 4px currentColor);
}

.crosshair {
  stroke: var(--color-border);
  stroke-width: 1;
}

.hover-dot {
  stroke: var(--color-surface);
  stroke-width: 2;
}

.chart-tooltip {
  position: absolute;
  top: 0;
  transform: translateX(-50%);
  background: var(--color-primary-dark);
  border: 1px solid var(--color-border);
  color: #fff;
  border-radius: 8px;
  padding: 0.6rem 0.75rem;
  font-size: 0.8rem;
  pointer-events: none;
  white-space: nowrap;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.6);
  z-index: 1;
}

.tooltip-date {
  font-weight: 700;
  margin-bottom: 0.35rem;
  font-family: "SFMono-Regular", Consolas, monospace;
}

.tooltip-row {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.tooltip-key {
  width: 10px;
  height: 3px;
  border-radius: 2px;
  flex-shrink: 0;
}

.tooltip-name {
  flex: 1;
  opacity: 0.85;
}

.tooltip-value {
  font-weight: 700;
  font-family: "SFMono-Regular", Consolas, monospace;
}

.legend-swatch {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.branch-totals {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  border-left: 1px solid var(--color-border);
  padding-left: 1.25rem;
}

.branch-totals li {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.85rem;
}

.branch-totals-name {
  flex: 1;
  color: var(--color-text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.branch-totals-value {
  font-family: "SFMono-Regular", Consolas, monospace;
  font-weight: 700;
  color: var(--color-text);
}

.branch-totals-all {
  margin-top: 0.4rem;
  padding-top: 0.6rem;
  border-top: 1px solid var(--color-border);
}

.branch-totals-all .branch-totals-name,
.branch-totals-all .branch-totals-value {
  color: var(--color-primary);
}

@media (max-width: 860px) {
  .stat-row {
    grid-template-columns: repeat(2, 1fr);
  }

  .monthly-body {
    grid-template-columns: 1fr;
  }

  .branch-totals {
    border-left: none;
    border-top: 1px solid var(--color-border);
    padding-left: 0;
    padding-top: 1rem;
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
