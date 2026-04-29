#!/usr/bin/env python3
"""
AIDOC 性能基准测试

可复现性能报告中所有数据。运行方式：

    cd ~/Source/aidoc
    micromamba run -n py310 python3 docs/bench.py

依赖：仅 Python 标准库（零第三方依赖）

结果说明：
- 测试分三组：小文件(2KB)、大文件(500KB)、文件尺寸扫描(1KB~1MB)
- 每组测试前预热 100~200 次，消除冷启动影响
- 记录纳秒级耗时，输出平均/中位数/P99
- 对比：极速模式 (aidoc.read_md_fast) vs 标准 ZIP (zipfile.ZipFile)
"""

import os
import sys
import time
import zipfile
import json
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.dirname(SCRIPT_DIR)
AIDOC_CLI = os.path.join(REPO_DIR, 'src', 'aidoc.py')

sys.path.insert(0, os.path.join(REPO_DIR, 'src'))
import aidoc

TMP = "/tmp/aidoc-bench"
os.makedirs(TMP, exist_ok=True)


def _create_aidoc(md_path, aidoc_path):
    """使用 CLI 创建 AIDOC 文件"""
    subprocess.run(
        [sys.executable, AIDOC_CLI, "create", md_path, "-o", aidoc_path],
        capture_output=True, cwd=REPO_DIR,
    )


def bench_read(title, func, path, n=10000, warmup=100):
    """通用基准测试"""
    for _ in range(warmup):
        func(path)

    times = []
    for _ in range(n):
        t0 = time.perf_counter_ns()
        _ = func(path)
        times.append(time.perf_counter_ns() - t0)

    times.sort()
    avg = sum(times) / len(times)
    median = times[len(times) // 2]
    p99 = times[int(len(times) * 0.99)]
    return {
        "title": title,
        "avg_us": avg / 1000,
        "median_us": median / 1000,
        "p99_us": p99 / 1000,
    }


def main():
    results = []
    sizes = []

    # ── Test 1: Small file (~2KB) ──
    print("▶ Small file (~2KB)...")
    small = "# Benchmark\n\n" + "\n".join(f"Line {i}" for i in range(50))
    with open(f"{TMP}/small.md", "w") as f:
        f.write(small)
    _create_aidoc(f"{TMP}/small.md", f"{TMP}/small.aidoc")

    r1 = bench_read("Fast Path (~2KB)", aidoc.read_md_fast, f"{TMP}/small.aidoc")
    results.append(r1)
    print(f"  {r1['title']}: {r1['avg_us']:.2f}μs")

    r2 = bench_read(
        "Standard ZIP (~2KB)",
        lambda p: zipfile.ZipFile(p).read("content.md").decode("utf-8-sig"),
        f"{TMP}/small.aidoc",
    )
    results.append(r2)
    print(f"  {r2['title']}: {r2['avg_us']:.2f}μs")

    # ── Test 2: Large file (~500KB) ──
    print("\n▶ Large file (~500KB)...")
    large = "# Large Document\n\n" + "\n".join(
        f"## Section {i}\n\nContent paragraph..." for i in range(5000)
    )
    with open(f"{TMP}/large.md", "w") as f:
        f.write(large)
    _create_aidoc(f"{TMP}/large.md", f"{TMP}/large.aidoc")

    r3 = bench_read("Fast Path (~500KB)", aidoc.read_md_fast, f"{TMP}/large.aidoc", n=1000)
    results.append(r3)
    print(f"  {r3['title']}: {r3['avg_us']:.2f}μs")

    r4 = bench_read(
        "Standard ZIP (~500KB)",
        lambda p: zipfile.ZipFile(p).read("content.md").decode("utf-8-sig"),
        f"{TMP}/large.aidoc",
        n=1000,
    )
    results.append(r4)
    print(f"  {r4['title']}: {r4['avg_us']:.2f}μs")

    # ── Test 3: Size sweep (1KB ~ 1MB) ──
    print("\n▶ Size sweep (1KB ~ 1MB)...")
    for kb in [1, 10, 100, 1000]:
        content = "# Test\n\n" + "x" * (kb * 1000)
        with open(f"{TMP}/size_{kb}kb.md", "w") as f:
            f.write(content)
        _create_aidoc(f"{TMP}/size_{kb}kb.md", f"{TMP}/size_{kb}kb.aidoc")

        fast = bench_read(
            f"Fast ({kb}KB)", aidoc.read_md_fast, f"{TMP}/size_{kb}kb.aidoc", n=500
        )
        std = bench_read(
            f"ZIP ({kb}KB)",
            lambda p: zipfile.ZipFile(p).read("content.md").decode("utf-8-sig"),
            f"{TMP}/size_{kb}kb.aidoc",
            n=500,
        )

        sizes.append(
            {
                "size_kb": kb,
                "fast_us": fast["avg_us"],
                "zip_us": std["avg_us"],
                "ratio": std["avg_us"] / fast["avg_us"],
            }
        )
        print(
            f"  {kb}KB: Fast={fast['avg_us']:.1f}μs,"
            f" ZIP={std['avg_us']:.1f}μs,"
            f" Ratio={sizes[-1]['ratio']:.1f}x"
        )

    # ── Summary ──
    print(f"\n{'='*60}")
    print("Summary")
    print(f"{'='*60}")
    print(f"\n{'Test':40s} {'Avg':>8s} {'Median':>8s} {'P99':>8s}")
    print(f"{'-'*40} {'-'*8} {'-'*8} {'-'*8}")
    for r in results:
        print(
            f"{r['title']:40s} {r['avg_us']:>7.1f}μs"
            f" {r['median_us']:>7.1f}μs {r['p99_us']:>7.1f}μs"
        )

    print(f"\n{'Test':30s} {'Fast(μs)':>10s} {'ZIP(μs)':>10s} {'Ratio':>10s}")
    print(f"{'-'*30} {'-'*10} {'-'*10} {'-'*10}")
    for s in sizes:
        print(
            f"{s['size_kb']:>4d}KB{'':26s}"
            f" {s['fast_us']:>9.1f}μs"
            f" {s['zip_us']:>9.1f}μs"
            f" {s['ratio']:>9.1f}x"
        )

    # 保存结果
    out = {"results": results, "sizes": sizes}
    result_path = f"{TMP}/bench-results.json"
    json.dump(out, open(result_path, "w"), indent=2)
    print(f"\nResults saved: {result_path}")

    # 清理临时文件
    for f in os.listdir(TMP):
        os.remove(os.path.join(TMP, f))


if __name__ == "__main__":
    main()
