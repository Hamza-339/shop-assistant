"""The 30 hand-curated Eval Pairs (#8), fixed against a snapshot of the
Shopify dev store's snowboard catalog and shop policies (fetched 2026-11-10).

Each pair's question targets a `kind` below it is written against,
independent of what `LocalEmbedder` retrieves for it at run time.
"""

from app.embeddings import LocalEmbedder
from app.eval_runner import EvalPair
from app.store import StoreEntry, VectorStore

# --- Product catalog snapshot (title + description, as synced from Admin API) ---

_PRODUCTS: list[tuple[str, str, str]] = [
    ("gid://shopify/Product/15467938283603", "Gift Card", "This is a gift card for the store"),
    ("gid://shopify/Product/15467938316371", "The Inventory Not Tracked Snowboard", ""),
    ("gid://shopify/Product/15467938381907", "The Archived Snowboard", ""),
    ("gid://shopify/Product/15467938414675", "The Hidden Snowboard", ""),
    ("gid://shopify/Product/15467938447443", "The Collection Snowboard: Hydrogen", ""),
    ("gid://shopify/Product/15467938480211", "The Minimal Snowboard", ""),
    ("gid://shopify/Product/15467938512979", "The Compare at Price Snowboard", ""),
    ("gid://shopify/Product/15467938545747", "Selling Plans Ski Wax", ""),
    ("gid://shopify/Product/15467938578515", "The Draft Snowboard", ""),
    (
        "gid://shopify/Product/15467938611283",
        "The Complete Snowboard",
        "This PREMIUM snowboard is so SUPERDUPER awesome!",
    ),
    ("gid://shopify/Product/15467938644051", "The Out of Stock Snowboard", ""),
    ("gid://shopify/Product/15467938676819", "The Videographer Snowboard", ""),
    ("gid://shopify/Product/15467938742355", "The Multi-location Snowboard", ""),
    ("gid://shopify/Product/15467938775123", "The 3p Fulfilled Snowboard", ""),
    ("gid://shopify/Product/15467938807891", "The Multi-managed Snowboard", ""),
    ("gid://shopify/Product/15467938840659", "The Collection Snowboard: Oxygen", ""),
    ("gid://shopify/Product/15467938938963", "The Collection Snowboard: Liquid", ""),
]

# --- Shop policy snapshot (plain-text distillation of the Admin API's shopPolicies) ---

_POLICIES: list[tuple[str, str]] = [
    (
        "refund",
        "Return eligibility depends on the items in your order. Returned items must be "
        "unworn or unused, with tags, and in their original packaging. Contact us to ask "
        "about return options and how to start a return. Unless we state otherwise or "
        "applicable law requires otherwise, you are responsible for return shipping costs "
        "for change-of-mind returns. Please inspect your order on receipt and contact us "
        "immediately if an item is defective, damaged, or wrong.",
    ),
    (
        "privacy",
        "shop-assistant-demo operates this store, powered by Shopify, to provide you with a "
        "curated shopping experience. We collect or process personal information that "
        "identifies or can reasonably be linked to you or another person; this does not "
        "include information collected anonymously or de-identified information.",
    ),
    (
        "shipping",
        "Orders are processed within 1 business day (excluding holidays); orders placed "
        "after noon or on weekends and holidays may begin processing the next business day. "
        "Shipping charges are calculated at checkout based on destination, order weight, "
        "and shipping method. Orders shipped to Canada may be subject to GST, HST, PST, "
        "QST, RST, customs duties, import taxes, and carrier brokerage or handling fees.",
    ),
    (
        "terms_of_service",
        "shop-assistant-demo operates this store, powered by Shopify, to provide the "
        "Services. By visiting, interacting with, or using the Services you agree to be "
        "bound by these Terms of Service and the Privacy Policy. You represent that you are "
        "at least the age of majority in your state or province of residence to use the "
        "Services.",
    ),
]


def build_eval_store(embedder: LocalEmbedder) -> VectorStore:
    """Builds the VectorStore the 30 Eval Pairs below are written against."""
    store = VectorStore()
    for product_id, title, description in _PRODUCTS:
        text = f"{title}\n{description}"
        store.add(StoreEntry(id=product_id, kind="product", text=text, embedding=embedder.embed(text)))
    for policy_type, body in _POLICIES:
        store.add(StoreEntry(id=policy_type, kind="policy", text=body, embedding=embedder.embed(body)))
    return store


EVAL_PAIRS: list[EvalPair] = [
    # --- Product: grounded answers about the snowboard/gift-card catalog ---
    EvalPair(
        id="product-gift-card",
        category="product",
        question="Do you sell gift cards?",
        expected_answer="Yes, we sell a Gift Card that can be used in the store.",
    ),
    EvalPair(
        id="product-complete-snowboard",
        category="product",
        question="Tell me about The Complete Snowboard.",
        expected_answer=(
            "The Complete Snowboard is described as a premium, awesome snowboard - our "
            "flagship, full-featured board."
        ),
    ),
    EvalPair(
        id="product-minimal-snowboard",
        category="product",
        question="Do you have a Minimal Snowboard available?",
        expected_answer="Yes, The Minimal Snowboard is one of the snowboards we carry.",
    ),
    EvalPair(
        id="product-draft-snowboard",
        category="product",
        question="Is the Draft Snowboard available to purchase?",
        expected_answer="Yes, The Draft Snowboard is listed in our catalog.",
    ),
    EvalPair(
        id="product-hidden-snowboard",
        category="product",
        question="Do you sell the Hidden Snowboard?",
        expected_answer="Yes, The Hidden Snowboard is one of our products.",
    ),
    EvalPair(
        id="product-archived-snowboard",
        category="product",
        question="Can I find the Archived Snowboard in your catalog?",
        expected_answer="Yes, The Archived Snowboard is one of our products.",
    ),
    EvalPair(
        id="product-collection-hydrogen",
        category="product",
        question="Do you carry the Collection Snowboard: Hydrogen?",
        expected_answer="Yes, The Collection Snowboard: Hydrogen is one of our snowboards.",
    ),
    EvalPair(
        id="product-collection-oxygen",
        category="product",
        question="Do you carry the Collection Snowboard: Oxygen?",
        expected_answer="Yes, The Collection Snowboard: Oxygen is one of our snowboards.",
    ),
    EvalPair(
        id="product-collection-liquid",
        category="product",
        question="Do you carry the Collection Snowboard: Liquid?",
        expected_answer="Yes, The Collection Snowboard: Liquid is one of our snowboards.",
    ),
    EvalPair(
        id="product-compare-at-price",
        category="product",
        question="What is the Compare at Price Snowboard?",
        expected_answer="The Compare at Price Snowboard is one of the snowboards we sell.",
    ),
    EvalPair(
        id="product-ski-wax",
        category="product",
        question="Do you sell the Selling Plans Ski Wax?",
        expected_answer="Yes, we sell Selling Plans Ski Wax.",
    ),
    EvalPair(
        id="product-multi-location",
        category="product",
        question="Do you carry the Multi-location Snowboard?",
        expected_answer="Yes, The Multi-location Snowboard is one of our products.",
    ),
    EvalPair(
        id="product-3p-fulfilled",
        category="product",
        question="Is the 3p Fulfilled Snowboard something you sell?",
        expected_answer="Yes, The 3p Fulfilled Snowboard is one of our products.",
    ),
    EvalPair(
        id="product-videographer",
        category="product",
        question="Do you have the Videographer Snowboard in your lineup?",
        expected_answer="Yes, The Videographer Snowboard is one of our products.",
    ),
    # --- Policy: grounded answers covering all four ShopPolicy types ---
    EvalPair(
        id="policy-refund-eligibility",
        category="policy_refund",
        question="What is your return policy?",
        expected_answer=(
            "Return eligibility depends on the items in your order. Returned items must be "
            "unworn or unused, with tags, in their original packaging, and you should "
            "contact us to start a return."
        ),
    ),
    EvalPair(
        id="policy-refund-return-shipping",
        category="policy_refund",
        question="Who pays for return shipping if I change my mind about an item?",
        expected_answer=(
            "Unless stated otherwise, you are responsible for return shipping costs on "
            "change-of-mind returns."
        ),
    ),
    EvalPair(
        id="policy-privacy-collection",
        category="policy_privacy",
        question="What personal information do you collect from customers?",
        expected_answer=(
            "We collect or process personal information that identifies or can reasonably "
            "be linked to you, such as information gathered when you visit, use, or make a "
            "purchase through the Services."
        ),
    ),
    EvalPair(
        id="policy-privacy-operator",
        category="policy_privacy",
        question="Who operates this store and provides the shopping service?",
        expected_answer="shop-assistant-demo operates the store, powered by Shopify, to provide the Services.",
    ),
    EvalPair(
        id="policy-shipping-processing-time",
        category="policy_shipping",
        question="How long does it take to process a purchase before it ships?",
        expected_answer=(
            "Orders are processed within 1 business day, excluding holidays; orders placed "
            "after noon or on weekends/holidays may begin processing the next business day."
        ),
    ),
    EvalPair(
        id="policy-shipping-canada-fees",
        category="policy_shipping",
        question="Are there extra fees for shipping to Canada?",
        expected_answer=(
            "Orders shipped to Canada may be subject to GST, HST, PST, QST, RST, customs "
            "duties, import taxes, and carrier brokerage or handling fees."
        ),
    ),
    EvalPair(
        id="policy-terms-agreement",
        category="policy_terms_of_service",
        question="What am I agreeing to by using your site?",
        expected_answer=(
            "By visiting, interacting with, or using the Services, you agree to be bound by "
            "the Terms of Service and the Privacy Policy."
        ),
    ),
    EvalPair(
        id="policy-terms-age",
        category="policy_terms_of_service",
        question="Is there a minimum age requirement to use your store?",
        expected_answer=(
            "You must be at least the age of majority in your state or province of "
            "residence to use the Services."
        ),
    ),
    # --- Deflected Topic: all four out-of-scope categories ---
    EvalPair(
        id="deflected-orders-status",
        category="deflected_orders",
        question="Where is my order #1234?",
        expected_answer="I'm not able to help with that here, but our support team can.",
    ),
    EvalPair(
        id="deflected-orders-tracking",
        category="deflected_orders",
        question="Can you track my recent order for me?",
        expected_answer="I'm not able to help with that here, but our support team can.",
    ),
    EvalPair(
        id="deflected-payments-declined",
        category="deflected_payments",
        question="I think my payment failed, what happened?",
        expected_answer="I'm not able to help with that here, but our support team can.",
    ),
    EvalPair(
        id="deflected-payments-method",
        category="deflected_payments",
        question="Is there a problem with my payment method on file?",
        expected_answer="I'm not able to help with that here, but our support team can.",
    ),
    EvalPair(
        id="deflected-stock-out-of-stock-snowboard",
        category="deflected_stock",
        question="Is the Out of Stock Snowboard back in stock?",
        expected_answer="I'm not able to help with that here, but our support team can.",
    ),
    EvalPair(
        id="deflected-stock-inventory-not-tracked-snowboard",
        category="deflected_stock",
        question="Do you track inventory for the Inventory Not Tracked Snowboard?",
        expected_answer="I'm not able to help with that here, but our support team can.",
    ),
    EvalPair(
        id="deflected-discount-code-not-working",
        category="deflected_discount",
        question="Why isn't my discount code working?",
        expected_answer="I'm not able to help with that here, but our support team can.",
    ),
    EvalPair(
        id="deflected-discount-coupon",
        category="deflected_discount",
        question="Do you have any coupon codes for snowboards?",
        expected_answer="I'm not able to help with that here, but our support team can.",
    ),
]
