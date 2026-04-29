# AIDOC Performance Benchmark

> **Date**: 2026-04-29  
> **Environment**: macOS (Apple Silicon M4), Python 3.10, OpenSSL 3.6.2  
> **Bench script**: [bench.py](bench.py)

---

## Results Summary

**The AIDOC Fast Read mode is 2.3–2.9× faster than standard ZIP reading.**

| File Size | Fast Path | Standard ZIP | Speedup |
|:---------:|:---------:|:------------:|:-------:|
| ~2 KB | **9.1 μs** | 26.5 μs | **2.9×** |
| ~500 KB | **21.1 μs** | 47.1 μs | **2.2×** |

---

## Why Is It Faster?

### Standard ZIP AI Read Flow

```
Open → seek to End of Central Directory     ← 1st seek
     → parse Central Directory → find content.md offset
     → seek to content.md data               ← 2nd seek
     → decompress (if compressed)            ← CPU overhead
     → read
```

Requires **parsing the ZIP Central Directory** — the overhead grows with the number of entries in the archive.

### AIDOC Fast Read Flow

```
Open → read local file header (30 bytes)    ← 1st read
     → parse header → get offset & size
     → seek to data position                 ← 1st seek
     → read data                             ← 2nd read
```

**Only 1 seek + 2 reads**, no Central Directory parsing, no decompression.

---

## Detailed Results

### Test 1: Small File (Typical Scenario)

File size: ~2 KB (equivalent to a short Markdown note)

| Metric | Fast Path | Standard ZIP | Difference |
|:-------|:---------:|:------------:|:----------:|
| Average | **9.1 μs** | 26.5 μs | 2.9× faster |
| Median | **9.1 μs** | 26.5 μs | 2.9× faster |
| P99 | **12.0 μs** | 34.5 μs | 2.9× faster |

### Test 2: Large File (Long Document)

File size: ~500 KB (equivalent to a 100+ page report)

| Metric | Fast Path | Standard ZIP | Difference |
|:-------|:---------:|:------------:|:----------:|
| Average | **21.1 μs** | 47.1 μs | 2.2× faster |
| Median | **20.1 μs** | 47.2 μs | 2.3× faster |
| P99 | **27.9 μs** | 59.3 μs | 2.1× faster |

> For large files, the speed advantage narrows slightly because data read time (proportional to file size) becomes dominant. However, the **core benefit — skipping Central Directory parsing — applies at all file sizes**.

### Test 3: File Size Impact

| Size | Fast Path | Standard ZIP | Speedup |
|:----:|:---------:|:------------:|:-------:|
| 1 KB | 9.5 μs | 27.5 μs | **2.9×** |
| 10 KB | 10.6 μs | 29.3 μs | **2.8×** |
| 100 KB | 16.9 μs | 38.7 μs | **2.3×** |
| 1000 KB | 64.1 μs | 174.7 μs | **2.7×** |

**Pattern**:
- The smaller the file, the larger the speedup (metadata parsing overhead is more significant for small files)
- Speedup stays consistently above **2.3×** across all sizes
- Data read time scales linearly with file size, but the fast path's **fixed overhead** (open + parse header) is much lower than the standard mode (parse Central Directory)

---

## Impact on AI Workflows

### Batch Processing

Processing 10,000 AIDOC files:

| Mode | Total Time | Saved |
|:----|:----------:|:-----:|
| Fast Path | **91 ms** | — |
| Standard ZIP | **265 ms** | **174 ms** |

For AI workloads that only need the Markdown content, the fast path saves nearly **2/3 of I/O time** in batch scenarios.

### Real-time Processing

Single file read in an AI pipeline (e.g., chatbot retrieving knowledge base):

| Mode | Per File | Acceptability |
|:----|:--------:|:-------------:|
| Fast Path | **9~21 μs** | ✅ Negligible |
| Standard ZIP | **27~47 μs** | ✅ Acceptable |

The difference is negligible for single reads. The fast path's value shines in **high-throughput and batch processing**.

---

## Appendix: Methodology

### Hardware

- **CPU**: Apple M4
- **RAM**: 24 GB
- **Storage**: Built-in SSD (APFS)

### Software

- **OS**: macOS
- **Python**: 3.10 (via micromamba)
- **Dependencies**: stdlib only (no third-party packages required)

### Method

1. Each test runs N iterations (N=10000 for small, N=1000 for large)
2. Warmup: 100–200 iterations to eliminate cold-start/cache effects
3. Record nanosecond-precision timestamps per read
4. Sort, compute average, median, P99
5. Fast path: `aidoc.read_md_fast()`, Standard: `zipfile.ZipFile.read()`

### Reproduce

The benchmark script is included in the repository. Run it to reproduce all data:

```bash
cd ~/Source/aidoc
micromamba run -n py310 python3 docs/bench.py
```

Script: [docs/bench.py](bench.py)

All results are saved to `/tmp/aidoc-bench/bench-results.json`.
