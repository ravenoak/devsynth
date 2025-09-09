#!/usr/bin/env python3
"""
Lightweight read/write benchmark across optional memory backends.

- Honors resource flags: DEVSYNTH_RESOURCE_TINYDB_AVAILABLE, DEVSYNTH_RESOURCE_DUCKDB_AVAILABLE,
  DEVSYNTH_RESOURCE_LMDB_AVAILABLE. If a backend isn't installed or the flag is false, it's skipped.
- Uses realistic payload sizes: ~1 KiB, 100 KiB, 1 MiB.
- Prints a compact JSON report to stdout.

This script is intentionally dependency-light and suitable for local runs.
It aligns with project guidelines and docs/plan.md (determinism) and addresses docs/tasks.md item 11.3.
"""
from __future__ import annotations

import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List


def _bool_env(name: str) -> bool:
    return os.environ.get(name, "false").strip().lower() in {"1", "true", "yes", "y"}


def payloads() -> list[bytes]:
    return [
        b"x" * 1024,  # 1 KiB
        b"x" * (100 * 1024),  # 100 KiB
        b"x" * (1024 * 1024),  # 1 MiB
    ]


def bench_tinydb(tmp: Path) -> dict[str, Any]:
    if not _bool_env("DEVSYNTH_RESOURCE_TINYDB_AVAILABLE"):
        return {"backend": "tinydb", "skipped": True, "reason": "flag false"}
    try:
        from tinydb import TinyDB  # type: ignore
    except Exception as e:  # pragma: no cover - optional dep
        return {"backend": "tinydb", "skipped": True, "reason": f"import error: {e}"}

    db_path = tmp / "tiny.json"
    results: dict[str, Any] = {"backend": "tinydb", "samples": []}
    with TinyDB(db_path) as db:  # type: ignore
        table = db.table("bench")
        for p in payloads():
            t0 = time.perf_counter()
            table.insert({"key": "k", "blob": p.decode("latin1")})
            write_s = time.perf_counter() - t0

            t1 = time.perf_counter()
            _ = table.get(doc_id=1)
            read_s = time.perf_counter() - t1

            results["samples"].append(
                {"size": len(p), "write_s": write_s, "read_s": read_s}
            )
    return results


def bench_duckdb(tmp: Path) -> dict[str, Any]:
    if not _bool_env("DEVSYNTH_RESOURCE_DUCKDB_AVAILABLE"):
        return {"backend": "duckdb", "skipped": True, "reason": "flag false"}
    try:
        import duckdb  # type: ignore
    except Exception as e:  # pragma: no cover
        return {"backend": "duckdb", "skipped": True, "reason": f"import error: {e}"}

    db_path = tmp / "duck.db"
    con = duckdb.connect(str(db_path))  # type: ignore
    try:
        con.execute("create table if not exists bench(key varchar, blob blob)")
        results: dict[str, Any] = {"backend": "duckdb", "samples": []}
        for p in payloads():
            t0 = time.perf_counter()
            con.execute("insert into bench values (?, ?)", ("k", p))
            write_s = time.perf_counter() - t0

            t1 = time.perf_counter()
            _ = con.execute("select * from bench limit 1").fetchone()
            read_s = time.perf_counter() - t1
            results["samples"].append(
                {"size": len(p), "write_s": write_s, "read_s": read_s}
            )
        return results
    finally:
        con.close()


def bench_lmdb(tmp: Path) -> dict[str, Any]:
    if not _bool_env("DEVSYNTH_RESOURCE_LMDB_AVAILABLE"):
        return {"backend": "lmdb", "skipped": True, "reason": "flag false"}
    try:
        import lmdb  # type: ignore
    except Exception as e:  # pragma: no cover
        return {"backend": "lmdb", "skipped": True, "reason": f"import error: {e}"}

    env = lmdb.open(str(tmp / "lmdb"), map_size=64 * 1024 * 1024)  # 64 MiB
    results: dict[str, Any] = {"backend": "lmdb", "samples": []}
    with env.begin(write=True) as txn:
        for p in payloads():
            t0 = time.perf_counter()
            txn.put(b"k", p)
            write_s = time.perf_counter() - t0

            t1 = time.perf_counter()
            _ = txn.get(b"k")
            read_s = time.perf_counter() - t1
            results["samples"].append(
                {"size": len(p), "write_s": write_s, "read_s": read_s}
            )
    env.close()
    return results


def main() -> None:
    tmpdir = Path(tempfile.mkdtemp(prefix="devsynth-bench-"))
    reports = []
    for fn in (bench_tinydb, bench_duckdb, bench_lmdb):
        reports.append(fn(tmpdir))
    print(json.dumps({"reports": reports}, indent=2))


if __name__ == "__main__":
    main()
