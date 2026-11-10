from app.embeddings import LocalEmbedder
from app.shopify_client import ShopifyClient, shopify_client_from_env
from app.store import StoreEntry, VectorStore


def run_sync(client: ShopifyClient, store: VectorStore, embedder: LocalEmbedder) -> None:
    store.wipe()

    for product in client.get_products():
        text = f"{product.title}\n{product.description}"
        store.add(StoreEntry(id=product.id, kind="product", text=text, embedding=embedder.embed(text)))

    for policy in client.get_policies():
        store.add(StoreEntry(id=policy.type, kind="policy", text=policy.body, embedding=embedder.embed(policy.body)))


if __name__ == "__main__":
    # Manual trigger: `python -m app.sync`. A scheduler calls the same
    # run_sync() entry point.
    from dotenv import load_dotenv

    load_dotenv()
    run_sync(shopify_client_from_env(), VectorStore(), LocalEmbedder())
