/**
 * Arrow Client - Apache Arrow IPC Streaming and Zero-Copy Client Module
 * Prototip 1: Binary Zero-Copy Data Ingestion & Live Serialization Benchmark
 */

export class ArrowClient {
  constructor() {
    this.arrowLoaded = false;
    this.initArrowLibrary();
  }

  async initArrowLibrary() {
    // Dynamically load Apache Arrow ES module from CDN if not already available
    if (window.Arrow) {
      this.arrowLoaded = true;
      return;
    }
    try {
      const arrowModule = await import("https://cdn.jsdelivr.net/npm/apache-arrow@18.1.0/+esm");
      window.Arrow = arrowModule;
      this.arrowLoaded = true;
      console.log("⚡ [ArrowClient] Apache Arrow JS kütüphanesi başarıyla yüklendi.");
    } catch (err) {
      console.warn("⚠️ [ArrowClient] CDN yüklemesi gecikmeli, yerel fallback hazır.", err);
    }
  }

  /**
   * Fetches the dataset as a binary Apache Arrow IPC stream
   * @param {number|null} maxRows
   * @returns {Promise<{table: any, meta: object, bytes: ArrayBuffer, durationMs: number}>}
   */
  async fetchArrowData(maxRows = null) {
    const startTime = performance.now();
    const url = maxRows ? `/get_arrow_data?max_rows=${maxRows}` : "/get_arrow_data";

    const response = await fetch(url);
    if (!response.ok) {
      const errJson = await response.json().catch(() => ({}));
      throw new Error(errJson.error || "Arrow IPC verisi alınamadı.");
    }

    const arrayBuffer = await response.arrayBuffer();
    const fetchDurationMs = performance.now() - startTime;

    let arrowTable = null;
    let parseDurationMs = 0;

    if (window.Arrow && window.Arrow.tableFromIPC) {
      const p0 = performance.now();
      arrowTable = window.Arrow.tableFromIPC(arrayBuffer);
      parseDurationMs = performance.now() - p0;
    }

    const meta = {
      rows: parseInt(response.headers.get("X-Arrow-Rows") || "0", 10),
      cols: parseInt(response.headers.get("X-Arrow-Cols") || "0", 10),
      byteSize: arrayBuffer.byteLength,
      serverSerializationMs: parseFloat(response.headers.get("X-Serialization-Ms") || "0"),
      networkAndClientMs: Math.round(fetchDurationMs),
      clientParseMs: Math.round(parseDurationMs * 100) / 100,
    };

    return { table: arrowTable, meta, bytes: arrayBuffer };
  }

  /**
   * Runs backend JSON vs Arrow IPC benchmark and displays results
   */
  async runBenchmark(sampleSize = 25000) {
    const res = await fetch(`/benchmark_json_vs_arrow?sample_size=${sampleSize}`);
    const data = await res.json();
    if (!data.success) {
      throw new Error(data.error || "Benchmark çalıştırılamadı.");
    }
    return data.benchmark;
  }
}

export const arrowClient = new ArrowClient();
window.arrowClient = arrowClient;
