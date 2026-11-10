import os
from typing import Protocol

import httpx

from app.models import Policy, Product

SHOPIFY_API_VERSION = "2024-10"

_PRODUCTS_QUERY = """
query {
  products(first: 250) {
    edges {
      node {
        id
        title
        description
        tags
        priceRangeV2 { minVariantPrice { amount currencyCode } }
        variants(first: 100) { edges { node { title } } }
      }
    }
  }
}
"""

_DEFAULT_VARIANT_TITLE = "Default Title"

_POLICIES_QUERY = """
query {
  shop {
    shopPolicies { type body }
  }
}
"""

_POLICY_TYPE_MAP = {
    "REFUND_POLICY": "refund",
    "PRIVACY_POLICY": "privacy",
    "TERMS_OF_SERVICE": "terms_of_service",
    "SHIPPING_POLICY": "shipping",
}


class ShopifyClient(Protocol):
    """Fetches Products and ShopPolicy objects from the Shopify Admin API.

    Custom Pages are not part of this interface (per GLOSSARY.md: Policy
    excludes Pages) and must never be added here.
    """

    def get_products(self) -> list[Product]: ...

    def get_policies(self) -> list[Policy]: ...


class ShopifyAdminClient:
    """Real token-based ShopifyClient using the Admin GraphQL API."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client

    def get_products(self) -> list[Product]:
        data = self._query(_PRODUCTS_QUERY)
        products = []
        for edge in data["products"]["edges"]:
            node = edge["node"]
            min_price = node["priceRangeV2"]["minVariantPrice"]
            variant_titles = [v["node"]["title"] for v in node["variants"]["edges"]]
            products.append(
                Product(
                    id=node["id"],
                    title=node["title"],
                    description=node["description"],
                    price=f"{min_price['amount']} {min_price['currencyCode']}",
                    variants=[title for title in variant_titles if title != _DEFAULT_VARIANT_TITLE],
                    tags=list(node["tags"]),
                )
            )
        return products

    def get_policies(self) -> list[Policy]:
        data = self._query(_POLICIES_QUERY)
        policies = []
        for policy in data["shop"]["shopPolicies"]:
            policy_type = _POLICY_TYPE_MAP.get(policy["type"])
            if policy_type is not None:
                policies.append(Policy(type=policy_type, body=policy["body"]))
        return policies

    def _query(self, query: str) -> dict:
        response = self._client.post("", json={"query": query})
        response.raise_for_status()
        return response.json()["data"]


def shopify_client_from_env() -> ShopifyAdminClient:
    """Builds a ShopifyAdminClient from SHOPIFY_STORE_DOMAIN/SHOPIFY_ACCESS_TOKEN."""
    domain = os.environ["SHOPIFY_STORE_DOMAIN"]
    token = os.environ["SHOPIFY_ACCESS_TOKEN"]
    client = httpx.Client(
        base_url=f"https://{domain}/admin/api/{SHOPIFY_API_VERSION}/graphql.json",
        headers={"X-Shopify-Access-Token": token, "Content-Type": "application/json"},
    )
    return ShopifyAdminClient(client)
