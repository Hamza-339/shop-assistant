from typing import Protocol

from app.models import Policy, Product


class ShopifyClient(Protocol):
    """Fetches Products and ShopPolicy objects from the Shopify Admin API.

    Custom Pages are not part of this interface (per GLOSSARY.md: Policy
    excludes Pages) and must never be added here.
    """

    def get_products(self) -> list[Product]: ...

    def get_policies(self) -> list[Policy]: ...
