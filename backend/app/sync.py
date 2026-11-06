from app.embeddings import LocalEmbedder
from app.shopify_client import ShopifyClient
from app.store import StoreEntry, VectorStore


def run_sync(client: ShopifyClient, store: VectorStore, embedder: LocalEmbedder) -> None:
    store.wipe()

    for product in client.get_products():
        text = f"{product.title}\n{product.description}"
        store.add(StoreEntry(id=product.id, kind="product", text=text, embedding=embedder.embed(text)))
