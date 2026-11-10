import httpx

from app.models import Policy, Product
from app.shopify_client import ShopifyAdminClient, shopify_client_from_env


def _client_with_response(response_json: dict) -> ShopifyAdminClient:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=response_json)

    transport = httpx.MockTransport(handler)
    return ShopifyAdminClient(httpx.Client(base_url="https://test-shop.myshopify.com", transport=transport))


def test_get_products_maps_the_graphql_response_to_products():
    client = _client_with_response(
        {
            "data": {
                "products": {
                    "edges": [
                        {
                            "node": {
                                "id": "gid://shopify/Product/1",
                                "handle": "classic-cotton-t-shirt",
                                "title": "Classic Cotton T-Shirt",
                                "description": "A tee.",
                                "tags": ["apparel", "cotton"],
                                "priceRangeV2": {"minVariantPrice": {"amount": "19.99", "currencyCode": "USD"}},
                                "variants": {"edges": [{"node": {"title": "Small"}}, {"node": {"title": "Large"}}]},
                            }
                        }
                    ]
                }
            }
        }
    )

    products = client.get_products()

    assert products == [
        Product(
            id="gid://shopify/Product/1",
            handle="classic-cotton-t-shirt",
            title="Classic Cotton T-Shirt",
            description="A tee.",
            price="19.99 USD",
            variants=["Small", "Large"],
            tags=["apparel", "cotton"],
        )
    ]


def test_get_products_omits_the_default_title_variant_for_single_variant_products():
    client = _client_with_response(
        {
            "data": {
                "products": {
                    "edges": [
                        {
                            "node": {
                                "id": "gid://shopify/Product/2",
                                "handle": "gift-card",
                                "title": "Gift Card",
                                "description": "",
                                "tags": [],
                                "priceRangeV2": {"minVariantPrice": {"amount": "25.00", "currencyCode": "USD"}},
                                "variants": {"edges": [{"node": {"title": "Default Title"}}]},
                            }
                        }
                    ]
                }
            }
        }
    )

    products = client.get_products()

    assert products[0].variants == []


def test_get_policies_maps_known_policy_types_and_skips_unrecognized_ones():
    client = _client_with_response(
        {
            "data": {
                "shop": {
                    "shopPolicies": [
                        {"type": "REFUND_POLICY", "body": "30 days."},
                        {"type": "LEGAL_NOTICE", "body": "N/A"},
                    ]
                }
            }
        }
    )

    policies = client.get_policies()

    assert policies == [Policy(type="refund", body="30 days.")]


def test_shopify_client_from_env_builds_a_client_against_the_configured_store(monkeypatch):
    monkeypatch.setenv("SHOPIFY_STORE_DOMAIN", "test-shop.myshopify.com")
    monkeypatch.setenv("SHOPIFY_ACCESS_TOKEN", "test-token")

    client = shopify_client_from_env()

    assert isinstance(client, ShopifyAdminClient)
