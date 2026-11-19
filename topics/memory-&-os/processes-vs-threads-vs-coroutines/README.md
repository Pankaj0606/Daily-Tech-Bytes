# 💡 Processes vs Threads vs Coroutines

> **TL;DR:** Processes are heavyweight, isolated memory containers; threads share memory but incur kernel‑level context switches; coroutines are ultra‑lightweight user‑space tasks scheduled without kernel involvement.

---

## 👶 Explain Like I'm 5 (ELI5)

Imagine a big house where each family lives in its own locked room. The rooms (processes) have their own kitchens, bathrooms, and toys, so one family can’t accidentally eat another’s cake. If two siblings want to play together, they open a shared living room (threads) where they can reach the same toys without breaking any doors, but they still need the house manager to tell them when to take turns, which can be a bit slow.

Now picture a swarm of tiny robot chefs (coroutines) that work on a single countertop. They never need the house manager because they decide among themselves when to pause and let another robot take over. They’re so small that you can have hundreds of them cooking side‑by‑side, and if one robot trips, the others keep cooking without the whole house shaking.

---

## 🔍 The Technical Deep-Dive

At the kernel level, a **process** is represented by a Process Control Block (PCB) that stores its virtual address space, file descriptors, scheduling priority, and resource limits. Creating a process (fork/exec) clones the parent’s PCB and, optionally, its memory pages (copy‑on‑write), establishing full memory isolation via separate page tables. Context switching a process requires the CPU to reload CR3 (or equivalent) to switch page tables, flush TLB entries, and restore the full register set, which incurs tens of microseconds of latency.

A **thread** lives inside a process and is described by a Thread Control Block (TCB). The TCB holds the thread’s register state, stack pointer, and scheduling metadata, but it points to the same page tables as its parent process. Because the address space is shared, a context switch only needs to swap the CPU registers and stack pointer, avoiding a page‑table switch. The kernel still performs the switch, so the overhead is lower (typically a few microseconds) but still involves a transition to kernel mode and back.

**Coroutines** (e.g., Go's goroutines, Kotlin's suspend functions, Python's async/await) are scheduled in user space. Their control block is a lightweight struct containing a program counter, a small stack (often a few kilobytes), and a few registers. The runtime maintains a run‑queue and performs cooperative or work‑stealing scheduling. Since the switch never leaves user mode, the overhead is measured in nanoseconds: the runtime simply saves the current stack pointer and jumps to the next coroutine's entry point. Memory isolation is absent; all coroutines share the process heap, so synchronization primitives (channels, mutexes) are required to avoid data races. The trade‑off is massive scalability: a single OS thread can multiplex thousands of coroutines, limited only by memory for their stacks.

The OS also provides **user‑space scheduling primitives** such as `epoll`/`kqueue` that allow event‑driven programs to multiplex I/O without blocking threads. Coroutines often build on these primitives, turning I/O readiness events into suspension points, further reducing kernel involvement.

### 📊 Comparison Matrix

| Feature | Process | Thread | Coroutine |
|---|---|---|---|
| Memory Isolation | Full (separate page tables) | Shared (same address space) | Shared (process heap) |
| Scheduling | Kernel pre‑emptive | Kernel pre‑emptive | User‑space cooperative / work‑stealing |
| Context Switch Cost | High (TLB flush, page table load) | Medium (register save/restore) | Low (stack pointer swap) |
| Creation Overhead | Heavy (fork/exec) | Light (pthread_create) | Very light (runtime alloc) |
| Typical Use Cases | Isolation, security, different binaries | Parallel compute within same app | Massive I/O‑bound workloads, lightweight concurrency |
| Language/Runtime Support | All OSes | POSIX, Windows API | Go, Rust async, Kotlin, Python asyncio |

---

## 🗺️ Visual Architecture & Flow

```mermaid
graph LR
    Process[Process (PCB)] --> Thread[Thread (TCB)]
    Thread --> Coroutine[Coroutine (runtime struct)]
    subgraph OS Kernel
        Process
        Thread
    end
    subgraph User Space Runtime
        Coroutine
    end
```

---

## 🛠️ Real-World Production Scenarios

1. **Microservice Isolation**: Deploying a payment service that must not crash the entire system. Use separate processes (Docker containers) so memory faults are contained and security boundaries are enforced.
2. **High‑Performance Computing**: A scientific simulation that performs heavy matrix multiplications across CPU cores. Spawn a pool of native threads (e.g., OpenMP or pthreads) to exploit shared memory while keeping cache locality.
3. **Web Server Handling Millions of Connections**: A Go‑based API gateway serving 2M concurrent HTTP requests. Implement each request as a goroutine; the runtime multiplexes them over a modest number of OS threads, achieving low latency and minimal memory footprint.

---

## ⚠️ Common Myths & Gotchas

*Myth 1*: "Threads are always faster than processes because they share memory." In reality, the extra kernel transition for thread scheduling can outweigh the memory‑sharing benefit for short‑lived tasks; coroutines often beat both.
*Myth 2*: "Coroutines eliminate the need for synchronization." They still share the same heap, so data races are possible; proper primitives (channels, mutexes) are required.
*Trivia*: The term *coroutine* was coined in 1963 by Melvin Conway, long before modern async frameworks, but only gained mainstream traction with languages like Go and Python in the 2010s.

---

## 🔗 Authoritative References & RFCs

- https://man7.org/linux/man-pages/man2/fork.2.html
- https://golang.org/doc/effective_go#goroutines
- https://www.cs.cmu.edu/~rwh/pfpl/02-threads.pdf
- https://en.wikipedia.org/wiki/Coroutine
