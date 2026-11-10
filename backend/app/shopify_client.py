import os
from typing import Protocol

import httpx

from app.models import Policy, Product

SHOPIFY_API_VERSION = "2024-10"

_PRODUCTS_QUERY = """
query {
  products(first: 250) {
    edges { node { id title description } }
  }
}
"""

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
        return [
            Product(id=edge["node"]["id"], title=edge["node"]["title"], description=edge["node"]["description"])
            for edge in data["products"]["edges"]
        ]

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
