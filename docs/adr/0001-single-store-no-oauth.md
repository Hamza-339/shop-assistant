# Single Shop per deployment, private custom-app token instead of OAuth

v1 serves exactly one Shopify Shop. We authenticate to the Admin API with a private custom-app access token (scopes `read_products`, `read_legal_policies`) rather than building the OAuth install flow a multi-merchant app would need. This keeps v1 to one deployable service with no App Store review, no per-merchant data isolation, and no token-refresh/install-uninstall lifecycle to handle.

**Consequences**: supporting a second Shop later requires retrofitting OAuth, a `shop_id`-scoped data model (currently the schema has no tenant key), and per-shop script tag distribution — not a config flag.
