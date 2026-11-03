# No per-request API auth — CORS allowlist + IP rate limiting only

The `/api` endpoint is called directly from a public storefront by a widget whose source (including any embedded token) is visible to every visitor. A request-level API key would be visible in page source and so cannot function as a real secret. v1's abuse protection is a CORS allowlist scoped to the Shop's storefront domain plus IP-based rate limiting (20 req/min/IP), not an API key or signed request.

**Consequences**: this is deliberate, not an oversight — a future reader adding an "API key" to this endpoint without also solving the client-secret-exposure problem would add complexity without adding security.
