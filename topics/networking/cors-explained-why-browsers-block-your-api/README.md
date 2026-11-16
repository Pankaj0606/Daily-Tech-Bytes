# 💡 CORS Explained: Why browsers block your API

> **TL;DR:** Browsers enforce the Same‑Origin Policy, so APIs must explicitly grant cross‑origin access via CORS headers.

---

## 👶 Explain Like I'm 5 (ELI5)

Imagine a playground where each kid has a colored wristband that says which sandbox they belong to. The rule is: a kid can only play with toys in the sandbox that matches their wristband color. If a kid from the red team wants to use a blue sandbox swing, the swing’s caretaker must first check a special permission slip that says "Red kids are allowed here today." Without that slip, the caretaker blocks the kid, even though the swing works perfectly.

Now picture a parent (the browser) watching the kids. The parent doesn’t let any kid grab a toy from another sandbox unless the caretaker shows the permission slip. The parent’s job is to keep the playground safe, preventing kids from accidentally breaking toys or taking things that aren’t theirs. That’s exactly what a browser does with web pages: it only lets a page talk to resources that belong to its own “color” (origin) unless the server hands over a signed permission note (CORS headers).

---

## 🔍 The Technical Deep-Dive

The Same‑Origin Policy (SOP) is enforced by the browser at the HTTP layer. An origin is defined as the tuple scheme://host:port. When a script issues a fetch/XHR to a different origin, the browser classifies the request as either a *simple request* (GET, HEAD, POST with safe content‑type and no custom headers) or a *non‑simple* request. Simple requests are sent directly, but the browser blocks the response unless the server includes an Access-Control-Allow-Origin header that matches the requesting origin (or '*').

For non‑simple requests, the browser performs a *preflight* OPTIONS request. This OPTIONS request contains Access-Control-Request-Method and Access-Control-Request-Headers listing the actual method and any custom headers the real request will use. The server must respond with Access-Control-Allow-Methods, Access-Control-Allow-Headers, and Access-Control-Allow-Origin. Only if all values satisfy the browser’s checks does it proceed to send the actual request. The preflight is a separate TCP/HTTP transaction, adding latency but protecting the server from unintended side‑effects (e.g., state‑changing methods) without explicit consent.

At the OS level, the browser’s networking stack opens a socket, performs DNS resolution, and establishes a TLS session (if HTTPS). The SOP check occurs after the HTTP response headers are parsed but before the response body is exposed to JavaScript. The Access-Control headers are not part of the TCP payload semantics; they are purely application‑layer conventions interpreted by the browser. Servers can configure these headers via web server modules (nginx, Apache) or application middleware (Express CORS, Spring). Misconfiguration (e.g., echoing back the Origin header without validation) can unintentionally open the API to any site, defeating the security intent of SOP.

### 📊 Comparison Matrix

| Feature | Simple Request | Preflight Request | No CORS (Blocked) |
|---|---|---|---|
| Browser Overhead | Minimal (single HTTP round‑trip) | Extra OPTIONS round‑trip adds latency | Immediate block, no network cost |
| Server Logic | Only need Access-Control-Allow-Origin | Must handle OPTIONS, validate methods/headers, return multiple Access-Control-* headers | None (request never reaches server) |
| Security Granularity | Origin‑wide allow or deny | Fine‑grained control per method/header | N/A |
| Best For | Public GET APIs, image assets, fonts | State‑changing APIs, custom headers, non‑standard methods | Internal same‑origin calls only |

---

## 🗺️ Visual Architecture & Flow

```mermaid
graph TD
    A[Browser (Page Origin)] -->|Simple GET/POST| B[Server (Different Origin)]
    B -->|Response with Access-Control-Allow-Origin| A
    A -->|Non‑simple request| C[Browser sends OPTIONS preflight]
    C -->|OPTIONS with Access-Control-Request-Method/Headers| B
    B -->|OPTIONS response with Access-Control-Allow-*| C
    C -->|Actual request (e.g., PUT with custom header)| B
    B -->|Response with Access-Control-Allow-Origin| A
```

---

## 🛠️ Real-World Production Scenarios

1. **Third‑party widget**: A news site embeds a weather widget hosted on weatherapi.com. The widget makes a GET request for JSON data. The API returns Access-Control-Allow-Origin: * so any site can fetch the data without a preflight, keeping latency low.
2. **Internal microservice with custom auth header**: A front‑end SPA on https://app.example.com calls https://api.example.com/users with an Authorization: Bearer token. Because the Authorization header is custom, the browser issues a preflight OPTIONS. The API must answer with Access-Control-Allow-Origin: https://app.example.com, Access-Control-Allow-Methods: GET, POST, PUT, and Access-Control-Allow-Headers: Authorization, Content-Type.
3. **Legacy integration using JSONP**: An older analytics dashboard cannot use CORS because it must support IE8. It loads a <script> tag pointing to https://analytics.example.com/collect?callback=handleData. The server wraps the JSON in a JavaScript function call, bypassing SOP but sacrificing POST support and security guarantees.

---

## ⚠️ Common Myths & Gotchas

*CORS is a server‑side security feature* – In reality, CORS is enforced by the browser; the server merely signals permission. Misconfiguring headers can expose data, but the browser is the gatekeeper.
*Disabling CORS in the browser makes an API safe* – Turning off SOP removes the browser’s protection, allowing any site to read responses, which is the opposite of security.
*Preflight always hurts performance* – While preflights add an extra round‑trip, they prevent unintended state changes and can be cached (Access-Control-Max-Age), mitigating the impact.

---

## 🔗 Authoritative References & RFCs

- [RFC 6454 – The Web Origin Concept](https://datatracker.ietf.org/doc/html/rfc6454)
- [MDN Web Docs – CORS](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)
- [W3C Recommendation – Cross-Origin Resource Sharing](https://www.w3.org/TR/cors/)
- [OWASP – Cross-Origin Resource Sharing (CORS) Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/CORS_Configuration_Cheat_Sheet.html)
