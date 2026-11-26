# 💡 CPU Caches: L1 vs L2 vs L3 and False Sharing

> **TL;DR:** L1 is tiny and fastest, L2 a bigger middle‑man, L3 is shared and slower, and false sharing wastes that speed by making cores fight over the same cache line.

---

## 👶 Explain Like I'm 5 (ELI5)

Imagine a kitchen where each chef has a personal spice rack (L1), a shared pantry on the same counter (L2), and a big walk‑in fridge in the back (L3). The personal rack is right at the chef’s fingertips, so they grab a pinch of salt instantly. The pantry is a step away – still quick, but the chef has to walk a few paces. The fridge is down the hallway; it holds a lot more, but it takes time to fetch items.

Now picture two chefs reaching for the same jar of pepper that sits on the pantry shelf. They both try to grab it at the same moment, causing a little tug‑of‑war. While they argue, the other chefs wait, and the whole kitchen slows down. That tug‑of‑war is like false sharing: different threads using different data that happen to live on the same 64‑byte cache line, forcing the CPU cores to constantly negotiate ownership and losing the speed advantage of the nearby spice racks.

---

## 🔍 The Technical Deep-Dive

CPU caches are hierarchical SRAM structures that bridge the speed gap between the ultra‑fast execution units and the comparatively slow main memory. L1 cache resides on each core, typically split into 32 KB instruction and 32 KB data slices, with a latency of ~4 cycles and a line size of 64 bytes. Its proximity (often within the same silicon die region as the decode/execute pipeline) enables the processor to fetch a line in a single clock tick after the address is decoded.

L2 cache is also core‑private but larger (256 KB‑1 MB) and slightly farther in the memory hierarchy, yielding ~12 cycles latency. It acts as a victim cache for L1: evicted L1 lines are written here, and on an L1 miss the core probes L2 before issuing a bus transaction. L3, when present, is a unified, chip‑wide cache (2‑64 MB) with ~30‑40 cycles latency. It is physically indexed, physically tagged (PIPT) and is the last stop before the memory controller. L3 is inclusive on many Intel designs, meaning any line present in L1/L2 must also exist in L3, simplifying coherence.

Cache coherence is enforced by the MESI protocol (Modified, Exclusive, Shared, Invalid). Each cache line carries a state that dictates which core may read or write it. When a core wants to write a line in Shared state, it issues a BusRdX (read‑exclusive) which invalidates other copies, transitioning the line to Modified. The protocol ensures that at most one core holds a writable copy, while others may hold read‑only copies.

False sharing occurs when distinct variables accessed by different threads reside on the same 64‑byte line. Even though the threads logically operate on independent data, any write forces the line into Modified state, invalidating the other core’s copy. The next read by the other core triggers a cache‑to‑cache transfer, incurring the full coherence latency repeatedly. This micro‑contention can degrade performance dramatically, turning an O(1) access pattern into a bandwidth‑bound bottleneck.

Operating systems contribute by allocating memory with page‑size granularity (4 KB) and providing APIs like `posix_memalign` or `aligned_alloc` to align structures to cache‑line boundaries. Modern compilers emit `__builtin_assume_aligned` hints and can pad structs (`alignas(64)`) to avoid inadvertent sharing. Profilers (e.g., Intel VTune, perf) expose cache‑miss and false‑sharing metrics, allowing engineers to refactor data layouts, employ per‑thread buffers, or use lock‑free algorithms that respect cache line ownership.

### 📊 Comparison Matrix

| Feature | L1 | L2 | L3 |
|---|---|---|---|
| Typical Size | 32‑64 KB per core | 256 KB‑1 MB per core | 2‑64 MB shared |
| Latency (cycles) | ~4 | ~12 | ~30‑40 |
| Associativity | 8‑way | 8‑way | 16‑way |
| Hit Rate Target | >99% | >95% | >90% |
| Coherence Scope | Core‑local (MESI) | Core‑local (MESI) | Chip‑wide (MESI) |
| Best For | Hot instruction/data, branch predictors | Working set that spills from L1, prefetch buffers | Large shared data, cross‑core reads |

---

## 🗺️ Visual Architecture & Flow

```mermaid
graph LR
    subgraph Core_A
        L1A[L1 Cache (Core A)]
    end
    subgraph Core_B
        L1B[L1 Cache (Core B)]
    end
    L2A[L2 Cache (Core A)]
    L2B[L2 Cache (Core B)]
    L3[L3 Shared Cache]
    MEM[Main Memory]
    L1A --> L2A --> L3 --> MEM
    L1B --> L2B --> L3
    classDef core fill:#f9f,stroke:#333,stroke-width:2px;
    class L1A,L1B core;
    classDef cache fill:#bbf,stroke:#333,stroke-width:1px;
    class L2A,L2B,L3 cache;
    classDef mem fill:#dfd,stroke:#333,stroke-width:1px;
    class MEM mem;
    %% False sharing illustration
    FS[False Sharing on a 64‑byte line]
    L1A -- Write --> FS
    L1B -- Invalidate --> FS
```

---

## 🛠️ Real-World Production Scenarios

1. **High‑frequency trading engine** – Uses lock‑free ring buffers where each thread writes to its own slot. Aligning each slot to 64 bytes prevents false sharing, keeping L1 hit rates >99% and latency under microseconds.
2. **Web server request handling** – Worker threads maintain per‑thread statistics counters. Padding the counters to a full cache line avoids the cache‑line ping‑pong that would otherwise occur when many cores update a shared counter, preserving L2 throughput.
3. **Scientific simulation with large matrices** – The matrix is tiled so that each tile fits in L2. Tiles are processed by different cores; the tile boundaries are aligned to cache lines, ensuring that L3 is only used for occasional cross‑tile reads and that false sharing does not degrade the compute‑bound loops.

---

## ⚠️ Common Myths & Gotchas

*Myth 1:* "L3 is always slower than RAM." In reality, L3 latency (~30 cycles) is an order of magnitude faster than DRAM (~150‑200 cycles), though its bandwidth is lower than L1/L2.
*Myth 2:* "Cache lines are always 64 bytes on every CPU." Older x86 CPUs used 32‑byte lines, and some ARM designs can use 128‑byte lines; however, 64 bytes has been the de‑facto standard for the last decade.
*Myth 3:* "False sharing only matters in multithreaded code." Even single‑threaded code can suffer when the compiler packs unrelated fields into the same line and the CPU performs write‑allocate on each store, causing unnecessary line fills.

---

## 🔗 Authoritative References & RFCs

- https://www.intel.com/content/www/us/en/architecture-and-technology/quick-reference-guide.html
- https://en.wikipedia.org/wiki/Cache_coherency#MESI_protocol
- https://software.intel.com/content/www/us/en/develop/articles/false-sharing.html
- https://www.cs.utexas.edu/~hunt/class/2016-spring/cs350/lecture_notes/lecture15.pdf
