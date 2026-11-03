# Scheduled/manual full resync instead of webhook-driven sync

Catalog and policy data sync via a scheduled or manually-triggered full resync (wipe and re-embed) rather than reacting to `products/update`/`products/delete` webhooks. This avoids standing up a webhook endpoint, HMAC verification, and incremental upsert/delete tracking — at single-Shop scale, re-embedding the whole catalog is cheap and eliminates drift bugs from missed events.

Real-time freshness (webhooks) was the alternative; we chose staleness-until-next-sync as an acceptable v1 trade-off.
