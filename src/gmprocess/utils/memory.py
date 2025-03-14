import tracemalloc
import linecache

MB = 1024**2
INDENT = " "*4

def display_total(message: str):
    mem_size, mem_peak = tracemalloc.get_traced_memory()
    print(f"MEMORY {message}: current={mem_size/MB:.3f} MB, peak={mem_peak/MB:.3f} MB")

def display_mallocs(message: str, snapshot, limit=20):
    snapshot = snapshot.filter_traces((
        tracemalloc.Filter(False, "<frozen importlib._bootstrap>"),
        tracemalloc.Filter(False, "<frozen importlib._bootstrap_external>"),
        tracemalloc.Filter(False, "<unknown>"),
    ))
    stats = snapshot.statistics("lineno", cumulative=True)

    print(f"MEMORY {message}: mallocs")
    for stat in stats[:limit]:
        frame = stat.traceback[0]
        print(f"{INDENT}{stat.size/MB:.3f} MB {frame.filename}:{frame.lineno}")
        line = linecache.getline(frame.filename, frame.lineno).strip()
        if line:
            print(f"{INDENT*2}{line}")

    other = stats[limit:]
    if other:
        total = sum(stat.size for stat in other)
        print(f"{INDENT}Other: {total/MB:.3f} MB in {len(other)} mallocs.")
    total = sum(stat.size for stat in stats)
    print(f"{INDENT}Total: {total/MB:.3f} MB in {len(stats)} mallocs.")