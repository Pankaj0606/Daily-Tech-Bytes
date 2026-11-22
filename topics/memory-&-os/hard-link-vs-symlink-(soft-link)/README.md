# 💡 Hard Link vs Symlink (Soft Link)

> **TL;DR:** Hard links point directly to the same inode, while symlinks are separate files that store a pathname to the target.

---

## 👶 Explain Like I'm 5 (ELI5)

Imagine a library where every book has a unique ID tag (the inode). A hard link is like putting two identical checkout cards on the same book – both cards point straight to the same ID, so no matter which card you use, you get the exact same physical book. A symbolic link, on the other hand, is like writing down the shelf location of the book on a separate piece of paper. If you hand someone that paper, they have to look up the location first; if the book is moved or removed, the paper points to nowhere, becoming a "dangling" note.

Now think about moving books between branches of the library. You can copy the checkout card (hard link) only if the branches share the same catalog (same filesystem). The paper note (symlink) can point to a book in any branch because it just records the address, but if the address changes, the note becomes stale. This captures why hard links are fast and reliable within one filesystem, while symlinks are flexible across devices but depend on the path staying valid.

---

## 🔍 The Technical Deep-Dive

In Unix-like file systems each file is represented by an inode, a fixed-size data structure that stores metadata (owner, permissions, timestamps) and a list of disk block pointers containing the file's data. The directory entry is merely a mapping from a human‑readable name to an inode number. A hard link creates an additional directory entry that references the same inode number; the inode's link count (st_nlink) is incremented. Because the inode is unchanged, all hard links share the same file attributes, permissions, and data blocks. Deleting any hard link merely decrements the link count; the data blocks are reclaimed only when the count reaches zero, guaranteeing no dangling references within the same filesystem. Hard links cannot span mount points because inode numbers are only unique within a single superblock; attempting to link across devices returns EXDEV.

A symbolic (soft) link is a distinct inode of type S_IFLNK. Its data payload is a null‑terminated string containing the target pathname, which may be absolute or relative. When the kernel resolves a pathname, it reads the symlink's data and restarts the lookup with the new path. This indirection adds a small overhead (extra lookup and possible additional cache miss) and introduces the possibility of dangling symlinks if the target is moved or deleted. Symlinks can point to any location, including directories and files on different filesystems, because they operate at the pathname level rather than the inode level. Permissions on a symlink are largely ignored; access checks are performed on the final target after resolution. The kernel also imposes a maximum symlink depth (commonly 40) to prevent infinite loops.

From a storage perspective, a hard link consumes no extra data blocks beyond the directory entry (a few bytes for the name). A symlink consumes at least one disk block (or the space allocated within the inode for small links) to store the path string. In terms of performance, hard links are essentially free after the initial directory entry creation, while symlinks incur an extra VFS lookup. However, modern caches and the rarity of deep symlink chains make the difference negligible for most workloads. Cross‑device linking, backup tools, and container overlay filesystems rely heavily on symlinks because they preserve logical relationships without requiring shared inode spaces.

### 📊 Comparison Matrix

| Feature | Hard Link | Symbolic (Soft) Link |
|---|---|---|
| Underlying Mechanism | Direct inode reference (same inode number) | Separate inode storing target pathname |
| Cross‑Device Support | Not allowed (EXDEV) | Allowed |
| Directory Linking | Not permitted (POSIX) | Allowed (but can cause loops) |
| Storage Overhead | Minimal (directory entry only) | At least one block for path string |
| Deletion Safety | Data persists until last link removed | Can become dangling if target removed |
| Permission Checks | Performed on the inode itself | Performed on the final target after resolution |
| Use Cases | Duplicate file names, versioning within same FS | Shortcut to files/dirs across FS, user‑friendly aliases |
| Performance Impact | None beyond directory lookup | Extra pathname resolution step |
| Link Count Impact | Increments inode's link count | No effect on target's link count

---

## 🗺️ Visual Architecture & Flow

```mermaid
graph TD
    subgraph FS1[Filesystem A]
        A1[Directory /foo]
        A2[File "data.txt" (inode 123)]
        A3[Hard Link "data_hard" (inode 123)]
        A4[Symlink "data_soft" (inode 124)]
    end
    subgraph FS2[Filesystem B]
        B1[Directory /bar]
        B2[File "other.txt" (inode 200)]
    end
    A1 --> A2
    A1 --> A3
    A1 --> A4
    A4 -->|points to| A2
    A4 -.->|can point across| B2
    click A2 "https://en.wikipedia.org/wiki/Inode" "Inode details"
    click A4 "https://en.wikipedia.org/wiki/Symbolic_link" "Symlink info"
```

---

## 🛠️ Real-World Production Scenarios

1. **Log Rotation on a Single Disk**: A service writes logs to `app.log`. To keep the latest N logs without moving files, a hard link `app_current.log` is created pointing to the same inode. When the original `app.log` is rotated (renamed to `app.log.1`), the hard link still accesses the same data until the process closes the file descriptor, ensuring zero‑downtime reads.
2. **Container Overlay Filesystems**: Docker uses symlinks extensively to map host directories into container namespaces. A host path `/var/data` is symlinked into the container at `/app/data`. This works across the host's root filesystem and the container's layered FS, allowing the container to see updates instantly without sharing inodes.
3. **Cross‑Device Configuration Files**: A build system stores common configuration in `/etc/common.cfg` on the root partition but needs the same file on a separate `/mnt/backup` partition. A symlink `/mnt/backup/common.cfg -> /etc/common.cfg` provides a single source of truth while spanning devices, avoiding the EXDEV error that a hard link would raise.

---

## ⚠️ Common Myths & Gotchas

*Myth 1*: "Symlinks are just shortcuts and have no security implications." In reality, symlinks can be exploited for path traversal attacks if applications blindly follow them without validating the resolved path.
*Myth 2*: "Hard links can be used for directories to create tree‑like structures." POSIX forbids hard links to directories (except by the system) to prevent cycles that would break recursive algorithms and `fsck` utilities.
*Trivia*: The original Unix V6 only supported hard links; symbolic links were introduced later (V7) to provide cross‑filesystem flexibility.

---

## 🔗 Authoritative References & RFCs

- https://www.kernel.org/doc/html/latest/filesystems/vfs.html#inode-link-counts
- https://man7.org/linux/man-pages/man2/link.2.html
- https://man7.org/linux/man-pages/man2/symlink.2.html
- https://en.wikipedia.org/wiki/Symbolic_link
