# 🧠 Daily Bite-Sized Tech & CS Fundamentals

An automated archive exploring computer science concepts, protocols, file formats, and systems design principles with ELI5 analogies, technical deep-dives, visual diagrams, and real-world production gotchas.

| ID | Category | Concept / Question | Core Takeaway | Status |
| :---: | :--- | :--- | :--- | :---: |
| #1 | `File Formats` | [JPEG vs JPG vs PNG vs WebP](./topics/file-formats/jpeg-vs-jpg-vs-png-vs-webp/README.md) | JPEG is lossy, PNG is lossless, and WebP combines both with optional transparency for superior web optimization. | ✅ Done |
| #2 | `Networking` | [HTTP/1.1 vs HTTP/2 vs HTTP/3](./topics/networking/http1.1-vs-http2-vs-http3/README.md) | HTTP/1.1 uses one TCP connection per request, HTTP/2 multiplexes many streams over a single TCP, and HTTP/3 does the same over QUIC/UDP, slashing latency and head‑of‑line blocking. | ✅ Done |
| #3 | `Storage & Encoding` | [UTF-8 vs ASCII vs Unicode](./topics/storage-&-encoding/utf-8-vs-ascii-vs-unicode/README.md) | UTF-8 encodes every Unicode code point using 1‑4 bytes, preserving ASCII’s 1‑byte legacy while supporting the world’s scripts. | ✅ Done |
| #4 | `Memory & OS` | [Stack vs Heap Memory](./topics/memory-&-os/stack-vs-heap-memory/README.md) | Stack memory is fast, ordered, and limited; heap memory is flexible, slower, and managed manually or by a garbage collector. | ✅ Done |
| #5 | `Security` | [Hashing vs Encryption vs Encoding](./topics/security/hashing-vs-encryption-vs-encoding/README.md) | Hashing is one‑way, encryption is two‑way with a secret key, and encoding is just a reversible format conversion. | ✅ Done |
| #6 | `Networking` | [TCP vs UDP](./topics/networking/tcp-vs-udp/README.md) | TCP guarantees ordered, reliable delivery via a handshake; UDP skips the ceremony for raw speed. | ✅ Done |
| #7 | `Networking` | [WebSockets vs SSE vs Long Polling](./topics/networking/websockets-vs-sse-vs-long-polling/README.md) | WebSockets give true full‑duplex, always‑on sockets; SSE provides simple server‑to‑client streams over HTTP; long polling mimics push with repeated request‑response cycles, incurring higher latency and overhead. | ✅ Done |
| #8 | `Networking` | [Forward Proxy vs Reverse Proxy](./topics/networking/forward-proxy-vs-reverse-proxy/README.md) | A forward proxy hides the client, a reverse proxy hides the server, each operating on opposite sides of the request flow. | ✅ Done |
