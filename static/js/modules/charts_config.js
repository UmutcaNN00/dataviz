// Safe Global Fallbacks
var axisConfig = window.axisConfig || { x: null, y: [] };
var numericColumns = window.numericColumns || [];
var categoricalColumns = window.categoricalColumns || [];
var activeFilters = window.activeFilters || [];
var PALETTE = window.PALETTE || [];

const CHART_SVGS = {
  "line": `<svg viewBox="0 0 24 24" class="dv-chart-svg"><path d="M3 18 L9 11 L14 15 L21 6"/><circle cx="3" cy="18" r="1.5" fill="currentColor"/><circle cx="9" cy="11" r="1.5" fill="currentColor"/><circle cx="14" cy="15" r="1.5" fill="currentColor"/><circle cx="21" cy="6" r="1.5" fill="currentColor"/><path d="M2 21h20" opacity="0.3"/></svg>`,
  "spline": `<svg viewBox="0 0 24 24" class="dv-chart-svg"><path d="M3 17 C 8 21, 8 7, 13 12 C 17 16, 18 6, 21 6"/><path d="M2 21h20" opacity="0.3"/></svg>`,
  "step": `<svg viewBox="0 0 24 24" class="dv-chart-svg"><path d="M3 18 H8 V13 H14 V8 H21"/><circle cx="3" cy="18" r="1.2" fill="currentColor"/><circle cx="8" cy="13" r="1.2" fill="currentColor"/><circle cx="14" cy="8" r="1.2" fill="currentColor"/><path d="M2 21h20" opacity="0.3"/></svg>`,
  "area": `<svg viewBox="0 0 24 24" class="dv-chart-svg"><path d="M3 18 L8 11 L14 15 L21 6 V21 H3 Z" fill="currentColor" fill-opacity="0.25"/><path d="M3 18 L8 11 L14 15 L21 6"/><path d="M2 21h20" opacity="0.3"/></svg>`,
  "stackedarea": `<svg viewBox="0 0 24 24" class="dv-chart-svg"><path d="M3 19 L9 15 L15 17 L21 12 V21 H3 Z" fill="currentColor" fill-opacity="0.35"/><path d="M3 13 L9 8 L15 12 L21 6 L21 12 L15 17 L9 15 L3 19 Z" fill="currentColor" fill-opacity="0.15"/><path d="M3 13 L9 8 L15 12 L21 6"/><path d="M3 19 L9 15 L15 17 L21 12"/><path d="M2 21h20" opacity="0.3"/></svg>`,
  "waterfall": `<svg viewBox="0 0 24 24" class="dv-chart-svg"><rect x="3" y="11" width="3.2" height="9" rx="0.6" fill="currentColor" fill-opacity="0.4"/><rect x="7.8" y="7" width="3.2" height="5" rx="0.6" fill="currentColor" fill-opacity="0.8"/><rect x="12.6" y="10" width="3.2" height="4" rx="0.6" fill="currentColor" fill-opacity="0.5"/><rect x="17.4" y="5" width="3.2" height="9" rx="0.6" fill="currentColor" fill-opacity="0.9"/><line x1="6.2" y1="12" x2="7.8" y2="12" stroke-dasharray="1 1" opacity="0.5"/><line x1="11" y1="12" x2="12.6" y2="12" stroke-dasharray="1 1" opacity="0.5"/><line x1="15.8" y1="14" x2="17.4" y2="14" stroke-dasharray="1 1" opacity="0.5"/><path d="M2 21h20" opacity="0.3"/></svg>`,
  "candlestick": `<svg viewBox="0 0 24 24" class="dv-chart-svg"><line x1="7" y1="3" x2="7" y2="21"/><rect x="5" y="7" width="4" height="8" rx="0.5" fill="currentColor" fill-opacity="0.75"/><line x1="17" y1="4" x2="17" y2="20"/><rect x="15" y="8" width="4" height="7" rx="0.5" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M2 21h20" opacity="0.3"/></svg>`,
  "ohlc": `<svg viewBox="0 0 24 24" class="dv-chart-svg"><line x1="7" y1="4" x2="7" y2="20"/><line x1="4" y1="9" x2="7" y2="9"/><line x1="7" y1="15" x2="10" y2="15"/><line x1="17" y1="4" x2="17" y2="20"/><line x1="14" y1="15" x2="17" y2="15"/><line x1="17" y1="8" x2="20" y2="8"/><path d="M2 21h20" opacity="0.3"/></svg>`,
  "bar": `<svg viewBox="0 0 24 24" class="dv-chart-svg"><rect x="4" y="11" width="3.5" height="9" rx="0.8" fill="currentColor" fill-opacity="0.3"/><rect x="10.25" y="4" width="3.5" height="16" rx="0.8" fill="currentColor" fill-opacity="0.85"/><rect x="16.5" y="8" width="3.5" height="12" rx="0.8" fill="currentColor" fill-opacity="0.55"/><path d="M2 21h20" opacity="0.3"/></svg>`,
  "horizontalbar": `<svg viewBox="0 0 24 24" class="dv-chart-svg"><rect x="4" y="4" width="16" height="3.5" rx="0.8" fill="currentColor" fill-opacity="0.85"/><rect x="4" y="10.25" width="10" height="3.5" rx="0.8" fill="currentColor" fill-opacity="0.4"/><rect x="4" y="16.5" width="14" height="3.5" rx="0.8" fill="currentColor" fill-opacity="0.65"/><path d="M3 2v20" opacity="0.3"/></svg>`,
  "groupedbar": `<svg viewBox="0 0 24 24" class="dv-chart-svg"><rect x="3" y="11" width="3" height="9" rx="0.5" fill="currentColor" fill-opacity="0.4"/><rect x="6.8" y="6" width="3" height="14" rx="0.5" fill="currentColor" fill-opacity="0.85"/><rect x="14" y="9" width="3" height="11" rx="0.5" fill="currentColor" fill-opacity="0.4"/><rect x="17.8" y="4" width="3" height="16" rx="0.5" fill="currentColor" fill-opacity="0.85"/><path d="M2 21h20" opacity="0.3"/></svg>`,
  "stackedbar": `<svg viewBox="0 0 24 24" class="dv-chart-svg"><rect x="5" y="14" width="4.5" height="6" rx="0.5" fill="currentColor" fill-opacity="0.3"/><rect x="5" y="7" width="4.5" height="6.5" rx="0.5" fill="currentColor" fill-opacity="0.65"/><rect x="5" y="3" width="4.5" height="3.5" rx="0.5" fill="currentColor" fill-opacity="0.95"/><rect x="14" y="12" width="4.5" height="8" rx="0.5" fill="currentColor" fill-opacity="0.3"/><rect x="14" y="6" width="4.5" height="5.5" rx="0.5" fill="currentColor" fill-opacity="0.75"/><path d="M2 21h20" opacity="0.3"/></svg>`,
  "funnel": `<svg viewBox="0 0 24 24" class="dv-chart-svg"><polygon points="3,4 21,4 17,9 7,9" fill="currentColor" fill-opacity="0.8"/><polygon points="7,10 17,10 15,15 9,15" fill="currentColor" fill-opacity="0.55"/><polygon points="9,16 15,16 13,20 11,20" fill="currentColor" fill-opacity="0.3"/></svg>`,
  "radar": `<svg viewBox="0 0 24 24" class="dv-chart-svg"><polygon points="12,2 21,8.5 18,19.5 6,19.5 3,8.5" opacity="0.35" fill="none"/><polygon points="12,6 18,11 16,17.5 8,17.5 6,11" fill="currentColor" fill-opacity="0.25"/><line x1="12" y1="2" x2="12" y2="19.5" opacity="0.3"/><line x1="3" y1="8.5" x2="21" y2="8.5" opacity="0.3"/></svg>`,
  "dotplot": `<svg viewBox="0 0 24 24" class="dv-chart-svg"><line x1="4" y1="6" x2="20" y2="6" opacity="0.3"/><line x1="4" y1="12" x2="20" y2="12" opacity="0.3"/><line x1="4" y1="18" x2="20" y2="18" opacity="0.3"/><circle cx="16" cy="6" r="2.5" fill="currentColor"/><circle cx="9" cy="12" r="2.5" fill="currentColor"/><circle cx="14" cy="18" r="2.5" fill="currentColor"/></svg>`,
  "bullet": `<svg viewBox="0 0 24 24" class="dv-chart-svg"><rect x="3" y="6" width="18" height="12" rx="1" opacity="0.2" fill="currentColor"/><rect x="3" y="8" width="13" height="8" fill="currentColor" fill-opacity="0.55"/><rect x="3" y="10" width="9" height="4" fill="currentColor"/><line x1="16" y1="5" x2="16" y2="19" stroke-width="2.5"/></svg>`,
  "dumbbell": `<svg viewBox="0 0 24 24" class="dv-chart-svg"><line x1="6" y1="8" x2="18" y2="8" stroke-width="2"/><circle cx="6" cy="8" r="2.5" fill="currentColor"/><circle cx="18" cy="8" r="2.5" fill="none" stroke="currentColor" stroke-width="2"/><line x1="8" y1="15" x2="16" y2="15" stroke-width="2"/><circle cx="8" cy="15" r="2.5" fill="currentColor"/><circle cx="16" cy="15" r="2.5" fill="none" stroke="currentColor" stroke-width="2"/><path d="M2 21h20" opacity="0.3"/></svg>`,
  "lollipop": `<svg viewBox="0 0 24 24" class="dv-chart-svg"><line x1="6" y1="8" x2="6" y2="20"/><circle cx="6" cy="8" r="2.5" fill="currentColor" fill-opacity="0.5"/><line x1="12" y1="4" x2="12" y2="20"/><circle cx="12" cy="4" r="2.5" fill="currentColor"/><line x1="18" y1="11" x2="18" y2="20"/><circle cx="18" cy="11" r="2.5" fill="currentColor" fill-opacity="0.75"/><path d="M2 21h20" opacity="0.3"/></svg>`,
  "gauge": `<svg viewBox="0 0 24 24" class="dv-chart-svg"><path d="M4 17 A 8 8 0 0 1 20 17" fill="none" stroke-width="2.5"/><line x1="12" y1="17" x2="16" y2="10" stroke-width="2"/><circle cx="12" cy="17" r="2" fill="currentColor"/></svg>`,
  "radialbar": `<svg viewBox="0 0 24 24" class="dv-chart-svg"><path d="M12 4 A 8 8 0 1 1 5 16" fill="none" stroke-width="2.2"/><path d="M12 7 A 5 5 0 1 1 8 15" fill="none" stroke-width="2.2" opacity="0.55"/></svg>`,
  "histogram": `<svg viewBox="0 0 24 24" class="dv-chart-svg"><rect x="3" y="13" width="3.4" height="7" fill="currentColor" fill-opacity="0.35"/><rect x="6.6" y="7" width="3.4" height="13" fill="currentColor" fill-opacity="0.65"/><rect x="10.2" y="4" width="3.4" height="16" fill="currentColor" fill-opacity="0.9"/><rect x="13.8" y="8" width="3.4" height="12" fill="currentColor" fill-opacity="0.6"/><rect x="17.4" y="14" width="3.4" height="6" fill="currentColor" fill-opacity="0.3"/><path d="M2 21h20" opacity="0.3"/></svg>`,
  "histogram2d": `<svg viewBox="0 0 24 24" class="dv-chart-svg"><rect x="4" y="4" width="4.5" height="4.5" rx="0.5" opacity="0.2" fill="currentColor"/><rect x="9.75" y="4" width="4.5" height="4.5" rx="0.5" opacity="0.5" fill="currentColor"/><rect x="15.5" y="4" width="4.5" height="4.5" rx="0.5" opacity="0.3" fill="currentColor"/><rect x="4" y="9.75" width="4.5" height="4.5" rx="0.5" opacity="0.4" fill="currentColor"/><rect x="9.75" y="9.75" width="4.5" height="4.5" rx="0.5" opacity="0.9" fill="currentColor"/><rect x="15.5" y="9.75" width="4.5" height="4.5" rx="0.5" opacity="0.6" fill="currentColor"/><rect x="4" y="15.5" width="4.5" height="4.5" rx="0.5" opacity="0.25" fill="currentColor"/><rect x="9.75" y="15.5" width="4.5" height="4.5" rx="0.5" opacity="0.55" fill="currentColor"/><rect x="15.5" y="15.5" width="4.5" height="4.5" rx="0.5" opacity="0.2" fill="currentColor"/></svg>`,
  "box": `<svg viewBox="0 0 24 24" class="dv-chart-svg"><line x1="12" y1="3" x2="12" y2="7"/><line x1="9" y1="3" x2="15" y2="3"/><rect x="7" y="7" width="10" height="10" rx="1" fill="currentColor" fill-opacity="0.25" stroke="currentColor" stroke-width="1.8"/><line x1="7" y1="12" x2="17" y2="12" stroke-width="2.5"/><line x1="12" y1="17" x2="12" y2="21"/><line x1="9" y1="21" x2="15" y2="21"/></svg>`,
  "violin": `<svg viewBox="0 0 24 24" class="dv-chart-svg"><path d="M12 3 C 8 7, 7 10, 10 12 C 7 14, 8 17, 12 21 C 16 17, 17 14, 14 12 C 17 10, 16 7, 12 3 Z" fill="currentColor" fill-opacity="0.25" stroke="currentColor" stroke-width="1.8"/><line x1="12" y1="7" x2="12" y2="17" stroke-width="2"/><circle cx="12" cy="12" r="1.5" fill="currentColor"/></svg>`,
  "strip": `<svg viewBox="0 0 24 24" class="dv-chart-svg"><circle cx="7" cy="8" r="1.5" fill="currentColor"/><circle cx="11" cy="8" r="1.5" fill="currentColor"/><circle cx="13" cy="8" r="1.5" fill="currentColor"/><circle cx="18" cy="8" r="1.5" fill="currentColor"/><circle cx="5" cy="15" r="1.5" fill="currentColor"/><circle cx="9" cy="15" r="1.5" fill="currentColor"/><circle cx="14" cy="15" r="1.5" fill="currentColor"/><circle cx="19" cy="15" r="1.5" fill="currentColor"/><path d="M2 21h20" opacity="0.3"/></svg>`,
  "rug": `<svg viewBox="0 0 24 24" class="dv-chart-svg"><path d="M3 11 C 7 6, 13 14, 21 6"/><line x1="3" y1="20" x2="21" y2="20" opacity="0.3"/><line x1="5" y1="17" x2="5" y2="21"/><line x1="7" y1="16" x2="7" y2="21"/><line x1="8.5" y1="16" x2="8.5" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/><line x1="15" y1="16" x2="15" y2="21"/><line x1="16.5" y1="16" x2="16.5" y2="21"/><line x1="19" y1="17" x2="19" y2="21"/></svg>`,
  "density2d": `<svg viewBox="0 0 24 24" class="dv-chart-svg"><ellipse cx="12" cy="12" rx="9" ry="7" fill="none" opacity="0.35"/><ellipse cx="12" cy="12" rx="6" ry="4.5" fill="none" opacity="0.65"/><ellipse cx="12" cy="12" rx="3" ry="2" fill="currentColor" fill-opacity="0.4"/></svg>`,
  "errorbar": `<svg viewBox="0 0 24 24" class="dv-chart-svg"><line x1="6" y1="6" x2="6" y2="16"/><line x1="4" y1="6" x2="8" y2="6"/><line x1="4" y1="16" x2="8" y2="16"/><circle cx="6" cy="11" r="2" fill="currentColor"/><line x1="16" y1="4" x2="16" y2="18"/><line x1="14" y1="4" x2="18" y2="4"/><line x1="14" y1="18" x2="18" y2="18"/><circle cx="16" cy="10" r="2" fill="currentColor"/><path d="M2 21h20" opacity="0.3"/></svg>`,
  "scatter": `<svg viewBox="0 0 24 24" class="dv-chart-svg"><circle cx="6" cy="16" r="2" fill="currentColor"/><circle cx="10" cy="13" r="2" fill="currentColor"/><circle cx="13" cy="9" r="2" fill="currentColor"/><circle cx="17" cy="12" r="2" fill="currentColor"/><circle cx="18" cy="6" r="2" fill="currentColor"/><circle cx="8" cy="8" r="2" fill="currentColor" opacity="0.6"/><path d="M2 21h20" opacity="0.3"/><path d="M2 2v19" opacity="0.3"/></svg>`,
  "bubble": `<svg viewBox="0 0 24 24" class="dv-chart-svg"><circle cx="7" cy="14" r="3.5" fill="currentColor" fill-opacity="0.35" stroke="currentColor"/><circle cx="16" cy="8" r="5" fill="currentColor" fill-opacity="0.45" stroke="currentColor"/><circle cx="14" cy="16" r="2.2" fill="currentColor" fill-opacity="0.65" stroke="currentColor"/><path d="M2 21h20" opacity="0.3"/><path d="M2 2v19" opacity="0.3"/></svg>`,
  "scattermatrix": `<svg viewBox="0 0 24 24" class="dv-chart-svg"><rect x="3" y="3" width="7" height="7" rx="1" fill="none" opacity="0.4"/><rect x="14" y="3" width="7" height="7" rx="1" fill="none" opacity="0.4"/><rect x="3" y="14" width="7" height="7" rx="1" fill="none" opacity="0.4"/><rect x="14" y="14" width="7" height="7" rx="1" fill="none" opacity="0.4"/><circle cx="6.5" cy="6.5" r="1.2" fill="currentColor"/><circle cx="17.5" cy="6.5" r="1.2" fill="currentColor"/><circle cx="6.5" cy="17.5" r="1.2" fill="currentColor"/><circle cx="17.5" cy="17.5" r="1.2" fill="currentColor"/></svg>`,
  "heatmap": `<svg viewBox="0 0 24 24" class="dv-chart-svg"><rect x="3" y="3" width="5.2" height="5.2" rx="0.8" fill="currentColor" fill-opacity="0.2"/><rect x="9.4" y="3" width="5.2" height="5.2" rx="0.8" fill="currentColor" fill-opacity="0.55"/><rect x="15.6" y="3" width="5.2" height="5.2" rx="0.8" fill="currentColor" fill-opacity="0.9"/><rect x="3" y="9.4" width="5.2" height="5.2" rx="0.8" fill="currentColor" fill-opacity="0.65"/><rect x="9.4" y="9.4" width="5.2" height="5.2" rx="0.8" fill="currentColor" fill-opacity="0.9"/><rect x="15.6" y="9.4" width="5.2" height="5.2" rx="0.8" fill="currentColor" fill-opacity="0.4"/><rect x="3" y="15.6" width="5.2" height="5.2" rx="0.8" fill="currentColor" fill-opacity="0.9"/><rect x="9.4" y="15.6" width="5.2" height="5.2" rx="0.8" fill="currentColor" fill-opacity="0.35"/><rect x="15.6" y="15.6" width="5.2" height="5.2" rx="0.8" fill="currentColor" fill-opacity="0.15"/></svg>`,
  "parcoords": `<svg viewBox="0 0 24 24" class="dv-chart-svg"><line x1="5" y1="3" x2="5" y2="21" opacity="0.4"/><line x1="12" y1="3" x2="12" y2="21" opacity="0.4"/><line x1="19" y1="3" x2="19" y2="21" opacity="0.4"/><path d="M5 8 L12 16 L19 10" stroke-width="1.8"/><path d="M5 16 L12 6 L19 15" stroke-width="1.8" opacity="0.6"/></svg>`,
  "parcats": `<svg viewBox="0 0 24 24" class="dv-chart-svg"><line x1="4" y1="4" x2="4" y2="20" stroke-width="3"/><line x1="20" y1="4" x2="20" y2="20" stroke-width="3"/><path d="M4 6 C 12 6, 12 14, 20 14" stroke-width="2.2" opacity="0.75"/><path d="M4 14 C 12 14, 12 6, 20 6" stroke-width="2.2" opacity="0.45"/></svg>`,
  "pie": `<svg viewBox="0 0 24 24" class="dv-chart-svg"><circle cx="12" cy="12" r="9" fill="none" stroke-width="2"/><path d="M12 12 L12 3 A 9 9 0 0 1 21 12 Z" fill="currentColor" fill-opacity="0.35"/><path d="M12 12 L21 12 A 9 9 0 0 1 12 21 Z" fill="currentColor" fill-opacity="0.8"/></svg>`,
  "donut": `<svg viewBox="0 0 24 24" class="dv-chart-svg"><circle cx="12" cy="12" r="8.5" fill="none" stroke-width="3.5" opacity="0.25"/><circle cx="12" cy="12" r="8.5" fill="none" stroke-width="3.5" stroke-dasharray="24 53" stroke="currentColor"/></svg>`,
  "sunburst": `<svg viewBox="0 0 24 24" class="dv-chart-svg"><circle cx="12" cy="12" r="3.2" fill="currentColor" fill-opacity="0.8"/><circle cx="12" cy="12" r="6.5" fill="none" stroke-width="1.8" stroke-dasharray="9 3 14 4"/><circle cx="12" cy="12" r="9.5" fill="none" stroke-width="1.8" stroke-dasharray="6 2 7 3 11 3" opacity="0.7"/></svg>`,
  "treemap": `<svg viewBox="0 0 24 24" class="dv-chart-svg"><rect x="3" y="3" width="18" height="18" rx="1.5" fill="none" stroke-width="1.5"/><rect x="3" y="3" width="11" height="12" fill="currentColor" fill-opacity="0.6"/><rect x="14" y="3" width="7" height="6" fill="currentColor" fill-opacity="0.3"/><rect x="14" y="9" width="7" height="6" fill="currentColor" fill-opacity="0.45"/><rect x="3" y="15" width="18" height="6" fill="currentColor" fill-opacity="0.2"/></svg>`,
  "funnelarea": `<svg viewBox="0 0 24 24" class="dv-chart-svg"><path d="M4 4 L20 4 L17 10 L7 10 Z" fill="currentColor" fill-opacity="0.8"/><path d="M7 11 L17 11 L15 16 L9 16 Z" fill="currentColor" fill-opacity="0.55"/><path d="M9 17 L15 17 L13 20 L11 20 Z" fill="currentColor" fill-opacity="0.3"/></svg>`,
  "icicle": `<svg viewBox="0 0 24 24" class="dv-chart-svg"><rect x="3" y="3" width="18" height="4" rx="0.5" fill="currentColor" fill-opacity="0.9"/><rect x="3" y="8" width="9" height="5" rx="0.5" fill="currentColor" fill-opacity="0.6"/><rect x="12" y="8" width="9" height="5" rx="0.5" fill="currentColor" fill-opacity="0.4"/><rect x="3" y="14" width="4" height="6" rx="0.5" fill="currentColor" fill-opacity="0.3"/><rect x="7.5" y="14" width="4.5" height="6" rx="0.5" fill="currentColor" fill-opacity="0.5"/><rect x="12.5" y="14" width="8.5" height="6" rx="0.5" fill="currentColor" fill-opacity="0.2"/></svg>`,
  "scatter3d": `<svg viewBox="0 0 24 24" class="dv-chart-svg"><path d="M12 3 L12 12 L21 16 M12 12 L3 16" opacity="0.4"/><circle cx="14" cy="8" r="1.8" fill="currentColor"/><circle cx="8" cy="11" r="2.2" fill="currentColor" fill-opacity="0.6"/><circle cx="16" cy="13" r="1.5" fill="currentColor" fill-opacity="0.8"/><circle cx="9" cy="15" r="2.4" fill="currentColor"/></svg>`,
  "line3d": `<svg viewBox="0 0 24 24" class="dv-chart-svg"><path d="M12 3 L12 12 L21 16 M12 12 L3 16" opacity="0.3"/><path d="M6 14 C 9 7, 11 16, 17 7" stroke-width="2"/></svg>`,
  "surface": `<svg viewBox="0 0 24 24" class="dv-chart-svg"><path d="M3 15 Q 12 7, 21 15 M3 11 Q 12 3, 21 11" fill="none" opacity="0.4"/><path d="M3 15 L3 11 M12 11 L12 7 M21 15 L21 11" opacity="0.3"/><path d="M3 15 C 8 18, 16 10, 21 15 L21 19 L3 19 Z" fill="currentColor" fill-opacity="0.25"/></svg>`,
  "contour": `<svg viewBox="0 0 24 24" class="dv-chart-svg"><ellipse cx="12" cy="12" rx="9" ry="7" fill="none" opacity="0.3"/><ellipse cx="12" cy="12" rx="6" ry="4.5" fill="none" opacity="0.6"/><ellipse cx="12" cy="12" rx="2.5" ry="2" fill="none"/></svg>`,
  "polarbar": `<svg viewBox="0 0 24 24" class="dv-chart-svg"><circle cx="12" cy="12" r="9" opacity="0.2" fill="none"/><path d="M12 12 L12 4 A 8 8 0 0 1 17 6 Z" fill="currentColor" fill-opacity="0.8"/><path d="M12 12 L19 12 A 7 7 0 0 1 17 17 Z" fill="currentColor" fill-opacity="0.5"/><path d="M12 12 L7 17 A 6 6 0 0 1 5 12 Z" fill="currentColor" fill-opacity="0.65"/></svg>`,
  "polarscatter": `<svg viewBox="0 0 24 24" class="dv-chart-svg"><circle cx="12" cy="12" r="9" opacity="0.2" fill="none"/><circle cx="12" cy="12" r="5" opacity="0.3" fill="none"/><circle cx="12" cy="5" r="1.8" fill="currentColor"/><circle cx="17" cy="14" r="1.8" fill="currentColor"/><circle cx="8" cy="15" r="1.8" fill="currentColor"/></svg>`,
  "windrose": `<svg viewBox="0 0 24 24" class="dv-chart-svg"><circle cx="12" cy="12" r="9" opacity="0.2" fill="none"/><path d="M12 3 L13.5 10.5 L12 12 L10.5 10.5 Z" fill="currentColor"/><path d="M21 12 L13.5 13.5 L12 12 L13.5 10.5 Z" fill="currentColor" fill-opacity="0.75"/><path d="M12 21 L10.5 13.5 L12 12 L13.5 13.5 Z" fill="currentColor" fill-opacity="0.5"/><path d="M3 12 L10.5 10.5 L12 12 L10.5 13.5 Z" fill="currentColor" fill-opacity="0.75"/></svg>`,
  "ternary": `<svg viewBox="0 0 24 24" class="dv-chart-svg"><polygon points="12,3 21,19 3,19" fill="none" stroke-width="1.8"/><circle cx="12" cy="12" r="2" fill="currentColor"/><circle cx="9" cy="16" r="2" fill="currentColor" opacity="0.7"/><circle cx="15" cy="15" r="2" fill="currentColor" opacity="0.6"/></svg>`,
  "carpet": `<svg viewBox="0 0 24 24" class="dv-chart-svg"><path d="M4 7 C 10 9, 14 5, 20 7" opacity="0.7"/><path d="M4 12 C 10 14, 14 10, 20 12"/><path d="M4 17 C 10 19, 14 15, 20 17" opacity="0.7"/><path d="M6 5 C 7 11, 5 15, 6 19" opacity="0.45"/><path d="M12 5 C 13 11, 11 15, 12 19" opacity="0.45"/><path d="M18 5 C 19 11, 17 15, 18 19" opacity="0.45"/></svg>`,
  "scattergeo": `<svg viewBox="0 0 24 24" class="dv-chart-svg"><circle cx="12" cy="12" r="9" fill="none" opacity="0.35"/><ellipse cx="12" cy="12" rx="4" ry="9" fill="none" opacity="0.35"/><line x1="3" y1="12" x2="21" y2="12" opacity="0.35"/><circle cx="15" cy="8" r="2" fill="currentColor"/><circle cx="8" cy="14" r="2" fill="currentColor"/></svg>`,
  "sankey": `<svg viewBox="0 0 24 24" class="dv-chart-svg"><rect x="3" y="5" width="2.5" height="14" rx="0.5" fill="currentColor"/><rect x="18.5" y="4" width="2.5" height="7" rx="0.5" fill="currentColor" fill-opacity="0.8"/><rect x="18.5" y="13" width="2.5" height="7" rx="0.5" fill="currentColor" fill-opacity="0.6"/><path d="M5.5 7 C 12 7, 12 6, 18.5 6 L 18.5 10 C 12 10, 12 12, 5.5 12 Z" fill="currentColor" fill-opacity="0.3"/><path d="M5.5 13 C 12 13, 12 15, 18.5 15 L 18.5 18 C 12 18, 12 17, 5.5 17 Z" fill="currentColor" fill-opacity="0.2"/></svg>`,
};
window.CHART_SVGS = CHART_SVGS;

const CHARTS = [
  // 📈 TREND
  {
    id: "line",
    name: "Çizgi",
    cat: "trend",
    icon: CHART_SVGS["line"],
    desc: "Zaman/Kategori trendi.",
  },
  {
    id: "spline",
    name: "Yumuşak Çizgi",
    cat: "trend",
    icon: CHART_SVGS["spline"],
    desc: "Kıvrımlı, pürüzsüz trend.",
  },
  {
    id: "step",
    name: "Basamak",
    cat: "trend",
    icon: CHART_SVGS["step"],
    desc: "Sıçramalı değişimler.",
  },
  {
    id: "area",
    name: "Alan",
    cat: "trend",
    icon: CHART_SVGS["area"],
    desc: "Altı dolu çizgi.",
  },
  {
    id: "stackedarea",
    name: "Yığılmış Alan",
    cat: "trend",
    icon: CHART_SVGS["stackedarea"],
    desc: "Kümülatif alan toplamı.",
  },
  {
    id: "waterfall",
    name: "Şelale",
    cat: "trend",
    icon: CHART_SVGS["waterfall"],
    desc: "Artış/Azalış etkileri.",
  },
  {
    id: "candlestick",
    name: "Mum (Finance)",
    cat: "trend",
    icon: CHART_SVGS["candlestick"],
    desc: "Finansal O/H/L/C.",
  },
  {
    id: "ohlc",
    name: "OHLC",
    cat: "trend",
    icon: CHART_SVGS["ohlc"],
    desc: "Finansal çubuk.",
  },

  // 📊 KIYASLAMA
  {
    id: "bar",
    name: "Çubuk",
    cat: "comp",
    icon: CHART_SVGS["bar"],
    desc: "Basit kıyaslama.",
  },
  {
    id: "horizontalbar",
    name: "Yatay Çubuk",
    cat: "comp",
    icon: CHART_SVGS["horizontalbar"],
    desc: "Uzun isimli kategoriler.",
  },
  {
    id: "groupedbar",
    name: "Gruplu Çubuk",
    cat: "comp",
    icon: CHART_SVGS["groupedbar"],
    desc: "Çoklu metrik kıyası.",
  },
  {
    id: "stackedbar",
    name: "Yığılmış Çubuk",
    cat: "comp",
    icon: CHART_SVGS["stackedbar"],
    desc: "Parça/Bütün kıyası.",
  },
  {
    id: "funnel",
    name: "Huni",
    cat: "comp",
    icon: CHART_SVGS["funnel"],
    desc: "Dönüşüm aşamaları.",
  },
  {
    id: "radar",
    name: "Radar (Örümcek)",
    cat: "comp",
    icon: CHART_SVGS["radar"],
    desc: "Çoklu eksen profili.",
  },
  {
    id: "dotplot",
    name: "Nokta Kıyas",
    cat: "comp",
    icon: CHART_SVGS["dotplot"],
    desc: "Hafif kıyaslama.",
  },
  {
    id: "bullet",
    name: "Bullet / KPI",
    cat: "comp",
    icon: CHART_SVGS["bullet"],
    desc: "Hedef takibi.",
  },
  {
    id: "dumbbell",
    name: "Halter (Dumbbell)",
    cat: "comp",
    icon: CHART_SVGS["dumbbell"],
    desc: "İki nokta arası fark.",
  },
  {
    id: "lollipop",
    name: "Lolipop",
    cat: "comp",
    icon: CHART_SVGS["lollipop"],
    desc: "Hafif çubuk kıyası.",
  },
  {
    id: "gauge",
    name: "Kadran (Gauge)",
    cat: "comp",
    icon: CHART_SVGS["gauge"],
    desc: "İbreli hedef göstergesi.",
  },
  {
    id: "radialbar",
    name: "Radyal Çubuk",
    cat: "comp",
    icon: CHART_SVGS["radialbar"],
    desc: "Dairesel oran kıyası.",
  },

  // 📉 DAĞILIM
  {
    id: "histogram",
    name: "Histogram",
    cat: "dist",
    icon: CHART_SVGS["histogram"],
    desc: "Frekans dağılımı.",
  },
  {
    id: "histogram2d",
    name: "2D Histogram",
    cat: "dist",
    icon: CHART_SVGS["histogram2d"],
    desc: "Matris yoğunluğu.",
  },
  {
    id: "box",
    name: "Kutu (Box)",
    cat: "dist",
    icon: CHART_SVGS["box"],
    desc: "Medyan ve çeyreklikler.",
  },
  {
    id: "violin",
    name: "Keman (Violin)",
    cat: "dist",
    icon: CHART_SVGS["violin"],
    desc: "Yoğunluk ve kutu.",
  },
  {
    id: "strip",
    name: "Şerit (Strip)",
    cat: "dist",
    icon: CHART_SVGS["strip"],
    desc: "Nokta yoğunluğu.",
  },
  {
    id: "rug",
    name: "Halı (Rug)",
    cat: "dist",
    icon: CHART_SVGS["rug"],
    desc: "Eksen üstü dağılım.",
  },
  {
    id: "density2d",
    name: "2D Yoğunluk",
    cat: "dist",
    icon: CHART_SVGS["density2d"],
    desc: "Kontur yoğunluğu.",
  },
  {
    id: "errorbar",
    name: "Hata Çubuğu",
    cat: "dist",
    icon: CHART_SVGS["errorbar"],
    desc: "Varyans/Hata payı.",
  },

  // 🔵 İLİŞKİ
  {
    id: "scatter",
    name: "Dağılım (Scatter)",
    cat: "rel",
    icon: CHART_SVGS["scatter"],
    desc: "Korelasyon.",
  },
  {
    id: "bubble",
    name: "Balon (Bubble)",
    cat: "rel",
    icon: CHART_SVGS["bubble"],
    desc: "3. boyut olarak büyüklük.",
  },
  {
    id: "scattermatrix",
    name: "Scatter Matris",
    cat: "rel",
    icon: CHART_SVGS["scattermatrix"],
    desc: "Tüm sütunların çarprazı.",
  },
  {
    id: "heatmap",
    name: "Isı Haritası",
    cat: "rel",
    icon: CHART_SVGS["heatmap"],
    desc: "Korelasyon matrisi.",
  },
  {
    id: "parcoords",
    name: "Paralel Koor.",
    cat: "rel",
    icon: CHART_SVGS["parcoords"],
    desc: "Sürekli çoklu ilişki.",
  },
  {
    id: "parcats",
    name: "Paralel Kateg.",
    cat: "rel",
    icon: CHART_SVGS["parcats"],
    desc: "Kategorik çoklu ilişki.",
  },

  // 🥧 PARÇA-BÜTÜN
  {
    id: "pie",
    name: "Pasta",
    cat: "part",
    icon: CHART_SVGS["pie"],
    desc: "Bütünün parçaları.",
  },
  {
    id: "donut",
    name: "Donut",
    cat: "part",
    icon: CHART_SVGS["donut"],
    desc: "Ortası boş pasta.",
  },
  {
    id: "sunburst",
    name: "Sunburst",
    cat: "part",
    icon: CHART_SVGS["sunburst"],
    desc: "Hiyerarşik pasta.",
  },
  {
    id: "treemap",
    name: "Ağaç (Treemap)",
    cat: "part",
    icon: CHART_SVGS["treemap"],
    desc: "Hiyerarşik kareler.",
  },
  {
    id: "funnelarea",
    name: "Huni Alanı",
    cat: "part",
    icon: CHART_SVGS["funnelarea"],
    desc: "Oransal dilimler.",
  },
  {
    id: "icicle",
    name: "Sarkıt (Icicle)",
    cat: "part",
    icon: CHART_SVGS["icicle"],
    desc: "Yukarıdan aşağı hiyerarşi.",
  },

  // 🌌 3D & BİLİMSEL
  {
    id: "scatter3d",
    name: "3D Scatter",
    cat: "sci",
    icon: CHART_SVGS["scatter3d"],
    desc: "Uzaysal korelasyon.",
  },
  {
    id: "line3d",
    name: "3D Çizgi",
    cat: "sci",
    icon: CHART_SVGS["line3d"],
    desc: "Uzayda yol.",
  },
  {
    id: "surface",
    name: "3D Yüzey",
    cat: "sci",
    icon: CHART_SVGS["surface"],
    desc: "Topolojik yüzey.",
  },
  {
    id: "contour",
    name: "Kontur",
    cat: "sci",
    icon: CHART_SVGS["contour"],
    desc: "Eş-yükselti haritası.",
  },
  {
    id: "polarbar",
    name: "Polar Çubuk",
    cat: "sci",
    icon: CHART_SVGS["polarbar"],
    desc: "Dairesel çubuk.",
  },
  {
    id: "polarscatter",
    name: "Polar Scatter",
    cat: "sci",
    icon: CHART_SVGS["polarscatter"],
    desc: "Kutupsal nokta.",
  },
  {
    id: "windrose",
    name: "Rüzgar Gülü",
    cat: "sci",
    icon: CHART_SVGS["windrose"],
    desc: "Yönsel frekans.",
  },
  {
    id: "ternary",
    name: "Ternary",
    cat: "sci",
    icon: CHART_SVGS["ternary"],
    desc: "3 eksenli üçgen.",
  },
  {
    id: "carpet",
    name: "Halı (Carpet)",
    cat: "sci",
    icon: CHART_SVGS["carpet"],
    desc: "Eğrisel koordinatlar.",
  },

  // Yedekler
  {
    id: "scattergeo",
    name: "Harita (Geo)",
    cat: "sci",
    icon: CHART_SVGS["scattergeo"],
    desc: "Coğrafi noktalar.",
  },
  {
    id: "sankey",
    name: "Akış (Sankey)",
    cat: "part",
    icon: CHART_SVGS["sankey"],
    desc: "A'dan B'ye akış.",
  },
];

function buildLayout(bg, sGrid, sLeg, isMini = false) {
  const currentTheme =
    document.documentElement.getAttribute("data-theme") || "dark";
  const isLight =
    currentTheme === "light" ||
    (bg &&
      ["#ffffff", "#fff", "#f8fafc", "white"].includes(String(bg).toLowerCase()));
  const gc = sGrid
    ? isLight
      ? "rgba(15, 23, 42, 0.08)"
      : "rgba(255, 255, 255, 0.08)"
    : "transparent";
  const tc = isLight ? "#0f172a" : "#f5f5f7";
  const plotBg = isLight ? (bg && bg !== "transparent" ? bg : "#ffffff") : (bg || "transparent");
  const customTitle = !isMini
    ? document.getElementById("customChartTitle")?.value?.trim() || ""
    : "";
  const titleSize = isMini ? 12 : 16;
  const layout = {
    autosize: true,
    paper_bgcolor: "transparent",
    plot_bgcolor: plotBg,
    font: { family: "Inter", color: tc },
    showlegend: sLeg,
    legend: { bgcolor: "transparent" },
    margin: isMini
      ? { t: 15, r: 15, b: 25, l: 35 }
      : { t: customTitle ? 50 : 30, r: 30, b: 50, l: 50 },
    xaxis: { gridcolor: gc, zeroline: false, title: { text: "" } },
    yaxis: { gridcolor: gc, zeroline: false, title: { text: "" } },
    polar: { angularaxis: { gridcolor: gc }, radialaxis: { gridcolor: gc } },
    ternary: {
      aaxis: { gridcolor: gc, linecolor: gc },
      baxis: { gridcolor: gc, linecolor: gc },
      caxis: { gridcolor: gc, linecolor: gc },
      bgcolor: "transparent",
    },
  };
  if (customTitle) {
    layout.title = {
      text: customTitle,
      font: { size: titleSize, color: isLight ? "#0f172a" : "#f8fafc" },
    };
  }
  return layout;
}

async function drawMegaPlotly(targetElementId, data, type, isMini = false) {
  const targetEl = document.getElementById(targetElementId);
  if (targetEl) {
    targetEl
      .querySelectorAll(".spinner, .chart-loading-spinner")
      .forEach((s) => s.remove());
  }
  const preLoader = document.getElementById("megaChartLoader");
  if (preLoader) preLoader.remove();

  const mainColor =
    window.currentPalette ||
    (typeof state !== "undefined" && state.currentPalette) ||
    document.getElementById("chartColor")?.value ||
    "#38bdf8";
  const bg = document.getElementById("chartBgColor")?.value || "#070711";
  const sGrid = document.getElementById("showGrid")?.checked ?? true;
  const sLeg = isMini
    ? false
    : (document.getElementById("showLegend")?.checked ?? true);
  const sz = parseInt(document.getElementById("traceSize")?.value || "5");

  let traces = [];
  const layout = buildLayout(bg, sGrid, sLeg, isMini);
  if (!isMini) {
    const curX =
      (window.axisConfig && window.axisConfig.x) ||
      (typeof state !== "undefined" &&
        state.axis &&
        state.axis.x &&
        state.axis.x.name) ||
      "";
    const curY =
      window.axisConfig && window.axisConfig.y && window.axisConfig.y.length
        ? window.axisConfig.y
        : typeof state !== "undefined" && state.axis && state.axis.y
          ? state.axis.y.map((i) => i.name)
          : [];
    if (layout.xaxis && layout.xaxis.title) {
      layout.xaxis.title.text =
        document.getElementById("customXTitle")?.value || curX;
    }
    if (layout.yaxis && layout.yaxis.title) {
      layout.yaxis.title.text =
        document.getElementById("customYTitle")?.value || curY.join(", ");
    }
  }

  const raw = data.raw || {},
    agg = data.agg || {},
    corr = data.corr || {};

  try {
    // ════════ 1. RAW DATA CHARTS ════════
    if (data.raw) {
      const keys = Object.keys(raw).filter((k) => k !== "__x__");
      const xVals = raw["__x__"] || [];

      // 3D Çizgiler & Noktalar
      if (type === "scatter3d" || type === "line3d") {
        const zKey = keys[1] || keys[0];
        traces.push({
          type: "scatter3d",
          mode: type === "line3d" ? "lines" : "markers",
          x: xVals.length ? xVals : raw[keys[0]],
          y: raw[keys[0]] || xVals,
          z: raw[zKey] || raw[keys[0]],
          marker: { size: sz * 1.5, color: PALETTE },
          line: { width: sz, color: mainColor },
        });
      }
      // SPLOM / Scatter Matrix
      else if (type === "scattermatrix") {
        traces.push({
          type: "splom",
          dimensions: keys.map((k) => ({ label: k, values: raw[k] })),
          marker: { color: mainColor, size: isMini ? 3 : 5 },
        });
      }
      // Parallel Coordinates & Categories
      else if (type === "parcoords") {
        const numKeys = keys.filter((k) => numericColumns.includes(k));
        const targetKeys = numKeys.length >= 2 ? numKeys : keys;
        traces.push({
          type: "parcoords",
          dimensions: targetKeys.map((k) => ({
            label: k,
            values: (raw[k] || []).map((v) => Number(v) || 0),
          })),
        });
      } else if (type === "parcats") {
        const allDimKeys = xVals.length ? ["__x__", ...keys] : keys;
        traces.push({
          type: "parcats",
          dimensions: allDimKeys.map((k) => ({
            label: k === "__x__" ? axisConfig.x || "Kategori" : k,
            values: k === "__x__" ? xVals : raw[k],
          })),
        });
      }
      // Finansal: Candlestick & OHLC
      else if (type === "candlestick" || type === "ohlc") {
        const y0 = keys[0] ? raw[keys[0]] : [];
        const hasValidNumbers =
          Array.isArray(y0) && y0.some((v) => Number.isFinite(Number(v)));
        if (!y0 || y0.length === 0 || !hasValidNumbers) {
          const el = document.getElementById(targetElementId);
          if (el)
            el.innerHTML =
              '<div style="color:var(--orange); padding:40px; text-align:center;">⚠️ Mum grafiği için en az bir sayısal fiyat sütunu seçiniz.</div>';
          return;
        }
        const numY0 = y0.map((v) => Number(v) || 0);
        const openVals = keys[1] ? raw[keys[1]] : numY0.map((v) => v * 0.98);
        const highVals = keys[2] ? raw[keys[2]] : numY0.map((v) => v * 1.03);
        const lowVals = keys[3] ? raw[keys[3]] : numY0.map((v) => v * 0.95);
        const closeVals = numY0;

        traces.push({
          type: type,
          x: xVals.length
            ? xVals
            : Array.from({ length: y0.length }, (_, i) => i + 1),
          open: openVals,
          high: highVals,
          low: lowVals,
          close: closeVals,
        });
        if (layout.xaxis) layout.xaxis.rangeslider = { visible: false };
      }
      // Ternary
      else if (type === "ternary") {
        traces.push({
          type: "scatterternary",
          mode: "markers",
          a: raw[keys[0]] || [],
          b: raw[keys[1]] || raw[keys[0]] || [],
          c: raw[keys[2]] || raw[keys[0]] || [],
          marker: { color: mainColor, size: sz * 2 },
        });
      }
      // Scattergeo Coğrafi Harita
      else if (type === "scattergeo") {
        keys.forEach((k, i) => {
          traces.push({
            type: "scattergeo",
            mode: "markers",
            name: k,
            lat: xVals.length ? xVals : raw[keys[0]],
            lon: raw[keys[1] || keys[0]],
            marker: {
              color: keys.length === 1 ? mainColor : PALETTE[i % 10],
              size: isMini ? sz * 2 : sz * 3,
              opacity: 0.8,
            },
          });
        });
        layout.geo = {
          bgcolor: "transparent",
          showcoastlines: true,
          coastlinecolor: "rgba(255,255,255,0.2)",
          showland: true,
          landcolor: "rgba(255,255,255,0.05)",
        };
      }
      // Scatter & Bubble
      else if (["scatter", "bubble"].includes(type)) {
        keys.forEach((k, i) => {
          traces.push({
            type: "scatter",
            mode: "markers",
            name: k,
            x: xVals.length ? xVals : undefined,
            y: raw[k],
            marker: {
              color: keys.length === 1 ? mainColor : PALETTE[i % 10],
              size: type === "bubble" ? sz * 4 : isMini ? sz * 2 : sz * 3,
              opacity: 0.75,
            },
          });
        });
      }
      // Dumbbell (Halter)
      else if (type === "dumbbell") {
        const s0 = keys[0] ? raw[keys[0]] || [] : [];
        const s1 = keys[1] ? raw[keys[1]] || [] : s0.map(() => 0);
        const yLabels = xVals.length
          ? xVals
          : s0.map((_, idx) => `Kayıt ${idx + 1}`);
        const segX = [],
          segY = [];
        for (let idx = 0; idx < yLabels.length; idx++) {
          segX.push(s1[idx], s0[idx], null);
          segY.push(yLabels[idx], yLabels[idx], null);
        }
        traces.push({
          type: "scatter",
          mode: "lines",
          name: "Fark",
          x: segX,
          y: segY,
          line: { color: "rgba(148, 163, 184, 0.45)", width: Math.max(2, sz) },
          showlegend: false,
          hoverinfo: "skip",
        });
        traces.push({
          type: "scatter",
          mode: "markers",
          name: keys[1] ? keys[0] : "Başlangıç",
          x: keys[1] ? s0 : s1,
          y: yLabels,
          marker: { color: PALETTE[0] || mainColor, size: sz * 2.5 + 4 },
        });
        traces.push({
          type: "scatter",
          mode: "markers",
          name: keys[1] ? keys[1] : keys[0] || "Değer",
          x: keys[1] ? s1 : s0,
          y: yLabels,
          marker: { color: PALETTE[1] || "#34d399", size: sz * 2.5 + 4 },
        });
      }
      // Histogram, Box, Violin, Strip, Rug
      else if (["histogram", "box", "violin", "strip", "rug"].includes(type)) {
        keys.forEach((k, i) => {
          let tr = {
            type: type === "strip" || type === "rug" ? "scatter" : type,
            name: k,
            x: type === "histogram" ? raw[k] : xVals.length ? xVals : undefined,
            y: type === "histogram" ? undefined : raw[k],
            marker: { color: keys.length === 1 ? mainColor : PALETTE[i % 10] },
          };
          if (type === "histogram" && keys.length > 1) {
            tr.opacity = 0.75;
          }
          if (type === "strip") {
            tr.mode = "markers";
            tr.marker.size = sz * 2;
            tr.marker.opacity = 0.6;
          }
          if (type === "rug") {
            tr.mode = "markers";
            tr.marker.symbol = "line-ns";
            tr.marker.size = 14;
          }
          if (type === "box") {
            tr.boxpoints = "outliers";
          }
          if (type === "violin") {
            tr.points = "none";
            tr.box = { visible: true };
          }
          traces.push(tr);
        });
        if (type === "histogram") layout.barmode = "overlay";
      }
      // 2D Density & 2D Histogram
      else if (type === "histogram2d" || type === "density2d") {
        if (keys.length > 0) {
          traces.push({
            type: type === "density2d" ? "histogram2dcontour" : "histogram2d",
            x: xVals.length ? xVals : raw[keys[0]],
            y: raw[keys[0]],
            colorscale: "Viridis",
          });
        }
      } else {
        keys.forEach((k) =>
          traces.push({
            type: "box",
            name: k,
            y: raw[k],
            marker: { color: mainColor },
          }),
        );
      }
    }

    // ════════ 2. CORRELATION / MATRIX CHARTS ════════
    else if (data.corr) {
      traces.push({
        type:
          type === "surface"
            ? "surface"
            : type === "contour" || type === "carpet"
              ? "contour"
              : "heatmap",
        x: corr.labels,
        y: corr.labels,
        z: corr.matrix,
        colorscale: "Blues",
        showscale: !isMini,
      });
      if (["heatmap", "contour", "carpet"].includes(type)) {
        layout.xaxis.showgrid = false;
        layout.yaxis.showgrid = false;
      }
    }

    // ════════ 3. AGGREGATED CHARTS ════════
    else if (data.agg) {
      const keys = Object.keys(agg).filter((k) => k !== "__x__");
      const xVals = agg["__x__"] || [];

      // Pie, Donut, Sunburst, Treemap, FunnelArea, Icicle, Sankey
      if (
        [
          "pie",
          "donut",
          "funnelarea",
          "sunburst",
          "treemap",
          "icicle",
          "sankey",
        ].includes(type)
      ) {
        if (type === "sankey") {
          let nodeLabels = [...xVals.map(x => String(x) + " "), ...keys];
          let source = [];
          let target = [];
          let value = [];

          keys.forEach((k, kIdx) => {
            let targetIdx = xVals.length + kIdx;
            xVals.forEach((x, xIdx) => {
              const val = Number(agg[k]?.[xIdx]) || 0;
              if (val > 0) {
                source.push(xIdx);
                target.push(targetIdx);
                value.push(val);
              }
            });
          });

          if (value.length === 0) {
            const el = document.getElementById(targetElementId);
            if (el)
              el.innerHTML =
                '<div style="color:var(--orange); padding:40px; text-align:center;">⚠️ Sankey akışı için en az bir pozitif sayısal değer ve kategori seçiniz.</div>';
            return;
          }

          traces.push({
            type: "sankey",
            orientation: "h",
            node: {
              pad: 15,
              thickness: 20,
              line: { color: "black", width: 0.5 },
              label: nodeLabels,
              color: PALETTE,
            },
            link: { source: source, target: target, value: value },
          });
        } else {
          const k = keys[0];
          if (k) {
            let _labels = xVals;
            let _parents = ["sunburst", "treemap", "icicle"].includes(type)
              ? xVals.map(() => "")
              : undefined;
            let _values = agg[k];
            let _ids = undefined;

            if (["sunburst", "treemap", "icicle"].includes(type)) {
              const cleanVals = (agg[k] || []).map((v) =>
                Math.max(0, Number(v) || 0),
              );
              const totalVal = cleanVals.reduce((a, b) => a + b, 0);
              const rootLabel = "Toplam";
              const safeLabels = xVals.map((x, idx) => {
                let s = String(x || `Kategori ${idx + 1}`).trim();
                return s === rootLabel ? s + " " : s;
              });
              
              _ids = [...safeLabels.map((s, idx) => `id_${idx}_${s}`), "id_root"];
              _labels = [...safeLabels, rootLabel];
              _parents = [...safeLabels.map(() => "id_root"), ""];
              _values = [...cleanVals, totalVal];
            }

            let traceObj = {
              type: ["sunburst", "treemap", "icicle"].includes(type)
                ? type
                : type === "funnelarea"
                  ? "funnelarea"
                  : "pie",
              labels: _labels,
              parents: _parents,
              [type === "funnelarea" ? "text" : "labels"]: _labels,
              values: _values,
              hole: type === "donut" ? 0.5 : 0,
              marker: { colors: PALETTE },
            };
            if (_ids) {
                traceObj.ids = _ids;
            }
            traces.push(traceObj);
            if (layout.xaxis) layout.xaxis.visible = false;
            if (layout.yaxis) layout.yaxis.visible = false;
          }
        }
      }
      // Bullet / Indicator / Gauge
      else if (type === "bullet" || type === "gauge") {
        const k = keys[0] || "Değer";
        const vals = (agg[k] || []).map((v) => Number(v) || 0);
        const val = vals.length ? vals[0] : 0;
        const maxRange = Math.max(...vals, val * 1.3, 1);
        traces.push({
          type: "indicator",
          mode: type === "gauge" ? "gauge+number" : "number+gauge+delta",
          value: val,
          title: { text: k, font: { size: 16 } },
          gauge: {
            shape: type === "gauge" ? "angular" : "bullet",
            axis: { range: [0, maxRange] },
            bar: { color: mainColor },
            threshold: {
              line: { color: "#f87171", width: 3 },
              thickness: 0.75,
              value: maxRange * 0.9,
            },
          },
        });
      }
      // Polar Bar, Polar Scatter, Windrose, Radial Bar
      else if (
        ["polarbar", "polarscatter", "windrose", "radialbar"].includes(type)
      ) {
        const k = keys[0];
        if (k) {
          traces.push({
            type: type === "polarscatter" ? "scatterpolar" : "barpolar",
            mode: type === "polarscatter" ? "markers" : undefined,
            name: k,
            r: agg[k],
            theta: xVals,
            marker: { color: PALETTE, size: sz * 2.5 },
          });
          if (type === "radialbar" && layout.polar) {
            layout.polar.hole = 0.25;
          }
        }
      }
      // Dumbbell (Halter)
      else if (type === "dumbbell") {
        const s0 = keys[0] ? agg[keys[0]] || [] : [];
        const s1 = keys[1] ? agg[keys[1]] || [] : s0.map(() => 0);
        const yLabels = xVals.length
          ? xVals
          : s0.map((_, idx) => `Kategori ${idx + 1}`);
        const segX = [],
          segY = [];
        for (let idx = 0; idx < yLabels.length; idx++) {
          segX.push(s1[idx], s0[idx], null);
          segY.push(yLabels[idx], yLabels[idx], null);
        }
        traces.push({
          type: "scatter",
          mode: "lines",
          name: "Fark",
          x: segX,
          y: segY,
          line: { color: "rgba(148, 163, 184, 0.45)", width: Math.max(2, sz) },
          showlegend: false,
          hoverinfo: "skip",
        });
        traces.push({
          type: "scatter",
          mode: "markers",
          name: keys[1] ? keys[0] : "Başlangıç",
          x: keys[1] ? s0 : s1,
          y: yLabels,
          marker: { color: PALETTE[0] || mainColor, size: sz * 2.5 + 4 },
        });
        traces.push({
          type: "scatter",
          mode: "markers",
          name: keys[1] ? keys[1] : keys[0] || "Değer",
          x: keys[1] ? s1 : s0,
          y: yLabels,
          marker: { color: PALETTE[1] || "#34d399", size: sz * 2.5 + 4 },
        });
      }
      // Lollipop (Lolipop)
      else if (type === "lollipop") {
        keys.forEach((k, i) => {
          const colColor = keys.length === 1 ? mainColor : PALETTE[i % 10];
          const ySeries = agg[k] || [];
          traces.push({
            type: "bar",
            name: `${k} (Gövde)`,
            x: xVals,
            y: ySeries,
            width: 0.12,
            marker: { color: colColor, opacity: 0.65 },
            showlegend: false,
            hoverinfo: "skip",
          });
          traces.push({
            type: "scatter",
            mode: "markers",
            name: k,
            x: xVals,
            y: ySeries,
            marker: {
              color: colColor,
              size: sz * 3 + 4,
              line: { color: "#ffffff", width: 1.5 },
            },
          });
        });
      }
      // Bars, Funnel, Waterfall, Radar, Dotplot, Errorbar
      else if (
        [
          "bar",
          "horizontalbar",
          "groupedbar",
          "stackedbar",
          "funnel",
          "waterfall",
          "radar",
          "dotplot",
          "errorbar",
        ].includes(type)
      ) {
        keys.forEach((k, i) => {
          let tr = {};
          if (type === "radar") {
            tr = {
              type: "scatterpolar",
              name: k,
              r: agg[k],
              theta: xVals,
              fill: "toself",
              marker: {
                color: keys.length === 1 ? mainColor : PALETTE[i % 10],
              },
            };
          } else if (type === "funnel") {
            tr = {
              type: "funnel",
              name: k,
              y: xVals,
              x: agg[k],
              marker: {
                color: keys.length === 1 ? mainColor : PALETTE[i % 10],
              },
            };
          } else if (type === "waterfall") {
            tr = {
              type: "waterfall",
              name: k,
              x: xVals,
              y: agg[k],
              marker: {
                color: keys.length === 1 ? mainColor : PALETTE[i % 10],
              },
            };
          } else if (type === "dotplot") {
            tr = {
              type: "scatter",
              mode: "markers",
              name: k,
              x: xVals,
              y: agg[k],
              marker: {
                size: sz * 3.5,
                color: keys.length === 1 ? mainColor : PALETTE[i % 10],
              },
            };
          } else if (type === "errorbar") {
            tr = {
              type: "bar",
              name: k,
              x: xVals,
              y: agg[k],
              error_y: {
                type: "data",
                array: agg[k].map((v) => v * 0.08),
                visible: true,
              },
              marker: {
                color: keys.length === 1 ? mainColor : PALETTE[i % 10],
              },
            };
          } else {
            tr = {
              type: "bar",
              name: k,
              [type === "horizontalbar" ? "y" : "x"]: xVals,
              [type === "horizontalbar" ? "x" : "y"]: agg[k],
              marker: {
                color: keys.length === 1 ? mainColor : PALETTE[i % 10],
              },
            };
            if (type === "horizontalbar") tr.orientation = "h";
          }
          traces.push(tr);
        });
        if (type === "groupedbar") layout.barmode = "group";
        if (type === "stackedbar") layout.barmode = "stack";
      }
      // Lines & Areas (Line, Spline, Step, Area, StackedArea)
      else {
        keys.forEach((k, i) => {
          let tr = {
            type: "scatter",
            mode: "lines+markers",
            name: k,
            x: xVals,
            y: agg[k],
            line: {
              color: keys.length === 1 ? mainColor : PALETTE[i % 10],
              width: sz,
            },
            marker: {
              size: sz + 3,
              color: keys.length === 1 ? mainColor : PALETTE[i % 10],
            },
          };
          if (type === "spline") tr.line.shape = "spline";
          if (type === "step") tr.line.shape = "vhv";
          if (type === "area" || type === "stackedarea")
            tr.fill =
              i === 0
                ? "tozeroy"
                : type === "stackedarea"
                  ? "tonexty"
                  : "tozeroy";
          traces.push(tr);
        });
      }
    }

    // ════════ 4. CANLI TRENDLINE & KORELASYON OVERLAY ════════
    if (
      !isMini &&
      (targetElementId === "chartArea" || targetElementId === "livePlotlyArea")
    ) {
      const curAxisX =
        (window.axisConfig && window.axisConfig.x) ||
        (typeof state !== "undefined" &&
          state.axis &&
          state.axis.x &&
          state.axis.x.name) ||
        null;
      const curAxisY =
        window.axisConfig && window.axisConfig.y && window.axisConfig.y.length
          ? window.axisConfig.y
          : typeof state !== "undefined" && state.axis && state.axis.y
            ? state.axis.y.map((i) => i.name)
            : [];
      const numCols =
        window.numericColumns ||
        (typeof state !== "undefined" &&
          state.activeDataset &&
          state.activeDataset.numericColumns) ||
        [];
      const curFilters =
        window.activeFilters ||
        (typeof state !== "undefined" && state.activeFilters) ||
        [];

      const isXNum = curAxisX && numCols.includes(curAxisX);
      const firstY = curAxisY.length > 0 ? curAxisY[0] : null;
      const isYNum = firstY && numCols.includes(firstY);
      const statsBadgeEl = document.getElementById("chartStatsBadge");
      const showTrend = type === "scatter";
      const regModel = "linear";
      const corrMethod = "pearson";

      if (isXNum && isYNum) {
        try {
          const regRes = await fetch("/get_regression_curve", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              x_col: curAxisX,
              y_col: firstY,
              model_type: regModel,
              corr_method: corrMethod,
              filters: curFilters,
            }),
          });
          const regData = await regRes.json();
          if (regData.success && regData.regression && regData.correlation) {
            const reg = regData.regression;
            const corr = regData.correlation;

            // 1. Canlı İstatistik Overlay Rozetini Güncelle
            const corrSymbol = "r";
            const corrText = corr.coef != null ? corr.coef.toFixed(4) : "-";
            const r2Text =
              reg.r_squared != null ? reg.r_squared.toFixed(4) : "-";
            const eqText = reg.equation || "-";

            const csbEquation = document.getElementById("csbEquation");
            const csbR2 = document.getElementById("csbR2");
            const csbCorrName = document.getElementById("csbCorrName");
            const csbCorr = document.getElementById("csbCorr");
            if (csbEquation) csbEquation.textContent = eqText;
            if (csbR2) csbR2.textContent = r2Text;
            if (csbCorrName) csbCorrName.textContent = corrSymbol;
            if (csbCorr) csbCorr.textContent = corrText;

            // 2. Trendline Çizgisi Ekle (Scatter Grafiği İçin)
            if (showTrend && reg.trend_x && reg.trend_x.length > 0) {
              traces.push({
                type: "scatter",
                mode: "lines",
                name: `Trend: ${reg.equation}`,
                x: reg.trend_x,
                y: reg.trend_y,
                line: {
                  color: "#f59e0b",
                  width: 3,
                  dash: "dash",
                },
                hoverinfo: "x+y+name",
              });

              statsBadgeEl?.classList.remove("hidden");
            } else {
              statsBadgeEl?.classList.add("hidden");
            }
          }
        } catch (regErr) {
          console.warn("Regresyon eğrisi yüklenirken hata:", regErr);
          statsBadgeEl?.classList.add("hidden");
        }
      } else {
        statsBadgeEl?.classList.add("hidden");
        const csbEquation = document.getElementById("csbEquation");
        if (csbEquation) csbEquation.textContent = "-";
        const csbR2 = document.getElementById("csbR2");
        if (csbR2) csbR2.textContent = "-";
        const csbCorr = document.getElementById("csbCorr");
        if (csbCorr) csbCorr.textContent = "-";
      }
    }

    if (targetEl) {
      targetEl
        .querySelectorAll(".spinner, .chart-loading-spinner")
        .forEach((s) => s.remove());
    }
    const midLoader = document.getElementById("megaChartLoader");
    if (midLoader) midLoader.remove();

    await Plotly.newPlot(targetElementId, traces, layout, {
      responsive: true,
      displayModeBar: !isMini,
      displaylogo: false,
    });

    const postLoader = document.getElementById("megaChartLoader");
    if (postLoader) postLoader.remove();
    if (targetEl) {
      targetEl
        .querySelectorAll(".spinner, .chart-loading-spinner")
        .forEach((s) => s.remove());
    }
  } catch (err) {
    const postLoader = document.getElementById("megaChartLoader");
    if (postLoader) postLoader.remove();
    const el = document.getElementById(targetElementId);
    if (el)
      el.innerHTML = `<div style="color:var(--red); padding:20px; font-size:0.85rem;">❌ Çizim Hatası: ${err.message}</div>`;
  }
}

// Window export
window.CHARTS = CHARTS;
window.buildLayout = buildLayout;
window.drawMegaPlotly = drawMegaPlotly;
