# 💡 WebSockets vs SSE vs Long Polling

> **TL;DR:** WebSockets give true full‑duplex, always‑on sockets; SSE provides simple server‑to‑client streams over HTTP; long polling mimics push with repeated request‑response cycles, incurring higher latency and overhead.

---

## 👶 Explain Like I'm 5 (ELI5)

Think of three ways to get a message from a friend who lives next door. A walkie‑talkie lets you both talk whenever you want – you press a button and speak, and they hear you instantly, and vice‑versa. That’s like WebSockets: a permanent two‑way radio channel that stays open.

Now imagine a newspaper stand that constantly updates a scrolling ticker with the latest headlines. You can only read what the paper pushes out; you can’t send anything back. That’s Server‑Sent Events – the server streams updates, but the client only listens.

Finally, picture a child who keeps knocking on the neighbor’s door every few seconds to ask, “Is there any candy yet?” The neighbor opens the door, says “No,” and closes it, only for the child to knock again later. That’s long polling: the client repeatedly makes a fresh request to see if there’s new data, which works but wastes effort and energy.

---

## 🔍 The Technical Deep-Dive

At the OS level all three techniques ultimately use TCP sockets, but they differ in how the socket lifecycle is managed and how data is framed.

**WebSockets** start with an HTTP/1.1 (or HTTP/2) GET request that includes an Upgrade: websocket header. The server replies with 101 Switching Protocols, after which the TCP connection is hijacked for the ws:// or wss:// scheme. From this point the protocol defines a lightweight binary framing format: each frame carries a FIN bit, opcode, payload length (7, 16, or 64‑bit), optional masking key (client‑to‑server only), and the payload. Because the socket stays open, the kernel’s TCP stack can keep the connection in the ESTABLISHED state, using Nagle’s algorithm or TCP_NODELAY as configured. No new TCP handshakes are needed for each message, so latency is limited to the round‑trip time plus framing overhead (typically <2 bytes per frame plus optional mask). The server must maintain per‑connection state (socket descriptor, buffers, subscription topics), which impacts scalability; epoll/kqueue or I/O‑completion ports are used to multiplex thousands of sockets efficiently.

**Server‑Sent Events (SSE)** reuse a plain HTTP GET request with the Accept: text/event-stream header. The server responds with a 200 OK and a Content-Type: text/event-stream, then keeps the response body open, flushing newline‑delimited "event" blocks as they become available. Each block consists of optional "event:" and "id:" fields followed by a mandatory "data:" line and a double‑newline terminator. The underlying TCP socket remains in the ESTABLISHED state, but the protocol does not define a binary framing layer – it is pure UTF‑8 text. Because the client never sends data on this channel, the server can treat the connection as read‑only, simplifying back‑pressure handling. Reconnection logic is baked in: the client automatically retries with the Last‑Event‑ID header if the connection drops. Battery impact is low on mobile because the OS can keep the socket in a low‑power state when idle, and HTTP/2 can multiplex the stream with other requests.

**Long Polling** is a pattern built on ordinary HTTP request/response cycles. The client issues a GET (or POST) and the server holds the request open until either new data is available or a timeout (often 30‑60 seconds) occurs. When the server responds, the client immediately issues a new request, repeating the cycle. Each poll incurs a full TCP handshake (or TLS handshake if wss) unless HTTP keep‑alive reuses the socket, but most browsers open a new connection after a timeout to avoid stale sockets. The server does not need to keep a persistent socket state beyond the request context; it can use thread pools, async I/O, or event‑driven frameworks to suspend the request. However, the repeated HTTP headers (≈400 bytes) and the need to re‑negotiate TLS add CPU and bandwidth overhead, and the latency includes the poll interval plus server processing time, making it less suitable for high‑frequency updates.

### 📊 Comparison Matrix

| Feature | WebSockets | Server‑Sent Events (SSE) | Long Polling |
|---|---|---|---|
| Direction | Full‑duplex (both) | Unidirectional (server→client) | Unidirectional (server→client) |
| Transport | TCP (ws/wss) | HTTP/1.1 (text/event-stream) | HTTP/1.1 (regular GET) |
| Latency | Low (single socket) | Low after initial request | Higher (new request each poll) |
| Overhead | Handshake + framing | Simple headers, no framing | Repeated HTTP headers each poll |
| Battery impact (mobile) | Moderate (keep socket) | Low (idle connection) | High (frequent wake‑ups) |
| Server scaling | Requires connection state | Stateless per client | Stateless per request |
| Browser support | All modern browsers | All modern browsers (except IE) | All browsers |
| Best use | Real‑time bidirectional apps (chat, gaming) | Live feeds, notifications | Legacy environments, simple alerts |

---

## 🗺️ Visual Architecture & Flow

```mermaid
graph TD
    C[Client] -->|HTTP GET (Long Poll)| LP[Long Polling Request]
    LP -->|Response| C
    C -->|HTTP GET (SSE Subscribe)| SSE[Server‑Sent Events Stream]
    SSE -->|Event Stream| C
    C -->|WebSocket Handshake| WS[WebSocket Upgrade]
    WS -->|Bidirectional Frames| C
```

---

## 🛠️ Real-World Production Scenarios

1. **Live collaborative editing** – A document editor where multiple users type simultaneously needs instant, two‑way updates. WebSockets are ideal because each client can push edits and receive others' edits over the same persistent channel with minimal latency.
2. **Stock ticker or news feed** – A financial dashboard that only displays new price points or headlines can use SSE. The server pushes new events as they arrive, the client never needs to send data back, and reconnection logic is handled automatically.
3. **Legacy IoT devices behind restrictive firewalls** – Some low‑cost sensors can only make occasional HTTP requests. Implementing long polling lets them poll a central server for configuration changes without requiring WebSocket support or additional ports, at the cost of higher bandwidth but with minimal client complexity.

---

## ⚠️ Common Myths & Gotchas

* **"WebSockets are just another version of HTTP"** – While the handshake starts with HTTP, once upgraded the protocol no longer follows HTTP semantics; it uses its own framing and can carry binary data directly.
* **"SSE works over HTTPS without any extra configuration"** – SSE relies on a persistent HTTP connection; many load balancers and proxies need explicit keep‑alive or timeout tuning, otherwise the stream may be cut off.
* **"Long polling is obsolete"** – In environments where WebSocket or HTTP/2 support is blocked (e.g., corporate proxies), long polling remains a reliable fallback that many CDNs still optimize for.

---

## 🔗 Authoritative References & RFCs

- [RFC 6455 – The WebSocket Protocol](https://datatracker.ietf.org/doc/html/rfc6455)
- [MDN Web Docs – Server‑Sent Events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
- [HTML5 Rocks – Long Polling vs. WebSockets](https://www.html5rocks.com/en/tutorials/websocket/basics/)
- [IETF – HTTP/2 Specification (relevant for multiplexed SSE)](https://datatracker.ietf.org/doc/html/rfc7540)
