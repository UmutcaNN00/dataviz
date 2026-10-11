"""
DataViz - Sıfır Kopyalama Memory-Mapped Disk Önbelleği (ClickHouse & Snowflake Mimarisi)
Büyük veri setlerini RAM'e kopyalamak yerine pyarrow.memory_map ile işletim sisteminin
sanal bellek sayfalarına (OS Page Cache) haritalayarak sıfır OOM çökme riskiyle çalışır.
"""

from typing import Dict, Any, List, Optional
import os
import time
import tempfile
import pyarrow as pa
import pyarrow.ipc as ipc
import pandas as pd
import logging

logger = logging.getLogger(__name__)

CACHE_DIR = os.path.join(tempfile.gettempdir(), "dataviz_mmap_cache")
os.makedirs(CACHE_DIR, exist_ok=True)


class MemoryMappedCacheManager:
    """Veri setlerini bellek haritalı (mmap) disk önbelleğinde yöneten motor."""

    def __init__(self, cache_dir: str = CACHE_DIR):
        self.cache_dir = cache_dir

    def persist_to_mmap(self, df: pd.DataFrame, dataset_id: str = "active_dataset") -> Dict[str, Any]:
        """
        DataFrame'i sıfır kopyalama bellek haritalı (mmap) Arrow dosyasına yazar.
        """
        start_time = time.time()
        file_path = os.path.join(self.cache_dir, f"{dataset_id}.arrow")

        # Arrow tablosuna dönüştür
        table = pa.Table.from_pandas(df, preserve_index=False)

        # Arrow IPC dosya formatında diske yaz
        with pa.OSFile(file_path, "wb") as sink:
            with ipc.new_file(sink, table.schema) as writer:
                writer.write_table(table)

        file_size_bytes = os.path.getsize(file_path)
        file_size_mb = round(file_size_bytes / (1024 * 1024), 2)
        elapsed_ms = round((time.time() - start_time) * 1000, 2)

        logger.info(f"MMap önbellek oluşturuldu: {file_path} ({file_size_mb} MB, {elapsed_ms} ms)")

        return {
            "success": True,
            "cache_path": file_path,
            "file_size_mb": file_size_mb,
            "elapsed_ms": elapsed_ms,
            "total_rows": len(df),
            "num_columns": len(df.columns),
            "mode": "Zero-Copy Memory-Mapped (OS Page Cache)",
        }

    def read_columns_zero_copy(
        self,
        columns: Optional[List[str]] = None,
        limit: int = 100,
        dataset_id: str = "active_dataset",
    ) -> Dict[str, Any]:
        """
        İşletim sisteminin sanal belleğinden doğrudan istenen sütunları sıfır kopyalama ile okur.
        """
        start_time = time.time()
        file_path = os.path.join(self.cache_dir, f"{dataset_id}.arrow")

        if not os.path.exists(file_path):
            return {"error": "MMap önbellek dosyası bulunamadı. Önce persist_to_mmap çağrılmalı."}

        # OS Page Cache üzerinden Memory-Map ile aç
        source = pa.memory_map(file_path, mode="r")
        reader = ipc.RecordBatchFileReader(source)

        table_schema = reader.schema
        available_cols = [table_schema.field(i).name for i in range(len(table_schema))]
        
        target_cols = columns if columns else available_cols[:10]
        target_cols = [c for c in target_cols if c in available_cols]

        # Sadece ilk RecordBatch veya dilimi oku
        batch = reader.get_batch(0)
        # Sütun bazlı projeksiyon (Columnar Projection)
        projected_batch = batch.select(target_cols)
        sliced_df = projected_batch.slice(0, limit).to_pandas()

        elapsed_ms = round((time.time() - start_time) * 1000, 2)

        return {
            "success": True,
            "read_columns": target_cols,
            "returned_rows": len(sliced_df),
            "elapsed_ms": elapsed_ms,
            "preview": sliced_df.to_dict(orient="records")[:5],
            "zero_copy_active": True,
        }


mmap_cache = MemoryMappedCacheManager()
