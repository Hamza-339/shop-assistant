export interface Citation {
  id: string;
  kind: string;
  handle: string;
}

export interface ApiResponse {
  answer: string;
  citations: Citation[];
  deflected: boolean;
}

export interface RenderedMessage {
  text: string;
  citations: Citation[];
}

export const FALLBACK_MESSAGE = "I'm not able to help with that here, but our support team can.";

export const GENERIC_ERROR_MESSAGE = "Something went wrong. Please try again.";
export const RATE_LIMIT_MESSAGE = "We're a little busy right now — please try again in a moment.";

export const WELCOME_MESSAGE = "Hi! I'm your AI shopping assistant. Ask me about our products or policies.";

export const SUGGESTION_CHIPS = [
  "What's your return policy?",
  "How long does shipping take?",
  "How can I contact support?",
] as const;

export function parseChips(raw: string | null | undefined): readonly string[] {
  if (!raw) {
    return SUGGESTION_CHIPS;
  }

  const chips = raw
    .split("|")
    .map((chip) => chip.trim())
    .filter((chip) => chip.length > 0);

  if (chips.length === 0) {
    return SUGGESTION_CHIPS;
  }

  return chips.slice(0, 3);
}

export interface AskFailure {
  status?: number;
  error?: unknown;
}

export function mapErrorToMessage(failure: AskFailure): string {
  return failure.status === 429 ? RATE_LIMIT_MESSAGE : GENERIC_ERROR_MESSAGE;
}

export function toRenderedMessage(response: ApiResponse): RenderedMessage {
  if (response.deflected) {
    return { text: FALLBACK_MESSAGE, citations: [] };
  }
  return { text: response.answer, citations: response.citations };
}

export function formatCitation(citation: Citation): string {
  const kindLabel = citation.kind.charAt(0).toUpperCase() + citation.kind.slice(1);
  return `${kindLabel} · ${citation.id}`;
}

export function citationUrl(citation: Citation): string {
  return citation.kind === "policy" ? `/policies/${citation.handle}` : `/products/${citation.handle}`;
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function isSafeUrl(url: string): boolean {
  if (url.startsWith("//")) {
    return false;
  }
  return /^(https?:\/\/|\/|#)/i.test(url) || !/^[a-z][a-z0-9+.-]*:/i.test(url);
}

function renderInline(text: string): string {
  let result = text.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  result = result.replace(/\[([^\]]*)\]\(((?:[^()]|\([^()]*\))*)\)/g, (match, label: string, url: string) => {
    return isSafeUrl(url) ? `<a href="${url}">${label}</a>` : label;
  });
  return result;
}

function renderListBlock(lines: string[]): string {
  const ordered = /^\d+\.\s/.test(lines[0]);
  const tag = ordered ? "ol" : "ul";
  const items = lines
    .map((line) => line.replace(ordered ? /^\d+\.\s/ : /^-\s/, ""))
    .map((item) => `<li>${renderInline(item)}</li>`)
    .join("");
  return `<${tag}>${items}</${tag}>`;
}

export function renderMarkdown(input: string): string {
  const escaped = escapeHtml(input);
  const blocks = escaped.split(/\n{2,}/);

  const html = blocks
    .filter((block) => block.trim().length > 0)
    .map((block) => {
      const lines = block.split("\n");

      const headingMatch = /^(#{1,3})\s+(.*)$/.exec(lines[0]);
      if (headingMatch && lines.length === 1) {
        const level = headingMatch[1].length;
        return `<h${level}>${renderInline(headingMatch[2])}</h${level}>`;
      }

      if (lines.every((line) => /^-\s/.test(line))) {
        return renderListBlock(lines);
      }

      if (lines.every((line) => /^\d+\.\s/.test(line))) {
        return renderListBlock(lines);
      }

      return `<p>${lines.map(renderInline).join("<br>")}</p>`;
    })
    .join("");

  return html;
}
