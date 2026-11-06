from app.embeddings import LocalEmbedder
from app.fake_shopify_client import FakeShopifyClient
from app.shopify_client import ShopifyClient
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
    # run_sync() entry point; FakeShopifyClient is swapped for the real
    # token-based client once it exists.
    run_sync(FakeShopifyClient(), VectorStore(), LocalEmbedder())
