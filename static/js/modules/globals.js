/* ════════════════════════════════════════════════════════════
   DATAVIZ PRO V6 — GLOBAL STATE & REACTIVE STORE
   Shared reactive state across all modules
════════════════════════════════════════════════════════════ */

var globalColumns = [];
var numericColumns = [];
var categoricalColumns = [];
var calculatedColumns = []; // Kullanıcının ürettiği özel formül sütunları
var joinedColumns = [];     // 2. dosyadan birleştirilen sütunlar
var sheetNames = [];
var currentChartData = null;
var currentStats = null;
var currentKpis = [];
var currentAiInsight = '';
var activeFileName = '';
var currentPlotType = '';

// Seçim Durumu (Eksenler)
var axisConfig = { x: null, y: [] };

// 🔍 Aktif Filtreler (Slicers)
var activeFilters = [];

// 🎛️ Çoklu Pano (Dashboard Canvas) Listesi
var dashboardCharts = [];

var PALETTE = ['#a78bfa', '#60a5fa', '#34d399', '#f472b6', '#fb923c', '#fbbf24', '#38bdf8', '#4ade80', '#c084fc', '#f97316'];

// Window nesnesine bağlama
window.globalColumns = globalColumns;
window.numericColumns = numericColumns;
window.categoricalColumns = categoricalColumns;
window.calculatedColumns = calculatedColumns;
window.joinedColumns = joinedColumns;
window.sheetNames = sheetNames;
window.currentChartData = currentChartData;
window.currentStats = currentStats;
window.currentKpis = currentKpis;
window.currentAiInsight = currentAiInsight;
window.activeFileName = activeFileName;
window.currentPlotType = currentPlotType;
window.axisConfig = axisConfig;
window.activeFilters = activeFilters;
window.dashboardCharts = dashboardCharts;
window.PALETTE = PALETTE;
