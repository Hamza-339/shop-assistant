from app.embeddings import LocalEmbedder
from app.models import Product
from app.shopify_client import ShopifyClient, shopify_client_from_env
from app.store import StoreEntry, VectorStore


def build_product_text(product: Product) -> str:
    """Assembles the text a product is embedded and grounded on.

    Includes price/variants/tags alongside title/description so a product
    with no description still has enough to ground an answer on (#21).
    """
    lines = [product.title, product.description]
    if product.price:
        lines.append(f"Price: {product.price}")
    if product.variants:
        lines.append(f"Options: {', '.join(product.variants)}")
    if product.tags:
        lines.append(f"Tags: {', '.join(product.tags)}")
    return "\n".join(lines)


def run_sync(client: ShopifyClient, store: VectorStore, embedder: LocalEmbedder) -> None:
    store.wipe()

    for product in client.get_products():
        text = build_product_text(product)
        store.add(StoreEntry(id=product.id, kind="product", text=text, embedding=embedder.embed(text)))

    for policy in client.get_policies():
        store.add(StoreEntry(id=policy.type, kind="policy", text=policy.body, embedding=embedder.embed(policy.body)))


if __name__ == "__main__":
    # Manual trigger: `python -m app.sync`. A scheduler calls the same
    # run_sync() entry point.
    from dotenv import load_dotenv

    load_dotenv()
    run_sync(shopify_client_from_env(), VectorStore(), LocalEmbedder())
