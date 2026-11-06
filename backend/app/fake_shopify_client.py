from app.models import Policy, Product

SAMPLE_PRODUCTS = [
    Product(
        id="gid://shopify/Product/1",
        title="Classic Cotton T-Shirt",
        description="A breathable 100% cotton t-shirt available in sizes S-XL.",
    ),
    Product(
        id="gid://shopify/Product/2",
        title="Insulated Water Bottle",
        description="24oz stainless steel bottle that keeps drinks cold for 24 hours.",
    ),
    Product(
        id="gid://shopify/Product/3",
        title="Canvas Tote Bag",
        description="Durable canvas tote with reinforced handles, machine washable.",
    ),
]

SAMPLE_POLICIES = [
    Policy(type="refund", body="Items may be returned within 30 days of delivery for a full refund."),
    Policy(type="privacy", body="We only collect data necessary to process and fulfill your order."),
    Policy(type="terms_of_service", body="By placing an order you agree to these terms of service."),
    Policy(type="shipping", body="Standard shipping takes 5-7 business days within the continental US."),
]


class FakeShopifyClient:
    """Sample Shopify Admin API client. Real token-based client comes later."""

    def get_products(self) -> list[Product]:
        return list(SAMPLE_PRODUCTS)

    def get_policies(self) -> list[Policy]:
        return list(SAMPLE_POLICIES)
