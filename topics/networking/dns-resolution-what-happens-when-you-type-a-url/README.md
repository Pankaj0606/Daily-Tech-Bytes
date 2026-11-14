# 💡 DNS Resolution: What happens when you type a URL?

> **TL;DR:** When you type a URL, your device’s recursive resolver walks the DNS hierarchy—from root to TLD to authoritative servers—caching results along the way to translate the name into an IP address.

---

## 👶 Explain Like I'm 5 (ELI5)

Imagine the internet as a massive library where every book (website) has a unique shelf number (IP address) but you only know its title (URL). When you ask the librarian (your computer) for a book, they first check a giant index board at the entrance (root servers) that points to the section for the first letter of the title (TLD nameservers). Then they go to the specific aisle (authoritative server) that knows exactly where that book sits. Once they find the shelf number, they write it on a sticky note (cache) so the next time you ask, they can hand you the book instantly without walking the whole library again.

In this analogy, the librarian never memorizes every book’s location; they rely on the organized signs (anycast‑shared root servers) and the quick notes they keep (TTL‑based caching). This way, even if a single sign is down, another identical one nearby can answer, keeping the library running smoothly for everyone.

---

## 🔍 The Technical Deep-Dive

The resolution process begins the moment an application calls getaddrinfo() or a similar API. The OS hands the query to the configured recursive resolver (usually provided by the ISP or a public DNS service). The resolver checks its cache; if the answer is fresh (TTL not expired), it returns the IP immediately. If not, it initiates an iterative lookup:
1. **Root Query** – The resolver sends a DNS query (UDP/TCP 53) to a root server IP (e.g., 198.41.0.4). Root servers are anycasted, meaning the same IP is advertised from many geographically dispersed nodes, ensuring low latency and resilience. The response contains NS records for the TLD (e.g., .com) and their corresponding glue A records.
2. **TLD Query** – Using the NS list, the resolver contacts a TLD nameserver (e.g., a.com‑ns.example.net). The response includes NS records for the domain’s authoritative zone and glue records for those name servers.
3. **Authoritative Query** – The resolver finally queries the domain’s authoritative server for the specific record type (A, AAAA, CNAME, etc.). The server returns the answer along with TTL values.
4. **Caching** – The resolver stores the answer and all intermediate NS and glue records in its cache, keyed by the query name and type, respecting each record’s TTL. Subsequent queries hit the cache, dramatically reducing latency and load on the hierarchy.
5. **Response to Client** – The resolver sends the final IP address back to the OS, which hands it to the application.

Protocol nuances: UDP is used for most queries; if the response exceeds 512 bytes (or EDNS0‑negotiated size), the resolver retries over TCP. DNSSEC validation can be performed at the resolver, requiring additional DNSKEY and DS lookups. The resolver may also implement features like DNS over HTTPS (DoH) or DNS over TLS (DoT) to encrypt traffic, but the core iterative algorithm remains unchanged.

Performance considerations: Anycast reduces round‑trip time to the nearest root/TLD node. TTL values balance freshness vs. cache hit ratio; short TTLs improve agility (e.g., CDNs) but increase query volume. Recursive resolvers often employ prefetching and negative caching (NXDOMAIN) to further optimize.

OS interaction: Modern OSes support stub resolvers that forward queries to the recursive resolver, while also providing a local cache (e.g., nscd, systemd-resolved). The stub may implement fallback mechanisms if the primary resolver fails, trying secondary resolvers in parallel.

### 📊 Comparison Matrix

| Feature | Root Servers | TLD Nameservers | Recursive Resolver |
|---|---|---|---|
| Scope | Global (anycast) | Per‑TLD (anycast) | Per‑client or ISP |
| Latency | ~20‑30 ms (closest) | ~30‑50 ms | Depends on cache hit/miss |
| Overhead | Minimal (just NS referrals) | Moderate (zone delegation) | High on miss (full walk) |
| Best For | Providing authoritative delegation points | Delegating domains within a TLD | End‑user name resolution, caching, security |

---

## 🗺️ Visual Architecture & Flow

```mermaid
graph TD
    A[Application] --> B[OS Stub Resolver]
    B --> C[Recursive Resolver]
    C -->|Cache Miss| D[Root Server (Anycast)]
    D --> E[TLD Nameserver]
    E --> F[Authoritative Server]
    F --> C
    C -->|Cache Hit| G[Resolver Cache]
    G --> B
    B --> A
```

---

## 🛠️ Real-World Production Scenarios

1. **Enterprise Internal Services** – A company runs an internal DNS zone (e.g., corp.example.com) with its own authoritative servers. Employees' workstations point to the corporate recursive resolver, which caches internal records for fast intra‑network lookups while still delegating external names to the public hierarchy.
2. **Global CDN Edge Routing** – A content delivery network uses short TTL (30 s) A records that point to the nearest edge PoP. The recursive resolver respects the low TTL, frequently refreshing the mapping to adapt to traffic shifts, ensuring users receive the optimal IP.
3. **High‑Security Environments** – A financial institution enforces DNSSEC validation at its recursive resolvers and routes DNS over TLS to a trusted upstream resolver. Any invalid signatures cause NXDOMAIN responses, protecting against cache poisoning while still leveraging the root/TLD hierarchy.

---

## ⚠️ Common Myths & Gotchas

*Myth 1:* "Root servers store every domain’s IP address.* In reality, root servers only know the NS records for each top‑level domain; they never hold individual domain records.
*Myth 2:* "Caching DNS is always a security risk.* While stale records can cause issues, proper TTL management and DNSSEC validation mitigate most risks, and caching dramatically improves performance.
*Trivia:* The original 13 root server IPs were chosen to fit within the 32‑bit IPv4 address space constraints of the early internet; today they are anycast clusters of hundreds of physical machines.

---

## 🔗 Authoritative References & RFCs

- RFC 1034 – Domain Names – Concepts and Facilities
- RFC 1035 – Domain Names – Implementation and Specification
- IANA Root Zone Database (https://www.iana.org/domains/root/files)
- Cloudflare DNS Overview (https://www.cloudflare.com/learning/dns/what-is-dns/)
