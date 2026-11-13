import { describe, expect, it } from "vitest";

import {
  citationUrl,
  FALLBACK_MESSAGE,
  formatCitation,
  GENERIC_ERROR_MESSAGE,
  mapErrorToMessage,
  parseChips,
  RATE_LIMIT_MESSAGE,
  renderMarkdown,
  SUGGESTION_CHIPS,
  toRenderedMessage,
  WELCOME_MESSAGE,
} from "./render.js";

describe("toRenderedMessage", () => {
  it("passes through the answer and citations for a grounded response", () => {
    const rendered = toRenderedMessage({
      answer: "It's a breathable cotton t-shirt.",
      citations: [{ id: "gid://shopify/Product/1", kind: "product", handle: "classic-cotton-t-shirt" }],
      deflected: false,
    });

    expect(rendered).toEqual({
      text: "It's a breathable cotton t-shirt.",
      citations: [{ id: "gid://shopify/Product/1", kind: "product", handle: "classic-cotton-t-shirt" }],
    });
  });

  it("overrides a deflected response with the fixed fallback message and drops citations", () => {
    const rendered = toRenderedMessage({
      answer: "fabricated answer text that should never be shown",
      citations: [{ id: "gid://shopify/Product/1", kind: "product", handle: "classic-cotton-t-shirt" }],
      deflected: true,
    });

    expect(rendered).toEqual({
      text: FALLBACK_MESSAGE,
      citations: [],
    });
  });
});

describe("formatCitation", () => {
  it("labels a product citation with its kind and id", () => {
    expect(
      formatCitation({ id: "gid://shopify/Product/1", kind: "product", handle: "classic-cotton-t-shirt" }),
    ).toBe("Product · gid://shopify/Product/1");
  });

  it("labels a policy citation with its kind and id", () => {
    expect(formatCitation({ id: "refund", kind: "policy", handle: "refund" })).toBe("Policy · refund");
  });
});

describe("renderMarkdown", () => {
  it("wraps plain text with no markdown in a paragraph", () => {
    expect(renderMarkdown("It's a breathable cotton t-shirt.")).toBe(
      "<p>It&#39;s a breathable cotton t-shirt.</p>",
    );
  });

  it("renders **bold** as <strong>", () => {
    expect(renderMarkdown("This is **important**.")).toBe("<p>This is <strong>important</strong>.</p>");
  });

  it("renders a single # heading as <h1>", () => {
    expect(renderMarkdown("# Shipping")).toBe("<h1>Shipping</h1>");
  });

  it("renders a ## heading as <h2>", () => {
    expect(renderMarkdown("## Shipping")).toBe("<h2>Shipping</h2>");
  });

  it("renders a ### heading as <h3>", () => {
    expect(renderMarkdown("### Shipping")).toBe("<h3>Shipping</h3>");
  });

  it("renders contiguous '- ' lines as an unordered list", () => {
    expect(renderMarkdown("- Small\n- Medium\n- Large")).toBe("<ul><li>Small</li><li>Medium</li><li>Large</li></ul>");
  });

  it("renders contiguous numbered lines as an ordered list", () => {
    expect(renderMarkdown("1. Add to cart\n2. Checkout")).toBe("<ol><li>Add to cart</li><li>Checkout</li></ol>");
  });

  it("renders a markdown link with a safe https url as a live link", () => {
    expect(renderMarkdown("See [our policy](https://example.com/policy).")).toBe(
      '<p>See <a href="https://example.com/policy">our policy</a>.</p>',
    );
  });

  it("renders a markdown link with a relative url as a live link", () => {
    expect(renderMarkdown("See [our policy](/policies/refund).")).toBe(
      '<p>See <a href="/policies/refund">our policy</a>.</p>',
    );
  });

  it("neutralizes a javascript: link url, rendering only the label as text", () => {
    expect(renderMarkdown("[click me](javascript:alert(1))")).toBe("<p>click me</p>");
  });

  it("neutralizes a protocol-relative link url, rendering only the label as text", () => {
    expect(renderMarkdown("[click me](//evil.com/phish)")).toBe("<p>click me</p>");
  });

  it("escapes raw HTML in the input so it cannot execute", () => {
    expect(renderMarkdown('<img src=x onerror=alert(1)>')).toBe(
      "<p>&lt;img src=x onerror=alert(1)&gt;</p>",
    );
  });

  it("separates blank-line blocks into paragraphs and single newlines into line breaks", () => {
    expect(renderMarkdown("First line\nSecond line\n\nSecond paragraph")).toBe(
      "<p>First line<br>Second line</p><p>Second paragraph</p>",
    );
  });
});

describe("mapErrorToMessage", () => {
  it("maps a 429 status to the distinct rate-limit message", () => {
    expect(mapErrorToMessage({ status: 429 })).toBe(RATE_LIMIT_MESSAGE);
  });

  it("maps a non-429 HTTP status to the generic friendly message", () => {
    expect(mapErrorToMessage({ status: 500 })).toBe(GENERIC_ERROR_MESSAGE);
  });

  it("maps a thrown error with no status to the generic friendly message", () => {
    expect(mapErrorToMessage({ error: new Error("network down") })).toBe(GENERIC_ERROR_MESSAGE);
  });
});

describe("WELCOME_MESSAGE and SUGGESTION_CHIPS", () => {
  it("exports a non-empty welcome message", () => {
    expect(WELCOME_MESSAGE.length).toBeGreaterThan(0);
  });

  it("exports exactly three suggestion chip labels", () => {
    expect(SUGGESTION_CHIPS).toHaveLength(3);
  });
});

describe("parseChips", () => {
  it("falls back to the default chips when given undefined", () => {
    expect(parseChips(undefined)).toEqual(SUGGESTION_CHIPS);
  });

  it("falls back to the default chips when given an empty string", () => {
    expect(parseChips("")).toEqual(SUGGESTION_CHIPS);
  });

  it("falls back to the default chips when given only whitespace and separators", () => {
    expect(parseChips("  | | ")).toEqual(SUGGESTION_CHIPS);
  });

  it("splits on pipes and trims whitespace from each question", () => {
    expect(parseChips(" Do you ship internationally? | What's your return policy? ")).toEqual([
      "Do you ship internationally?",
      "What's your return policy?",
    ]);
  });

  it("caps the result at a maximum of three chips", () => {
    expect(parseChips("One?|Two?|Three?|Four?")).toEqual(["One?", "Two?", "Three?"]);
  });
});

describe("citationUrl", () => {
  it("links a product citation to /products/<handle>", () => {
    expect(
      citationUrl({ id: "gid://shopify/Product/1", kind: "product", handle: "classic-cotton-t-shirt" }),
    ).toBe("/products/classic-cotton-t-shirt");
  });

  it("links a policy citation to /policies/<type>", () => {
    expect(citationUrl({ id: "refund", kind: "policy", handle: "refund" })).toBe("/policies/refund");
  });
});
