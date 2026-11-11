from app.fake_shopify_client import FakeShopifyClient
from app.models import Policy, Product
from app.store import VectorStore
from app.sync import run_sync


class StubEmbedder:
    """Doesn't call any real embedding API; sync's own text/handle plumbing
    is what these tests check, not retrieval quality."""

    dimensions = 1
    match_threshold = 0.0

    def embed(self, text: str) -> list[float]:
        return [0.0]


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

    run_sync(client, store, StubEmbedder())

    product_ids = {entry.id for entry in store.entries if entry.kind == "product"}
    assert product_ids == {product.id for product in client.get_products()}


def test_run_sync_carries_the_product_handle_onto_its_store_entry():
    product = Product(
        id="gid://shopify/Product/1",
        handle="classic-cotton-t-shirt",
        title="Classic Cotton T-Shirt",
        description="A tee.",
    )
    store = VectorStore()

    run_sync(StubShopifyClient([product], []), store, StubEmbedder())

    [entry] = store.entries
    assert entry.handle == "classic-cotton-t-shirt"


def test_run_sync_carries_the_policy_type_as_the_handle_onto_its_store_entry():
    client = FakeShopifyClient()
    store = VectorStore()

    run_sync(client, store, StubEmbedder())

    policy_entries = [entry for entry in store.entries if entry.kind == "policy"]
    assert {entry.handle for entry in policy_entries} == {entry.id for entry in policy_entries}


def test_run_sync_embeds_all_four_shop_policies():
    client = FakeShopifyClient()
    store = VectorStore()

    run_sync(client, store, StubEmbedder())

    policy_types = {entry.id for entry in store.entries if entry.kind == "policy"}
    assert policy_types == {"refund", "privacy", "terms_of_service", "shipping"}


def test_run_sync_embeds_price_variants_and_tags_alongside_title_and_description():
    product = Product(
        id="gid://shopify/Product/thin",
        title="The Draft Snowboard",
        description="",
        price="629.95 USD",
        variants=["Ice", "Electric Blue"],
        tags=["snowboard", "winter"],
    )
    store = VectorStore()

    run_sync(StubShopifyClient([product], []), store, StubEmbedder())

    [entry] = store.entries
    assert "The Draft Snowboard" in entry.text
    assert "629.95 USD" in entry.text
    assert "Ice" in entry.text and "Electric Blue" in entry.text
    assert "snowboard" in entry.text and "winter" in entry.text


def test_run_sync_removes_products_no_longer_returned_by_the_client():
    store = VectorStore()
    stale_product = Product(id="gid://shopify/Product/old", title="Discontinued Mug", description="Gone.")
    run_sync(StubShopifyClient([stale_product], []), store, StubEmbedder())
    assert {entry.id for entry in store.entries} == {stale_product.id}

    run_sync(StubShopifyClient([], []), store, StubEmbedder())

    assert store.entries == []


def test_fake_shopify_client_exposes_no_way_to_fetch_pages():
    client = FakeShopifyClient()

    assert not hasattr(client, "get_pages")
