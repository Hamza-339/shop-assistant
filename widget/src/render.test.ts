import { describe, expect, it } from "vitest";

import { FALLBACK_MESSAGE, toRenderedMessage } from "./render.js";

describe("toRenderedMessage", () => {
  it("passes through the answer and citations for a grounded response", () => {
    const rendered = toRenderedMessage({
      answer: "It's a breathable cotton t-shirt.",
      citations: [{ id: "gid://shopify/Product/1", kind: "product" }],
      deflected: false,
    });

    expect(rendered).toEqual({
      text: "It's a breathable cotton t-shirt.",
      citations: [{ id: "gid://shopify/Product/1", kind: "product" }],
    });
  });

  it("overrides a deflected response with the fixed fallback message and drops citations", () => {
    const rendered = toRenderedMessage({
      answer: "fabricated answer text that should never be shown",
      citations: [{ id: "gid://shopify/Product/1", kind: "product" }],
      deflected: true,
    });

    expect(rendered).toEqual({
      text: FALLBACK_MESSAGE,
      citations: [],
    });
  });
});
