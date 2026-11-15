# 💡 REST vs GraphQL vs gRPC

> **TL;DR:** REST is resource‑centric and text‑based, GraphQL is query‑driven and schema‑centric, while gRPC is contract‑driven, binary, and optimized for low‑latency RPC.

---

## 👶 Explain Like I'm 5 (ELI5)

Think of a restaurant. With REST, the menu lists whole dishes – you order a plate and get everything on it, even if you only wanted a bite of one ingredient. With GraphQL, you tell the chef exactly which ingredients you want on your plate, and the kitchen assembles just that, no waste. gRPC is like a fast‑food drive‑through where the order is written in a precise, pre‑agreed code (the contract), the kitchen speaks a secret language (binary protobuf) and hands you the food through a high‑speed conveyor belt (HTTP/2), so you get it in the blink of an eye.

In this analogy, the menu (REST) is simple to read but can give you more than you need (over‑fetching). The chef’s custom request (GraphQL) needs a clear recipe book (schema) so the kitchen knows what ingredients exist. The drive‑through (gRPC) requires both you and the kitchen to have the same exact ordering form, but when they do, the service is lightning fast and uses very little bandwidth.

---

## 🔍 The Technical Deep-Dive

At the OS level each protocol ultimately becomes a series of socket syscalls. REST traditionally rides on HTTP/1.1 over TCP: the client opens a TCP socket, writes an ASCII request line, headers, and optionally a body, then reads the response. The kernel’s TCP stack handles congestion control, retransmission, and flow control, while the HTTP library parses the textual protocol into a request object.

GraphQL still uses HTTP as the transport, but the payload is a JSON‑encoded query string that describes a selection set. The server first parses the query, validates it against a strongly typed schema (often built with GraphQL‑SDL), and then resolves each field by invoking resolver functions. Because the schema is introspectable, tooling can generate type‑safe client code that knows exactly which fields are available, eliminating over‑fetching. Internally the same TCP socket is used, but the request body can be larger or smaller depending on the query, and the server may batch resolver calls to reduce round‑trips.

gRPC flips the stack. It mandates HTTP/2 as the transport, which introduces multiplexed streams, binary framing, header compression (HPACK), and server push. The client and server exchange a .proto definition that the protoc compiler turns into language‑specific stubs. Those stubs serialize method arguments into Protocol Buffers – a compact binary format with field numbers, varint encoding, and optional fields. When a call is made, the stub writes a HEADERS frame (containing :method, :path, and gRPC‑specific metadata) followed by a DATA frame containing the protobuf payload. The HTTP/2 layer handles flow control per stream, allowing many RPCs to share a single TCP connection without head‑of‑line blocking. The kernel still deals with TCP, but the binary framing reduces CPU cycles spent on parsing text and cuts bandwidth, yielding sub‑millisecond latency for intra‑datacenter services.

### 📊 Comparison Matrix

| Feature | REST (HTTP/1.1) | GraphQL | gRPC (HTTP/2) |
|---|---|---|---|
| Transport | Text‑based HTTP/1.1 | Text‑based HTTP/1.1 or 2 | Binary HTTP/2 |
| Schema | Optional (OpenAPI) | Mandatory (SDL) | Mandatory (proto) |
| Over‑fetching | Common (fixed endpoints) | Rare (client selects fields) | None (method contracts) |
| Payload format | JSON, XML, etc. | JSON query + JSON response | Protobuf (binary) |
| Latency | Higher due to header size & parsing | Similar to REST, but can reduce round‑trips | Lowest – multiplexed streams & binary framing |
| Tooling | Mature, language‑agnostic | Strong introspection, auto‑generated types | Strong code‑gen, streaming support |
| Best for | Simple CRUD, public APIs | UI‑driven apps needing flexible queries | High‑throughput microservices, streaming |

---

## 🗺️ Visual Architecture & Flow

```mermaid
graph LR
    Client -->|HTTP/1.1| REST_Server
    Client -->|HTTP/1.1 (POST) JSON| GraphQL_Server
    Client -->|HTTP/2 binary frames| gRPC_Server
    subgraph REST_Server
        REST_Endpoint1[GET /users]
        REST_Endpoint2[POST /orders]
    end
    subgraph GraphQL_Server
        Resolver1[UserResolver]
        Resolver2[OrderResolver]
    end
    subgraph gRPC_Server
        ServiceA[UserService]
        ServiceB[OrderService]
    end
    REST_Endpoint1 --> Resolver1
    REST_Endpoint2 --> Resolver2
    ServiceA -->|Protobuf| ServiceB
```

---

## 🛠️ Real-World Production Scenarios

1. **Mobile app with highly variable UI data** – The app needs to fetch a user profile, posts, and comments in a single screen, but each screen shows a different subset of fields. GraphQL lets the client request exactly the needed fields, cutting down on over‑fetching and reducing the number of HTTP calls.
2. **High‑frequency trading platform** – Services exchange market ticks and order confirmations millions of times per second across data‑center clusters. gRPC’s HTTP/2 multiplexing and protobuf’s compact binary format keep latency sub‑millisecond and CPU overhead minimal.
3. **Public third‑party API for legacy integrations** – External partners expect simple, cache‑friendly URLs and can work with any language. A RESTful API over HTTP/1.1 with well‑documented OpenAPI specs provides the broadest compatibility and easy debugging via browsers or curl.

---

## ⚠️ Common Myths & Gotchas

*Myth 1*: "GraphQL always outperforms REST." In reality, GraphQL adds parsing and validation overhead; for simple fixed‑shape requests REST can be faster.
*Myth 2*: "gRPC can only be used inside a private network." While gRPC‑Web and gRPC‑JSON transcoding enable browser access, the core protocol works over the public internet as long as TLS is used.
*Trivia*: The term “gRPC” originally stood for “Google Remote Procedure Call,” and the project was open‑sourced in 2015 after powering many of Google’s internal services.

---

## 🔗 Authoritative References & RFCs

- [RFC 7230 – HTTP/1.1 Message Syntax and Routing](https://datatracker.ietf.org/doc/html/rfc7230)
- [GraphQL Specification](https://spec.graphql.org/October2021/)
- [gRPC Official Documentation](https://grpc.io/docs/)
- [HTTP/2 RFC 7540](https://datatracker.ietf.org/doc/html/rfc7540)
