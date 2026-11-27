# 💡 B-Trees vs B+ Trees vs LSM-Trees

> **TL;DR:** B‑Trees store keys in internal nodes, B+‑Trees push all records to a linked leaf level for fast range scans, while LSM‑Trees batch writes in immutable files to slash disk seeks at the expense of read‑amplification.

---

## 👶 Explain Like I'm 5 (ELI5)

Imagine a giant bookshelf where each shelf not only holds books but also tells you where to find other shelves – that’s a B‑Tree. You can jump straight to the right shelf without scanning every book, but the books are scattered across the whole shelf system.

Now picture the same library where every shelf only holds a tiny index card pointing to the next shelf, and all the actual books sit neatly on a single long hallway of shelves linked together – that’s a B+‑Tree. Finding a range of books becomes a stroll down the hallway, because the books are all in order.

Finally, think of a mailroom that never writes directly to the filing cabinets. Instead, it piles incoming letters in a tray (memory), writes a quick receipt (WAL), and later moves whole batches of sorted letters into the cabinets as sealed boxes. This batch‑moving mailroom is an LSM‑Tree – it avoids the hassle of opening a cabinet for each letter, but you sometimes have to open many boxes to find a single letter later.

---

## 🔍 The Technical Deep-Dive

At the OS level, each node of a B‑Tree or B+‑Tree occupies one or more disk pages (typically 4‑16KB). The tree is kept balanced by splitting/merging pages on insert/delete, guaranteeing O(logₙ N) disk seeks where n is the fan‑out (page size / key size). B+‑Trees differ by storing only keys (and child pointers) in internal pages, while leaf pages hold full records and a sibling pointer, forming a doubly‑linked list that enables sequential scans with a single seek followed by contiguous reads.

LSM‑Trees replace the mutable on‑disk structure with an in‑memory memtable (often a sorted skip‑list or red‑black tree) and an append‑only write‑ahead log (WAL). When the memtable fills, it is frozen and flushed as an immutable SSTable (Sorted String Table) on disk, typically in a hierarchical tiered layout (Level‑0, Level‑1, …). Reads must merge results from the memtable and multiple SSTable levels, incurring read amplification, while background compaction rewrites overlapping SSTables to reduce this cost, at the price of write amplification (each record may be rewritten O(log L) times, L = number of levels). Disk seeks are minimized because writes are sequential appends, and reads can be served by Bloom filters that skip irrelevant SSTables.

PostgreSQL’s default index type is a B‑Tree, optimized for point lookups and moderate range scans; its implementation uses the OS page cache and supports deduplication via HOT (Heap‑Only Tuple) updates. PostgreSQL also offers B+‑Tree‑like behavior via BRIN (Block Range INdexes) for very large tables. Apache Cassandra, on the other hand, employs an LSM‑Tree engine (based on the original Google Bigtable design) to sustain high write throughput across distributed nodes, using configurable compaction strategies (Size‑Tiered, Leveled, Time‑Window) to balance read latency and storage overhead.

### 📊 Comparison Matrix

| Feature | B‑Tree | B+‑Tree | LSM‑Tree |
|---|---|---|---|
| Disk Seek Pattern | Random reads/writes on split/merge | Sequential leaf scan after single seek | Mostly sequential writes, occasional read‑amplified merges |
| Write Amplification | Low (single page write) | Low (leaf page write) | High (memtable flush + compaction) |
| Read Amplification | Low to moderate | Low for point, moderate for range | High (multiple SSTable levels) |
| Range Scan Performance | Good (requires tree traversal) | Excellent (linked leaf list) | Poor to moderate (needs merge across SSTables) |
| Update/Delete Cost | In‑place page modification | In‑place leaf modification | Write‑only; updates become new entries, old versions reclaimed by compaction |
| Typical Use‑Case | OLTP, primary key lookups | OLAP, ordered scans, secondary indexes | Write‑heavy workloads, time‑series, log aggregation |
| Example DBs | PostgreSQL, MySQL InnoDB | PostgreSQL (via B+‑Tree index), SQLite | Cassandra, RocksDB, HBase |
| Memory Footprint | Moderate (cache pages) | Moderate (cache pages + leaf list) | Memtable + multiple SSTable metadata |
| Concurrency Control | Latch/lock per page | Latch/lock per leaf page | Lock‑free memtable, compaction runs in background |

---

## 🗺️ Visual Architecture & Flow

```mermaid
graph TD
    subgraph Write_Path
        A[Client Write] --> B[WAL Append]
        B --> C[Memtable Insert]
        C -->|Memtable Full| D[Flush to SSTable]
        D --> E[Background Compaction]
    end
    subgraph BTree_Insert
        F[Client Write] --> G[Locate Leaf]
        G --> H[Insert/ Split]
        H --> I[Update Parent Nodes]
    end
    subgraph BPlus_Insert
        J[Client Write] --> K[Locate Leaf]
        K --> L[Insert in Leaf]
        L --> M[Update Sibling Links]
        M --> N[Update Internal Keys]
    end
    style Write_Path fill:#f9f,stroke:#333,stroke-width:2px
    style BTree_Insert fill:#bbf,stroke:#333,stroke-width:2px
    style BPlus_Insert fill:#bfb,stroke:#333,stroke-width:2px
```

---

## 🛠️ Real-World Production Scenarios

1. **High‑throughput OLTP system (e.g., banking transactions) – PostgreSQL B‑Tree**: The workload consists of millions of point lookups and occasional short range queries. B‑Tree indexes give O(log N) point latency with minimal write amplification, fitting the strict ACID requirements.
2. **Analytical dashboard over time‑ordered logs – PostgreSQL B+‑Tree (or BRIN)**: Users frequently run queries like “show all events between 09:00 and 10:00”. The leaf‑linked list of a B+‑Tree lets the engine scan the relevant leaf pages sequentially after a single seek, dramatically speeding up range scans.
3. **Globally distributed write‑heavy telemetry store – Apache Cassandra LSM‑Tree**: Thousands of IoT devices push sensor readings continuously. Cassandra’s LSM engine batches writes into sequential SSTables, avoiding random disk I/O and scaling linearly across nodes, while background compaction keeps read latency acceptable for occasional point lookups.

---

## ⚠️ Common Myths & Gotchas

*Myth 1*: “B+‑Trees are always faster than B‑Trees.” In reality, B+‑Trees excel at range scans but have comparable point‑lookup cost; for pure point queries the extra leaf‑link overhead can even be a slight penalty.
*Myth 2*: “LSM‑Trees eliminate disk seeks, so they are the best choice for any database.” LSM reduces write‑seek cost but introduces read‑amplification and higher storage use; workloads dominated by random reads or low‑latency point lookups often perform better with B‑Tree indexes.
*Historical Trivia*: The original B‑Tree (Bayer & McCreight, 1972) was designed for magnetic disks where minimizing seeks was paramount; LSM‑Trees (O'Neil et al., 1996) emerged later to exploit the rise of cheap sequential storage and massive write workloads.

---

## 🔗 Authoritative References & RFCs

- https://www.postgresql.org/docs/current/indexes-types.html
- https://cassandra.apache.org/doc/latest/architecture/disk.html
- https://www.cs.cmu.edu/~scandal/cacm97.pdf
- https://www.oracle.com/technical-resources/articles/database/btree.html
