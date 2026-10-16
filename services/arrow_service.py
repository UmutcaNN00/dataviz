"""
Arrow Service - Apache Arrow IPC Streaming and Zero-Copy Serialization
High-performance binary communication bridge between Polars/PyArrow backend and frontend.
"""

import io
import logging
import time
from typing import Any, Optional, Tuple

import pandas as pd
import pyarrow as pa
import pyarrow.ipc as ipc

logger = logging.getLogger(__name__)


def serialize_df_to_arrow_ipc(df: pd.DataFrame, max_rows: Optional[int] = None) -> Tuple[bytes, dict[str, Any]]:
    """
    Serializes a Pandas/Polars DataFrame directly into an Apache Arrow IPC stream (Feather binary stream).
    Zero-copy columnar format eliminates JSON string serialization and parsing bottlenecks.
    """
    start_time = time.perf_counter()

    if df is None:
        return b"", {"num_rows": 0, "num_columns": 0, "column_names": [], "byte_size": 0, "serialization_ms": 0.0}

    if max_rows and len(df) > max_rows:
        target_df = df.iloc[:max_rows]
    else:
        target_df = df

    # Convert to PyArrow Table (zero-copy when compatible, with object fallback)
    try:
        table = pa.Table.from_pandas(target_df, preserve_index=False)
    except Exception:
        safe_df = target_df.copy()
        for c in safe_df.select_dtypes(include=["object"]).columns:
            safe_df[c] = safe_df[c].astype(str)
        table = pa.Table.from_pandas(safe_df, preserve_index=False)

    # Write to in-memory Arrow IPC RecordBatch stream
    sink = io.BytesIO()
    with ipc.new_stream(sink, table.schema) as writer:
        writer.write_table(table)

    binary_data = sink.getvalue()
    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    metadata = {
        "num_rows": table.num_rows,
        "num_columns": table.num_columns,
        "column_names": table.column_names,
        "byte_size": len(binary_data),
        "serialization_ms": round(elapsed_ms, 2),
    }

    logger.info(
        f"Arrow IPC stream created: {table.num_rows} rows, {table.num_columns} cols -> "
        f"{len(binary_data)} bytes in {elapsed_ms:.2f}ms"
    )
    return binary_data, metadata


def benchmark_serialization(df: pd.DataFrame, sample_size: int = 25000) -> dict[str, Any]:
    """
    Benchmarks JSON serialization vs Apache Arrow IPC streaming performance
    on the current active dataset.
    """
    import json

    test_df = df.iloc[:sample_size] if len(df) > sample_size else df

    # 1. JSON Serialization Benchmark
    t0 = time.perf_counter()
    # Standard Flask/Pandas to_json/records approach
    records = test_df.to_dict(orient="records")
    json_bytes = json.dumps(records, default=str).encode("utf-8")
    json_time_ms = (time.perf_counter() - t0) * 1000.0
    json_size_kb = len(json_bytes) / 1024.0

    # 2. Apache Arrow IPC Benchmark
    t1 = time.perf_counter()
    try:
        table = pa.Table.from_pandas(test_df, preserve_index=False)
    except Exception:
        safe_b_df = test_df.copy()
        for c in safe_b_df.select_dtypes(include=["object"]).columns:
            safe_b_df[c] = safe_b_df[c].astype(str)
        table = pa.Table.from_pandas(safe_b_df, preserve_index=False)
    sink = io.BytesIO()
    with ipc.new_stream(sink, table.schema) as writer:
        writer.write_table(table)
    arrow_bytes = sink.getvalue()
    arrow_time_ms = (time.perf_counter() - t1) * 1000.0
    arrow_size_kb = len(arrow_bytes) / 1024.0

    speedup = round(json_time_ms / max(arrow_time_ms, 0.01), 1)
    size_reduction_pct = round((1.0 - (arrow_size_kb / max(json_size_kb, 0.01))) * 100.0, 1)

    return {
        "sample_rows": len(test_df),
        "num_cols": len(test_df.columns),
        "json": {
            "time_ms": round(json_time_ms, 2),
            "size_kb": round(json_size_kb, 1),
        },
        "arrow_ipc": {
            "time_ms": round(arrow_time_ms, 2),
            "size_kb": round(arrow_size_kb, 1),
        },
        "speedup_ratio": f"{speedup}x",
        "size_reduction": f"{size_reduction_pct}%",
    }
