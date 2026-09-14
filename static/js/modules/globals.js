let globalColumns = [];
let numericColumns = [];
let categoricalColumns = [];
let calculatedColumns = []; // Kullanıcının ürettiği özel formül sütunları
let joinedColumns = []; // 2. dosyadan birleştirilen sütunlar
let sheetNames = [];
let currentChartData = null;
let currentStats = null;
let currentKpis = [];
let currentAiInsight = '';
let activeFileName = '';

// Seçim Durumu
let axisConfig = { x: null, y: [] };

// 🔍 Aktif Filtreler (Slicers)
let activeFilters = [];

// 🎛️ Çoklu Pano (Dashboard Canvas) Listesi
let dashboardCharts = [];

const PALETTE = ['#a78bfa', '#60a5fa', '#34d399', '#f472b6', '#fb923c', '#fbbf24', '#38bdf8', '#4ade80', '#c084fc', '#f97316'];
