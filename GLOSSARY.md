# Shop Assistant

An AI chat widget embedded on a single Shopify store's storefront that answers shopper questions about products and shop policies, grounded in synced catalog data.

## Language

**Policy**:
One of the four structured `ShopPolicy` objects exposed by Shopify's Admin API: refund, privacy, terms of service, shipping. Does not include custom Pages (FAQs, size guides, blog posts) — those are a distinct, unsupported content type in v1.
_Avoid_: Page, FAQ, policy page (when meaning a custom Page rather than a `ShopPolicy`)

**Citation**:
A reference attached to an assistant answer pointing back to the specific Product or Policy the answer was grounded in.

**Deflected Topic**:
A question category the assistant recognizes as out of scope (orders, payments, inventory/stock levels, discount codes) and responds to with a fixed fallback message instead of attempting an answer.
_Avoid_: unsupported question, rejected query

**Shop**:
The single Shopify store this deployment serves. v1 serves exactly one Shop per deployment; there is no concept of a Shop the assistant doesn't belong to.
_Avoid_: store, merchant (when meaning the Shop itself rather than the business operator), tenant

**Eval Pair**:
One hand-curated (question, expected answer) case in the fixed 30-pair set used to detect answer-quality regressions. Graded by an LLM judge, not string matching.
_Avoid_: test case, example, sample
