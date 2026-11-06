from app.embeddings import LocalEmbedder
from app.fake_shopify_client import FakeShopifyClient
from app.store import VectorStore
from app.sync import run_sync


def test_run_sync_embeds_every_product_from_the_client():
    client = FakeShopifyClient()
    store = VectorStore()

    run_sync(client, store, LocalEmbedder())

    product_ids = {entry.id for entry in store.entries if entry.kind == "product"}
    assert product_ids == {product.id for product in client.get_products()}


def test_run_sync_embeds_all_four_shop_policies():
    client = FakeShopifyClient()
    store = VectorStore()

    run_sync(client, store, LocalEmbedder())

    policy_types = {entry.id for entry in store.entries if entry.kind == "policy"}
    assert policy_types == {"refund", "privacy", "terms_of_service", "shipping"}
