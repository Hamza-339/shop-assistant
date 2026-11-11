# Shop Assistant

An AI chat widget embedded on a single Shopify store's storefront that answers shopper questions about products and shop policies, grounded in synced catalog data.

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
- **Widget**: a static Vercel deployment (`widget/vercel.json`) serving `dist/widget.js`. The live storefront's script tag points `data-api-base` at the deployed backend's `/api` URL.
