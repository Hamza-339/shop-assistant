from app.embeddings import LocalEmbedder
from app.fake_shopify_client import FakeShopifyClient
from app.models import Policy, Product
from app.store import VectorStore
from app.sync import run_sync


class StubShopifyClient:
    def __init__(self, products: list[Product], policies: list[Policy]) -> None:
        self._products = products
        self._policies = policies

    def get_products(self) -> list[Product]:
        return self._products

    def get_policies(self) -> list[Policy]:
        return self._policies


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


def test_run_sync_removes_products_no_longer_returned_by_the_client():
    store = VectorStore()
    stale_product = Product(id="gid://shopify/Product/old", title="Discontinued Mug", description="Gone.")
    run_sync(StubShopifyClient([stale_product], []), store, LocalEmbedder())
    assert {entry.id for entry in store.entries} == {stale_product.id}

    run_sync(StubShopifyClient([], []), store, LocalEmbedder())

    assert store.entries == []
