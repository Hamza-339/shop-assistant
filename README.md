# Shop Assistant

An AI chat widget embedded on a single Shopify store's storefront that answers shopper questions about products and shop policies, grounded in synced catalog data.

**Live demo:** https://shop-assistant-demo.myshopify.com

## How it works

1. The Shopify storefront page loads `widget.js` from the Vercel-hosted widget deployment.
2. The widget calls the FastAPI backend's `/api` endpoint with the shopper's question.
3. The backend searches Neon (synced product and policy data, embedded via Voyage) for relevant context.
4. The backend asks Claude to answer grounded in that retrieved context, returning the answer (with citation) or a fallback for deflected topics.

## Running locally

Two projects, one deployable backend service (see ADR-0001, ADR-0005): the widget is a static build artifact with no backend of its own.

### Backend

```sh
cd backend
python -m venv .venv
.venv/Scripts/activate   # .venv/bin/activate on macOS/Linux
pip install -e ".[dev]"
uvicorn app.main:app --reload
pytest
```

### Widget

```sh
cd widget
npm install
npm run build   # outputs dist/widget.js
npm run lint
```

## Deployment

Both projects deploy to Vercel's free Hobby plan as separate Vercel projects pointed at the `backend/` and `widget/` root directories of this repo (see ADR-0005: Vercel's 500MB Python bundle limit is why embedding runs against a hosted API instead of in-process).

- **Backend**: a Vercel Python Function (`backend/vercel.json`, entrypoint set in `backend/pyproject.toml`). Reads synced data from Neon (`DATABASE_URL`) at boot and never calls Shopify itself - `python -m app.sync` is the only writer, run manually or on a schedule (ADR-0002). Required environment variables, set in the Vercel project (see `backend/.env.example` for the full list): `ANTHROPIC_API_KEY`, `SHOPIFY_STORE_DOMAIN`, `SHOPIFY_ACCESS_TOKEN`, `VOYAGE_API_KEY`, `DATABASE_URL`, `STOREFRONT_ORIGIN` (the live storefront's real origin, for the CORS allowlist).
- **Widget**: a static Vercel deployment (`widget/vercel.json`) serving `dist/widget.js`. The live storefront's script tag points `data-api-base` at the deployed backend's `/api` URL. Optional attributes: `data-color` (brand color, hex) and `data-chips` (pipe-separated suggestion questions, max 3; defaults to policy questions if omitted or empty).

## Eval score

90% (27/30) on the answer-quality eval set.

## Known limits

- Broad or open-ended product questions can miss relevant catalog items.
- Answers can be long.
- Voyage's free tier caps embedding calls at roughly 3 requests per minute, so the live demo can only handle about 3 questions per minute (see ADR-0005).

## ADRs

- [ADR-0001: Single Shop per deployment, private custom-app token instead of OAuth](docs/adr/0001-single-store-no-oauth.md)
- [ADR-0002: Scheduled/manual full resync instead of webhook-driven sync](docs/adr/0002-scheduled-sync-not-webhooks.md)
- [ADR-0003: In-process local embedding model instead of an external embeddings API](docs/adr/0003-in-process-local-embeddings.md)
- [ADR-0004: No per-request API auth — CORS allowlist + IP rate limiting only](docs/adr/0004-no-request-level-auth.md)
- [ADR-0005: Hosted embeddings API (Voyage AI) instead of an in-process local model](docs/adr/0005-hosted-embeddings-api-instead-of-in-process-model.md)
